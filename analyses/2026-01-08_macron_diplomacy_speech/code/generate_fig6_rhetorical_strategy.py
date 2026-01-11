#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig6_rhetorical_strategy.py

MAIN OBJECTIVE:
---------------
Analyze Macron's rhetorical strategy through speech act classification
and emotional register distribution. Computes action orientation and
tone indices to characterize the communicative intent.

Dependencies:
-------------
- compute_indices (load_data, prepare_rhetorical_data)
- config (get_labels, EMOTIONAL_REGISTER_PALETTE)
- html_utils (COLORS, save_figure)

MAIN FEATURES:
--------------
1) Display speech act profile via radar chart (stating, proposing, exhorting, etc.)
2) Show emotional register distribution (pragmatic, confident, combative, etc.)
3) Compute Action Orientation Index and Tone Index
4) Show labeled excerpts for each dimension
5) Generate bilingual output (FR/EN)

Author:
-------
Antoine Lemor
"""

import math
import re
from pathlib import Path
from compute_indices import load_data, prepare_rhetorical_data
from config import get_labels, EMOTIONAL_REGISTER_PALETTE
from html_utils import COLORS, save_figure

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output" / "figures"


def generate_html(data, lang='fr'):
    """Generate the rhetorical strategy HTML."""
    labels = get_labels(lang)
    speech_acts = data['speech_acts']
    emotional_registers = data['emotional_registers']
    action_idx = data['action_index']
    tone_idx = data['tone_index']

    if lang == 'fr':
        title = "La stratégie rhétorique de Macron"
        subtitle = "Actes de langage et registre émotionnel : que fait Macron avec ses mots ?"
        acts_title = "Profil des actes de langage"
        acts_desc = "Ce que Macron fait avec ses énoncés : décrire, proposer, dénoncer, exhorter..."
        emo_title = "Registre émotionnel"
        emo_desc = "Le ton général du discours : pragmatique, solennel, combatif..."
        summary = f"Orientation action : {action_idx:.0%} • Indice de ton : {tone_idx:+.2f}"
        methodology = "Méthodologie : Les actes de langage révèlent l'intention communicative. Le registre émotionnel caractérise le ton dominant de chaque segment."
        excerpts_title = "Extraits labellisés"
        act_prefix = "Acte"
        emo_prefix = "Registre"
    else:
        title = "Macron's Rhetorical Strategy"
        subtitle = "Speech acts and emotional register: what does Macron do with his words?"
        acts_title = "Speech Acts Profile"
        acts_desc = "What Macron does with statements: describe, propose, denounce, exhort..."
        emo_title = "Emotional Register"
        emo_desc = "The overall tone: pragmatic, solemn, combative..."
        summary = f"Action orientation: {action_idx:.0%} • Tone index: {tone_idx:+.2f}"
        methodology = "Methodology: Speech acts reveal communicative intent. Emotional register characterizes the dominant tone of each segment."
        excerpts_title = "Labeled excerpts"
        act_prefix = "Speech act"
        emo_prefix = "Register"

    # Generate radar chart for speech acts
    act_items = list(speech_acts.items())
    n = len(act_items)
    max_val = max(speech_acts.values()) if speech_acts else 1
    center_x, center_y = 220, 220
    radius = 140

    radar_points = []
    label_positions = []

    for i, (act, count) in enumerate(act_items):
        angle = (2 * math.pi * i / n) - math.pi / 2
        normalized = count / max_val
        x = center_x + radius * normalized * math.cos(angle)
        y = center_y + radius * normalized * math.sin(angle)
        radar_points.append(f"{x},{y}")

        lx = center_x + (radius + 50) * math.cos(angle)
        ly = center_y + (radius + 50) * math.sin(angle)
        label = labels.get(act, act.replace('_', ' ').title())
        label_positions.append((lx, ly, label, count))

    radar_path = " ".join(radar_points)

    grid_circles = ""
    for r in [0.25, 0.5, 0.75, 1.0]:
        grid_circles += f'<circle cx="{center_x}" cy="{center_y}" r="{radius * r}" fill="none" stroke="#e7e5e4" stroke-width="1"/>'

    grid_lines = ""
    for i in range(n):
        angle = (2 * math.pi * i / n) - math.pi / 2
        x2 = center_x + radius * math.cos(angle)
        y2 = center_y + radius * math.sin(angle)
        grid_lines += f'<line x1="{center_x}" y1="{center_y}" x2="{x2}" y2="{y2}" stroke="#e7e5e4" stroke-width="1"/>'

    radar_labels = ""
    for lx, ly, label, count in label_positions:
        anchor = "middle"
        if lx < center_x - 20:
            anchor = "end"
        elif lx > center_x + 20:
            anchor = "start"
        radar_labels += f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-size="13" font-weight="500" fill="#44403c">{label}</text>'
        radar_labels += f'<text x="{lx}" y="{ly + 15}" text-anchor="{anchor}" font-size="12" font-weight="700" fill="#1D4ED8">{count}</text>'

    # Generate emotional register bars
    total_emo = sum(emotional_registers.values())
    max_emo = max(emotional_registers.values()) if emotional_registers else 1
    emo_bars = ""
    for emo, count in emotional_registers.items():
        pct = (count / total_emo * 100) if total_emo > 0 else 0
        width_pct = (count / max_emo) * 100
        color = EMOTIONAL_REGISTER_PALETTE.get(emo, COLORS['neutral'])
        label = labels.get(emo, emo.replace('_', ' ').title())
        emo_bars += f'''
        <div class="emo-row">
            <div class="emo-label">{label}</div>
            <div class="emo-track">
                <div class="emo-fill" style="width: {width_pct}%; background: {color};"></div>
            </div>
            <div class="emo-value">{count} <span class="emo-pct">({pct:.0f}%)</span></div>
        </div>'''

    quotes = data.get('quotes', [])

    def format_quote(text):
        cleaned = ' '.join(str(text).split())
        match = re.search(r'^(.*?[.!?])(?:\s|$)', cleaned)
        return match.group(1) if match else cleaned

    def build_quote_cards(items, count=2):
        cards = ""
        for i in range(count):
            if i < len(items):
                q = items[i]
                label = labels.get(q.get('label', ''), q.get('label', '').replace('_', ' ').title())
                prefix = act_prefix if q.get('kind') == 'speech_act' else emo_prefix
                cards += f'''
                <div class="quote-card">
                    <div class="quote-meta">
                        <span class="quote-kicker">{excerpts_title}</span>
                        <span class="quote-label">{prefix}: {label}</span>
                    </div>
                    <div class="quote-text">« {format_quote(q.get('text', ''))} »</div>
                </div>'''
            else:
                cards += f'''
                <div class="quote-card quote-empty">
                    <div class="quote-meta">
                        <span class="quote-kicker">{excerpts_title}</span>
                    </div>
                    <div class="quote-text">—</div>
                </div>'''
        return cards

    quote_cards_html = build_quote_cards(quotes, count=4)

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
        .title-block {{
            max-width: 1200px;
        }}
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

        /* Index box */
        .index-box {{
            text-align: center;
            padding: 18px 26px;
            background: var(--card);
            border: 1px solid var(--line);
            border-left: 10px solid #1D4ED8;
            border-radius: 16px;
            box-shadow: var(--shadow-soft);
        }}
        .index-value {{
            font-family: 'STIX Two Text', serif;
            font-size: 52px;
            font-weight: 700;
            color: #1D4ED8;
            line-height: 1;
        }}
        .index-label {{
            font-size: 14px;
            font-weight: 600;
            color: var(--muted);
            margin-top: 8px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .index-interp {{
            font-size: 14px;
            color: #1D4ED8;
            font-weight: 600;
            margin-top: 4px;
        }}

        /* Main content */
        .main-content {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            flex: 0 0 auto;
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
        }}
        .section-header {{ margin-bottom: 12px; }}
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

        .radar-container {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .radar-svg {{
            width: 380px;
            height: 380px;
        }}

        .emo-row {{
            display: flex;
            align-items: center;
            margin-bottom: 14px;
        }}
        .emo-label {{
            width: 140px;
            font-size: 17px;
            font-weight: 600;
            color: var(--ink);
        }}
        .emo-track {{
            flex: 1;
            height: 28px;
            background: var(--bg-deep);
            border-radius: 8px;
            overflow: hidden;
        }}
        .emo-fill {{
            height: 100%;
            border-radius: 8px;
        }}
        .emo-value {{
            width: 100px;
            text-align: right;
            font-family: 'STIX Two Text', serif;
            font-size: 19px;
            font-weight: 700;
            color: var(--ink);
            margin-left: 12px;
        }}
        .emo-pct {{
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 14px;
            font-weight: 400;
            color: var(--muted);
        }}

        .quotes-section {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 20px;
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
            width: 100%;
        }}
        .quote-card {{
            background: var(--card);
            border-radius: 14px;
            border: 1px solid var(--line);
            padding: 14px 16px;
            box-shadow: var(--shadow-soft);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .quote-card.quote-empty {{
            border-left: 8px solid var(--line);
        }}
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
            <div class="title-block">
                <h1 class="main-title">{title}</h1>
                <p class="subtitle">{subtitle}</p>
            </div>
            <div class="index-box">
                <div class="index-value">{action_idx:.0%}</div>
                <div class="index-label">{"Orientation action" if lang == "fr" else "Action orientation"}</div>
                <div class="index-interp">{"Prescriptif" if action_idx > 0.5 else "Mixte" if action_idx > 0.3 else "Descriptif" if lang == "fr" else "Prescriptive" if action_idx > 0.5 else "Mixed" if action_idx > 0.3 else "Descriptive"}</div>
            </div>
        </header>

        <div class="main-content">
            <div class="panel">
                <div class="section-header">
                    <div class="section-title">{acts_title}</div>
                    <div class="section-desc">{acts_desc}</div>
                </div>
                <div class="radar-container">
                    <svg viewBox="0 0 440 440" class="radar-svg">
                        {grid_circles}
                        {grid_lines}
                        <polygon points="{radar_path}" fill="#1D4ED8" fill-opacity="0.2" stroke="#1D4ED8" stroke-width="2.5"/>
                        {radar_labels}
                    </svg>
                </div>
            </div>

            <div class="panel">
                <div class="section-header">
                    <div class="section-title">{emo_title}</div>
                    <div class="section-desc">{emo_desc}</div>
                </div>
                {emo_bars}
            </div>
        </div>

        <div class="quotes-section">
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
    print("Generating Figure 6: Rhetorical Strategy")
    print("=" * 70)

    print("\nLoading data...")
    df = load_data()
    data = prepare_rhetorical_data(df)

    for lang in ['fr', 'en']:
        print(f"\n--- {lang.upper()} ---")
        html = generate_html(data, lang)
        save_figure(html, OUTPUT_DIR, f"fig6_rhetorical_strategy_{lang}")

    print("\nDone!")


if __name__ == "__main__":
    main()
