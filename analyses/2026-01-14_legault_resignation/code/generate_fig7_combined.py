#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig7_rhetoric.py

MAIN OBJECTIVE:
---------------
Generate figure analyzing rhetorical strategies in Legault's resignation speech.
Shows legacy framing patterns and speech acts as two donut charts.

Dependencies:
-------------
- config (colors, labels)
- load_and_validate (data loading)
- compute_indices (aggregation)
- html_utils (HTML generation, export)

MAIN FEATURES:
--------------
1) Legacy framing donut chart (left)
2) Speech acts donut chart (right)

Author:
-------
Antoine Lemor
"""

import html as html_lib
import math

from config import (
    get_labels, LEGACY_FRAMING_COLORS, SPEECH_ACT_COLORS, QUEBEC_BLUE
)
from load_and_validate import load_data, OUTPUT_DIR
from compute_indices import (
    aggregate_legacy_framing,
    aggregate_speech_acts,
    compute_legacy_emphasis_index,
    reset_excerpts
)
from html_utils import save_figure


def build_donut_svg(data, colors_map, labels_map, center_value, center_label, size=520):
    """Build a donut chart SVG."""
    cx, cy = size / 2, size / 2
    outer_radius = size / 2 - 50
    inner_radius = outer_radius * 0.50

    total = sum(d['count'] for d in data)
    if total == 0:
        return ''

    # Build arcs
    arcs_svg = ''
    current_angle = -90  # Start from top

    for d in data:
        pct = d['count'] / total
        sweep_angle = pct * 360

        if sweep_angle < 0.5:  # Skip tiny slices
            continue

        # Calculate arc path
        start_rad = math.radians(current_angle)
        end_rad = math.radians(current_angle + sweep_angle)

        # Outer arc points
        x1_outer = cx + outer_radius * math.cos(start_rad)
        y1_outer = cy + outer_radius * math.sin(start_rad)
        x2_outer = cx + outer_radius * math.cos(end_rad)
        y2_outer = cy + outer_radius * math.sin(end_rad)

        # Inner arc points
        x1_inner = cx + inner_radius * math.cos(end_rad)
        y1_inner = cy + inner_radius * math.sin(end_rad)
        x2_inner = cx + inner_radius * math.cos(start_rad)
        y2_inner = cy + inner_radius * math.sin(start_rad)

        large_arc = 1 if sweep_angle > 180 else 0
        color = colors_map.get(d['key'], '#6B7280')

        path = f'''M {x1_outer} {y1_outer}
                   A {outer_radius} {outer_radius} 0 {large_arc} 1 {x2_outer} {y2_outer}
                   L {x1_inner} {y1_inner}
                   A {inner_radius} {inner_radius} 0 {large_arc} 0 {x2_inner} {y2_inner}
                   Z'''

        arcs_svg += f'<path d="{path}" fill="{color}" stroke="white" stroke-width="2"/>\n'

        current_angle += sweep_angle

    # Build legend
    legend_svg = ''
    legend_y = 40
    legend_x = size + 20

    for i, d in enumerate(data[:7]):  # Max 7 items in legend
        color = colors_map.get(d['key'], '#6B7280')
        label = labels_map.get(d['key'], d['key'])
        if len(label) > 22:
            label = label[:21] + '...'
        pct = round(d['count'] / total * 100, 1)

        legend_svg += f'''
        <g transform="translate({legend_x}, {legend_y + i * 38})">
            <rect x="0" y="0" width="18" height="18" rx="4" fill="{color}"/>
            <text x="26" y="14" font-family="IBM Plex Sans" font-size="16" font-weight="600" fill="#1f1b16">{html_lib.escape(label)}</text>
            <text x="26" y="32" font-family="STIX Two Text" font-size="14" fill="#6b625a">{d['count']} ({pct}%)</text>
        </g>'''

    # Center text
    center_svg = f'''
    <text x="{cx}" y="{cy - 12}" text-anchor="middle" font-family="STIX Two Text" font-size="56" font-weight="700" fill="#1f1b16">{center_value}</text>
    <text x="{cx}" y="{cy + 22}" text-anchor="middle" font-family="IBM Plex Sans" font-size="16" fill="#6b625a">{center_label}</text>
    '''

    svg = f'''
    <svg viewBox="0 0 {size + 240} {size}" class="donut-svg">
        {arcs_svg}
        {center_svg}
        {legend_svg}
    </svg>
    '''

    return svg


def generate_html(df, lang='fr'):
    """Generate rhetoric figure with two donut charts."""
    labels = get_labels(lang)

    # Get data
    legacy_agg = aggregate_legacy_framing(df)
    speech_acts = aggregate_speech_acts(df)
    legacy_idx, legacy_meta = compute_legacy_emphasis_index(df)

    total_sentences = len(df)
    legacy_total = legacy_agg['count'].sum() if not legacy_agg.empty else 0
    acts_total = speech_acts['count'].sum() if not speech_acts.empty else 0

    # Labels
    if lang == 'fr':
        title = "Strategie rhetorique"
        subtitle = "Comment Legault construit son discours de demission"
        section1_title = "Postures adoptees"
        section2_title = "Actes de discours"
        legacy_center_label = "mentions"
        acts_center_label = "actes"
        methodology = (
            f"Methodologie : Classification de {legacy_total} mentions de postures (cadrage de l'heritage) "
            f"et {acts_total} actes de discours identifies dans les {total_sentences} phrases."
        )
    else:
        title = "Rhetorical Strategy"
        subtitle = "How Legault constructs his resignation speech"
        section1_title = "Adopted stances"
        section2_title = "Speech acts"
        legacy_center_label = "mentions"
        acts_center_label = "acts"
        methodology = (
            f"Methodology: Classification of {legacy_total} stance mentions (legacy framing) "
            f"and {acts_total} speech acts identified in {total_sentences} sentences."
        )

    framing_labels = labels.get('legacy_framing', {})
    act_labels = labels.get('speech_act', {})

    # Prepare data for donuts
    legacy_data = [{'key': row['legacy_framing'], 'count': row['count']}
                   for _, row in legacy_agg.iterrows()]
    acts_data = [{'key': row['speech_act'], 'count': row['count']}
                 for _, row in speech_acts.iterrows()]

    # Build donut SVGs
    legacy_donut = build_donut_svg(legacy_data, LEGACY_FRAMING_COLORS, framing_labels,
                                    legacy_total, legacy_center_label)
    acts_donut = build_donut_svg(acts_data, SPEECH_ACT_COLORS, act_labels,
                                  acts_total, acts_center_label)

    html = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <title>{html_lib.escape(title)}</title>
    <link href="https://fonts.googleapis.com/css2?family=STIX+Two+Text:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #fbf8f2;
            --bg-deep: #f1ede6;
            --card: #ffffff;
            --ink: #1f1b16;
            --muted: #6b625a;
            --line: #e7e1d8;
            --accent: {QUEBEC_BLUE};
            --shadow-soft: 0 10px 24px rgba(31, 27, 22, 0.06);
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: 1920px;
            height: 1080px;
            background:
                radial-gradient(900px 500px at 12% 0%, rgba(0, 61, 165, 0.12), transparent 70%),
                radial-gradient(800px 600px at 90% 12%, rgba(180, 83, 9, 0.12), transparent 72%),
                linear-gradient(180deg, var(--bg) 0%, var(--bg-deep) 100%);
            font-family: 'IBM Plex Sans', sans-serif;
            color: var(--ink);
            overflow: hidden;
        }}
        .container {{
            padding: 52px 90px 40px;
            height: 100%;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }}

        /* Header */
        .header {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--ink);
        }}
        .header-left {{ flex: 1; }}
        .main-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 62px;
            font-weight: 600;
            letter-spacing: -0.02em;
            line-height: 1.1;
        }}
        .subtitle {{
            font-size: 21px;
            color: var(--muted);
            margin-top: 8px;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }}
        .header-stat {{
            text-align: right;
        }}
        .stat-number {{
            font-family: 'STIX Two Text', serif;
            font-size: 66px;
            font-weight: 700;
            color: var(--ink);
            line-height: 1;
        }}
        .stat-label {{
            font-size: 16px;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        /* Main content - two columns */
        .main-content {{
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            min-height: 0;
            overflow: hidden;
            padding: 10px 20px;
        }}

        /* Donut section */
        .donut-section {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .section-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 32px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 16px;
            text-align: center;
        }}
        .donut-container {{
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .donut-svg {{
            width: 760px;
            height: 520px;
        }}

        /* Footer */
        .methodology {{
            margin-top: auto;
            padding-top: 10px;
        }}
        .methodology-text {{
            font-size: 15px;
            color: var(--muted);
            border-top: 1px solid var(--line);
            padding-top: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="header-left">
                <h1 class="main-title">{html_lib.escape(title)}</h1>
                <p class="subtitle">{html_lib.escape(subtitle)}</p>
            </div>
            <div class="header-stat">
                <div class="stat-number">{legacy_idx:.0%}</div>
                <div class="stat-label">{"du discours sur l'heritage" if lang == 'fr' else "of speech on legacy"}</div>
            </div>
        </header>

        <div class="main-content">
            <!-- Left: Legacy Framing Donut -->
            <div class="donut-section">
                <h2 class="section-title">{html_lib.escape(section1_title)}</h2>
                <div class="donut-container">
                    {legacy_donut}
                </div>
            </div>

            <!-- Right: Speech Acts Donut -->
            <div class="donut-section">
                <h2 class="section-title">{html_lib.escape(section2_title)}</h2>
                <div class="donut-container">
                    {acts_donut}
                </div>
            </div>
        </div>

        <footer class="methodology">
            <p class="methodology-text">{html_lib.escape(methodology)}</p>
        </footer>
    </div>
</body>
</html>'''

    return html


# =============================================================================
# MAIN
# =============================================================================

def main(df=None, export_png=True):
    """Generate rhetoric figure."""
    if df is None:
        df = load_data()

    reset_excerpts()

    for lang in ['fr', 'en']:
        html_content = generate_html(df, lang)
        save_figure(html_content, OUTPUT_DIR, f'fig7_rhetoric_{lang}', export_png=export_png)


if __name__ == '__main__':
    main()
