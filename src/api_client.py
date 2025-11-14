import requests
import datetime

# The base URL for the Club Elo API.
# We append a date in 'YYYY-MM-DD' format to get all ratings for that day.
BASE_URL = "http://api.clubelo.com/"

def fetch_ratings_by_date(date_str: str) -> str | None:
    """
    Fetches the raw CSV data for all club ratings on a specific date.

    Args:
        date_str: The date in "YYYY-MM-DD" format.

    Returns:
        The raw CSV data as a string if successful, otherwise None.
    """
    # Construct the full URL, e.g., http://api.clubelo.com/2025-11-14
    url = f"{BASE_URL}{date_str}"

    print(f"Attempting to fetch data from: {url}")

    try:
        response = requests.get(url)

        # Check if the request was successful (HTTP 200)
        if response.status_code == 200:
            print("Successfully fetched data.")
            # Return the raw text content (which is the CSV data)
            return response.text
        else:
            # Handle common errors
            print(f"Error: Received status code {response.status_code}")
            if response.status_code == 404:
                print("Data not found for this date. Are you sure it's not a future date?")
            return None

    except requests.exceptions.RequestException as e:
        # Handle network-level errors (e.g., no internet connection)
        print(f"Error during request: {e}")
        return None


# ... (keep the existing BASE_URL and fetch_ratings_by_date function) ...

def fetch_all_fixtures() -> str | None:
    """
    Fetches the raw CSV data for all upcoming fixtures.
    This endpoint includes pre-calculated probabilities.

    Returns:
        The raw CSV data as a string if successful, otherwise None.
    """
    # This URL provides all upcoming fixtures
    url = f"{BASE_URL}Fixtures"

    print(f"Attempting to fetch data from: {url}")

    try:
        response = requests.get(url)

        if response.status_code == 200:
            print("Successfully fetched fixture data.")
            return response.text
        else:
            print(f"Error: Received status code {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return None


# This block allows us to test the file directly
if __name__ == "__main__":
    # Get today's date and format it as required by the API
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    print(f"--- Running API Client Test (Date: {today_str}) ---")

    ratings_csv = fetch_ratings_by_date(today_str)

    if ratings_csv:
        print("\n--- Sample of Fetched Data (First 500 characters) ---")
        print(ratings_csv[:500])
        print("\n...")
    else:
        print("\n--- Data fetching failed ---")