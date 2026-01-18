#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig3b_domain_acts.py

MAIN OBJECTIVE:
---------------
Generate figure crossing policy domains with speech acts in Legault's resignation speech.
Shows which communicative functions are used for each policy domain via Sankey diagram.

Dependencies:
-------------
- config (colors, labels)
- load_and_validate (data loading)
- compute_indices (aggregation)
- html_utils (HTML generation, export)

MAIN FEATURES:
--------------
1) Policy domain distribution (left)
2) Sankey diagram showing domain -> speech act flows (center)
3) Speech acts distribution (right)

Author:
-------
Antoine Lemor
"""

import html as html_lib
import json
from collections import Counter

import pandas as pd

from config import (
    get_labels, POLICY_DOMAIN_COLORS, SPEECH_ACT_COLORS, QUEBEC_BLUE
)
from load_and_validate import load_data, OUTPUT_DIR
from compute_indices import aggregate_policy_domains, aggregate_speech_acts
from html_utils import save_figure


def get_domain_act_flows(df):
    """Get flow data for Sankey: policy_domain -> speech_act connections."""
    flows = []
    for idx, row in df.iterrows():
        ann = row.get('annotation')
        if pd.notna(ann):
            try:
                data = json.loads(ann)
                domains = data.get('policy_domain', [])
                acts = data.get('speech_act', [])

                # Normalize to lists
                if isinstance(domains, str):
                    domains = [domains]
                if isinstance(acts, str):
                    acts = [acts]

                # Create flows for each domain-act pair
                for domain in domains:
                    if domain and domain != 'NONE':
                        for act in acts:
                            if act and isinstance(act, str):
                                flows.append((domain, act))
            except:
                pass
    return Counter(flows)


def generate_html(df, lang='fr'):
    """Generate domain x speech acts figure with Sankey diagram."""
    labels = get_labels(lang)

    # Get data
    domains_agg = aggregate_policy_domains(df)
    speech_acts = aggregate_speech_acts(df)
    flows = get_domain_act_flows(df)

    total_sentences = len(df)

    # Labels
    if lang == 'fr':
        title = "Domaines et actes de discours"
        subtitle = "Quelle fonction communicative pour chaque thematique"
        section1_title = "Domaines politiques"
        section2_title = "Actes de discours"
        sankey_label = "Domaine -> Acte"
        methodology = (
            f"Methodologie : Analyse croisee des {total_sentences} phrases par domaine politique (CAP) "
            f"et acte de discours. Les flux montrent quels actes sont utilises pour chaque domaine."
        )
    else:
        title = "Domains and Speech Acts"
        subtitle = "Which communicative function for each policy area"
        section1_title = "Policy domains"
        section2_title = "Speech acts"
        sankey_label = "Domain -> Act"
        methodology = (
            f"Methodology: Cross-analysis of {total_sentences} sentences by policy domain (CAP) "
            f"and speech act. Flows show which acts are used for each domain."
        )

    domain_labels = labels.get('policy_domain', {})
    act_labels = labels.get('speech_act', {})

    # Filter out NONE domain
    domains_agg = domains_agg[domains_agg['policy_domain'] != 'NONE']

    # Build domain bars HTML - show ALL
    domain_html = ''
    max_domain = domains_agg['count'].max() if not domains_agg.empty else 1

    for _, row in domains_agg.iterrows():
        domain = row['policy_domain']
        count = row['count']
        bar_width = (count / max_domain) * 100
        color = POLICY_DOMAIN_COLORS.get(domain, '#6B7280')
        label = domain_labels.get(domain, domain)

        domain_html += f'''
        <div class="item-compact">
            <div class="item-header-compact">
                <span class="item-dot-small" style="background: {color};"></span>
                <span class="item-name-compact">{html_lib.escape(label)}</span>
                <span class="item-stat-compact">{count}</span>
            </div>
            <div class="item-bar-track-compact">
                <div class="item-bar" style="width: {bar_width}%; background: {color};"></div>
            </div>
        </div>
        '''

    # Build speech acts bars HTML - limit to top 8 to avoid cutoff
    acts_html = ''
    max_acts = speech_acts['count'].max() if not speech_acts.empty else 1

    for _, row in speech_acts.head(8).iterrows():
        act = row['speech_act']
        count = row['count']
        bar_width = (count / max_acts) * 100
        color = SPEECH_ACT_COLORS.get(act, '#6B7280')
        label = act_labels.get(act, act)

        acts_html += f'''
        <div class="item-compact">
            <div class="item-header-compact">
                <span class="item-dot-small" style="background: {color};"></span>
                <span class="item-name-compact">{html_lib.escape(label)}</span>
                <span class="item-stat-compact">{count}</span>
            </div>
            <div class="item-bar-track-compact">
                <div class="item-bar" style="width: {bar_width}%; background: {color};"></div>
            </div>
        </div>
        '''

    # Build Sankey diagram SVG - show ALL domains and acts
    all_domains = [row['policy_domain'] for _, row in domains_agg.iterrows()]
    all_acts = [row['speech_act'] for _, row in speech_acts.iterrows()]

    # SVG parameters - wide layout, content starts from top
    left_x = 180      # Margin for left labels
    right_x = 720     # Margin for right labels
    node_height = 32
    node_gap = 2
    top_margin = 20

    # Calculate positions for domains (left side) - start from top
    domain_positions = {}
    for i, domain in enumerate(all_domains):
        domain_positions[domain] = top_margin + i * (node_height + node_gap) + node_height / 2

    # Calculate positions for acts (right side) - start from top
    act_positions = {}
    for i, act in enumerate(all_acts):
        act_positions[act] = top_margin + i * (node_height + node_gap) + node_height / 2

    # Calculate SVG height based on actual content
    total_domain_height = len(all_domains) * node_height + (len(all_domains) - 1) * node_gap
    total_act_height = len(all_acts) * node_height + (len(all_acts) - 1) * node_gap
    svg_height = top_margin + max(total_domain_height, total_act_height) + 30  # 30px bottom margin
    svg_width = 900

    # Build paths - no filtering
    sankey_paths = ''
    max_flow = max(flows.values()) if flows else 1

    for (domain, act), count in flows.items():
        if domain in domain_positions and act in act_positions:
            y1 = domain_positions[domain]
            y2 = act_positions[act]
            stroke_width = max(1.5, (count / max_flow) * 12)
            color = POLICY_DOMAIN_COLORS.get(domain, QUEBEC_BLUE)

            cx1 = left_x + 100
            cx2 = right_x - 100
            sankey_paths += f'''
            <path d="M {left_x + 6} {y1} C {cx1} {y1}, {cx2} {y2}, {right_x - 6} {y2}"
                  fill="none" stroke="{color}" stroke-width="{stroke_width}"
                  stroke-opacity="0.35" stroke-linecap="round"/>'''

    # Helper function to split long multi-word labels into 2 lines
    def split_label(label, max_len=14):
        # Only split if there are multiple words
        words = label.split()
        if len(words) < 2:
            return [label]  # Never split single words
        if len(label) <= max_len:
            return [label]
        # Split at word boundary
        mid = len(words) // 2
        line1 = ' '.join(words[:mid])
        line2 = ' '.join(words[mid:])
        return [line1, line2]

    # Domain dots and labels (multiline)
    domain_svg = ''
    for domain, y in domain_positions.items():
        color = POLICY_DOMAIN_COLORS.get(domain, QUEBEC_BLUE)
        label = domain_labels.get(domain, domain)
        lines = split_label(label, 14)

        domain_svg += f'''
        <circle cx="{left_x}" cy="{y}" r="6" fill="{color}"/>'''

        if len(lines) == 1:
            domain_svg += f'''
        <text x="{left_x - 12}" y="{y + 4}" text-anchor="end"
              font-family="IBM Plex Sans" font-size="10" font-weight="600"
              fill="#1f1b16">{html_lib.escape(lines[0])}</text>'''
        else:
            domain_svg += f'''
        <text x="{left_x - 12}" text-anchor="end"
              font-family="IBM Plex Sans" font-size="10" font-weight="600" fill="#1f1b16">
            <tspan x="{left_x - 12}" y="{y - 2}">{html_lib.escape(lines[0])}</tspan>
            <tspan x="{left_x - 12}" y="{y + 10}">{html_lib.escape(lines[1])}</tspan>
        </text>'''

    # Act dots and labels (multiline)
    act_svg = ''
    for act, y in act_positions.items():
        color = SPEECH_ACT_COLORS.get(act, '#6B7280')
        label = act_labels.get(act, act)
        lines = split_label(label, 12)

        act_svg += f'''
        <circle cx="{right_x}" cy="{y}" r="6" fill="{color}"/>'''

        if len(lines) == 1:
            act_svg += f'''
        <text x="{right_x + 12}" y="{y + 4}" text-anchor="start"
              font-family="IBM Plex Sans" font-size="10" font-weight="600"
              fill="#1f1b16">{html_lib.escape(lines[0])}</text>'''
        else:
            act_svg += f'''
        <text x="{right_x + 12}" text-anchor="start"
              font-family="IBM Plex Sans" font-size="10" font-weight="600" fill="#1f1b16">
            <tspan x="{right_x + 12}" y="{y - 2}">{html_lib.escape(lines[0])}</tspan>
            <tspan x="{right_x + 12}" y="{y + 10}">{html_lib.escape(lines[1])}</tspan>
        </text>'''

    sankey_svg = f'''
    <svg class="sankey-svg" viewBox="0 0 {svg_width} {svg_height}">
        {sankey_paths}
        {domain_svg}
        {act_svg}
    </svg>
    '''

    # Count domains with content
    domains_with_content = len(domains_agg[domains_agg['count'] > 0])

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

        /* Main content - two columns: narrow left stacked lists, wide right sankey */
        .main-content {{
            flex: 1;
            display: grid;
            grid-template-columns: 0.35fr 1fr;
            gap: 30px;
            min-height: 0;
            overflow: hidden;
        }}

        /* Left column with stacked sections */
        .left-column {{
            display: flex;
            flex-direction: column;
            gap: 16px;
            overflow-y: auto;
        }}

        .section {{
            display: flex;
            flex-direction: column;
        }}
        .section-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 18px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 8px;
        }}

        /* Compact items */
        .item-compact {{
            margin-bottom: 6px;
        }}
        .item-header-compact {{
            display: flex;
            align-items: center;
            margin-bottom: 2px;
        }}
        .item-dot-small {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            margin-right: 6px;
        }}
        .item-name-compact {{
            font-weight: 600;
            font-size: 12px;
            color: var(--ink);
            flex: 1;
        }}
        .item-stat-compact {{
            font-family: 'STIX Two Text', serif;
            font-size: 13px;
            font-weight: 600;
            color: var(--ink);
        }}
        .item-bar-track-compact {{
            height: 6px;
            background: var(--bg-deep);
            border-radius: 3px;
        }}
        .item-bar {{
            height: 100%;
            border-radius: inherit;
        }}

        /* Sankey container */
        .sankey-container {{
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow-soft);
            padding: 16px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            overflow: visible;
        }}
        .sankey-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 20px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 8px;
            text-align: center;
        }}
        .sankey-svg {{
            width: 100%;
            flex: 1;
            min-height: 0;
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
                <div class="stat-number">{domains_with_content}</div>
                <div class="stat-label">{"domaines abordes" if lang == 'fr' else "domains addressed"}</div>
            </div>
        </header>

        <div class="main-content">
            <!-- Left: Stacked Policy Domains + Speech Acts -->
            <div class="left-column">
                <div class="section">
                    <h2 class="section-title">{html_lib.escape(section1_title)}</h2>
                    {domain_html}
                </div>
                <div class="section">
                    <h2 class="section-title">{html_lib.escape(section2_title)}</h2>
                    {acts_html}
                </div>
            </div>

            <!-- Right: Sankey diagram -->
            <div class="sankey-container">
                <h3 class="sankey-title">{html_lib.escape(sankey_label)}</h3>
                {sankey_svg}
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
    """Generate domain x speech acts figure."""
    if df is None:
        df = load_data()

    for lang in ['fr', 'en']:
        html_content = generate_html(df, lang)
        save_figure(html_content, OUTPUT_DIR, f'fig3b_domain_acts_{lang}', export_png=export_png)


if __name__ == '__main__':
    main()
