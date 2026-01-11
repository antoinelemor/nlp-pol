#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig2_geopolitical.py

MAIN OBJECTIVE:
---------------
Generate a visualization of Macron's geopolitical worldview based on
threat vs opportunity framing. Computes a composite index combining
geopolitical frame balance and emotional tone.

Dependencies:
-------------
- compute_indices (load_data, prepare_geopolitical_data)
- config (get_labels, GEOPOLITICAL_FRAME_PALETTE)
- html_utils (COLORS, POSITIVE_COLOR, NEGATIVE_COLOR, save_figure)

MAIN FEATURES:
--------------
1) Display threat frames (disorder, power politics, etc.) vs opportunity frames
2) Compute weighted worldview index from frame balance and tone
3) Show representative excerpts for each frame type
4) Generate bilingual output (FR/EN)

Author:
-------
Antoine Lemor
"""

import math
import re
from pathlib import Path
from compute_indices import load_data, prepare_geopolitical_data
from config import get_labels, GEOPOLITICAL_FRAME_PALETTE
from html_utils import COLORS, POSITIVE_COLOR, NEGATIVE_COLOR, save_figure

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output" / "figures"


def generate_html(data, lang='fr'):
    """Generate the geopolitical anxiety HTML."""
    labels = get_labels(lang)
    gai = data['gai']
    threat_data = data['threat_data']
    opp_data = data['opportunity_data']
    threat_total = data['threat_total']
    opp_total = data['opportunity_total']
    frame_total = data.get('frame_total', threat_total + opp_total)
    tone_total = data.get('tone_total', 0)
    tone_index = data.get('tone_index', 0.0)
    weight_frame = data.get('weight_frame', 1.0 if tone_total == 0 else 0.0)
    weight_tone = data.get('weight_tone', 0.0 if tone_total == 0 else 1.0 - weight_frame)

    if lang == 'fr':
        title = "La vision du monde de Macron"
        subtitle = "Cadrage menace vs opportunité : comment Macron perçoit-il la situation internationale ?"
        threat_title = "Cadres de menace"
        opp_title = "Cadres d'opportunité"
        gai_label = "Indice de vision du monde"
        gai_desc = "Combine l'équilibre menaces/opportunités et le ton émotionnel."
        methodology = (
            "Méthodologie : Indice = w_cadrage × (Opportunité − Menace) / Total + "
            "w_ton × Indice de ton émotionnel. Pondérations selon la couverture annotée "
            f"(w_cadrage={weight_frame:.2f}, w_ton={weight_tone:.2f}; "
            f"N_cadrage={frame_total}, N_ton={tone_total})."
        )
        index_kicker = "Indice"
        balance_title = "Balance menace/opportunité"
        if gai < -0.3:
            interp = "Vision pessimiste"
        elif gai < 0.1:
            interp = "Vision prudente"
        else:
            interp = "Vision optimiste"
    else:
        title = "Macron's Worldview"
        subtitle = "Threat vs opportunity framing: how does Macron perceive the international situation?"
        threat_title = "Threat Frames"
        opp_title = "Opportunity Frames"
        gai_label = "Worldview Index"
        gai_desc = "Combines threat/opportunity balance with emotional tone."
        methodology = (
            "Methodology: Index = w_frame × (Opportunity − Threat) / Total + "
            "w_tone × Emotional tone index. Weights follow annotation coverage "
            f"(w_frame={weight_frame:.2f}, w_tone={weight_tone:.2f}; "
            f"N_frame={frame_total}, N_tone={tone_total})."
        )
        index_kicker = "Index"
        balance_title = "Threat/opportunity balance"
        if gai < -0.3:
            interp = "Pessimistic view"
        elif gai < 0.1:
            interp = "Cautious view"
        else:
            interp = "Optimistic view"

    interp_color = NEGATIVE_COLOR if gai < -0.2 else POSITIVE_COLOR if gai > 0.2 else COLORS['warning']

    quote_open = '«' if lang == 'fr' else '“'
    quote_close = '»' if lang == 'fr' else '”'

    def limit_sentences(text, max_sentences=1):
        if max_sentences <= 1:
            match = re.search(r'^(.*?[.!?])(?:\s|$)', text.strip())
            return match.group(1) if match else text.strip()
        parts = re.split(r'(?<=[.!?])\s+', text.strip())
        parts = [p for p in parts if p]
        if not parts:
            return text.strip()
        return ' '.join(parts[:max_sentences])

    def format_quote(text):
        cleaned = ' '.join(str(text).split())
        cleaned = limit_sentences(cleaned, 2)
        return f"{quote_open} {cleaned} {quote_close}"

    # Generate threat bars
    max_count = max([c for _, c in threat_data] + [c for _, c in opp_data]) if threat_data or opp_data else 1

    threat_bars = ""
    for frame, count in threat_data[:6]:
        width_pct = (count / threat_total * 100) if threat_total > 0 else 0
        pct = (count / threat_total * 100) if threat_total > 0 else 0
        color = GEOPOLITICAL_FRAME_PALETTE.get(frame, NEGATIVE_COLOR)
        label = labels.get(frame, frame.replace('_', ' ').title())
        threat_bars += f'''
        <div class="bar-row">
            <div class="bar-label">{label}</div>
            <div class="bar-track">
                <div class="bar-fill" style="width: {width_pct}%; background: {color};"></div>
                <span class="bar-pct">{pct:.0f}%</span>
            </div>
            <div class="bar-count">n={count}</div>
        </div>'''

    opp_bars = ""
    for frame, count in opp_data[:6]:
        width_pct = (count / opp_total * 100) if opp_total > 0 else 0
        pct = (count / opp_total * 100) if opp_total > 0 else 0
        color = GEOPOLITICAL_FRAME_PALETTE.get(frame, POSITIVE_COLOR)
        label = labels.get(frame, frame.replace('_', ' ').title())
        opp_bars += f'''
        <div class="bar-row">
            <div class="bar-label">{label}</div>
            <div class="bar-track">
                <div class="bar-fill" style="width: {width_pct}%; background: {color};"></div>
                <span class="bar-pct">{pct:.0f}%</span>
            </div>
            <div class="bar-count">n={count}</div>
        </div>'''

    # Balance percentages
    total = threat_total + opp_total
    threat_pct = (threat_total / total * 100) if total > 0 else 50
    opp_pct = (opp_total / total * 100) if total > 0 else 50

    threat_quotes = data.get('threat_quotes', [])
    opp_quotes = data.get('opportunity_quotes', [])
    quotes_title = "Extraits labellisés" if lang == 'fr' else "Labeled excerpts"
    threat_quote_title = "Menace" if lang == 'fr' else "Threat"
    opp_quote_title = "Opportunité" if lang == 'fr' else "Opportunity"
    empty_quote = "Aucun extrait disponible." if lang == 'fr' else "No labeled excerpt available."

    def build_quote_cards(quotes, theme_label, theme_class, max_items=2):
        items = quotes[:max_items]
        if not items:
            return f'''
                <div class="quote-card {theme_class}">
                    <div class="quote-meta">
                        <span class="quote-theme">{theme_label}</span>
                    </div>
                    <div class="quote-text quote-empty">{empty_quote}</div>
                </div>'''
        cards = ""
        for q in items:
            frame_label = labels.get(q['frame'], q['frame'].replace('_', ' ').title())
            cards += f'''
                <div class="quote-card {theme_class}">
                    <div class="quote-meta">
                        <span class="quote-theme">{theme_label}</span>
                        <span class="quote-frame">{frame_label}</span>
                    </div>
                    <div class="quote-text">{format_quote(q['text'])}</div>
                </div>'''
        return cards

    threat_quotes_html = build_quote_cards(threat_quotes, threat_quote_title, "quote-threat")
    opp_quotes_html = build_quote_cards(opp_quotes, opp_quote_title, "quote-opp")
    index_quotes_title = "Extraits labellisés — clés" if lang == 'fr' else "Labeled excerpts — key"
    index_quotes_html = (
        build_quote_cards(threat_quotes[:1], threat_quote_title, "quote-threat", max_items=1)
        + build_quote_cards(opp_quotes[:1], opp_quote_title, "quote-opp", max_items=1)
    )

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
        }}

        /* Header */
        .header {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--ink);
            margin-bottom: 18px;
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

        /* Main content */
        .main-content {{
            display: grid;
            grid-template-columns: 1fr 1fr 0.7fr;
            gap: 24px;
            flex: 1;
            min-height: 0;
        }}
        .column {{
            display: flex;
            flex-direction: column;
            gap: 18px;
            min-height: 0;
        }}

        /* Panels */
        .panel {{
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow-soft);
            padding: 22px 26px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        .value-card {{
            padding: 18px 22px;
        }}
        .panel-threat {{ border-left: 8px solid {NEGATIVE_COLOR}; }}
        .panel-opp {{ border-left: 8px solid {POSITIVE_COLOR}; }}

        .panel-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
        }}
        .panel-title {{
            font-size: 22px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .panel-title.threat {{ color: {NEGATIVE_COLOR}; }}
        .panel-title.opp {{ color: {POSITIVE_COLOR}; }}
        .panel-count {{
            font-size: 17px;
            color: var(--muted);
        }}

        .bar-row {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }}
        .bar-row:last-child {{
            margin-bottom: 0;
        }}
        .bar-label {{
            width: 180px;
            font-size: 17px;
            font-weight: 500;
            color: var(--ink);
        }}
        .bar-track {{
            flex: 1;
            height: 24px;
            background: var(--bg-deep);
            border-radius: 8px;
            overflow: hidden;
            position: relative;
        }}
        .bar-fill {{
            height: 100%;
            border-radius: 8px;
        }}
        .bar-pct {{
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 14px;
            font-weight: 700;
            color: var(--ink);
        }}
        .bar-count {{
            width: 70px;
            text-align: right;
            font-family: 'STIX Two Text', serif;
            font-size: 19px;
            font-weight: 600;
            color: var(--ink);
            margin-left: 12px;
        }}

        .quote-area {{
            display: flex;
            flex-direction: column;
            gap: 0;
            flex: 1;
            min-height: 0;
            align-items: center;
            justify-content: center;
        }}
        .quote-stack {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            align-items: center;
            justify-content: flex-start;
        }}
        .quote-area-label {{
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--muted);
            text-align: center;
        }}
        .quote-cards {{
            display: flex;
            flex-direction: column;
            gap: 12px;
            justify-content: center;
            align-items: center;
        }}
        .quote-card {{
            background: var(--card);
            border-radius: 14px;
            border: 1px solid var(--line);
            padding: 16px 18px;
            box-shadow: var(--shadow-soft);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 12px;
            width: fit-content;
            max-width: 100%;
            align-self: center;
        }}
        .quote-card.quote-threat {{
            border-left: 8px solid {NEGATIVE_COLOR};
        }}
        .quote-card.quote-opp {{
            border-left: 8px solid {POSITIVE_COLOR};
        }}
        .quote-meta {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }}
        .quote-theme {{
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--muted);
        }}
        .quote-frame {{
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--muted);
        }}
        .quote-text {{
            font-family: 'STIX Two Text', serif;
            font-size: 19px;
            line-height: 1.55;
            color: var(--ink);
            max-width: 620px;
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        .quote-text.quote-empty {{
            color: var(--muted);
        }}

        /* Balance bar */
        .insight-column {{
            display: flex;
            flex-direction: column;
            gap: 18px;
        }}
        .insight-stack {{
            display: flex;
            flex-direction: column;
            gap: 18px;
        }}

        .insight-card {{
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow-soft);
            padding: 18px 22px;
        }}

        .index-card {{
            border-left: 10px solid {interp_color};
        }}

        .index-kicker {{
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--muted);
        }}

        .index-value {{
            font-family: 'STIX Two Text', serif;
            font-size: 60px;
            font-weight: 700;
            color: {interp_color};
            line-height: 1;
            margin-top: 10px;
        }}

        .index-label {{
            font-size: 17px;
            font-weight: 600;
            color: var(--muted);
            margin-top: 8px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .index-interp {{
            font-size: 17px;
            color: {interp_color};
            font-weight: 600;
            margin-top: 4px;
        }}
        .index-meta {{
            font-size: 16px;
            color: var(--muted);
            margin-top: 10px;
            line-height: 1.4;
        }}

        .balance-card {{
        }}

        .balance-bar {{
            display: flex;
            height: 48px;
            border-radius: 10px;
            overflow: hidden;
        }}
        .balance-threat {{
            background: {NEGATIVE_COLOR};
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 24px;
        }}
        .balance-opp {{
            background: {POSITIVE_COLOR};
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 24px;
        }}
        .balance-labels {{
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            font-weight: 600;
            font-size: 16px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .balance-labels .threat {{ color: {NEGATIVE_COLOR}; }}
        .balance-labels .opp {{ color: {POSITIVE_COLOR}; }}


        /* Footer */
        .methodology {{
            margin-top: auto;
            padding-top: 32px;
        }}
        .methodology-text {{
            font-size: 16px;
            color: var(--muted);
            text-align: left;
            border-top: 1px solid var(--line);
            padding-top: 20px;
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
        </header>

        <div class="main-content">
            <div class="column">
                <div class="panel value-card panel-threat">
                    <div class="panel-header">
                        <span class="panel-title threat">{threat_title}</span>
                        <span class="panel-count">n = {threat_total}</span>
                    </div>
                    {threat_bars}
                </div>
                <div class="quote-area">
                    <div class="quote-stack">
                        <div class="quote-area-label">{quotes_title}</div>
                        <div class="quote-cards">
                            {threat_quotes_html}
                        </div>
                    </div>
                </div>
            </div>

            <div class="column">
                <div class="panel value-card panel-opp">
                    <div class="panel-header">
                        <span class="panel-title opp">{opp_title}</span>
                        <span class="panel-count">n = {opp_total}</span>
                    </div>
                    {opp_bars}
                </div>
                <div class="quote-area">
                    <div class="quote-stack">
                        <div class="quote-area-label">{quotes_title}</div>
                        <div class="quote-cards">
                            {opp_quotes_html}
                        </div>
                    </div>
                </div>
            </div>

            <div class="column insight-column">
                <div class="insight-stack">
                    <div class="insight-card index-card">
                        <div class="index-kicker">{index_kicker}</div>
                        <div class="index-value">{gai:+.2f}</div>
                        <div class="index-label">{gai_label}</div>
                        <div class="index-interp">{interp}</div>
                        <div class="index-meta">{threat_title}: {threat_total} ({threat_pct:.0f}%) · {opp_title}: {opp_total} ({opp_pct:.0f}%)</div>
                    </div>

                    <div class="insight-card balance-card">
                        <div class="index-kicker">{balance_title}</div>
                        <div class="balance-bar">
                            <div class="balance-threat" style="width: {threat_pct}%;">{threat_pct:.0f}%</div>
                            <div class="balance-opp" style="width: {opp_pct}%;">{opp_pct:.0f}%</div>
                        </div>
                        <div class="balance-labels">
                            <span class="threat">{"MENACE" if lang == "fr" else "THREAT"} ({threat_total})</span>
                            <span class="opp">{"OPPORTUNITÉ" if lang == "fr" else "OPPORTUNITY"} ({opp_total})</span>
                        </div>
                    </div>
                </div>

                <div class="quote-area">
                    <div class="quote-stack">
                        <div class="quote-area-label">{index_quotes_title}</div>
                        <div class="quote-cards">
                            {index_quotes_html}
                        </div>
                    </div>
                </div>
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
    print("Generating Figure 2: Geopolitical Worldview Index")
    print("=" * 70)

    print("\nLoading data...")
    df = load_data()
    data = prepare_geopolitical_data(df)

    for lang in ['fr', 'en']:
        print(f"\n--- {lang.upper()} ---")
        html = generate_html(data, lang)
        save_figure(html, OUTPUT_DIR, f"fig2_geopolitical_anxiety_{lang}")

    print("\nDone!")


if __name__ == "__main__":
    main()
