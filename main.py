import sys

from src.api_client import fetch_all_fixtures, fetch_ratings_by_date
from src.data_processor import process_fixtures
from src.predictor import find_most_likely_outcome

# Add the 'src' folder to the Python path so we can import our modules
sys.path.append('src')

def run_analysis():
    """
    Executes the full data pipeline:
    1. Fetches raw fixture data.
    2. Processes data to find Premier League probabilities.
    3. Analyzes probabilities to find the most likely outcome.
    """
    print("--- Starting ELO Predictor Analysis ---")

    # 1. Fetch Data
    print("\n[Step 1] Fetching raw fixture data from Clubelo API...")
    raw_csv_data = fetch_all_fixtures()

    if not raw_csv_data:
        print("Failed to fetch data. Exiting.")
        return

    # 2. Process Data
    print("[Step 2] Processing data and calculating 1X2 probabilities...")
    fixtures_df = process_fixtures(raw_csv_data)

    if fixtures_df.empty:
        print("No upcoming Premier League fixtures found. Exiting.")
        return

    print("\n--- ⚽ Upcoming Premier League Fixtures ---")
    print(fixtures_df.to_string())

    # 3. Find Most Likely Outcome
    print("\n[Step 3] Analyzing fixtures for the most likely outcome...")
    most_likely = find_most_likely_outcome(fixtures_df)

    if most_likely is not None:
        print("\n" + "=" * 40)
        print("   🎯 MOST LIKELY OUTCOME OF THE GAMEWEEK")
        print("=" * 40)

        # Custom formatting for the output
        if most_likely['Outcome'] == 'HomeWin %':
            result_str = f"{most_likely['Home']} to WIN"
        elif most_likely['Outcome'] == 'AwayWin %':
            result_str = f"{most_likely['Away']} to WIN"
        else:  # Draw
            result_str = "DRAW"

        print(f"Match:      {most_likely['Home']} vs. {most_likely['Away']}")
        print(f"Prediction: {result_str}")
        print(f"Confidence: {most_likely['Probability']}%")
        print("=" * 40)
    else:
        # This should be covered by the .empty check, but good to have
        print("\n--- No results to analyze. ---")


# Standard Python entry point
if __name__ == "__main__":
    run_analysis()