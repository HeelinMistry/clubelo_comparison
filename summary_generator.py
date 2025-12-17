import os
import sys

sys.path.insert(0, os.path.abspath('src'))

from src.api_client import fetch_all_fixtures, fetch_ratings_by_date, fetch_club_history
from src.data_processor import process_fixtures, filter_level_1, get_momentum
from src.predictor import find_most_likely_outcome, find_max_momentum_match

# Define which functions you want to summarize
TARGET_FUNCTIONS = [
    (fetch_all_fixtures, "Data Fetching"),
    (fetch_ratings_by_date, "Data Fetching"),
    (fetch_club_history, "Data Fetching"),
    (filter_level_1, "Data Processing"),
    (process_fixtures, "Data Processing"),
    (get_momentum, "Data Processing"),
    (find_most_likely_outcome, "Prediction Logic"),
    (find_max_momentum_match, "Prediction Logic"),
]


def clean_docstring(doc):
    """Cleans up the docstring for Markdown output, ensuring arguments and returns
       are listed on separate lines and descriptions are clearly separated by ':'.
    """
    if not doc:
        return "No documentation available."

    lines = doc.strip().split('\n')
    summary_lines = []
    details = []
    capture_details = False

    # 1. Capture the summary until the first structured keyword
    for line in lines:
        stripped = line.strip()

        # Check for structured section keywords (Args/Returns)
        if stripped.startswith('Args:'):
            # FIX 1: Use two newlines to guarantee separation from the summary text
            details.append("\n\n**Arguments:**\n")
            capture_details = True
            continue
        elif stripped.startswith('Returns:'):
            # FIX 1: Use two newlines to guarantee separation
            details.append("\n\n**Returns:**\n")
            capture_details = True
            continue

            # If we are not capturing structured details yet:
        if not capture_details:
            if not stripped:
                # Stop capturing the summary on the first blank line
                capture_details = True
                continue
            summary_lines.append(stripped)

        # 2. Capture the details (Argument/Return lines)
        elif capture_details and stripped:
            clean_item = stripped.lstrip('*- ').strip()

            if ':' in clean_item:
                parts = clean_item.split(':', 1)
                name = parts[0].strip()
                description = parts[1].strip()

                # Clean up name part (e.g., remove type annotations like ': str')
                if ' ' in name:
                    name = name.split(' ')[0]

                    # Append the formatted line, guaranteeing a new line for each item
                details.append(f"* **{name}:** {description}")
            else:
                # Handle multi-line descriptions (appending to the last item)
                if details and details[-1].startswith('* '):
                    details[-1] = details[-1] + ' ' + clean_item
                else:
                    details.append(f"* {clean_item}")

    # Join the summary text with spaces
    summary = ' '.join(summary_lines)

    # FIX 2: Join the summary and all details using minimal space
    # The newlines are already embedded in the details list items (e.g., "\n\n**Arguments:**")
    return f"{summary}{' '.join(details)}"


def generate_readme_section(functions):
    """Generates a Markdown section detailing key functions."""
    output = """
A Python-based project to fetch live fixture data from the Club Elo API, calculate the traditional 1X2 match probabilities (Home Win, Draw, Away Win), and identify the single most likely outcome across a set of fixtures.\n\n
"""
    output += "## 🚀 Core Logic and Functions\n"

    current_section = None

    for func, section_title in functions:
        if section_title != current_section:
            output += f"\n### ⚙️ {section_title}\n"
            current_section = section_title

        doc = clean_docstring(func.__doc__)
        output += f"#### `{func.__name__}`\n"
        output += f"{doc}\n\n---\n"

    return output


if __name__ == "__main__":
    markdown_output = generate_readme_section(TARGET_FUNCTIONS)

    # Print the output so it can be redirected to a file or copied
    print(markdown_output)

    # You can pipe this output into a specific file section
    # with open("README_functions.md", "w") as f:
    #     f.write(markdown_output)