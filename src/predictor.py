from typing import Any, Dict, Optional

import pandas as pd


def create_mock_fixtures() -> pd.DataFrame:
    """
    Creates a sample DataFrame of fixtures for testing purposes.
    This simulates the output of the data processing steps, including
    momentum columns which must be present for the predictor to work.

    Returns:
        A pandas DataFrame containing mock fixture data.
    """
    print("--- Using MOCK Data ---")
    data = {
        'Date': ['2025-11-15', '2025-11-15', '2025-11-16', '2025-11-16'],
        'Home': ['Man City', 'Everton', 'Arsenal', 'Man United'],
        'Away': ['Bournemouth', 'Liverpool', 'Fulham', 'West Ham'],
        'HomeWin %': [85.0, 30.2, 45.5, 42.1],
        'Draw %': [10.0, 33.1, 28.0, 29.9],
        'AwayWin %': [5.0, 36.7, 26.5, 28.0],
        # Add mock momentum data, essential for the logic below
        'Home_Momentum': [50.0, -10.0, 20.0, 0.0],
        'Away_Momentum': [-20.0, 30.0, 5.0, -5.0],
        'Momentum_Diff': [70.0, -40.0, 15.0, 5.0]
    }
    return pd.DataFrame(data)


def find_max_momentum_match(df: pd.DataFrame) -> Optional[pd.Series]:
    """
    Identifies the fixture with the largest absolute Momentum_Diff,
    indicating the biggest form vs. slump mismatch. This is used for
    highlighting high-volatility betting opportunities.

    Args:
        df: DataFrame containing fixture data, including the 'Momentum_Diff' column.

    Returns:
        The pandas Series representing the row of the match with the highest
        absolute momentum differential, or None if the DataFrame is empty.
    """
    if df.empty:
        return None

    # Find the index of the row with the maximum absolute Momentum_Diff
    max_diff_index = df['Momentum_Diff'].abs().idxmax()

    # Return the entire row as a Series
    return df.loc[max_diff_index]


def find_most_likely_outcome(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Finds the strongest predicted outcome across all fixtures by calculating
    a 'Confidence Score' that weights raw Elo probability with recent momentum.
    The score formula is designed to reward outcomes supported by positive momentum
    and penalize draws where momentum heavily favors one side.

    Args:
        df: DataFrame containing processed fixtures, probabilities, and momentum data.

    Returns:
        A dictionary representing the single predicted outcome with the highest
        Confidence Score, or None if the DataFrame is empty.
    """
    if df.empty:
        return None

    # Melt the data to compare all 1X2 outcomes in one column
    df_long = pd.melt(
        df,
        id_vars=['Date', 'Home', 'Away', 'Home_Momentum', 'Away_Momentum', 'Momentum_Diff'],
        value_vars=['HomeWin %', 'Draw %', 'AwayWin %'],
        var_name='Outcome',
        value_name='Probability'
    )

    # --- Momentum-Weighted Ranking ---
    def get_weighted_momentum(row: pd.Series) -> float:
        """Calculates the Confidence Score for a single outcome row."""
        momentum = row['Momentum_Diff']
        outcome = row['Outcome']
        probability = row['Probability']

        # Home Win: Rewards positive Momentum_Diff
        if outcome == 'HomeWin %':
            return probability + (momentum / 10)

        # Away Win: Rewards negative Momentum_Diff (uses abs)
        elif outcome == 'AwayWin %':
            return probability + (abs(momentum) / 10)

        # Draw: Penalizes divergence from zero momentum
        else:  # Draw %
            return probability - (abs(momentum) / 5)

    df_long['Confidence_Score'] = df_long.apply(get_weighted_momentum, axis=1)

    # Find the entry with the highest Confidence Score
    strongest_prediction = df_long.loc[df_long['Confidence_Score'].idxmax()]

    return strongest_prediction.to_dict()


def main():
    """
    Main execution function to test the prediction logic with mock data.
    """
    # 1. Create mock data for testing
    mock_df = create_mock_fixtures()

    # 2. Find the most confident prediction
    confident_prediction = find_most_likely_outcome(mock_df)

    # 3. Find the most momentum-driven match
    momentum_match = find_max_momentum_match(mock_df)

    print("\n--- TEST RESULTS ---")
    if confident_prediction:
        print("\nMost Confident Prediction (Weighted Score):")
        print(pd.Series(confident_prediction))

    if momentum_match is not None:
        print("\nMatch with Max Absolute Momentum Differential:")
        print(momentum_match)


if __name__ == "__main__":
    main()