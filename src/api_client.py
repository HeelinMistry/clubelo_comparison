import requests
import datetime
from typing import Optional

# The base URL for the Club Elo API.
BASE_URL = "http://api.clubelo.com/"


def fetch_api_data(endpoint: str) -> Optional[str]:
    """
    Generic function to fetch raw CSV data from a Club Elo API endpoint.

    Args:
        endpoint: The specific API path (e.g., '2025-12-06', 'Fixtures', or 'ClubName').

    Returns:
        The raw CSV data as a string if successful (HTTP 200), otherwise None.
    """
    url = f"{BASE_URL}{endpoint}"

    # We will let the calling functions print the context, e.g., "Fetching history for X"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()  # Raises HTTPError for 4xx or 5xx status codes

        # Check for empty response content, which can happen for future/invalid dates
        if not response.text.strip():
            print(f"Warning: Response for {endpoint} was empty.")
            return None

        return response.text

    except requests.exceptions.HTTPError as e:
        # Handle specific HTTP errors (404, 500, etc.)
        status = e.response.status_code if e.response else 'Unknown'
        print(f"Error fetching data from {url}: Received status code {status}")
        if status == 404 and endpoint.count('-') == 2:
            # Heuristic check for date format
            print("Hint: Data not found. Check if the date is too far in the future.")
        return None

    except requests.exceptions.RequestException as e:
        # Handle network-level errors (timeout, connection loss, etc.)
        print(f"Network error during request to {url}: {e}")
        return None


def fetch_ratings_by_date(date_str: str) -> Optional[str]:
    """
    Fetches the raw CSV data for all club ratings on a specific date.

    Args:
        date_str: The date in "YYYY-MM-DD" format.

    Returns:
        The raw CSV data as a string if successful, otherwise None.
    """
    print(f"Attempting to fetch ratings for: {date_str}")
    return fetch_api_data(date_str)


def fetch_all_fixtures() -> Optional[str]:
    """
    Fetches the raw CSV data for all upcoming fixtures, including 1X2 probabilities.

    Returns:
        The raw CSV data as a string if successful, otherwise None.
    """
    print("Attempting to fetch all upcoming fixture data...")
    return fetch_api_data("Fixtures")


def fetch_club_history(club_name: str) -> str:
    """
    Fetches the full Elo history for a specific club from its foundation until the present day.

    The club name is cleaned to remove spaces for the API endpoint.

    Args:
        club_name: The name of the club (e.g., 'Man City').

    Returns:
        The raw CSV history data as a string. Returns an empty string on failure.
    """
    # Clean the club name (e.g., 'Man City' -> 'ManCity')
    endpoint = club_name.replace(' ', '')

    print(f"Attempting to fetch history for: {club_name}")

    # Use the generic function, but wrap the result for the specific return type
    result = fetch_api_data(endpoint)
    if result is None:
        return ""
    return result


def main():
    """
    Main execution function to test the API client functions directly.
    """
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    print(f"--- Running API Client Test (Date: {today_str}) ---")

    # Test 1: Fetch Ratings
    ratings_csv = fetch_ratings_by_date(today_str)

    if ratings_csv:
        print("\n--- Ratings Data Sample ---")
        # Ensure we only print the first few lines to avoid spamming the console
        sample_lines = ratings_csv.split('\n')[:4]
        print('\n'.join(sample_lines))

    # Test 2: Fetch Fixtures
    fixtures_csv = fetch_all_fixtures()
    if fixtures_csv:
        print("\n--- Fixtures Data Sample ---")
        sample_lines = fixtures_csv.split('\n')[:4]
        print('\n'.join(sample_lines))

    # Test 3: Fetch History
    history_csv = fetch_club_history("Liverpool")
    if history_csv:
        print("\n--- Liverpool History Sample ---")
        sample_lines = history_csv.split('\n')[:4]
        print('\n'.join(sample_lines))


if __name__ == "__main__":
    main()