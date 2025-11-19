import sys

from src.api_client import fetch_all_fixtures
from src.data_processor import process_fixtures
from src.predictor import find_most_likely_outcome

# Add the 'src' folder to the Python path so we can import our modules
sys.path.append('src')

def run_analysis():
    # ... (Step 1: Fetch Data) ...
    # ... (Step 2: Process Data and calculate all columns including Momentum/Form) ...
    raw_csv_data = fetch_all_fixtures()
    fixtures_df = process_fixtures(raw_csv_data)

    if fixtures_df.empty:
        print("No upcoming Premier League fixtures found. Exiting.")
        return

    print("\n--- ⚽ Upcoming Premier League Fixtures & Momentum ---")
    # Print the full table here if desired
    print(fixtures_df.to_string(index=False, float_format="%.1f"))

    # --- Step 3: Find Key Metrics for Summary ---
    print("\n[Step 3] Analyzing fixtures for summary insights...")

    # A. Most Confident Prediction (Maximized Confidence Score)
    most_likely = find_most_likely_outcome(fixtures_df)

    # B. Biggest Momentum Differential (Highest absolute value of Momentum_Diff)
    # Use idxmax on the absolute value to find the biggest magnitude change
    biggest_diff_match = fixtures_df.loc[fixtures_df['Momentum_Diff'].abs().idxmax()]

    # C. Strongest Home Form (Maximized Home_Form_Index)
    # Assuming Home_Form_Index is a calculated column
    best_home_form = fixtures_df.loc[fixtures_df['Home_Momentum'].idxmax()]

    # D. Strongest Away Form (Maximized Away_Momentum)
    best_away_form = fixtures_df.loc[fixtures_df['Away_Momentum'].idxmax()]

    # --- Step 4: Print Comprehensive Summary ---
    print_analysis_summary(
        most_likely,
        biggest_diff_match,
        best_home_form,
        best_away_form
    )

# --- New Function to Handle Printing ---
def print_analysis_summary(most_likely, biggest_diff_match, best_home_form, best_away_form):
    print("\n" + "=" * 70)
    print("             ⚽ WEEKLY FIXTURE INSIGHTS ⚽")
    print("=" * 70)

    # --- 1. MOST CONFIDENT PREDICTION ---
    print("\n## 🥇 MOST CONFIDENT PREDICTION (Highest Weighted Score)")
    outcome = most_likely['Outcome']

    if outcome == 'HomeWin %':
        result_str = f"Home WIN: {most_likely['Home']}"
        momentum_for_favored = most_likely['Home_Momentum']
    elif outcome == 'AwayWin %':
        result_str = f"Away WIN: {most_likely['Away']}"
        momentum_for_favored = most_likely['Away_Momentum']
    else:  # Draw
        result_str = "DRAW (Neutral Momentum Favored)"
        momentum_for_favored = most_likely['Momentum_Diff']

    print(f"Fixture:       **{most_likely['Home']}** vs. **{most_likely['Away']}**")
    print(f"Prediction:    {result_str}")
    print(f"Probability:   {most_likely['Probability']:.1f}% (Raw Elo)")
    print(f"Form Advantage: {momentum_for_favored:+.2f} Elo")
    print(f"Confidence:    {most_likely['Confidence_Score']:.2f} (Maximized)")
    print("-" * 30)

    # --- 2. BIGGEST MOMENTUM DIFFERENTIAL ---
    print("\n## ⚠️ BIGGEST MOMENTUM OPPORTUNITY (Form vs. Slump)")
    diff = biggest_diff_match['Momentum_Diff']

    print(f"Fixture:       {biggest_diff_match['Home']} vs. {biggest_diff_match['Away']}")
    print(f"Momentum Diff: **{diff:+.1f} Elo Points**")

    if diff > 0:
        print(
            f"Insight:       Strong form advantage for **{biggest_diff_match['Home']}** (Home Momentum: {biggest_diff_match['Home_Momentum']:.1f} vs. Away Momentum: {biggest_diff_match['Away_Momentum']:.1f}).")
    else:
        print(
            f"Insight:       Strong form advantage for **{biggest_diff_match['Away']}** (Away Momentum: {biggest_diff_match['Away_Momentum']:.1f} vs. Home Momentum: {biggest_diff_match['Home_Momentum']:.1f}).")
    print("-" * 30)

    # --- 3. TEAM FORM SPOTLIGHTS ---
    print("\n## 📈 TEAM FORM SPOTLIGHTS")

    # BEST HOME FORM
    print(f"**Best Recent Home Form:**")
    print(f"Team:          **{best_home_form['Home']}** (Momentum: {best_home_form['Home_Momentum']:+.1f} Elo Gain)")
    print(f"Upcoming Match: Home vs. {best_home_form['Away']}")

    # BEST AWAY FORM
    print(f"\n**Best Recent Away Form:**")
    print(f"Team:          **{best_away_form['Away']}** (Momentum: {best_away_form['Away_Momentum']:+.1f} Elo Gain)")
    print(f"Upcoming Match: {best_away_form['Home']} vs. Away")
    print("-" * 30)

# Standard Python entry point
if __name__ == "__main__":
    run_analysis()