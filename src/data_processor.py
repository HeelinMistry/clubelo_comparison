import datetime
from io import StringIO

import pandas as pd

from .api_client import fetch_all_fixtures, fetch_club_history


def process_fixtures(csv_data: str) -> pd.DataFrame:
    """
    Converts the raw fixtures CSV string into a clean, filtered DataFrame
    containing only Premier League fixtures and calculated 1X2 probabilities.

    Args:
        csv_data: The raw CSV string from the API.

    Returns:
        A pandas DataFrame with upcoming Premier League fixtures.
    """
    if not csv_data:
        print("No data to process.")
        return pd.DataFrame()  # Return an empty DataFrame

    # Use StringIO to treat the CSV string as a file
    data_file = StringIO(csv_data)

    # Read the CSV data into a pandas DataFrame
    df = pd.read_csv(data_file)

    # --- Data Filtering ---
    # Filter 1: Keep only English ('ENG') league fixtures
    df = df[df['Country'] == 'ENG'].copy()

    if df.empty:
        print("No English fixtures found in the raw data.")
        return pd.DataFrame()

    df['Home_Momentum'] = df['Home'].apply(get_momentum)
    df['Away_Momentum'] = df['Away'].apply(get_momentum)
    df['Momentum_Diff'] = df['Home_Momentum'] - df['Away_Momentum']

    # --- Probability Calculation (The New Logic) ---
    # Define the columns for each outcome based on the API docs
    away_win_cols = ['GD<-5', 'GD=-5', 'GD=-4', 'GD=-3', 'GD=-2', 'GD=-1']
    draw_cols = ['GD=0']
    home_win_cols = ['GD=1', 'GD=2', 'GD=3', 'GD=4', 'GD=5', 'GD>5']

    # Sum the probabilities for each outcome (axis=1 sums across columns)
    df['AwayWin %'] = df[away_win_cols].sum(axis=1)
    df['Draw %'] = df[draw_cols].sum(axis=1)
    df['HomeWin %'] = df[home_win_cols].sum(axis=1)

    # Convert from 0.0-1.0 scale to 0-100 scale and round
    df['HomeWin %'] = (df['HomeWin %'] * 100).round(1)
    df['Draw %'] = (df['Draw %'] * 100).round(1)
    df['AwayWin %'] = (df['AwayWin %'] * 100).round(1)

    # --- Data Cleaning ---
    # Select only the columns we care about
    relevant_columns = ['Date', 'Home', 'Away', 'HomeWin %', 'Draw %', 'AwayWin %', 'Home_Momentum', 'Away_Momentum', 'Momentum_Diff']
    df_clean = df[relevant_columns]

    # Sort by date to see the next fixtures first
    df_clean = df_clean.sort_values(by='Date').reset_index(drop=True)

    return df_clean


def get_momentum(club_name: str, lookback: int = 5) -> float:
    """
    Calculates the Elo change (Momentum) over the last 'lookback' ACTUAL games.
    Filters future projections using the current date.
    """
    history_csv = fetch_club_history(club_name)
    if not history_csv:
        return 0.0

    try:
        # 1. Read data and prepare dates
        hist_df = pd.read_csv(StringIO(history_csv))
        hist_df['From'] = pd.to_datetime(hist_df['From'])
        hist_df = hist_df.sort_values(by='From').reset_index(drop=True)

        # --- NEW DATE FILTER ---
        # 2. Filter out future entries (Elo projections past the current date)
        current_date = pd.to_datetime(datetime.datetime.now().date())
        # Keep rows where the 'From' date is today or earlier
        hist_df = hist_df[hist_df['From'] <= current_date].copy()

        # Check if any history remains after filtering
        if hist_df.empty:
            return 0.0

        # 3. Identify "Games" (Rows where Elo changed compared to previous row)
        hist_df['Prev_Elo'] = hist_df['Elo'].shift(1)

        # Game rows are those where the Elo rating was updated
        # (This is the most reliable way to count games)
        game_rows = hist_df[hist_df['Elo'] != hist_df['Prev_Elo']].dropna()

        # 4. Get Current Elo
        # Always the latest available Elo after the date filter
        current_elo = hist_df['Elo'].iloc[-1]

        # 5. Get Starting Elo (from 'lookback' games ago)
        if len(game_rows) < lookback:
            # If fewer than N games, use the very first Elo score for momentum calculation
            start_elo = hist_df['Elo'].iloc[0]
        else:
            # Get the row of the Nth most recent game update
            # 'Prev_Elo' on that row gives the rating *before* that update
            target_game_row = game_rows.iloc[-lookback]
            start_elo = target_game_row['Prev_Elo']

        # 6. Calculate Momentum
        return round(current_elo - start_elo, 2)

    except Exception as e:
        print(f"Error calculating momentum for {club_name}: {e}")
        return 0.0


# This block allows us to test the file directly
if __name__ == "__main__":
    print("--- Running Data Processor Test (with GD logic) ---")

    # 1. Fetch raw data
    raw_fixture_data = fetch_all_fixtures()

    if raw_fixture_data:
        # 2. Process the data
        pl_fixtures = process_fixtures(raw_fixture_data)

        if not pl_fixtures.empty:
            print("\n--- Upcoming Premier League Fixtures & Probabilities ---")
            print(pl_fixtures.to_string())  # .to_string() prints all rows
        else:
            print("\n--- No Premier League fixtures found to process. ---")
    else:
        print("\n--- Fixture data fetching failed. ---")
