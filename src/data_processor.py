from io import StringIO  # Required to read a string as if it were a file

import pandas as pd

from .api_client import fetch_all_fixtures


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
    # df = df[df['Country'] == 'ESP'].copy()

    if df.empty:
        print("No English fixtures found in the raw data.")
        return pd.DataFrame()

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
    relevant_columns = ['Date', 'Home', 'Away', 'HomeWin %', 'Draw %', 'AwayWin %']
    df_clean = df[relevant_columns]

    # Sort by date to see the next fixtures first
    df_clean = df_clean.sort_values(by='Date').reset_index(drop=True)

    return df_clean


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