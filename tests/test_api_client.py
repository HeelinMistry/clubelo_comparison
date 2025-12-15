import unittest
from unittest.mock import patch, Mock
import requests

# Assuming your refactored functions are in src/api_client.py
from src.api_client import fetch_api_data, fetch_ratings_by_date, fetch_all_fixtures, fetch_club_history

# Mock response data for success cases
MOCK_SUCCESS_CSV = "header1,header2\nvalue1,value2\n"


class TestApiClient(unittest.TestCase):

    @patch('requests.get')
    def test_fetch_api_data_success(self, mock_get):
        """Tests successful fetching from a generic endpoint."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = MOCK_SUCCESS_CSV
        mock_response.raise_for_status.return_value = None  # No exception raised
        mock_get.return_value = mock_response

        result = fetch_api_data("TestEndpoint")
        self.assertEqual(result, MOCK_SUCCESS_CSV)
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_fetch_api_data_http_error(self, mock_get):
        """Tests handling of an HTTP error (e.g., 404)."""
        # --- FIX: Set up the Mock response and the Error structure correctly ---
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = ""
        mock_response.url = "http://api.clubelo.com/404Test"

        # Create an HTTPError instance and attach the mock response to it
        http_error = requests.exceptions.HTTPError("404 Client Error")
        http_error.response = mock_response  # <--- CRITICAL FIX

        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        # The function should handle the exception and return None
        result = fetch_api_data("404Test")
        self.assertIsNone(result)

    @patch('requests.get')
    def test_fetch_club_history_cleaning(self, mock_get):
        """Tests that club names are cleaned (spaces removed) before fetching history."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = MOCK_SUCCESS_CSV
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        fetch_club_history("Man City")
        # Check that the URL was constructed with 'ManCity'
        mock_get.assert_called_once_with('http://api.clubelo.com/ManCity', timeout=15)

    # --- Integration Tests for Specific Functions (ensuring they call fetch_api_data correctly) ---

    @patch('src.api_client.fetch_api_data')
    def test_fetch_ratings_by_date(self, mock_fetch):
        mock_fetch.return_value = MOCK_SUCCESS_CSV
        result = fetch_ratings_by_date("2025-12-01")
        mock_fetch.assert_called_once_with("2025-12-01")
        self.assertEqual(result, MOCK_SUCCESS_CSV)

    @patch('src.api_client.fetch_api_data')
    def test_fetch_all_fixtures(self, mock_fetch):
        mock_fetch.return_value = MOCK_SUCCESS_CSV
        result = fetch_all_fixtures()
        mock_fetch.assert_called_once_with("Fixtures")
        self.assertEqual(result, MOCK_SUCCESS_CSV)


if __name__ == '__main__':
    unittest.main()