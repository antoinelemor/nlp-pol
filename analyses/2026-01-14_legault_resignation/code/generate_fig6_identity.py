#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig6_identity.py

MAIN OBJECTIVE:
---------------
Generate figure analyzing identity themes in Legault's resignation speech.
Shows Quebec nationalist themes, language identity, and cultural references.

Dependencies:
-------------
- config (colors, labels)
- load_and_validate (data loading)
- compute_indices (aggregation)
- html_utils (HTML generation, export)

MAIN FEATURES:
--------------
1) Identity theme distribution with N (%) format
2) Stance on identity issues
3) Identity emphasis index
4) Representative excerpts with quotes under bars

Author:
-------
Antoine Lemor
"""

import html as html_lib
import json
import pandas as pd

from config import (
    get_labels, IDENTITY_THEME_COLORS, IDENTITY_STANCE_COLORS, QUEBEC_BLUE,
    POSITIVE_COLOR, NEGATIVE_COLOR
)
from load_and_validate import load_data, OUTPUT_DIR, extract_identity_themes
from compute_indices import (
    aggregate_identity_themes,
    compute_identity_emphasis_index,
    get_excerpts_for_nested_category,
    reset_excerpts
)
from html_utils import save_figure


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_identity_stance_excerpt(df, stance, limit=1):
    """Get excerpt for a specific identity stance."""
    results = []
    for idx, row in df.iterrows():
        ann = row.get('annotation')
        if pd.notna(ann):
            try:
                data = json.loads(ann)
                id_themes = data.get('identity_themes', {})
                if isinstance(id_themes, dict) and id_themes.get('present'):
                    if id_themes.get('stance') == stance:
                        text = row['text']
                        if len(text) >= 60:
                            results.append(text)
                            if len(results) >= limit:
                                return results
            except:
                pass
    return results


def get_theme_stance_flows(df):
    """Get flow data for Sankey diagram: theme -> stance connections."""
    from collections import Counter
    flows = []
    for idx, row in df.iterrows():
        ann = row.get('annotation')
        if pd.notna(ann):
            try:
                data = json.loads(ann)
                id_themes = data.get('identity_themes', {})
                if isinstance(id_themes, dict) and id_themes.get('present'):
                    themes = id_themes.get('theme', [])
                    stance = id_themes.get('stance', '')
                    if isinstance(themes, list):
                        for theme in themes:
                            if theme and stance:
                                flows.append((theme, stance))
                    elif themes and stance:
                        flows.append((themes, stance))
            except:
                pass
    return Counter(flows)


# =============================================================================
# FIGURE GENERATION
# =============================================================================

def generate_html(df, lang='fr', theme_excerpts=None, stance_excerpts=None):
    """Generate identity themes figure HTML for specified language."""
    labels = get_labels(lang)

    # Get data
    identity_df = extract_identity_themes(df)
    identity_agg = aggregate_identity_themes(df)
    identity_idx, identity_meta = compute_identity_emphasis_index(df)

    # Count by theme and stance
    if not identity_df.empty:
        theme_counts = identity_df['identity_theme'].value_counts().to_dict()
        stance_counts = identity_df['identity_stance'].value_counts().to_dict()
    else:
        theme_counts = {}
        stance_counts = {}

    total_mentions = len(identity_df)
    total_sentences = len(df)
    identity_pct = round(identity_idx * 100)

    # Title and subtitle
    if lang == 'fr':
        title = "Thèmes identitaires"
        subtitle = "Références à l'identité québécoise dans le discours"
        section1_title = "Distribution des thèmes"
        section1_desc = "Sujets liés à l'identité québécoise"
        section2_title = "Posture identitaire"
        section2_desc = "Type de positionnement sur ces enjeux"
        stat_label = "du discours sur l'identité"
        methodology = (
            f"Méthodologie : Identification de {total_mentions} références identitaires. "
            f"Indice = proportion de phrases contenant un thème identitaire ({identity_meta['n']}/{total_sentences})."
        )
        quote_open, quote_close = '«\u202F', '\u202F»'
    else:
        title = "Identity Themes"
        subtitle = "References to Quebec identity in the speech"
        section1_title = "Theme distribution"
        section1_desc = "Topics related to Quebec identity"
        section2_title = "Identity stance"
        section2_desc = "Type of positioning on these issues"
        stat_label = "of speech on identity"
        methodology = (
            f"Methodology: Identification of {total_mentions} identity references. "
            f"Index = proportion of sentences containing an identity theme ({identity_meta['n']}/{total_sentences})."
        )
        quote_open, quote_close = '"', '"'

    theme_labels = labels.get('identity_theme', {})

    # Build themes HTML with quotes under bars
    themes_html = ''
    max_count = identity_agg['count'].max() if not identity_agg.empty else 1

    for _, row in identity_agg.iterrows():
        theme = row['identity_theme']
        count = row['count']
        pct = round(count / total_mentions * 100, 1) if total_mentions > 0 else 0
        bar_width = (count / max_count) * 100
        color = IDENTITY_THEME_COLORS.get(theme, QUEBEC_BLUE)
        label = theme_labels.get(theme, theme)

        # Get excerpt (use pre-extracted if available)
        if theme_excerpts is not None:
            quote_text = theme_excerpts.get(theme, '')
        else:
            excerpts = get_excerpts_for_nested_category(df, 'identity_themes', 'theme', theme, limit=1)
            quote_text = excerpts[0]['text'] if excerpts else ''
        # Show full quote without truncation

        quote_html = ''
        if quote_text:
            quote_html = f'''
            <blockquote class="item-quote" style="border-left-color: {color};">
                <span class="quote-text">{quote_open}{html_lib.escape(quote_text)}{quote_close}</span>
            </blockquote>
            '''

        themes_html += f'''
        <div class="item">
            <div class="item-header">
                <span class="item-dot" style="background: {color};"></span>
                <span class="item-name">{html_lib.escape(label)}</span>
                <span class="item-stat">{count} <span class="item-pct">({pct}%)</span></span>
            </div>
            <div class="item-bar-track">
                <div class="item-bar" style="width: {bar_width}%; background: {color};"></div>
            </div>
            {quote_html}
        </div>
        '''

    # Build stance HTML with quotes
    stances_html = ''
    total_stances = sum(stance_counts.values()) if stance_counts else 1
    max_stance_count = max(stance_counts.values()) if stance_counts else 1

    stance_labels_map = {
        'fr': {'DEFENSIVE': 'Défensif', 'CELEBRATORY': 'Célébratoire', 'CONCERNED': 'Préoccupé', 'ASSERTIVE': 'Affirmatif'},
        'en': {'DEFENSIVE': 'Defensive', 'CELEBRATORY': 'Celebratory', 'CONCERNED': 'Concerned', 'ASSERTIVE': 'Assertive'}
    }

    for stance, count in sorted(stance_counts.items(), key=lambda x: -x[1])[:4]:
        pct = round(count / total_stances * 100, 1) if total_stances > 0 else 0
        bar_width = (count / max_stance_count) * 100
        color = IDENTITY_STANCE_COLORS.get(stance, '#6B7280')
        label = stance_labels_map.get(lang, {}).get(stance, stance)

        # Get excerpt for this stance (use pre-extracted if available)
        if stance_excerpts is not None:
            quote_text = stance_excerpts.get(stance, '')
        else:
            stance_excerpt_list = get_identity_stance_excerpt(df, stance, limit=1)
            quote_text = stance_excerpt_list[0] if stance_excerpt_list else ''
        # Show full quote without truncation

        quote_html = ''
        if quote_text:
            quote_html = f'''
            <blockquote class="item-quote-small" style="border-left-color: {color};">
                <span class="quote-text">{quote_open}{html_lib.escape(quote_text)}{quote_close}</span>
            </blockquote>
            '''

        stances_html += f'''
        <div class="item-small">
            <div class="item-header">
                <span class="item-dot" style="background: {color};"></span>
                <span class="item-name">{html_lib.escape(label)}</span>
                <span class="item-stat">{count} <span class="item-pct">({pct}%)</span></span>
            </div>
            <div class="item-bar-track-small">
                <div class="item-bar" style="width: {bar_width}%; background: {color};"></div>
            </div>
            {quote_html}
        </div>
        '''

    # If no themes, show placeholder
    if not themes_html:
        if lang == 'fr':
            themes_html = '<p style="color: var(--muted); padding: 20px;">Aucun thème identitaire explicite détecté.</p>'
        else:
            themes_html = '<p style="color: var(--muted); padding: 20px;">No explicit identity theme detected.</p>'

    # Build Sankey diagram SVG
    flows = get_theme_stance_flows(df)
    sankey_title = "Thèmes × Postures" if lang == 'fr' else "Themes × Stances"

    # Get unique themes and stances from flows
    themes_in_flows = list(dict.fromkeys([t for (t, s) in flows.keys()]))
    stances_in_flows = list(dict.fromkeys([s for (t, s) in flows.keys()]))

    # Sort themes by total flow (descending)
    theme_totals = {}
    for (t, s), count in flows.items():
        theme_totals[t] = theme_totals.get(t, 0) + count
    themes_in_flows = sorted(themes_in_flows, key=lambda x: -theme_totals.get(x, 0))

    # Sort stances by total flow (descending)
    stance_totals = {}
    for (t, s), count in flows.items():
        stance_totals[s] = stance_totals.get(s, 0) + count
    stances_in_flows = sorted(stances_in_flows, key=lambda x: -stance_totals.get(x, 0))

    # SVG dimensions - compact
    svg_width = 360
    svg_height = 220
    left_x = 90
    right_x = 270
    node_height = 16
    node_gap = 6

    # Calculate theme positions (left side)
    total_theme_height = len(themes_in_flows) * node_height + (len(themes_in_flows) - 1) * node_gap
    theme_start_y = (svg_height - total_theme_height) / 2
    theme_positions = {}
    for i, theme in enumerate(themes_in_flows):
        theme_positions[theme] = theme_start_y + i * (node_height + node_gap) + node_height / 2

    # Calculate stance positions (right side)
    total_stance_height = len(stances_in_flows) * node_height + (len(stances_in_flows) - 1) * node_gap
    stance_start_y = (svg_height - total_stance_height) / 2
    stance_positions = {}
    for i, stance in enumerate(stances_in_flows):
        stance_positions[stance] = stance_start_y + i * (node_height + node_gap) + node_height / 2

    # Build SVG paths and labels
    sankey_paths = ''
    max_flow = max(flows.values()) if flows else 1

    for (theme, stance), count in flows.items():
        if theme in theme_positions and stance in stance_positions:
            y1 = theme_positions[theme]
            y2 = stance_positions[stance]
            stroke_width = max(2, (count / max_flow) * 12)
            theme_color = IDENTITY_THEME_COLORS.get(theme, QUEBEC_BLUE)
            stance_color = IDENTITY_STANCE_COLORS.get(stance, '#6B7280')

            # Curved path
            cx1 = left_x + 60
            cx2 = right_x - 60
            sankey_paths += f'''
            <path d="M {left_x + 5} {y1} C {cx1} {y1}, {cx2} {y2}, {right_x - 5} {y2}"
                  fill="none" stroke="{theme_color}" stroke-width="{stroke_width}"
                  stroke-opacity="0.5" stroke-linecap="round"/>'''

    # Theme labels (left)
    theme_labels_svg = ''
    for theme, y in theme_positions.items():
        label = theme_labels.get(theme, theme)
        # Truncate long labels
        if len(label) > 12:
            label = label[:11] + '…'
        theme_labels_svg += f'''
        <text x="{left_x - 8}" y="{y + 4}" text-anchor="end"
              font-family="IBM Plex Sans" font-size="11" font-weight="600"
              fill="#1f1b16">{html_lib.escape(label)}</text>'''

    # Stance labels (right)
    stance_labels_map = {
        'fr': {'DEFENSIVE': 'Défensif', 'CELEBRATORY': 'Célébratoire', 'CONCERNED': 'Préoccupé', 'ASSERTIVE': 'Affirmatif'},
        'en': {'DEFENSIVE': 'Defensive', 'CELEBRATORY': 'Celebratory', 'CONCERNED': 'Concerned', 'ASSERTIVE': 'Assertive'}
    }
    stance_labels_svg = ''
    for stance, y in stance_positions.items():
        label = stance_labels_map.get(lang, {}).get(stance, stance)
        color = IDENTITY_STANCE_COLORS.get(stance, '#6B7280')
        stance_labels_svg += f'''
        <text x="{right_x + 8}" y="{y + 4}" text-anchor="start"
              font-family="IBM Plex Sans" font-size="11" font-weight="600"
              fill="{color}">{html_lib.escape(label)}</text>'''

    # Theme dots (left)
    theme_dots_svg = ''
    for theme, y in theme_positions.items():
        color = IDENTITY_THEME_COLORS.get(theme, QUEBEC_BLUE)
        theme_dots_svg += f'''
        <circle cx="{left_x}" cy="{y}" r="5" fill="{color}"/>'''

    # Stance dots (right)
    stance_dots_svg = ''
    for stance, y in stance_positions.items():
        color = IDENTITY_STANCE_COLORS.get(stance, '#6B7280')
        stance_dots_svg += f'''
        <circle cx="{right_x}" cy="{y}" r="5" fill="{color}"/>'''

    sankey_svg = f'''
    <svg class="sankey-svg" viewBox="0 0 {svg_width} {svg_height}">
        {sankey_paths}
        {theme_dots_svg}
        {stance_dots_svg}
        {theme_labels_svg}
        {stance_labels_svg}
    </svg>
    '''

    # Index color (kept for potential use)
    idx_color = QUEBEC_BLUE

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

        /* Main content */
        .main-content {{
            flex: 1;
            display: grid;
            grid-template-columns: 1.4fr 1fr;
            gap: 30px;
            min-height: 0;
            overflow: hidden;
        }}

        /* Section styling */
        .section {{
            display: flex;
            flex-direction: column;
        }}
        .section-header {{
            margin-bottom: 12px;
        }}
        .section-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 24px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 4px;
        }}
        .section-desc {{
            font-size: 15px;
            color: var(--muted);
        }}

        /* Item styling */
        .item {{
            margin-bottom: 10px;
        }}
        .item-small {{
            margin-bottom: 4px;
        }}
        .item-header {{
            display: flex;
            align-items: center;
            margin-bottom: 4px;
        }}
        .item-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        .item-name {{
            font-weight: 600;
            font-size: 16px;
            color: var(--ink);
            flex: 1;
        }}
        .item-stat {{
            font-family: 'STIX Two Text', serif;
            font-size: 18px;
            font-weight: 600;
            color: var(--ink);
        }}
        .item-pct {{
            font-size: 13px;
            font-weight: 400;
            color: var(--muted);
        }}
        .item-bar-track {{
            height: 12px;
            background: var(--bg-deep);
            border-radius: 6px;
            margin-bottom: 4px;
        }}
        .item-bar-track-small {{
            height: 10px;
            background: var(--bg-deep);
            border-radius: 5px;
        }}
        .item-bar {{
            height: 100%;
            border-radius: inherit;
        }}
        .item-quote {{
            font-family: 'STIX Two Text', serif;
            font-size: 13px;
            color: var(--ink);
            line-height: 1.4;
            padding: 5px 10px 5px 12px;
            border-left: 4px solid var(--line);
            border-radius: 6px;
            background: var(--card);
            margin-top: 4px;
            margin-bottom: 6px;
        }}
        .item-quote .quote-text {{
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        .item-quote-small {{
            font-family: 'STIX Two Text', serif;
            font-size: 11px;
            color: var(--ink);
            line-height: 1.3;
            padding: 3px 6px 3px 8px;
            border-left: 2px solid var(--line);
            border-radius: 4px;
            background: var(--card);
            margin-top: 2px;
            margin-bottom: 3px;
        }}
        .item-quote-small .quote-text {{
            display: -webkit-box;
            -webkit-line-clamp: 1;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        /* Right column */
        .right-column {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        /* Sankey diagram */
        .sankey-card {{
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow-soft);
            padding: 16px 20px;
            flex: 1;
        }}
        .sankey-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 18px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 8px;
            text-align: center;
        }}
        .sankey-svg {{
            width: 100%;
            height: auto;
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
                <div class="stat-number">{identity_pct}%</div>
                <div class="stat-label">{stat_label}</div>
            </div>
        </header>

        <div class="main-content">
            <!-- Left: Identity themes -->
            <div class="section">
                <div class="section-header">
                    <h2 class="section-title">{html_lib.escape(section1_title)}</h2>
                    <p class="section-desc">{html_lib.escape(section1_desc)}</p>
                </div>
                {themes_html}
            </div>

            <!-- Right: Stance + Index -->
            <div class="right-column">
                <div class="section">
                    <div class="section-header">
                        <h2 class="section-title">{html_lib.escape(section2_title)}</h2>
                        <p class="section-desc">{html_lib.escape(section2_desc)}</p>
                    </div>
                    {stances_html}
                </div>

                <div class="sankey-card">
                    <h3 class="sankey-title">{html_lib.escape(sankey_title)}</h3>
                    {sankey_svg}
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
    """Generate identity themes figure."""
    if df is None:
        df = load_data()

    # Reset excerpt registry to ensure fresh extraction
    reset_excerpts()

    # Pre-extract excerpts BEFORE language loop to ensure both FR and EN get the same quotes
    identity_agg = aggregate_identity_themes(df)
    theme_excerpts = {}
    for _, row in identity_agg.iterrows():
        theme = row['identity_theme']
        excerpts = get_excerpts_for_nested_category(df, 'identity_themes', 'theme', theme, limit=1)
        theme_excerpts[theme] = excerpts[0]['text'] if excerpts else ''

    # Pre-extract stance excerpts
    identity_df = extract_identity_themes(df)
    stance_counts = identity_df['identity_stance'].value_counts().to_dict() if not identity_df.empty else {}
    stance_excerpts = {}
    for stance in stance_counts.keys():
        excerpts = get_identity_stance_excerpt(df, stance, limit=1)
        stance_excerpts[stance] = excerpts[0] if excerpts else ''

    for lang in ['fr', 'en']:
        html_content = generate_html(df, lang, theme_excerpts, stance_excerpts)
        save_figure(html_content, OUTPUT_DIR, f'fig6_identity_{lang}', export_png=export_png)


if __name__ == '__main__':
    main()
