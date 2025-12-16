# src/report_generator.py
import pandas as pd
from fpdf import FPDF
from datetime import date


def generate_report(df: pd.DataFrame, filename: str = "clubelo_report.pdf"):
    """
    Generates a PDF report from the final processed DataFrame.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "ClubElo Fixture Comparison Report", 0, 1, "C")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Date Generated: {date.today().strftime('%Y-%m-%d')}", 0, 1)
    pdf.ln(5)

    # Convert the DataFrame to a list of lists for the table
    # Select and format only the columns you want in the report
    report_df = df[['Date', 'Home', 'Away', 'HomeWin %', 'Draw %', 'AwayWin %', 'Momentum_Diff']]
    data = [report_df.columns.tolist()] + report_df.values.tolist()

    # Table Setup
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(200, 220, 255)  # Light blue background for header

    # Calculate column widths (approximate for 7 columns on a portrait A4 page)
    col_widths = [15, 30, 30, 20, 15, 20, 20]

    with pdf.table(
            headings_style=pdf.font_config.pop("B"),
            line_height=8,
            text_align='CENTER'
    ) as table:

        # Add Header
        header_row = table.row()
        for i, header in enumerate(data[0]):
            header_row.cell(header, width=col_widths[i], fill=True)

        # Add Data Rows
        pdf.set_font("helvetica", "", 10)
        pdf.set_fill_color(240, 240, 240)  # Alternate row color

        for i, row_data in enumerate(data[1:]):
            row = table.row()
            fill = i % 2 == 0
            for j, item in enumerate(row_data):
                row.cell(str(item), width=col_widths[j], fill=fill)

    pdf.output(filename)
    print(f"Report generated: {filename}")

# You would call this function at the end of your main execution script
# generate_report(processed_df)