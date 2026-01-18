#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig3_policy_domains.py

MAIN OBJECTIVE:
---------------
Generate figure analyzing policy domains mentioned in Legault's resignation speech.
Uses CAP categories with quotes directly under each domain bar.

Dependencies:
-------------
- config (colors, labels)
- load_and_validate (data loading)
- compute_indices (aggregation)
- html_utils (HTML generation, export)

MAIN FEATURES:
--------------
1) Policy domain bars with n= count and percentage
2) Quote directly under each domain bar
3) Summary statistics on the right

Author:
-------
Antoine Lemor
"""

import html as html_lib
from pathlib import Path

from config import get_labels, POLICY_DOMAIN_COLORS, QUEBEC_BLUE
from load_and_validate import load_data, OUTPUT_DIR
from compute_indices import (
    aggregate_policy_domains,
    get_excerpts_for_category
)
from html_utils import save_figure


# =============================================================================
# FIGURE GENERATION
# =============================================================================

def generate_html(df, lang='fr', domain_excerpts=None):
    """Generate policy domains figure HTML for specified language."""
    labels = get_labels(lang)

    # Get aggregated data
    domains = aggregate_policy_domains(df)

    # Calculate total
    total_mentions = domains['count'].sum() if not domains.empty else 0

    # Title and subtitle
    if lang == 'fr':
        title = "Domaines politiques abordés"
        subtitle = "Répartition thématique du discours de démission"
        section_title = "Répartition par domaine"
        section_desc = "Chaque phrase est classée selon son domaine politique principal (catégories CAP)."
        methodology = (
            f"Méthodologie : Classification de {total_mentions} phrases selon les catégories "
            f"du Comparative Agendas Project (CAP) adaptées au contexte québécois."
        )
    else:
        title = "Policy Domains Addressed"
        subtitle = "Thematic distribution of the resignation speech"
        section_title = "Distribution by domain"
        section_desc = "Each sentence is classified by its main policy domain (CAP categories)."
        methodology = (
            f"Methodology: Classification of {total_mentions} sentences using "
            f"Comparative Agendas Project (CAP) categories adapted for Quebec context."
        )

    domain_labels = labels['policy_domain']
    treemap_title = "Vue d'ensemble" if lang == 'fr' else "Overview"

    # Build domain items HTML with quotes under each bar - show ALL domains
    domains_html = ''
    max_count = domains['count'].max() if not domains.empty else 1

    # Collect data for visualization
    treemap_data = []

    for _, row in domains.iterrows():
        domain = row['policy_domain']
        count = row['count']
        pct = row['percentage']
        bar_width = (count / max_count) * 100
        color = POLICY_DOMAIN_COLORS.get(domain, '#6B7280')
        label = domain_labels.get(domain, domain)

        # Store for treemap
        treemap_data.append({
            'domain': domain,
            'label': label,
            'count': count,
            'pct': pct,
            'color': color
        })

        # Get excerpt for this domain (use pre-extracted if available)
        if domain_excerpts is not None:
            quote_text = domain_excerpts.get(domain, '')
        else:
            excerpts = get_excerpts_for_category(df, 'policy_domain', domain, limit=1)
            quote_text = excerpts[0]['text'] if excerpts else ''

        # Show full quotes without truncation

        quote_html = ''
        if quote_text:
            quote_html = f'''
            <blockquote class="domain-quote" style="border-left-color: {color};">
                <span class="quote-text">« {html_lib.escape(quote_text)} »</span>
            </blockquote>
            '''

        domains_html += f'''
        <div class="domain-item">
            <div class="domain-header">
                <span class="domain-dot" style="background: {color};"></span>
                <span class="domain-name">{html_lib.escape(label)}</span>
                <span class="domain-stat">{count} <span class="domain-pct">({pct}%)</span></span>
            </div>
            <div class="domain-bar-track">
                <div class="domain-bar" style="width: {bar_width}%; background: {color};"></div>
            </div>
            {quote_html}
        </div>
        '''

    # Build sunburst SVG - radial bars from center
    import math
    sunburst_html = ''
    if treemap_data:
        # SVG parameters - maximize chart within container
        size = 400
        cx, cy = size / 2, size / 2
        inner_radius = 60  # Space for center text
        max_bar_length = 115  # Maximum bar length
        bar_width = 22
        num_domains = len(treemap_data)
        angle_step = 360 / num_domains
        max_pct = max(d['pct'] for d in treemap_data)

        bars_svg = ''
        labels_svg = ''

        for i, d in enumerate(treemap_data):
            angle_deg = i * angle_step - 90  # Start from top
            angle_rad = math.radians(angle_deg)

            # Bar length proportional to percentage
            bar_length = (d['pct'] / max_pct) * max_bar_length if max_pct > 0 else 20

            # Bar start and end positions
            x1 = cx + inner_radius * math.cos(angle_rad)
            y1 = cy + inner_radius * math.sin(angle_rad)
            x2 = cx + (inner_radius + bar_length) * math.cos(angle_rad)
            y2 = cy + (inner_radius + bar_length) * math.sin(angle_rad)

            # Draw bar as a line with rounded caps
            bars_svg += f'''
            <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
                  stroke="{d['color']}" stroke-width="{bar_width}"
                  stroke-linecap="round"/>'''

            # Label position (at end of bar + offset)
            label_radius = inner_radius + bar_length + 15
            lx = cx + label_radius * math.cos(angle_rad)
            ly = cy + label_radius * math.sin(angle_rad)

            # Determine text anchor and alignment based on angle
            # Right side (roughly -90 to 90): text starts from bar end
            # Left side (roughly 90 to 270): text ends at bar end
            normalized_angle = angle_deg % 360
            if normalized_angle < 0:
                normalized_angle += 360

            if normalized_angle <= 90 or normalized_angle > 270:
                # Right side - text goes outward
                anchor = "start"
                text_x = 8
            else:
                # Left side - text goes outward (but anchor at end)
                anchor = "end"
                # Special case: bring "Politique linguistique" closer to avoid cutoff
                if d['domain'] == 'LANGUAGE_POLICY':
                    text_x = -2
                else:
                    text_x = -8

            # Keep labels horizontal (no rotation) for better readability
            labels_svg += f'''
            <g transform="translate({lx},{ly})">
                <text x="{text_x}" y="-3" text-anchor="{anchor}"
                      font-family="IBM Plex Sans" font-size="11" font-weight="600"
                      fill="#1f1b16">{html_lib.escape(d['label'])}</text>
                <text x="{text_x}" y="11" text-anchor="{anchor}"
                      font-family="STIX Two Text" font-size="13" font-weight="700"
                      fill="{d['color']}">{d['pct']}%</text>
            </g>'''

        center_label = "phrases" if lang == 'fr' else "sentences"

        sunburst_html = f'''
        <svg class="sunburst-svg" viewBox="0 0 {size} {size}">
            {bars_svg}
            {labels_svg}
            <circle cx="{cx}" cy="{cy}" r="{inner_radius - 5}" fill="white"/>
            <text x="{cx}" y="{cy - 4}" text-anchor="middle"
                  font-family="STIX Two Text" font-size="30" font-weight="700"
                  fill="#1f1b16">{total_mentions}</text>
            <text x="{cx}" y="{cy + 14}" text-anchor="middle"
                  font-family="IBM Plex Sans" font-size="10" font-weight="400"
                  fill="#6b625a">{center_label}</text>
        </svg>
        '''

    # Header stat
    unique_domains = len(domains) if not domains.empty else 0

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
            margin-top: 4px;
        }}

        /* Main content - two columns */
        .main-content {{
            flex: 1;
            display: grid;
            grid-template-columns: 1.6fr 0.8fr;
            gap: 40px;
            min-height: 0;
            overflow: hidden;
        }}

        .left-column {{
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }}

        .right-column {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            height: 100%;
        }}

        .section-header {{
            margin-bottom: 16px;
        }}
        .section-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 24px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 4px;
        }}
        .section-desc {{
            font-size: 16px;
            color: var(--muted);
            line-height: 1.35;
        }}

        /* Sunburst chart */
        .sunburst-container {{
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow-soft);
            padding: 8px 4px;
            overflow: visible;
        }}
        .sunburst-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 20px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 0;
            text-align: center;
        }}
        .sunburst-content {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: visible;
        }}
        .sunburst-svg {{
            width: 100%;
            height: 100%;
        }}

        /* Domain items */
        .domain-item {{
            margin-bottom: 8px;
        }}
        .domain-header {{
            display: flex;
            align-items: center;
            margin-bottom: 3px;
        }}
        .domain-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .domain-name {{
            font-weight: 600;
            font-size: 15px;
            color: var(--ink);
            flex: 1;
        }}
        .domain-stat {{
            font-family: 'STIX Two Text', serif;
            font-size: 18px;
            font-weight: 600;
            color: var(--ink);
        }}
        .domain-pct {{
            font-size: 13px;
            font-weight: 400;
            color: var(--muted);
        }}
        .domain-bar-track {{
            height: 10px;
            background: var(--bg-deep);
            border-radius: 5px;
            margin-bottom: 3px;
        }}
        .domain-bar {{
            height: 100%;
            border-radius: 5px;
        }}
        .domain-quote {{
            font-family: 'STIX Two Text', serif;
            font-size: 13px;
            color: var(--ink);
            line-height: 1.4;
            padding: 4px 10px 4px 12px;
            border-left: 3px solid var(--line);
            border-radius: 4px;
            background: var(--card);
            margin-top: 2px;
            margin-bottom: 6px;
        }}
        .domain-quote .quote-text {{
            font-size: 13px;
            color: var(--ink);
            display: -webkit-box;
            -webkit-line-clamp: 1;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* Footer */
        .methodology {{
            margin-top: auto;
            padding-top: 10px;
        }}
        .methodology-text {{
            font-size: 16px;
            color: var(--muted);
            text-align: left;
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
                <div class="stat-number">{total_mentions}</div>
                <div class="stat-label">{"phrases classées" if lang == 'fr' else "sentences classified"}</div>
            </div>
        </header>

        <div class="main-content">
            <!-- Left: Domain bars with quotes -->
            <div class="left-column">
                <div class="section-header">
                    <h2 class="section-title">{html_lib.escape(section_title)}</h2>
                    <p class="section-desc">{html_lib.escape(section_desc)}</p>
                </div>
                {domains_html}
            </div>

            <!-- Right: Sunburst chart -->
            <div class="right-column">
                <div class="sunburst-container">
                    <h3 class="sunburst-title">{html_lib.escape(treemap_title)}</h3>
                    <div class="sunburst-content">
                        {sunburst_html}
                    </div>
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
    """Generate policy domains figure."""
    if df is None:
        df = load_data()

    # Pre-extract excerpts BEFORE language loop to ensure both FR and EN get the same quotes
    domains = aggregate_policy_domains(df)
    domain_excerpts = {}
    for _, row in domains.iterrows():
        domain = row['policy_domain']
        excerpts = get_excerpts_for_category(df, 'policy_domain', domain, limit=1)
        domain_excerpts[domain] = excerpts[0]['text'] if excerpts else ''

    for lang in ['fr', 'en']:
        html_content = generate_html(df, lang, domain_excerpts)
        save_figure(html_content, OUTPUT_DIR, f'fig3_policy_domains_{lang}', export_png=export_png)


if __name__ == '__main__':
    main()
