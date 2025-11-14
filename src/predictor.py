from typing import Any

import pandas as pd


def create_mock_fixtures() -> pd.DataFrame:
    """
    Creates a sample DataFrame of fixtures for testing purposes.
    This simulates the output of data_processor.py.
    """
    print("--- Using MOCK Data ---")
    data = {
        'Date': ['2025-11-15', '2025-11-15', '2025-11-16', '2025-11-16'],
        'Home': ['Man City', 'Everton', 'Arsenal', 'Man United'],
        'Away': ['Bournemouth', 'Liverpool', 'Fulham', 'West Ham'],
        'HomeWin %': [85.0, 30.2, 45.5, 42.1],
        'Draw %': [10.0, 33.1, 28.0, 29.9],
        'AwayWin %': [5.0, 36.7, 26.5, 28.0]
    }
    return pd.DataFrame(data)


def find_most_likely_outcome(fixtures_df: pd.DataFrame) -> Any | None:
    """
    Analyzes a DataFrame of fixtures and probabilities to find the
    single most confident prediction (highest probability).

    Args:
        fixtures_df: The DataFrame from data_processor.py.

    Returns:
        A pandas Series containing the details of the most likely match outcome.
        Returns None if the DataFrame is empty.
    """
    if fixtures_df.empty:
        return None

    # We need to find the highest probability value across three different
    # columns. The easiest way is to "melt" the DataFrame.
    # This turns the 3 probability columns into one 'Outcome' column
    # and one 'Probability' column, making it easy to find the max.

    df_melted = fixtures_df.melt(
        id_vars=['Date', 'Home', 'Away'],
        value_vars=['HomeWin %', 'Draw %', 'AwayWin %'],
        var_name='Outcome',
        value_name='Probability'
    )

    # Find the row with the highest 'Probability'
    most_likely_series = df_melted.loc[df_melted['Probability'].idxmax()]

    return most_likely_series


if __name__ == "__main__":
    # 1. Create mock data for testing
    mock_data = {
        'Date': ['2025-11-15'],
        'Home': ['Man City'],
        'Away': ['Bournemouth'],
        'HomeWin %': [85.0], 'Draw %': [10.0], 'AwayWin %': [5.0]
    }
    mock_df = pd.DataFrame(mock_data)

    # 2. Create an instance of the Predictor
    predictor = find_most_likely_outcome(mock_df)

    # 3. Get the formatted result
    print(predictor)