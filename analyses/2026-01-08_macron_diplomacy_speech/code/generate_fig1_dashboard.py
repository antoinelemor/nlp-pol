#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig1_dashboard.py

MAIN OBJECTIVE:
---------------
Generate an executive dashboard summarizing Macron's diplomatic doctrine.
Displays composite indices (Geopolitical Anxiety, Agency, Policy Ambition,
Diplomatic Tone, Action Orientation) alongside a data-driven thesis statement.

Dependencies:
-------------
- compute_indices (load_data, compute_all_indices, compute_summary_stats)
- html_utils (COLORS, POSITIVE_COLOR, NEGATIVE_COLOR, save_figure)

MAIN FEATURES:
--------------
1) Compute and display 5 composite indices with color-coded values
2) Generate a central thesis statement based on index combinations
3) Show methodology note with corpus statistics
4) Generate bilingual output (FR/EN)

Author:
-------
Antoine Lemor
"""

from pathlib import Path
from compute_indices import load_data, compute_all_indices, compute_summary_stats
from html_utils import COLORS, POSITIVE_COLOR, NEGATIVE_COLOR, save_figure

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output" / "figures"


def generate_html(indices, stats, lang='fr'):
    """Generate the dashboard HTML with central thesis."""

    gai = indices['geopolitical_anxiety']
    agency = indices['agency']
    ambition = indices['policy_ambition']
    tone = indices['diplomatic_tone']
    action = indices['action_orientation']

    if lang == 'fr':
        title = "La doctrine diplomatique de Macron"
        subtitle = f"Analyse quantitative de {stats['n_sentences']} énoncés"
        thesis_label = "Constat de l'analyse"

        # Central thesis based on the data
        if agency > 0.7 and gai < -0.2:
            thesis = "Un volontarisme lucide : la France se veut actrice d'un monde qu'elle perçoit comme menaçant"
        elif agency > 0.7 and gai > 0.1:
            thesis = "Un optimisme conquérant : la France se positionne comme leader d'un ordre en reconstruction"
        elif agency > 0.5:
            thesis = "Une diplomatie active dans un contexte de tensions : agir malgré l'incertitude"
        else:
            thesis = "Une posture de prudence face aux bouleversements géopolitiques"

        metrics = [
            {
                'value': gai,
                'label': 'Vision du monde',
                'format': 'signed',
                'interp': 'pessimiste' if gai < -0.2 else 'très prudente' if gai < 0.1 else 'optimiste',
                'desc': 'Cadrage menace vs opportunité',
            },
            {
                'value': agency,
                'label': 'Agentivité',
                'format': 'percent',
                'interp': 'très active' if agency > 0.7 else 'active' if agency > 0.5 else 'modérée',
                'desc': 'Positionnement comme acteur',
            },
            {
                'value': ambition,
                'label': 'Concrétude',
                'format': 'percent',
                'interp': 'élevée' if ambition > 0.6 else 'moyenne' if ambition > 0.4 else 'faible',
                'desc': 'Précision des propositions',
            },
            {
                'value': tone,
                'label': 'Tonalité',
                'format': 'signed',
                'interp': 'confiante' if tone > 0.2 else 'neutre' if tone > -0.2 else 'inquiète',
                'desc': 'Registre émotionnel',
            },
            {
                'value': action,
                'label': 'Orientation',
                'format': 'percent',
                'interp': 'prescriptive' if action > 0.5 else 'mixte' if action > 0.3 else 'descriptive',
                'desc': 'Appels à l\'action',
            },
        ]

        methodology = f"Analyse fondée sur {stats['n_policies']} propositions politiques, {stats['n_actors']} mentions d'acteurs et {stats['n_frames']} cadres géopolitiques."

    else:
        title = "Macron's Diplomatic Doctrine"
        subtitle = f"Quantitative analysis of {stats['n_sentences']} statements"
        thesis_label = "Analytical finding"

        if agency > 0.7 and gai < -0.2:
            thesis = "Clear-eyed voluntarism: France aims to be a driving force in a world it views as menacing."
        elif agency > 0.7 and gai > 0.1:
            thesis = "Conquering optimism: France positions itself as leader of a reconstructing order"
        elif agency > 0.5:
            thesis = "Active diplomacy amid tensions: acting despite uncertainty"
        else:
            thesis = "A posture of prudence facing geopolitical upheavals"

        metrics = [
            {
                'value': gai,
                'label': 'Worldview',
                'format': 'signed',
                'interp': 'pessimistic' if gai < -0.2 else 'very cautious' if gai < 0.1 else 'optimistic',
                'desc': 'Threat vs opportunity framing',
            },
            {
                'value': agency,
                'label': 'Agency',
                'format': 'percent',
                'interp': 'very active' if agency > 0.7 else 'active' if agency > 0.5 else 'moderate',
                'desc': 'Positioning as actor',
            },
            {
                'value': ambition,
                'label': 'Concreteness',
                'format': 'percent',
                'interp': 'high' if ambition > 0.6 else 'medium' if ambition > 0.4 else 'low',
                'desc': 'Proposal precision',
            },
            {
                'value': tone,
                'label': 'Tone',
                'format': 'signed',
                'interp': 'confident' if tone > 0.2 else 'neutral' if tone > -0.2 else 'concerned',
                'desc': 'Emotional register',
            },
            {
                'value': action,
                'label': 'Orientation',
                'format': 'percent',
                'interp': 'prescriptive' if action > 0.5 else 'mixed' if action > 0.3 else 'descriptive',
                'desc': 'Calls to action',
            },
        ]

        methodology = f"Analysis based on {stats['n_policies']} policy proposals, {stats['n_actors']} actor mentions and {stats['n_frames']} geopolitical frames."

    # Generate metric cards
    metrics_html = ""
    for m in metrics:
        if m['format'] == 'signed':
            val_display = f"{m['value']:+.2f}"
            if m['value'] < -0.2:
                color = NEGATIVE_COLOR
            elif m['value'] > 0.2:
                color = POSITIVE_COLOR
            else:
                color = '#b45309'
        else:
            val_display = f"{m['value']:.0%}"
            if m['value'] >= 0.7:
                color = POSITIVE_COLOR
            elif m['value'] >= 0.5:
                color = COLORS['primary']
            else:
                color = '#b45309'

        metrics_html += f'''
        <div class="metric">
            <div class="metric-header">
                <div class="metric-label">{m['label']}</div>
                <div class="metric-interp">{m['interp']}</div>
            </div>
            <div class="metric-value" style="color: {color};">{val_display}</div>
            <div class="metric-desc">{m['desc']}</div>
        </div>
        '''

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
            padding: 56px 90px 48px;
            height: 100%;
            display: grid;
            grid-template-rows: auto 1fr auto auto;
            gap: 26px;
        }}

        /* Header */
        .header {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            padding-bottom: 18px;
            border-bottom: 2px solid var(--ink);
        }}
        .title-block {{
            max-width: 1200px;
        }}
        .main-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 60px;
            font-weight: 600;
            line-height: 1.1;
            letter-spacing: -0.02em;
        }}
        .subtitle {{
            font-size: 18px;
            color: var(--muted);
            margin-top: 10px;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }}

        /* Central thesis */
        .thesis-section {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .thesis-card {{
            width: 100%;
            background: var(--card);
            border: 1px solid var(--line);
            border-left: 10px solid var(--accent);
            border-radius: 20px;
            padding: 32px 44px;
            box-shadow: 0 16px 40px rgba(31, 27, 22, 0.08);
        }}
        .thesis-label {{
            display: inline-block;
            font-size: 16px;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--accent);
            background: var(--accent-soft);
            padding: 8px 18px;
            border-radius: 999px;
            font-weight: 700;
        }}

        .thesis {{
            font-family: 'STIX Two Text', serif;
            font-size: 46px;
            font-weight: 500;
            color: var(--ink);
            text-align: left;
            line-height: 1.25;
            margin-top: 18px;
        }}

        /* Metrics row */
        .metrics-row {{
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 22px;
        }}

        .metric {{
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 20px 22px 18px;
            box-shadow: 0 10px 24px rgba(31, 27, 22, 0.06);
            display: flex;
            flex-direction: column;
            min-height: 210px;
        }}

        .metric-header {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .metric-value {{
            font-family: 'STIX Two Text', serif;
            font-size: 76px;
            font-weight: 600;
            line-height: 1;
            margin-top: 8px;
        }}

        .metric-label {{
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--ink);
        }}

        .metric-interp {{
            font-size: 14px;
            font-weight: 600;
            color: var(--accent-2);
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }}

        .metric-desc {{
            font-size: 14px;
            color: var(--muted);
            margin-top: auto;
            line-height: 1.3;
        }}

        /* Footer */
        .methodology {{
            padding-top: 8px;
        }}
        .methodology-text {{
            font-size: 14px;
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
        </header>

        <section class="thesis-section">
            <div class="thesis-card">
                <div class="thesis-label">{thesis_label}</div>
                <div class="thesis">{thesis}</div>
            </div>
        </section>

        <section class="metrics-row">
            {metrics_html}
        </section>

        <footer class="methodology">
            <p class="methodology-text">{methodology}</p>
        </footer>
    </div>
</body>
</html>'''

    return html


def main():
    print("=" * 70)
    print("Generating Figure 1: Diplomatic Doctrine Dashboard")
    print("=" * 70)

    print("\nLoading data...")
    df = load_data()
    indices = compute_all_indices(df)
    stats = compute_summary_stats(df)

    for lang in ['fr', 'en']:
        print(f"\n--- {lang.upper()} ---")
        html = generate_html(indices, stats, lang)
        save_figure(html, OUTPUT_DIR, f"fig1_dashboard_{lang}")

    print("\nDone!")


if __name__ == "__main__":
    main()
