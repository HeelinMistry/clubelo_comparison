import datetime
from io import StringIO
from typing import Tuple, Any, Dict

import pandas as pd

from src.api_client import fetch_all_fixtures, fetch_ratings_by_date
from src.data_processor import process_fixtures, filter_level_1
from src.predictor import find_most_likely_outcome, find_max_momentum_match


def fetch_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetches raw data for upcoming fixtures and current Elo ratings from the API.

    Returns:
        A tuple containing:
        - pd.DataFrame of raw fixture data.
        - pd.DataFrame of raw current Elo ratings.
    """
    print(f"--- Fetching Fixtures Data ---")
    fixtures_df = pd.DataFrame()
    ratings_df = pd.DataFrame()

    fixtures_data = fetch_all_fixtures()
    if fixtures_data:
        fixtures_df = pd.read_csv(StringIO(fixtures_data))

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    print(f"--- Fetching Ratings (Date: {today_str}) ---")

    ratings_data = fetch_ratings_by_date(today_str)
    if ratings_data:
        ratings_df = pd.read_csv(StringIO(ratings_data))

    return fixtures_df, ratings_df


def run_analysis(fixtures_raw: pd.DataFrame, ratings_raw: pd.DataFrame):
    """
    Runs the full analysis pipeline: filtering, processing, finding key insights, and printing the summary.

    Args:
        fixtures_raw: Raw DataFrame of all upcoming fixtures.
        ratings_raw: Raw DataFrame of current Elo ratings (with Level column).
    """
    # 1. Filter and Process
    fixtures = filter_level_1(fixtures_raw, ratings_raw)
    fixtures = process_fixtures(fixtures)

    if fixtures.empty:
        print("No upcoming Level 1 (top-tier) fixtures found. Exiting.")
        return

    print("\n--- ⚽ Upcoming Fixtures & Momentum ---")
    print(fixtures.to_string(index=False, float_format="%.1f"))

    # --- 2. Find Key Metrics for Summary ---
    print("\n[Step 3] Analyzing fixtures for summary insights...")

    # A. Most Confident Prediction (Maximized Confidence Score)
    most_likely = find_most_likely_outcome(fixtures)

    # B. Match with the Largest Momentum Differential
    most_momentum_favored = find_max_momentum_match(fixtures)

    # C. Strongest Team Form Spots (used for the spotlight section)
    best_home_form = fixtures.loc[fixtures['Home_Momentum'].idxmax()]
    best_away_form = fixtures.loc[fixtures['Away_Momentum'].idxmax()]

    # --- 3. Print Comprehensive Summary ---
    print_analysis_summary(
        most_likely,
        most_momentum_favored,
        best_home_form,
        best_away_form
    )

    # --- 4. Write markdown for readme ---
    write_analysis_summary_to_file_markdown(
        fixtures,
        most_likely,
        most_momentum_favored,
        best_home_form,
        best_away_form
    )

    # --- 5. Write history to File ---
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    write_analysis_summary_to_file(
        fixtures,
        most_likely,
        most_momentum_favored,
        best_home_form,
        best_away_form,
        f"data/history/{today_str}.txt"
    )


def print_analysis_summary(
        most_likely: Dict[str, Any],
        most_momentum_favored: pd.Series,
        best_home_form: pd.Series,
        best_away_form: pd.Series
):
    """
    Formats and prints the multi-section summary of the analysis.

    Args:
        most_likely: The result from find_most_likely_outcome (highest weighted score).
        most_momentum_favored: The result from find_max_momentum_match (biggest form differential).
        best_home_form: The fixture row containing the team with the highest Home_Momentum.
        best_away_form: The fixture row containing the team with the highest Away_Momentum.
    """
    print("=" * 70)
    print("             ⚽ WEEKLY FIXTURE INSIGHTS ⚽")
    print("=" * 70)

    # --- 1. MOST MOMENTUM-FAVORED PREDICTION (The New Focus) ---
    print("\n" + "=" * 70)
    print("      🥇 MOST MOMENTUM-FAVORED PREDICTION (Highest Form Backing)")
    print("=" * 70)

    favored_diff = most_momentum_favored['Momentum_Diff']

    # Determine predicted winner based on momentum differential sign
    if favored_diff >= 0:
        predicted_winner = most_momentum_favored['Home']
        raw_prob = most_momentum_favored['HomeWin %']
        result_str = f"Home WIN: {predicted_winner}"
    else:
        predicted_winner = most_momentum_favored['Away']
        raw_prob = most_momentum_favored['AwayWin %']
        result_str = f"Away WIN: {predicted_winner}"

    print(f"Fixture:       **{most_momentum_favored['Home']}** vs. **{most_momentum_favored['Away']}**")
    print(f"Prediction:    {result_str}")
    print(f"Probability:   {raw_prob:.1f}% (Raw Elo)")
    print(f"Form Advantage: **{favored_diff:+.1f} Elo** (Largest differential this week)")
    print("-" * 30)

    # --- 2. MOST CONFIDENT PREDICTION (Highest Weighted Score) ---
    print("\n## 📈 MOST CONFIDENT PREDICTION (Highest Weighted Score)")
    outcome = most_likely['Outcome']

    if outcome == 'HomeWin %':
        result_str = f"Home WIN: {most_likely['Home']}"
        momentum_for_favored = most_likely['Home_Momentum']
    elif outcome == 'AwayWin %':
        result_str = f"Away WIN: {most_likely['Away']}"
        momentum_for_favored = most_likely['Away_Momentum']
    else:  # Draw
        result_str = "DRAW (Neutral Momentum Favored)"
        momentum_for_favored = most_likely['Momentum_Diff']  # Use the Diff for Draw context

    print(f"Fixture:       **{most_likely['Home']}** vs. **{most_likely['Away']}**")
    print(f"Prediction:    {result_str}")
    print(f"Probability:   {most_likely['Probability']:.1f}% (Raw Elo)")
    print(f"Form Advantage: {momentum_for_favored:+.2f} Elo")
    print(f"Confidence:    {most_likely['Confidence_Score']:.2f} (Maximized)")
    print("-" * 30)

    # --- 3. TEAM FORM SPOTLIGHTS ---
    print("\n## ✨ TEAM FORM SPOTLIGHTS")

    # BEST HOME FORM
    print(f"**Best Recent Home Form:**")
    print(f"Team:          **{best_home_form['Home']}** (Momentum: {best_home_form['Home_Momentum']:+.1f} Elo Gain)")
    print(f"Upcoming Match: Home vs. {best_home_form['Away']}")

    # BEST AWAY FORM
    print(f"\n**Best Recent Away Form:**")
    print(f"Team:          **{best_away_form['Away']}** (Momentum: {best_away_form['Away_Momentum']:+.1f} Elo Gain)")
    print(f"Upcoming Match: {best_away_form['Home']} vs. Away")
    print("-" * 30)


def write_analysis_summary_to_file(
        fixtures: pd.DataFrame,
        most_likely: Dict[str, Any],
        most_momentum_favored: pd.Series,
        best_home_form: pd.Series,
        best_away_form: pd.Series,
        file_path: str = "data/analysis_summary.txt"
):
    """
    Formats and writes the multi-section summary of the analysis to a specified file.

    Args:
        fixtures: The upcoming fixtures.
        most_likely: The result from find_most_likely_outcome (highest weighted score).
        most_momentum_favored: The result from find_max_momentum_match (biggest form differential).
        best_home_form: The fixture row containing the team with the highest Home_Momentum.
        best_away_form: The fixture row containing the team with the highest Away_Momentum.
        file_path: The path to the file where the output should be written.

    """

    # Use a 'with' statement to ensure the file is correctly opened and closed,
    # even if errors occur.
    with open(file_path, 'w') as f:
        # Helper function to write a line followed by a newline
        def write_line(line):
            f.write(line + "\n")

        # --- HEADER ---
        write_line("=" * 70)
        write_line("             ⚽ WEEKLY FIXTURE INSIGHTS ⚽")
        write_line("=" * 70)

        write_line("\n--- ⚽ Upcoming Fixtures & Momentum ---")
        write_line(fixtures.to_string(index=False, float_format="%.1f"))

        # --- 1. MOST MOMENTUM-FAVORED PREDICTION ---
        write_line("\n" + "=" * 70)
        write_line("      🥇 MOST MOMENTUM-FAVORED PREDICTION (Highest Form Backing)")
        write_line("=" * 70)

        favored_diff = most_momentum_favored['Momentum_Diff']

        # Determine predicted winner based on momentum differential sign
        if favored_diff >= 0:
            predicted_winner = most_momentum_favored['Home']
            raw_prob = most_momentum_favored['HomeWin %']
            result_str = f"Home WIN: {predicted_winner}"
        else:
            predicted_winner = most_momentum_favored['Away']
            raw_prob = most_momentum_favored['AwayWin %']
            result_str = f"Away WIN: {predicted_winner}"

        write_line(f"Fixture:       **{most_momentum_favored['Home']}** vs. **{most_momentum_favored['Away']}**")
        write_line(f"Prediction:    {result_str}")
        write_line(f"Probability:   {raw_prob:.1f}% (Raw Elo)")
        write_line(f"Form Advantage: **{favored_diff:+.1f} Elo** (Largest differential this week)")
        write_line("-" * 30)

        # --- 2. MOST CONFIDENT PREDICTION ---
        write_line("\n## 📈 MOST CONFIDENT PREDICTION (Highest Weighted Score)")
        outcome = most_likely['Outcome']

        if outcome == 'HomeWin %':
            result_str = f"Home WIN: {most_likely['Home']}"
            momentum_for_favored = most_likely['Home_Momentum']
        elif outcome == 'AwayWin %':
            result_str = f"Away WIN: {most_likely['Away']}"
            momentum_for_favored = most_likely['Away_Momentum']
        else:  # Draw
            result_str = "DRAW (Neutral Momentum Favored)"
            momentum_for_favored = most_likely['Momentum_Diff']  # Use the Diff for Draw context

        write_line(f"Fixture:       **{most_likely['Home']}** vs. **{most_likely['Away']}**")
        write_line(f"Prediction:    {result_str}")
        write_line(f"Probability:   {most_likely['Probability']:.1f}% (Raw Elo)")
        write_line(f"Form Advantage: {momentum_for_favored:+.2f} Elo")
        write_line(f"Confidence:    {most_likely['Confidence_Score']:.2f} (Maximized)")
        write_line("-" * 30)

        # --- 3. TEAM FORM SPOTLIGHTS ---
        write_line("\n## ✨ TEAM FORM SPOTLIGHTS")

        # BEST HOME FORM
        write_line(f"**Best Recent Home Form:**")
        write_line(
            f"Team:          **{best_home_form['Home']}** (Momentum: {best_home_form['Home_Momentum']:+.1f} Elo Gain)")
        write_line(f"Upcoming Match: Home vs. {best_home_form['Away']}")

        # BEST AWAY FORM
        write_line(f"\n**Best Recent Away Form:**")
        write_line(
            f"Team:          **{best_away_form['Away']}** (Momentum: {best_away_form['Away_Momentum']:+.1f} Elo Gain)")
        write_line(f"Upcoming Match: {best_away_form['Home']} vs. Away")
        write_line("-" * 30)

    print(f"Analysis summary written successfully to {file_path}")


def write_analysis_summary_to_file_markdown(
        fixtures: pd.DataFrame,
        most_likely: Dict[str, Any],
        most_momentum_favored: pd.Series,
        best_home_form: pd.Series,
        best_away_form: pd.Series,
        file_path: str = "data/ANALYSIS.md"
):
    """
    Formats and writes the multi-section summary of the analysis to a file
    using Markdown formatting suitable for a README.
    """

    with open(file_path, 'w') as f:
        def write_line(line):
            f.write(line + "\n")

        # --- HEADER ---
        write_line("# ⚽ WEEKLY FIXTURE INSIGHTS ⚽")
        write_line("\n***\n")

        # --- FIXTURES TABLE ---
        write_line("## ⚽ Upcoming Fixtures & Momentum")
        write_line("\n" + fixtures.to_markdown(
            index=False,
            floatfmt=".1f"
        ))
        write_line("\n***\n")

        # --- 1. MOST MOMENTUM-FAVORED PREDICTION (Converted to Markdown Table) ---
        write_line("## 🥇 MOST MOMENTUM-FAVORED PREDICTION (Highest Form Backing)")

        favored_diff = most_momentum_favored['Momentum_Diff']

        if favored_diff >= 0:
            predicted_winner = most_momentum_favored['Home']
            raw_prob = most_momentum_favored['HomeWin %']
            result_str = f"Home WIN: {predicted_winner}"
        else:
            predicted_winner = most_momentum_favored['Away']
            raw_prob = most_momentum_favored['AwayWin %']
            result_str = f"Away WIN: {predicted_winner}"

        # Write the data as a Markdown Table
        data = [
            ("Fixture", f"**{most_momentum_favored['Home']}** vs. **{most_momentum_favored['Away']}**"),
            ("Prediction", result_str),
            ("Probability", f"{raw_prob:.1f}% (Raw Elo)"),
            ("Form Advantage", f"**{favored_diff:+.1f} Elo** (Largest differential this week)")
        ]

        write_line("| Key | Value |")
        write_line("| :--- | :--- |")
        for key, value in data:
            write_line(f"| {key} | {value} |")

        write_line("\n***\n")

        # --- 2. MOST CONFIDENT PREDICTION (Converted to Markdown Table) ---
        write_line("## 📈 MOST CONFIDENT PREDICTION (Highest Weighted Score)")

        outcome = most_likely['Outcome']

        if outcome == 'HomeWin %':
            result_str = f"Home WIN: {most_likely['Home']}"
            momentum_for_favored = most_likely['Home_Momentum']
        elif outcome == 'AwayWin %':
            result_str = f"Away WIN: {most_likely['Away']}"
            momentum_for_favored = most_likely['Away_Momentum']
        else:
            result_str = "DRAW (Neutral Momentum Favored)"
            momentum_for_favored = most_likely['Momentum_Diff']

        data = [
            ("Fixture", f"**{most_likely['Home']}** vs. **{most_likely['Away']}**"),
            ("Prediction", result_str),
            ("Probability", f"{most_likely['Probability']:.1f}% (Raw Elo)"),
            ("Form Advantage", f"{momentum_for_favored:+.2f} Elo"),
            ("Confidence", f"{most_likely['Confidence_Score']:.2f} (Maximized)")
        ]

        write_line("| Key | Value |")
        write_line("| :--- | :--- |")
        for key, value in data:
            write_line(f"| {key} | {value} |")

        write_line("\n***\n")

        # --- 3. TEAM FORM SPOTLIGHTS ---
        write_line("## ✨ TEAM FORM SPOTLIGHTS")

        # BEST HOME FORM
        write_line("#### **Best Recent Home Form:**")
        write_line("* **Team:** " +
                   f"**{best_home_form['Home']}** (Momentum: {best_home_form['Home_Momentum']:+.1f} Elo Gain)")
        write_line(f"* **Upcoming Match:** Home vs. {best_home_form['Away']}")

        # BEST AWAY FORM
        write_line("\n#### **Best Recent Away Form:**")
        write_line("* **Team:** " +
                   f"**{best_away_form['Away']}** (Momentum: {best_away_form['Away_Momentum']:+.1f} Elo Gain)")
        write_line(f"* **Upcoming Match:** {best_away_form['Home']} vs. Away")

        write_line("\n***\n")

    print(f"Analysis summary written successfully to {file_path}")


# Standard Python entry point
if __name__ == "__main__":
    fixtures_df, ratings_df = fetch_data()
    # Only run analysis if data was successfully fetched
    if not fixtures_df.empty and not ratings_df.empty:
        run_analysis(fixtures_df, ratings_df)
    else:
        print("\n--- Failed to fetch required data. Cannot run analysis. ---")