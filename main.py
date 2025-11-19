#!/usr/bin/env python3
"""
Generate month-by-month US national parks hiking-condition heat maps.

Inputs:
    - national_parks_hiking_conditions.csv
      Expected columns:
        Park, State, Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec,
        Latitude, Longitude

Usage:
    # Single month
    python parks_hiking_heatmaps.py --month Apr

    # All months
    python parks_hiking_heatmaps.py --all

    # Interactive dashboard
    python parks_hiking_heatmaps.py --interactive

Output:
    - HTML files (interactive) saved in ./output_maps/
      Example: hiking_conditions_Apr.html
        - Interactive dashboard includes month selector with an Average tab.
        - Console message includes the park with the highest average score.
"""

import argparse
from copy import deepcopy
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CSV_PATH = "data/national_parks_hiking_conditions.csv"
OUTPUT_DIR = Path("output_maps")

MONTH_COLUMNS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def load_data(csv_path: str = CSV_PATH) -> pd.DataFrame:
    """Load the hiking conditions CSV and do basic validation."""
    df = pd.read_csv(csv_path)

    required_cols = {"Park", "State", "Latitude", "Longitude"} | set(MONTH_COLUMNS)
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    df = df.copy()
    df["AverageScore"] = df[MONTH_COLUMNS].mean(axis=1)

    return df


def print_average_scores(df: pd.DataFrame) -> None:
    """Print all parks sorted by average score (descending)."""
    sorted_df = df.sort_values("AverageScore", ascending=False, ignore_index=True)
    print("\nAverage hiking condition scores (high → low):")
    for idx, row in sorted_df.iterrows():
        rank = idx + 1
        park = row["Park"]
        state = row["State"]
        avg = row["AverageScore"]
        print(f"{rank:>2}. {park} ({state}) – {avg:.2f}")


def normalize_month_name(month: str) -> str:
    """Return canonical month abbreviation (e.g., 'Jan', 'Feb')."""
    month = month.strip().lower()

    mapping = {
        "january": "Jan", "jan": "Jan",
        "february": "Feb", "feb": "Feb",
        "march": "Mar", "mar": "Mar",
        "april": "Apr", "apr": "Apr",
        "may": "May",
        "june": "Jun", "jun": "Jun",
        "july": "Jul", "jul": "Jul",
        "august": "Aug", "aug": "Aug",
        "september": "Sep", "sep": "Sep",
        "october": "Oct", "oct": "Oct",
        "november": "Nov", "nov": "Nov",
        "december": "Dec", "dec": "Dec",
    }

    if month not in mapping:
        raise ValueError(
            f"Unrecognized month '{month}'. "
            f"Use one of: {', '.join(sorted(set(mapping.values())))}"
        )

    return mapping[month]


def make_month_heatmap(df: pd.DataFrame, month_col: str, output_dir: Path = OUTPUT_DIR):
    """
    Create an interactive heat map for a single month.

    - Colors: hiking condition score (e.g., 1–10)
    - Scope: USA
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    title = f"US National Parks Hiking Conditions – {month_col}"
    fig = px.scatter_geo(
        df,
        lat="Latitude",
        lon="Longitude",
        color=month_col,
        hover_name="Park",
        hover_data={
            "State": True,
            month_col: True,
            "Latitude": False,
            "Longitude": False,
        },
        color_continuous_scale="Viridis",
        range_color=(df[month_col].min(), df[month_col].max()),
        projection="albers usa",
        scope="usa",
        title=title,
    )

    fig.update_traces(marker=dict(size=8))  # tweak point size if you like
    fig.update_layout(
        legend_title_text="Hiking Condition Score",
        coloraxis_colorbar={
            "title": "Condition",
            "ticks": "outside",
        },
        margin=dict(l=20, r=20, t=60, b=20),
    )

    output_path = output_dir / f"hiking_conditions_{month_col}.html"
    fig.write_html(str(output_path), include_plotlyjs="cdn")

    print(f"Saved: {output_path}")


def generate_all_months(df: pd.DataFrame, output_dir: Path = OUTPUT_DIR):
    """Generate heat maps for all 12 months."""
    for month_col in MONTH_COLUMNS:
        print(f"Generating map for {month_col}...")
        make_month_heatmap(df, month_col, output_dir=output_dir)


def make_interactive_dashboard(df: pd.DataFrame, output_dir: Path = OUTPUT_DIR):
    """Create a single HTML file with buttons to toggle between months."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "hiking_conditions_interactive.html"

    overall_min = min(df[MONTH_COLUMNS].min().min(), df["AverageScore"].min())
    overall_max = max(df[MONTH_COLUMNS].max().max(), df["AverageScore"].max())
    dropdown_labels = MONTH_COLUMNS + ["Average"]
    value_series_map = {}
    for label in dropdown_labels:
        if label == "Average":
            value_series_map[label] = df["AverageScore"]
        else:
            value_series_map[label] = df[label]

    top_lists = {}
    for label, series in value_series_map.items():
        top_entries = series.sort_values(ascending=False).head(15)
        lines = [f"<b>Top 15 – {label}</b>"]
        for idx, (park_idx, score) in enumerate(top_entries.items(), start=1):
            park = df.at[park_idx, "Park"]
            state = df.at[park_idx, "State"]
            lines.append(f"{idx}. {park} ({state}) – {score:.1f}")
        top_lists[label] = "<br>".join(lines)

    def make_top_annotation(text: str) -> dict:
        return {
            "text": text,
            "showarrow": False,
            "x": 1.02,
            "y": 0.5,
            "xref": "paper",
            "yref": "paper",
            "align": "left",
            "bgcolor": "rgba(255,255,255,0.9)",
            "bordercolor": "#1f2328",
            "borderwidth": 1,
            "font": {"size": 12},
        }

    traces = []
    for idx, label in enumerate(dropdown_labels):
        value_series = value_series_map[label]
        hover_label = label

        customdata = df[["State"]].assign(
            SelectedValue=value_series,
            AverageScore=df["AverageScore"],
        ).to_numpy()

        traces.append(
            go.Scattergeo(
                lat=df["Latitude"],
                lon=df["Longitude"],
                mode="markers",
                text=df["Park"],
                marker=dict(
                    size=8,
                    color=value_series,
                    coloraxis="coloraxis",
                ),
                customdata=customdata,
                hovertemplate=(
                    "<b>%{text}</b><br>State: %{customdata[0]}<br>"
                    f"Condition ({hover_label}): %{{customdata[1]:.1f}}<br>"
                    "Average: %{customdata[2]:.1f}<extra></extra>"
                ),
                visible=(idx == 0),
                name=label,
            )
        )

    select_annotation = dict(
        text="Select data",
        showarrow=False,
        x=0,
        xanchor="left",
        y=1.12,
        yanchor="top",
        font=dict(size=12),
    )

    buttons = []
    for idx, label in enumerate(dropdown_labels):
        visibility = [False] * len(dropdown_labels)
        visibility[idx] = True
        buttons.append(
            dict(
                label=label,
                method="update",
                args=[
                    {"visible": visibility},
                    {
                        "title": f"US National Parks Hiking Conditions – {label}",
                        "annotations": [
                            deepcopy(select_annotation),
                            make_top_annotation(top_lists[label]),
                        ],
                    },
                ],
            )
        )

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=f"US National Parks Hiking Conditions – {dropdown_labels[0]}",
        legend_title_text="Dataset",
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.1,
                yanchor="top",
            )
        ],
        annotations=[
            deepcopy(select_annotation),
            make_top_annotation(top_lists[dropdown_labels[0]]),
        ],
        margin=dict(l=20, r=20, t=60, b=20),
        geo=dict(scope="usa", projection_type="albers usa"),
        coloraxis=dict(
            colorscale="Viridis",
            cmin=overall_min,
            cmax=overall_max,
            colorbar=dict(
                title="Hiking condition score",
                ticks="outside",
                len=0.75,
                thickness=16,
            ),
        ),
    )

    fig.write_html(
        str(output_path),
        include_plotlyjs="cdn",
        full_html=True,
        config={"responsive": True},
    )
    print(f"Saved interactive dashboard: {output_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate month-by-month US national parks hiking-condition heat maps."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--month",
        type=str,
        help="Month to plot (e.g., Jan, February, apr, etc.)",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Generate maps for all 12 months.",
    )
    group.add_argument(
        "--interactive",
        action="store_true",
        help="Generate a single HTML file with controls to switch between months.",
    )

    parser.add_argument(
        "--csv",
        type=str,
        default=CSV_PATH,
        help=f"Path to CSV file (default: {CSV_PATH})",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default=str(OUTPUT_DIR),
        help=f"Output directory for HTML maps (default: {OUTPUT_DIR})",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    df = load_data(args.csv)
    outdir = Path(args.outdir)

    print_average_scores(df)

    if args.interactive:
        make_interactive_dashboard(df, output_dir=outdir)
    elif args.all:
        generate_all_months(df, output_dir=outdir)
    else:
        month_col = normalize_month_name(args.month)
        if month_col not in MONTH_COLUMNS:
            raise ValueError(f"Month column '{month_col}' not found in data.")
        make_month_heatmap(df, month_col, output_dir=outdir)


if __name__ == "__main__":
    main()
