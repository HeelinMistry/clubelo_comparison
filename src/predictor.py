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


def find_most_likely_outcome(df: pd.DataFrame) -> dict:
    """Finds the strongest outcome using Probability AND Momentum Difference."""

    # 1. Melt the data to easily compare all 1X2 outcomes in one column
    # This creates a long list of all HomeWin, Draw, and AwayWin probabilities
    df_long = pd.melt(
        df,
        id_vars=['Date', 'Home', 'Away', 'Home_Momentum', 'Away_Momentum', 'Momentum_Diff'],
        value_vars=['HomeWin %', 'Draw %', 'AwayWin %'],
        var_name='Outcome',
        value_name='Probability'
    )

    # 2. Filter for only the predicted outcome (i.e., Probability > 50% for Win/Loss)
    # Since Draw is a central tendency, we treat it separately.
    df_filtered = df_long.copy()

    # --- Momentum-Weighted Ranking ---
    # Create a single numerical score that incorporates both probability and momentum.
    # We'll use Probability as the primary measure, and Momentum as a tie-breaker,
    # or just use the largest positive or smallest negative Momentum_Diff.

    # Assign a Weight for the momentum based on the outcome
    def get_weighted_momentum(row):
        momentum = row['Momentum_Diff']
        outcome = row['Outcome']

        # Home Win: Momentum_Diff should be positive (Home - Away)
        if outcome == 'HomeWin %':
            return row['Probability'] + (momentum / 10)  # Add a bonus for positive momentum

        # Away Win: Momentum_Diff should be negative
        elif outcome == 'AwayWin %':
            # The momentum difference is negative, so we add the absolute value
            return row['Probability'] + (abs(momentum) / 10)

            # Draw: Momentum_Diff should be close to zero, so we penalize divergence
        else:  # Draw %
            # Penalize draws where momentum heavily favors one side
            return row['Probability'] - (abs(momentum) / 5)

    df_filtered['Confidence_Score'] = df_filtered.apply(get_weighted_momentum, axis=1)

    # 3. Find the entry with the highest Confidence Score
    # We still ensure the outcome is the most likely for that specific match.

    # Find the top predicted outcome across ALL fixtures based on the Confidence Score
    strongest_prediction = df_filtered.loc[df_filtered['Confidence_Score'].idxmax()]

    # Convert the result back to a standard dictionary format
    return strongest_prediction.to_dict()


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