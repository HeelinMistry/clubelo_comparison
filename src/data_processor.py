import datetime
import io

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


def get_momentum(club_name: str, lookback: int = 5) -> float:
    """
    Calculates the Elo change (Momentum) over the last 'lookback' actual games
    by comparing the current Elo to the Elo before the Nth game back.
    Future Elo projections are filtered out.

    Args:
        club_name: The name of the club to fetch history for.
        lookback: The number of games to look back to calculate momentum (default is 5).

    Returns:
        The total Elo change over the lookback period, rounded to 2 decimal places.
        Returns 0.0 if data is unavailable or an error occurs.
    """
    history_csv = fetch_club_history(club_name)
    if not history_csv:
        return 0.0

    try:
        hist_df = pd.read_csv(io.StringIO(history_csv))
        hist_df['Elo'] = pd.to_numeric(hist_df['Elo'], errors='coerce')
        hist_df.dropna(subset=['Elo'], inplace=True)
        hist_df['From'] = pd.to_datetime(hist_df['From'])
        hist_df = hist_df.sort_values(by='From').reset_index(drop=True)

        # Filter out future Elo projections
        current_date = pd.to_datetime(datetime.datetime.now().date())
        hist_df = hist_df[hist_df['From'] <= current_date].copy()

        if hist_df.empty:
            return 0.0

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
        print(f"Error calculating momentum for {club_name}: {e}")
        return 0.0


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