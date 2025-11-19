#!/usr/bin/env python3
"""
Generate interactive US national parks hiking-condition heat map dashboard.

Inputs:
    - national_parks_hiking_conditions.csv
      Expected columns:
        Park, State, Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec,
        Latitude, Longitude

Usage:
    python parks_hiking_heatmaps.py

Output:
    - HTML file (interactive) saved in ./output_maps/hiking_conditions_interactive.html
    - Interactive dashboard includes month selector with an Average tab.
    - Console message includes all parks sorted by average score.
"""

import argparse
from copy import deepcopy
from pathlib import Path

import pandas as pd
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


def make_interactive_dashboard(df: pd.DataFrame, output_dir: Path = OUTPUT_DIR):
    """Create a single HTML file with buttons to toggle between months and rating filter."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "hiking_conditions_interactive.html"

    overall_min = min(df[MONTH_COLUMNS].min().min(), df["AverageScore"].min())
    overall_max = max(df[MONTH_COLUMNS].max().max(), df["AverageScore"].max())
    
    # Create rating filter steps (0-10 in 0.5 increments)
    rating_steps = [i * 0.5 for i in range(21)]
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

    # Create traces for each month/average and each rating threshold
    traces = []
    trace_map = {}  # (month_idx, rating_threshold) -> trace_idx
    
    for month_idx, label in enumerate(dropdown_labels):
        value_series = value_series_map[label]
        hover_label = label

        for rating_threshold in rating_steps:
            # Filter points based on rating threshold
            mask = value_series >= rating_threshold
            
            filtered_df = df[mask]
            filtered_values = value_series[mask]
            
            customdata = filtered_df[["State"]].assign(
                SelectedValue=filtered_values,
                AverageScore=filtered_df["AverageScore"],
            ).to_numpy()

            trace_idx = len(traces)
            trace_map[(month_idx, rating_threshold)] = trace_idx
            
            traces.append(
                go.Scattergeo(
                    lat=filtered_df["Latitude"],
                    lon=filtered_df["Longitude"],
                    mode="markers",
                    text=filtered_df["Park"],
                    marker=dict(
                        size=8,
                        color=filtered_values,
                        coloraxis="coloraxis",
                    ),
                    customdata=customdata,
                    hovertemplate=(
                        "<b>%{text}</b><br>State: %{customdata[0]}<br>"
                        f"Condition ({hover_label}): %{{customdata[1]:.1f}}<br>"
                        "Average: %{customdata[2]:.1f}<extra></extra>"
                    ),
                    visible=(month_idx == 0 and rating_threshold == 0),
                    name=label,
                )
            )

    select_annotation = dict(
        text="Select month",
        showarrow=False,
        x=0,
        xanchor="left",
        y=1.12,
        yanchor="top",
        font=dict(size=12),
    )
    
    rating_annotation = dict(
        text="Min rating: 0.0",
        showarrow=False,
        x=0.18,
        xanchor="left",
        y=1.12,
        yanchor="top",
        font=dict(size=12),
    )

    buttons = []
    current_month_idx = [0]  # Track current month for slider updates
    
    for month_idx, label in enumerate(dropdown_labels):
        # When a month button is clicked, show that month with rating 0 (all parks)
        visibility = [False] * len(traces)
        visibility[trace_map[(month_idx, 0)]] = True
        
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
                            dict(
                                text="Min rating: 0.0",
                                showarrow=False,
                                x=0.18,
                                xanchor="left",
                                y=1.12,
                                yanchor="top",
                                font=dict(size=12),
                            ),
                            make_top_annotation(top_lists[label]),
                        ],
                        "sliders": [{
                            "active": 0,
                            "currentvalue": {"prefix": "Min rating: ", "visible": True},
                            "steps": [
                                {
                                    "label": f"{threshold:.1f}",
                                    "method": "update",
                                    "args": [
                                        {"visible": [i == trace_map[(month_idx, threshold)] for i in range(len(traces))]},
                                        {}
                                    ]
                                }
                                for threshold in rating_steps
                            ]
                        }]
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
        sliders=[
            dict(
                active=0,
                currentvalue={"prefix": "Min rating: ", "visible": True},
                pad={"t": 50},
                steps=[
                    dict(
                        label=f"{threshold:.1f}",
                        method="update",
                        args=[
                            {"visible": [i == trace_map[(0, threshold)] for i in range(len(traces))]},
                            {}
                        ]
                    )
                    for threshold in rating_steps
                ]
            )
        ],
        annotations=[
            deepcopy(select_annotation),
            deepcopy(rating_annotation),
            make_top_annotation(top_lists[dropdown_labels[0]]),
        ],
        margin=dict(l=20, r=20, t=60, b=60),
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
    print(f"\nSaved interactive dashboard: {output_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate interactive US national parks hiking-condition heat map dashboard."
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
        help=f"Output directory for HTML map (default: {OUTPUT_DIR})",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    df = load_data(args.csv)
    outdir = Path(args.outdir)

    print_average_scores(df)
    make_interactive_dashboard(df, output_dir=outdir)


if __name__ == "__main__":
    main()