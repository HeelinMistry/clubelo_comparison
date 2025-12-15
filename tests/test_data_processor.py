import unittest
import pandas as pd
from unittest.mock import patch, MagicMock

from src.data_processor import filter_level_1, get_momentum, process_fixtures


class TestDataProcessor(unittest.TestCase):
    # --- Setup Mock Data ---

    # Mock ratings data with Level 1 (top tier) and Level 2 teams
    MOCK_RATINGS_DF = pd.DataFrame({
        'Club': ['Arsenal', 'Man Utd', 'Man City', 'Leeds', 'Forest', 'Coventry'],
        'Country': ['ENG', 'ENG', 'ENG', 'ENG', 'ENG', 'ENG'],
        'Level': [1, 1, 1, 2, 1, 2],
        'Elo': [2000, 1900, 1950, 1700, 1800, 1600]
    })

    # Mock raw fixtures data (pre-probability calc)
    MOCK_FIXTURES_RAW = pd.DataFrame({
        'Date': ['2025-12-01', '2025-12-01', '2025-12-01'],
        'Country': ['ENG', 'ENG', 'ENG'],
        'Home': ['Arsenal', 'Leeds', 'Man City'],
        'Away': ['Man Utd', 'Coventry', 'Forest'],
        # Mock probability columns (simplified for testing)
        'GD<-5': [0.1, 0.0, 0.05], 'GD=-1': [0.1, 0.2, 0.1], 'GD=0': [0.2, 0.3, 0.1],
        'GD=1': [0.3, 0.4, 0.3], 'GD>5': [0.3, 0.1, 0.45]
    })

    # This represents the MOCK_FIXTURES_RAW with momentum added based on the old side_effect logic
    MOCK_FIXTURES_WITH_MOMENTUM = pd.DataFrame({
        'Date': ['2025-12-01', '2025-12-01', '2025-12-01'],
        'Country': ['ENG', 'ENG', 'ENG'],
        'Home': ['Arsenal', 'Leeds', 'Man City'],
        'Away': ['Man Utd', 'Coventry', 'Forest'],

        # Probability Columns (must include all expected by the production code)
        'GD<-5': [0.0, 0.0, 0.0],  # Mocked
        'GD=-5': [0.0, 0.0, 0.0],  # Missing column 1 -> ADDED
        'GD=-4': [0.0, 0.0, 0.0],  # Missing column 2 -> ADDED
        'GD=-3': [0.0, 0.0, 0.0],  # Missing column 3 -> ADDED
        'GD=-2': [0.0, 0.0, 0.0],  # Missing column 4 -> ADDED
        'GD=-1': [0.1, 0.2, 0.1],  # Existing
        'GD=0': [0.2, 0.3, 0.1],  # Existing
        'GD=1': [0.3, 0.4, 0.3],  # Existing
        'GD=2': [0.0, 0.0, 0.0],  # Potentially missing -> ADDED
        'GD=3': [0.0, 0.0, 0.0],  # Potentially missing -> ADDED
        'GD=4': [0.0, 0.0, 0.0],  # Potentially missing -> ADDED
        'GD=5': [0.0, 0.0, 0.0],  # Potentially missing -> ADDED
        'GD>5': [0.3, 0.1, 0.45],  # Existing

        'Level': [1, 2, 1],
        # Crucial Pre-Calculated Columns (for bypassing apply)
        'Home_Momentum': [10.0, 2.0, 5.0],
        'Away_Momentum': [-5.0, 0.0, 1.0],
    })

    # Mock Elo history data for get_momentum test
    # A 5-game lookback will start before the 5th game (2025-11-25)
    MOCK_HISTORY_CSV = """
Rank,Club,From,Elo
1,Arsenal,2025-11-20,2000.0
2,Arsenal,2025-11-21,2005.0  
3,Arsenal,2025-11-22,2005.0
4,Arsenal,2025-11-23,2001.0 
5,Arsenal,2025-11-24,2001.0
6,Arsenal,2025-11-25,2006.0 
7,Arsenal,2025-11-26,2002.0 
8,Arsenal,2025-11-27,2008.0 
9,Arsenal,2025-11-28,2008.0 
"""

    # --- Test filter_level_1 ---

    def test_filter_level_1(self):
        """Tests that only fixtures where BOTH teams are Level 1 are kept."""
        # Arsenal (L1) vs Man Utd (L1) -> Kept
        # Leeds (L2) vs Coventry (L2) -> Dropped
        # Man City (L1) vs Forest (L1) -> Kept

        filtered_df = filter_level_1(self.MOCK_FIXTURES_RAW, self.MOCK_RATINGS_DF)

        self.assertEqual(len(filtered_df), 2)
        self.assertIn('Arsenal', filtered_df['Home'].values)
        self.assertNotIn('Leeds', filtered_df['Home'].values)

    # --- Test get_momentum ---

    @patch('src.data_processor.fetch_club_history')
    @patch('src.data_processor.datetime')
    def test_get_momentum_5_games(self, mock_dt, mock_fetch):
        """Tests momentum calculation for a standard 5-game lookback."""
        mock_fetch.return_value = self.MOCK_HISTORY_CSV
        # Set current date to ensure no future projections are accidentally included
        mock_dt.datetime.now.return_value = pd.to_datetime('2025-11-27')

        # Start Elo (5th game back, 2025-11-21) = 2000.0
        # Current Elo (last entry before or on mock_dt date) = 2008.0 (from 2025-11-27)
        # Momentum = 2008.0 - 2000.0 = +8.0
        expected_momentum = 8.0

        result = get_momentum("Arsenal")
        self.assertEqual(result, expected_momentum)

    @patch('src.data_processor.fetch_club_history')
    def test_get_momentum_less_than_lookback(self, mock_fetch):
        """Tests momentum when history has fewer than 'lookback' games."""
        # History with only 2 unique game results
        mock_fetch.return_value = """
Rank,Club,From,Elo
1,TeamA,2025-11-20,1500.0
2,TeamA,2025-11-21,1505.0
3,TeamA,2025-11-22,1503.0
"""
        # Start Elo = 1500.0 (first available Elo)
        # Current Elo = 1503.0
        # Momentum = 3.00
        result = get_momentum("TeamA", lookback=5)
        self.assertEqual(result, 3.00)

    # --- Test process_fixtures ---
    def test_process_fixtures_probability_calc(self):
        """Tests that probability percentages and momentum columns are correctly calculated."""

        # Pass the pre-calculated mock data (which has Home_Momentum and Away_Momentum)
        processed_df = process_fixtures(self.MOCK_FIXTURES_WITH_MOMENTUM.copy())

        # NOTE: After filter_level_1 runs, the Leeds row (Level 2) is dropped.

        # Test 1: Arsenal vs Man Utd (Level 1)
        # GD>5(0.3) + GD=1(0.3) = 0.6 Home Win -> 60.0%
        self.assertAlmostEqual(processed_df.iloc[0]['HomeWin %'], 60.0)
        self.assertAlmostEqual(processed_df.iloc[0]['Draw %'], 20.0)
        self.assertAlmostEqual(processed_df.iloc[0]['AwayWin %'], 10.0)

        # Test Momentum Diff: Arsenal (10.0) vs Man Utd (-5.0) -> Diff = 15.0
        self.assertAlmostEqual(processed_df.iloc[0]['Momentum_Diff'], 15.0)
        self.assertAlmostEqual(processed_df.iloc[0]['Home_Momentum'], 10.0)

        # Test 2: Man City vs Forest (The 3rd row in MOCK_FIXTURES_RAW, now index 1)
        # Home (5.0), Away (1.0) -> Diff = 4.0
        self.assertAlmostEqual(processed_df.iloc[1]['Momentum_Diff'], 2.0)

        # Ensure only relevant columns are present
        expected_cols = {'Date', 'Home', 'Away', 'HomeWin %', 'Draw %', 'AwayWin %', 'Home_Momentum', 'Away_Momentum',
                         'Momentum_Diff'}
        self.assertEqual(set(processed_df.columns), expected_cols)


if __name__ == '__main__':
    unittest.main()