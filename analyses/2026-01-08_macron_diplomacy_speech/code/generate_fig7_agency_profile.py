#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig7_agency_profile.py

MAIN OBJECTIVE:
---------------
Analyze how Macron positions France's agency in international affairs.
Classifies positioning types (active agent, partner, leader, etc.) into
agency levels and computes a composite Agency Index.

Dependencies:
-------------
- compute_indices (load_data, prepare_agency_data)
- config (get_labels, FRANCE_POSITIONING_PALETTE)
- html_utils (COLORS, POSITIVE_COLOR, save_figure)

MAIN FEATURES:
--------------
1) Extract france_positioning annotations (active_agent, partner, leader, etc.)
2) Group into agency levels: Active/Leading, Cooperative, Reactive/Defensive
3) Compute Agency Index: weighted combination of positioning types
4) Display breakdown by positioning type and agency level
5) Generate bilingual output (FR/EN)

Author:
-------
Antoine Lemor
"""

import math
import re
from pathlib import Path
from compute_indices import load_data, prepare_agency_data
from config import get_labels, FRANCE_POSITIONING_PALETTE
from html_utils import COLORS, POSITIVE_COLOR, save_figure

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output" / "figures"


def generate_html(data, lang='fr'):
    """Generate the agency profile HTML."""
    labels = get_labels(lang)
    pos_counts = data['positioning_counts']
    categories = data['categories']
    agency_idx = data['agency_index']

    if lang == 'fr':
        title = "L'image de la France : profil d'agentivité"
        subtitle = "Comment Macron positionne-t-il la France sur la scène internationale ?"
        pos_title = "Types de positionnement"
        pos_desc = "Comment la France se présente : agent actif, leader, partenaire, modèle..."
        cat_title = "Par niveau d'agentivité"
        cat_desc = "Répartition des postures en trois familles, du leadership à la réactivité."
        cat_labels = ['Actif / Leader', 'Coopératif', 'Réactif / Défensif']
        gauge_label = "Indice d'agentivité"
        gauge_desc = "Mesure le niveau d'action : 100% = très actif, 0% = passif."
        methodology = "Méthodologie : Indice = Actif×100% + Coopératif×70% + Réactif×30%. La France est positionnée comme agent actif dans la majorité des énoncés."
        excerpts_title = "Extraits labellisés"
        quote_labels = {
            'ACTIVE': 'Actif / Leader',
            'COOPERATIVE': 'Coopératif',
            'REACTIVE': 'Réactif / Défensif',
        }
        cat_summary_prefix = "Dominant"
        if agency_idx > 0.7:
            interp = "Très actif"
        elif agency_idx > 0.5:
            interp = "Modérément actif"
        else:
            interp = "Mixte"
    else:
        title = "France's Self-Image: Agency Profile"
        subtitle = "How does Macron position France on the international stage?"
        pos_title = "Positioning Types"
        pos_desc = "How France presents itself: active agent, leader, partner, model..."
        cat_title = "By agency level"
        cat_desc = "Distribution of stances across leadership, cooperation, and reactivity."
        cat_labels = ['Active / Leading', 'Cooperative', 'Reactive / Defensive']
        gauge_label = "Agency Index"
        gauge_desc = "Measures action level: 100% = very active, 0% = passive."
        methodology = "Methodology: Index = Active×100% + Cooperative×70% + Reactive×30%. France is positioned as an active agent in most statements."
        excerpts_title = "Labeled excerpts"
        quote_labels = {
            'ACTIVE': 'Active / Leading',
            'COOPERATIVE': 'Cooperative',
            'REACTIVE': 'Reactive / Defensive',
        }
        cat_summary_prefix = "Dominant"
        if agency_idx > 0.7:
            interp = "Highly Active"
        elif agency_idx > 0.5:
            interp = "Moderately Active"
        else:
            interp = "Mixed"

    # Generate positioning bars
    total = sum(pos_counts.values())
    max_count = max(pos_counts.values()) if pos_counts else 1
    pos_bars = ""
    for pos, count in pos_counts.items():
        pct = (count / total * 100) if total > 0 else 0
        width_pct = (count / max_count) * 100
        color = FRANCE_POSITIONING_PALETTE.get(pos, COLORS['primary'])
        label = labels.get(pos, pos.replace('_', ' ').title())
        pos_bars += f'''
        <div class="pos-row">
            <div class="pos-label">{label}</div>
            <div class="pos-track">
                <div class="pos-fill" style="width: {width_pct}%; background: {color};"></div>
            </div>
            <div class="pos-value">{count} <span class="pos-pct">({pct:.0f}%)</span></div>
        </div>'''

    # Category bars
    cat_values = [categories['active'], categories['cooperative'], categories['reactive']]
    cat_colors = ['#1D4ED8', '#059669', '#D97706']
    max_cat = max(cat_values) if cat_values else 1
    if max_cat == 0:
        max_cat = 1

    cat_bars = ""
    cat_pcts = []
    for label, val, color in zip(cat_labels, cat_values, cat_colors):
        pct = (val / total * 100) if total > 0 else 0
        cat_pcts.append(pct)
        width_pct = (val / max_cat) * 100
        cat_bars += f'''
        <div class="cat-col">
            <div class="cat-bar-wrapper">
                <div class="cat-bar" style="height: {width_pct}%; background: {color};"></div>
            </div>
            <div class="cat-info">
                <span class="cat-value">{val}</span>
                <span class="cat-pct">({pct:.0f}%)</span>
            </div>
            <div class="cat-label">{label}</div>
        </div>'''

    dominant_idx = cat_values.index(max(cat_values)) if cat_values else 0
    dominant_label = cat_labels[dominant_idx]
    dominant_pct = cat_pcts[dominant_idx] if cat_pcts else 0
    cat_summary = f"{cat_summary_prefix}: {dominant_label} ({dominant_pct:.0f}%)"

    all_quotes = data.get('quotes', [])

    # Select quotes ensuring at least one from each category
    active_quotes = [q for q in all_quotes if q.get('label') == 'ACTIVE']
    coop_quotes = [q for q in all_quotes if q.get('label') == 'COOPERATIVE']
    reactive_quotes = [q for q in all_quotes if q.get('label') == 'REACTIVE']

    selected_quotes = []
    if active_quotes:
        selected_quotes.append(active_quotes[0])
    if coop_quotes:
        selected_quotes.append(coop_quotes[0])
    if reactive_quotes:
        selected_quotes.append(reactive_quotes[0])
    # Fill remaining slots with any quotes
    for q in all_quotes:
        if q not in selected_quotes and len(selected_quotes) < 4:
            selected_quotes.append(q)

    def format_quote(text):
        cleaned = ' '.join(str(text).split())
        match = re.search(r'^(.*?[.!?])(?:\s|$)', cleaned)
        return match.group(1) if match else cleaned

    def build_quote_card(q, excerpts_title, quote_labels):
        label = quote_labels.get(q.get('label', ''), q.get('label', '').title())
        return f'''
            <div class="quote-card quote-{q.get('label', '').lower()}">
                <div class="quote-meta">
                    <span class="quote-label">{label}</span>
                </div>
                <div class="quote-text">« {format_quote(q.get('text', ''))} »</div>
            </div>'''

    quote_cards_html = ""
    for q in selected_quotes[:4]:
        quote_cards_html += build_quote_card(q, excerpts_title, quote_labels)

    # Gauge
    normalized = agency_idx
    angle = 180 - (normalized * 180)
    needle_x = 150 + 100 * math.cos(math.radians(angle))
    needle_y = 150 - 100 * math.sin(math.radians(angle))

    html = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=STIX+Two+Text:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #fbf8f2;
            --bg-deep: #f1ede6;
            --card: #ffffff;
            --ink: #1f1b16;
            --muted: #6b625a;
            --line: #e7e1d8;
            --accent: #0f766e;
            --accent-soft: rgba(15, 118, 110, 0.12);
            --accent-2: #b45309;
            --shadow: 0 16px 40px rgba(31, 27, 22, 0.08);
            --shadow-soft: 0 10px 24px rgba(31, 27, 22, 0.06);
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: 1920px;
            height: 1080px;
            background:
                radial-gradient(900px 500px at 12% 0%, rgba(15, 118, 110, 0.12), transparent 70%),
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
            line-height: 1.1;
            letter-spacing: -0.02em;
        }}
        .subtitle {{
            font-size: 21px;
            color: var(--muted);
            margin-top: 8px;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }}

        /* Gauge box */
        .gauge-box {{
            text-align: center;
            padding: 18px 26px;
            background: var(--card);
            border: 1px solid var(--line);
            border-left: 10px solid #1D4ED8;
            border-radius: 16px;
            box-shadow: var(--shadow-soft);
        }}
        .gauge-value {{
            font-family: 'STIX Two Text', serif;
            font-size: 60px;
            font-weight: 700;
            color: #1D4ED8;
            line-height: 1;
        }}
        .gauge-label {{
            font-size: 15px;
            font-weight: 600;
            color: var(--muted);
            margin-top: 8px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .gauge-interp {{
            font-size: 15px;
            color: #1D4ED8;
            font-weight: 600;
            margin-top: 4px;
        }}

        /* Main content */
        .main-content {{
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 24px;
            flex: 1;
            min-height: 0;
        }}

        /* Panel */
        .panel {{
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow-soft);
            padding: 22px 26px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .section-header {{ margin-bottom: 14px; }}
        .section-title {{
            font-size: 22px;
            font-weight: 700;
            color: var(--ink);
            margin-bottom: 4px;
        }}
        .section-desc {{
            font-size: 16px;
            color: var(--muted);
        }}

        .pos-row {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }}
        .pos-label {{
            width: 170px;
            font-size: 17px;
            font-weight: 600;
            color: var(--ink);
        }}
        .pos-track {{
            flex: 1;
            height: 26px;
            background: var(--bg-deep);
            border-radius: 8px;
            overflow: hidden;
        }}
        .pos-fill {{
            height: 100%;
            border-radius: 8px;
        }}
        .pos-value {{
            width: 100px;
            text-align: right;
            font-family: 'STIX Two Text', serif;
            font-size: 19px;
            font-weight: 700;
            color: var(--ink);
            margin-left: 12px;
        }}
        .pos-pct {{
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 14px;
            font-weight: 400;
            color: var(--muted);
        }}

        /* Category bars */
        .cat-grid {{
            display: flex;
            gap: 20px;
            margin-top: 16px;
        }}
        .cat-col {{
            flex: 1;
            text-align: center;
        }}
        .cat-bar-wrapper {{
            height: 140px;
            background: var(--bg-deep);
            border-radius: 8px;
            display: flex;
            align-items: flex-end;
            overflow: hidden;
        }}
        .cat-bar {{
            width: 100%;
            border-radius: 8px 8px 0 0;
        }}
        .cat-info {{
            margin-top: 10px;
        }}
        .cat-value {{
            font-family: 'STIX Two Text', serif;
            font-size: 30px;
            font-weight: 700;
            color: var(--ink);
        }}
        .cat-pct {{
            font-size: 16px;
            color: var(--muted);
            margin-left: 4px;
        }}
        .cat-label {{
            margin-top: 6px;
            font-size: 16px;
            font-weight: 600;
            color: var(--muted);
        }}
        .cat-summary {{
            margin-top: 14px;
            font-size: 16px;
            font-weight: 600;
            color: var(--accent);
        }}

        .quote-area {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 16px;
        }}
        .quote-area-label {{
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--muted);
        }}
        .quote-cards {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }}
        .quote-card {{
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 14px 16px;
            box-shadow: var(--shadow-soft);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .quote-card.quote-active {{ border-left: 8px solid #1D4ED8; }}
        .quote-card.quote-cooperative {{ border-left: 8px solid #059669; }}
        .quote-card.quote-reactive {{ border-left: 8px solid #D97706; }}
        .quote-card.quote-empty {{ border-left: 8px solid var(--line); }}
        .quote-meta {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }}
        .quote-kicker {{
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--muted);
        }}
        .quote-label {{
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--muted);
        }}
        .quote-text {{
            font-family: 'STIX Two Text', serif;
            font-size: 19px;
            line-height: 1.5;
            color: var(--ink);
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
                <h1 class="main-title">{title}</h1>
                <p class="subtitle">{subtitle}</p>
            </div>
            <div class="gauge-box">
                <div class="gauge-value">{agency_idx:.0%}</div>
                <div class="gauge-label">{gauge_label}</div>
                <div class="gauge-interp">{interp}</div>
            </div>
        </header>

        <div class="main-content">
            <div class="panel">
                <div class="section-header">
                    <div class="section-title">{pos_title}</div>
                    <div class="section-desc">{pos_desc}</div>
                </div>
                {pos_bars}
            </div>

            <div class="panel">
                <div class="section-header">
                    <div class="section-title">{cat_title}</div>
                    <div class="section-desc">{cat_desc}</div>
                </div>
                <div class="cat-grid">
                    {cat_bars}
                </div>
                <div class="cat-summary">{cat_summary}</div>
            </div>
        </div>

        <div class="quote-area">
            <div class="quote-area-label">{excerpts_title}</div>
            <div class="quote-cards">
                {quote_cards_html}
            </div>
        </div>

        <footer class="methodology">
            <p class="methodology-text">{methodology}</p>
        </footer>
    </div>
</body>
</html>'''

    return html


def main():
    print("=" * 70)
    print("Generating Figure 7: Agency Profile")
    print("=" * 70)

    print("\nLoading data...")
    df = load_data()
    data = prepare_agency_data(df)

    for lang in ['fr', 'en']:
        print(f"\n--- {lang.upper()} ---")
        html = generate_html(data, lang)
        save_figure(html, OUTPUT_DIR, f"fig7_agency_profile_{lang}")

    print("\nDone!")


if __name__ == "__main__":
    main()
