# ClubElo Comparison Tool - Function Documentation

This document provides a detailed, auto-generated summary of the core Python functions used in the project, extracted directly from docstrings.


# ⚽ Club Elo Predictor
    
A Python-based project to fetch live fixture data from the Club Elo API, calculate the traditional 1X2 match probabilities (Home Win, Draw, Away Win), and identify the single most likely outcome across a set of fixtures.


## 🚀 Core Logic and Functions

### ⚙️ Data Fetching
#### `fetch_all_fixtures`
Fetches the raw CSV data for all upcoming fixtures, including 1X2 probabilities.

**Returns:** * The raw CSV data as a string if successful, otherwise None.

---
#### `fetch_ratings_by_date`
Fetches the raw CSV data for all club ratings on a specific date.

**Arguments:** * date_str: The date in "YYYY-MM-DD" format. 
**Returns:** * The raw CSV data as a string if successful, otherwise None.

---
#### `fetch_club_history`
Fetches the full Elo history for a specific club from its foundation until the present day.
* The club name is cleaned to remove spaces for the API endpoint. 
**Arguments:** * club_name: The name of the club (e.g., 'Man City'). 
**Returns:** * The raw CSV history data as a string. Returns an empty string on failure.

---

### ⚙️ Data Processing
#### `filter_level_1`
Filters fixtures_df to include only matches where *both* the Home and Away teams are classified as Level 1 (top tier) in their respective countries.

**Arguments:** * fixtures_df: DataFrame of upcoming fixtures. * ratings_df: DataFrame containing current Elo ratings and the 'Level' column. 
**Returns:** * Filtered DataFrame containing only Level 1 league fixtures.

---
#### `process_fixtures`
Converts the raw fixtures DataFrame into a clean, calculated DataFrame by filtering for English teams, calculating 1X2 probabilities, and calculating momentum scores.

**Arguments:** * df: The raw DataFrame containing fixtures and Elo data (including GD columns). 
**Returns:** * A pandas DataFrame with upcoming fixtures, probabilities, and momentum scores, * sorted by date. Returns an empty DataFrame if no English fixtures are found.

---
#### `get_momentum`
Calculates the Elo change (Momentum) over the last 'lookback' actual games by comparing the current Elo to the Elo before the Nth game back. Future Elo projections are filtered out.

**Arguments:** * club_name: The name of the club to fetch history for. * lookback: The number of games to look back to calculate momentum (default is 5). 
**Returns:** * The total Elo change over the lookback period, rounded to 2 decimal places. * Returns 0.0 if data is unavailable or an error occurs.

---

### ⚙️ Prediction Logic
#### `find_most_likely_outcome`
Finds the strongest predicted outcome across all fixtures by calculating a 'Confidence Score' that weights raw Elo probability with recent momentum.
* The score formula is designed to reward outcomes supported by positive momentum * and penalize draws where momentum heavily favors one side. 
**Arguments:** * df: DataFrame containing processed fixtures, probabilities, and momentum data. 
**Returns:** * A dictionary representing the single predicted outcome with the highest * Confidence Score, or None if the DataFrame is empty.

---
#### `find_max_momentum_match`
Identifies the fixture with the largest absolute Momentum_Diff, indicating the biggest form vs. slump mismatch. This is used for highlighting high-volatility betting opportunities.

**Arguments:** * df: DataFrame containing fixture data, including the 'Momentum_Diff' column. 
**Returns:** * The pandas Series representing the row of the match with the highest * absolute momentum differential, or None if the DataFrame is empty.

---
