import datetime
import io
from typing import Optional

import pandas as pd

from .api_client import fetch_all_fixtures, fetch_club_history


def filter_level_1(fixtures_df: pd.DataFrame, ratings_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters fixtures_df to include only matches where *both* the Home and
    Away teams are classified as Level 1 (top tier) in their respective countries.

    Args:
        fixtures_df: DataFrame of upcoming fixtures.
        ratings_df: DataFrame containing current Elo ratings and the 'Level' column.

    Returns:
        Filtered DataFrame containing only Level 1 league fixtures.
    """
    # Filter the ratings to include only Level 1 teams
    level_1_teams = ratings_df[ratings_df['Level'] == 1][['Club', 'Level']].copy()

    # Merge on Home team (only keep fixtures where the Home team is Level 1)
    merged_home = fixtures_df.merge(
        level_1_teams,
        left_on='Home',
        right_on='Club',
        how='inner'
    ).drop(columns=['Club', 'Level'])

    # Merge again on Away team (ensuring BOTH teams are Level 1)
    final_df = merged_home.merge(
        level_1_teams,
        left_on='Away',
        right_on='Club',
        how='inner'
    ).drop(columns=['Club', 'Level'])

    print(f"\n[Filter] Fixtures filtered: {len(fixtures_df)} -> {len(final_df)} (Level 1 only)")

    return final_df


def get_momentum(club_name: str, lookback: int = 5) -> Optional[float]:
    """
    Calculates the Elo change (Momentum) over the last 'lookback' actual games.

    Returns:
        float: The total Elo change, rounded to 2 decimal places.
        None: On critical network failure (to signal unreliability and trigger job retry).
        0.0: If data is available but insufficient (e.g., empty DataFrame, not enough games).
    """

    # --- 1. Network/Fetch Failure Check ---
    # Assume fetch_club_history is where network I/O happens and returns None
    # or an empty string/False on critical failure (like Read Timed Out).
    history_csv = fetch_club_history(club_name)

    # If the fetch failed critically (Network Error), return None to signal upstream failure
    if not history_csv:
        print(f"CRITICAL: Failed to fetch history for {club_name}. Signaling failure (None).")
        return None  # <-- CHANGE 1: Return None on hard network/fetch failure

    try:
        hist_df = pd.read_csv(io.StringIO(history_csv))
        hist_df['Elo'] = pd.to_numeric(hist_df['Elo'], errors='coerce')
        hist_df.dropna(subset=['Elo'], inplace=True)
        hist_df['From'] = pd.to_datetime(hist_df['From'])
        hist_df = hist_df.sort_values(by='From').reset_index(drop=True)

        # Filter out future Elo projections
        current_date = pd.to_datetime(datetime.datetime.now().date())
        hist_df = hist_df[hist_df['From'] <= current_date].copy()

        # --- 2. Insufficient Data Check ---
        # If data is available but insufficient (empty after filtering), return 0.0
        if hist_df.empty:
            print(f"Warning: No valid historical data for {club_name} after filtering.")
            return 0.0  # <-- Keep 0.0 for known non-critical data gaps

        # Identify actual games (where Elo changed)
        hist_df['Prev_Elo'] = hist_df['Elo'].shift(1)
        game_rows = hist_df[hist_df['Elo'] != hist_df['Prev_Elo']].dropna()

        current_elo = hist_df['Elo'].iloc[-1]

        if len(game_rows) < lookback:
            # Not enough games; use the very first available Elo
            start_elo = hist_df['Elo'].iloc[0]
        else:
            # Use the Elo from *before* the Nth most recent game update
            target_game_row = game_rows.iloc[-lookback]
            start_elo = target_game_row['Prev_Elo']

        return round(current_elo - start_elo, 2)

    except Exception as e:
        # --- 3. Parsing/Processing Failure Check ---
        # If CSV parsing or calculation fails, this is a soft error (data format issue),
        # so we still return 0.0, as it's not a recoverable network error.
        print(f"Error calculating momentum for {club_name} (Parsing/Processing): {e}")
        return 0.0  # <-- Keep 0.0 for calculation/data errors


MOMENTUM_FAILURE_THRESHOLD = 0.10

def process_fixtures(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts the raw fixtures DataFrame into a clean, calculated DataFrame
    by filtering for English teams, calculating 1X2 probabilities, and
    calculating momentum scores.

    Args:
        df: The raw DataFrame containing fixtures and Elo data (including GD columns).

    Returns:
        A pandas DataFrame with upcoming fixtures, probabilities, and momentum scores,
        sorted by date. Returns an empty DataFrame if no English fixtures are found.
    """
    # Filter 1: Keep only English ('ENG') league fixtures
    df = df[df['Country'] == 'ENG'].copy()

    if df.empty:
        print("No English fixtures found in the raw data.")
        return pd.DataFrame()

    # Calculate Momentum Scores
    if 'Home_Momentum' not in df.columns:
        print("Attempting to calculate momentum data...")
        # NOTE: The actual club history API calls happen inside get_momentum
        df['Home_Momentum'] = df['Home'].apply(get_momentum)
        df['Away_Momentum'] = df['Away'].apply(get_momentum)

    # Total failures (ensuring we don't double count if a club fails home and away)
    # A cleaner way is to just look at the total number of fixtures with *any* failure:
    total_fixtures = len(df)
    failed_fixtures = df.apply(lambda row: pd.isna(row['Home_Momentum']) or pd.isna(row['Away_Momentum']), axis=1).sum()

    # Calculate the percentage of fixtures where at least one team failed to get momentum
    failure_rate = failed_fixtures / total_fixtures

    if failure_rate > MOMENTUM_FAILURE_THRESHOLD:
        error_msg = (
            f"CRITICAL: Momentum data lookup failed for {failed_fixtures} of {total_fixtures} fixtures "
            f"({failure_rate:.1%}). Data is unreliable. Triggering job retry."
        )
        print(error_msg)
        # Raise an error to be caught by the main execution block
        raise ValueError(error_msg)

    # Replace remaining None values with 0.0 only after the failure check
    df['Home_Momentum'] = df['Home_Momentum'].fillna(0.0)
    df['Away_Momentum'] = df['Away_Momentum'].fillna(0.0)

    # This calculation runs whether the columns were calculated or mocked (pre-existing)
    df['Momentum_Diff'] = df['Home_Momentum'] - df['Away_Momentum']

    # Probability Calculation
    away_win_cols = ['GD<-5', 'GD=-5', 'GD=-4', 'GD=-3', 'GD=-2', 'GD=-1']
    draw_cols = ['GD=0']
    home_win_cols = ['GD=1', 'GD=2', 'GD=3', 'GD=4', 'GD=5', 'GD>5']

    df['AwayWin %'] = (df[away_win_cols].sum(axis=1) * 100).round(1)
    df['Draw %'] = (df[draw_cols].sum(axis=1) * 100).round(1)
    df['HomeWin %'] = (df[home_win_cols].sum(axis=1) * 100).round(1)

    # Data Cleaning and Sorting
    relevant_columns = [
        'Date', 'Home', 'Away', 'HomeWin %', 'Draw %', 'AwayWin %',
        'Home_Momentum', 'Away_Momentum', 'Momentum_Diff'
    ]

    df_clean = df[relevant_columns].sort_values(by='Date').reset_index(drop=True)

    return df_clean


def main():
    """
    Main execution function to fetch, process, and display upcoming Premier League fixtures.
    """
    print("--- Running Data Processor Test ---")

    raw_fixture_data = fetch_all_fixtures()

    if raw_fixture_data:
        try:
            # 1. Process the data (filters for ENG, calculates probabilities/momentum)
            fixtures_df = pd.read_csv(io.StringIO(raw_fixture_data))
            pl_fixtures = process_fixtures(fixtures_df)
        except Exception as e:
            print(f"An error occurred during fixture processing: {e}")
            return

        if not pl_fixtures.empty:
            print("\n--- Upcoming Premier League Fixtures & Probabilities ---")
            print(pl_fixtures.to_string())
        else:
            print("\n--- No Premier League fixtures found to process. ---")
    else:
        print("\n--- Fixture data fetching failed. ---")


if __name__ == "__main__":
    main()