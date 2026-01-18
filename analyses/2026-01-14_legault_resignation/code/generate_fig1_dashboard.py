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
Generate dashboard figure with key indices, thesis, and summary statistics
for the Legault Resignation Speech analysis.

Dependencies:
-------------
- config (colors, labels)
- load_and_validate (data loading)
- compute_indices (index computation)
- html_utils (HTML generation, export)

MAIN FEATURES:
--------------
1) Central thesis statement
2) 5 composite indices with interpretations
3) Methodology footer with N values

Author:
-------
Antoine Lemor
"""

import html as html_lib
from pathlib import Path

from config import (
    get_labels, POSITIVE_COLOR, NEGATIVE_COLOR,
    NEUTRAL_COLOR, PRIMARY_COLOR, QUEBEC_BLUE
)
from load_and_validate import load_data, OUTPUT_DIR
from compute_indices import (
    compute_emotional_tone_index,
    compute_justification_balance_index,
    compute_legacy_emphasis_index,
    compute_identity_emphasis_index,
    compute_gratitude_index,
    aggregate_speech_acts,
    aggregate_emotional_register,
    aggregate_actors_by_valence,
    aggregate_policy_domains
)
from html_utils import save_figure


# =============================================================================
# FIGURE GENERATION
# =============================================================================

def get_interpretation(value, thresholds, labels_pos_neg_neu):
    """Get interpretation label based on value and thresholds."""
    if value > thresholds[0]:
        return labels_pos_neg_neu[0]
    elif value < thresholds[1]:
        return labels_pos_neg_neu[1]
    else:
        return labels_pos_neg_neu[2]


def get_index_color(value: float, neutral_threshold: float = 0.1) -> str:
    """Get color based on index value."""
    if value > neutral_threshold:
        return POSITIVE_COLOR
    elif value < -neutral_threshold:
        return NEGATIVE_COLOR
    else:
        return '#b45309'  # Amber for neutral/moderate


def generate_html(df, lang='fr'):
    """Generate dashboard HTML for specified language."""
    labels = get_labels(lang)

    # Compute indices
    tone_idx, tone_meta = compute_emotional_tone_index(df)
    balance_idx, balance_meta = compute_justification_balance_index(df)
    legacy_idx, legacy_meta = compute_legacy_emphasis_index(df)
    identity_idx, identity_meta = compute_identity_emphasis_index(df)
    gratitude_idx, gratitude_meta = compute_gratitude_index(df)

    # Get actor sentiment summary and compute actor index
    actors_by_valence = aggregate_actors_by_valence(df)
    pos_actor_mentions = actors_by_valence.get('POSITIVE', {'count': []}).get('count', []).sum() if 'POSITIVE' in actors_by_valence else 0
    neg_actor_mentions = actors_by_valence.get('NEGATIVE', {'count': []}).get('count', []).sum() if 'NEGATIVE' in actors_by_valence else 0
    if isinstance(pos_actor_mentions, int) or hasattr(pos_actor_mentions, 'item'):
        pos_actor_mentions = int(pos_actor_mentions) if hasattr(pos_actor_mentions, 'item') else pos_actor_mentions
    else:
        pos_actor_mentions = actors_by_valence['POSITIVE']['count'].sum() if 'POSITIVE' in actors_by_valence else 0
    if isinstance(neg_actor_mentions, int) or hasattr(neg_actor_mentions, 'item'):
        neg_actor_mentions = int(neg_actor_mentions) if hasattr(neg_actor_mentions, 'item') else neg_actor_mentions
    else:
        neg_actor_mentions = actors_by_valence['NEGATIVE']['count'].sum() if 'NEGATIVE' in actors_by_valence else 0

    total_actor_mentions = pos_actor_mentions + neg_actor_mentions
    actor_idx = (pos_actor_mentions - neg_actor_mentions) / total_actor_mentions if total_actor_mentions > 0 else 0

    # Get top policy domain
    domains = aggregate_policy_domains(df)
    domains = domains[domains['policy_domain'] != 'NONE']
    top_domain = domains.iloc[0]['policy_domain'] if not domains.empty else 'NONE'
    top_domain_count = int(domains.iloc[0]['count']) if not domains.empty else 0

    # Get emotion summary
    emotions = aggregate_emotional_register(df)
    top_emotion = emotions.iloc[0]['emotional_register'] if not emotions.empty else 'NEUTRAL'

    total_actors = total_actor_mentions

    # Get domain labels
    domain_labels = get_labels(lang).get('policy_domain', {})
    top_domain_label = domain_labels.get(top_domain, top_domain)

    # Title and content
    if lang == 'fr':
        title = "Discours de démission"
        subtitle = f"Analyse de {len(df)} phrases · François Legault · 14 janvier 2026"
        thesis_label = "Constat de l'analyse"
        thesis_text = "Un discours de bilan plus que de démission, centré sur la politique partisane : fierté du parcours, défense du bilan CAQ, gratitude envers les équipes"

        # Index labels and interpretations
        tone_label = "Tonalité"
        tone_interp = "positive" if tone_idx > 0.2 else ("négative" if tone_idx < -0.2 else "modérée")
        tone_desc = "Registre émotionnel"

        theme_label = "Thème"
        theme_interp = top_domain_label.lower()
        theme_desc = f"{top_domain_count} mentions · 1er domaine"

        legacy_label = "Héritage"
        legacy_interp = "très présent" if legacy_idx > 0.5 else ("présent" if legacy_idx > 0.2 else "limité")
        legacy_desc = f"{legacy_meta['n']}/{legacy_meta['total']} phrases"

        actor_label = "Acteurs"
        actor_interp = "positifs" if actor_idx > 0.3 else ("négatifs" if actor_idx < -0.3 else "mixtes")
        actor_desc = f"{pos_actor_mentions} positifs · {neg_actor_mentions} négatifs"

        identity_label = "Nationalisme"
        identity_interp = "présent" if identity_idx > 0.1 else "limité"
        identity_desc = f"Identité québécoise · {identity_meta['n']}/{identity_meta['total']} phrases"

        methodology = (
            f"Analyse fondée sur {balance_meta['n']} justifications, "
            f"{total_actors} mentions d'acteurs et {tone_meta['n']} registres émotionnels annotés."
        )
    else:
        title = "Resignation Speech"
        subtitle = f"Analysis of {len(df)} sentences · François Legault · January 14, 2026"
        thesis_label = "Key finding"
        thesis_text = "A legacy speech more than a resignation, centered on party politics: pride in achievements, defense of CAQ record, gratitude to teams"

        tone_label = "Tone"
        tone_interp = "positive" if tone_idx > 0.2 else ("negative" if tone_idx < -0.2 else "moderate")
        tone_desc = "Emotional register"

        theme_label = "Theme"
        theme_interp = top_domain_label.lower()
        theme_desc = f"{top_domain_count} mentions · top domain"

        legacy_label = "Legacy"
        legacy_interp = "very present" if legacy_idx > 0.5 else ("present" if legacy_idx > 0.2 else "limited")
        legacy_desc = f"{legacy_meta['n']}/{legacy_meta['total']} sentences"

        actor_label = "Actors"
        actor_interp = "positive" if actor_idx > 0.3 else ("negative" if actor_idx < -0.3 else "mixed")
        actor_desc = f"{pos_actor_mentions} positive · {neg_actor_mentions} negative"

        identity_label = "Nationalism"
        identity_interp = "present" if identity_idx > 0.1 else "limited"
        identity_desc = f"Quebec identity · {identity_meta['n']}/{identity_meta['total']} sentences"

        methodology = (
            f"Analysis based on {balance_meta['n']} justifications, "
            f"{total_actors} actor mentions and {tone_meta['n']} emotional registers annotated."
        )

    # Build metrics HTML
    def make_metric(value, label, interp, desc, color, fmt="{:+.2f}"):
        formatted_value = fmt.format(value) if callable(getattr(fmt, 'format', None)) else fmt.format(value)
        return f'''
        <div class="metric">
            <div class="metric-header">
                <div class="metric-label">{html_lib.escape(label)}</div>
                <div class="metric-interp">{html_lib.escape(interp)}</div>
            </div>
            <div class="metric-value" style="color: {color};">{formatted_value}</div>
            <div class="metric-desc">{html_lib.escape(desc)}</div>
        </div>
        '''

    # Distinct colors for each metric
    TONE_COLOR = '#0891B2'      # Cyan/teal for tone
    THEME_COLOR = '#B45309'     # Amber for theme
    LEGACY_COLOR = QUEBEC_BLUE  # Quebec blue for legacy
    ACTOR_COLOR = '#059669'     # Green for actors
    IDENTITY_COLOR = '#DC2626'  # Red for nationalism

    metrics_html = f'''
    {make_metric(tone_idx, tone_label, tone_interp, tone_desc, TONE_COLOR)}
    {make_metric(top_domain_count, theme_label, theme_interp, theme_desc, THEME_COLOR, "{}")}
    {make_metric(legacy_idx, legacy_label, legacy_interp, legacy_desc, LEGACY_COLOR, "{:.0%}")}
    {make_metric(actor_idx, actor_label, actor_interp, actor_desc, ACTOR_COLOR, "{:+.2f}")}
    {make_metric(identity_idx, identity_label, identity_interp, identity_desc, IDENTITY_COLOR, "{:.0%}")}
    '''

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
            --accent-soft: rgba(0, 61, 165, 0.12);
            --accent-2: #b45309;
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
        .title-block {{ max-width: 1200px; }}
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

        /* Thesis card */
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
            font-size: 42px;
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
                <h1 class="main-title">{html_lib.escape(title)}</h1>
                <p class="subtitle">{html_lib.escape(subtitle)}</p>
            </div>
        </header>

        <section class="thesis-section">
            <div class="thesis-card">
                <div class="thesis-label">{html_lib.escape(thesis_label)}</div>
                <div class="thesis">{html_lib.escape(thesis_text)}</div>
            </div>
        </section>

        <section class="metrics-row">
            {metrics_html}
        </section>

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
    """Generate dashboard figure."""
    if df is None:
        df = load_data()

    for lang in ['fr', 'en']:
        html_content = generate_html(df, lang)
        save_figure(html_content, OUTPUT_DIR, f'fig1_dashboard_{lang}', export_png=export_png)


if __name__ == '__main__':
    main()
