#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig1b_resignation_rationale.py

MAIN OBJECTIVE:
---------------
Generate figure analyzing specifically HOW Legault justifies his resignation decision.
Cross-references justification_type (DECISION_RATIONALE -> RESIGNATION) with other
annotation dimensions (speech_act, emotional_register, temporality, rhetorical_devices).

Dependencies:
-------------
- config (colors, labels)
- load_and_validate (data loading)
- html_utils (HTML generation, export)

MAIN FEATURES:
--------------
1) Full excerpts of the 6 resignation rationale sentences
2) Speech acts used in justification
3) Emotional trajectory of the justification
4) Temporal framing analysis
5) Rhetorical devices employed

Author:
-------
Antoine Lemor
"""

import html as html_lib
import json
from pathlib import Path
from collections import Counter

from config import (
    get_labels, QUEBEC_BLUE, SPEECH_ACT_COLORS, EMOTIONAL_REGISTER_COLORS,
    POSITIVE_COLOR, NEGATIVE_COLOR, PRIMARY_COLOR, POLICY_DOMAIN_COLORS
)
from load_and_validate import load_data, OUTPUT_DIR
from html_utils import save_figure


# =============================================================================
# DATA EXTRACTION
# =============================================================================

def parse_json(val):
    """Parse JSON from annotation field."""
    if not val or (isinstance(val, float) and str(val) == 'nan'):
        return None
    try:
        return json.loads(str(val).replace("'", '"'))
    except:
        try:
            return json.loads(str(val))
        except:
            return None


def get_resignation_rationale_data(df):
    """Extract sentences where Legault justifies his resignation decision."""
    results = []

    # Sentences that are transition statements, not justifications
    EXCLUDE_PHRASES = [
        "je vais rester en place le temps que mon parti",
    ]

    for idx, row in df.iterrows():
        ann = parse_json(row.get('annotation'))
        if not ann:
            continue

        jt = ann.get('justification_type', {})
        if not jt or not jt.get('present'):
            continue

        # Check if this is DECISION_RATIONALE targeting RESIGNATION
        if jt.get('justification_category') == 'DECISION_RATIONALE':
            targets = jt.get('target', [])
            if 'RESIGNATION' in targets:
                text = row.get('text', '')

                # Filter out transition statements that aren't actual justifications
                text_lower = text.lower()
                if any(excl in text_lower for excl in EXCLUDE_PHRASES):
                    continue

                # Get policy domains
                policy_domain = ann.get('policy_domain', [])
                if isinstance(policy_domain, str):
                    policy_domain = [policy_domain] if policy_domain else []

                results.append({
                    'idx': idx,
                    'text': text,
                    'speech_acts': ann.get('speech_act', []),
                    'emotional_register': ann.get('emotional_register', 'NEUTRAL'),
                    'temporality': ann.get('temporality', []),
                    'rhetorical_devices': ann.get('rhetorical_devices', []),
                    'legacy_framing': ann.get('legacy_framing', 'NONE'),
                    'policy_domain': policy_domain
                })

    return results


def aggregate_cross_data(rationale_data):
    """Aggregate speech acts, emotions, etc. from resignation rationale sentences."""
    speech_acts = Counter()
    emotions = Counter()
    temporality = Counter()
    policy_domains = Counter()

    for item in rationale_data:
        # Speech acts
        for sa in item.get('speech_acts', []):
            if sa and sa != 'NONE':
                speech_acts[sa] += 1

        # Emotional register
        emo = item.get('emotional_register', 'NEUTRAL')
        if emo and emo != 'NONE':
            emotions[emo] += 1

        # Temporality
        for temp in item.get('temporality', []):
            if temp and temp != 'NONE':
                temporality[temp] += 1

        # Policy domains
        for pol in item.get('policy_domain', []):
            if pol and pol != 'NONE':
                policy_domains[pol] += 1

    return {
        'speech_acts': speech_acts.most_common(5),
        'emotions': emotions.most_common(5),
        'temporality': temporality.most_common(5),
        'policy_domains': policy_domains.most_common(5),
        'raw_counters': {
            'speech_acts': speech_acts,
            'emotions': emotions,
            'temporality': temporality,
            'policy_domains': policy_domains
        }
    }


def compute_justification_profile(aggregated):
    """
    Compute justification profile showing what the justification is substantively based on.

    Returns:
        Dict with:
        - dominant_theme: The main policy domain
        - dominant_pct: Percentage of that domain
        - theme_breakdown: List of (theme, count, pct) tuples
        - orientation: Temporal orientation score
        - register: Emotional register score
    """
    raw = aggregated.get('raw_counters', {})
    temporality = raw.get('temporality', Counter())
    emotions = raw.get('emotions', Counter())
    policy = raw.get('policy_domains', Counter())

    # Theme breakdown
    total_policy = sum(v for k, v in policy.items() if k != 'NONE')
    theme_breakdown = []
    for theme, count in policy.most_common():
        if theme != 'NONE' and count > 0:
            pct = round(count / total_policy * 100, 0) if total_policy > 0 else 0
            theme_breakdown.append((theme, count, pct))

    dominant_theme = theme_breakdown[0][0] if theme_breakdown else 'NONE'
    dominant_pct = theme_breakdown[0][2] if theme_breakdown else 0

    # Orientation score (future vs past)
    future_oriented = ['FUTURE_HOPE', 'FUTURE_TRANSITION', 'FUTURE_WARNING']
    past_oriented = ['PAST_REFERENCE', 'PAST_ACHIEVEMENT', 'PAST_REGRET']

    future_count = sum(temporality.get(t, 0) for t in future_oriented)
    past_count = sum(temporality.get(t, 0) for t in past_oriented)
    present_count = sum(v for k, v in temporality.items()
                        if k not in future_oriented + past_oriented and k != 'NONE')
    total_temporal = future_count + past_count + present_count

    if total_temporal > 0:
        orientation_score = (future_count - past_count) / total_temporal
    else:
        orientation_score = 0

    # Register score (constructive vs reactive)
    constructive = ['HOPEFUL', 'SOLEMN', 'DETERMINED', 'PROUD']
    reactive = ['CONCERNED', 'RESIGNED', 'DEFENSIVE', 'COMBATIVE']

    constructive_count = sum(emotions.get(e, 0) for e in constructive)
    reactive_count = sum(emotions.get(e, 0) for e in reactive)
    total_emotions = constructive_count + reactive_count

    if total_emotions > 0:
        register_score = (constructive_count - reactive_count) / total_emotions
    else:
        register_score = 0

    return {
        'dominant_theme': dominant_theme,
        'dominant_pct': dominant_pct,
        'theme_breakdown': theme_breakdown,
        'orientation': orientation_score,
        'register': register_score,
        'counts': {
            'future': future_count,
            'past': past_count,
            'present': present_count,
            'constructive': constructive_count,
            'reactive': reactive_count,
            'total_policy': total_policy
        }
    }


# =============================================================================
# FIGURE GENERATION
# =============================================================================

def generate_html(df, lang='fr'):
    """Generate resignation rationale figure HTML."""
    labels = get_labels(lang)

    # Get data
    rationale_data = get_resignation_rationale_data(df)
    aggregated = aggregate_cross_data(rationale_data)

    # Compute justification profile
    justif_profile = compute_justification_profile(aggregated)

    # Get raw counters for dimensions
    raw = aggregated.get('raw_counters', {})
    policy_domains = raw.get('policy_domains', {})
    total_policy = sum(v for k, v in policy_domains.items() if k != 'NONE')
    party_count = policy_domains.get('PARTY_POLITICS', 0)

    # Calculate percentages for policy content
    party_pct = round(party_count / total_policy * 100) if total_policy > 0 else 0

    total_sentences = len(rationale_data)

    # Labels
    if lang == 'fr':
        title = "Justification de la démission"
        subtitle = "Comment Legault explique sa décision de quitter"
        quote_open, quote_close = '«\u202F', '\u202F»'
        excerpts_title = "Les arguments"
        profile_title = "Profil rhétorique"
        content_title = "Fondement de la justification"
        party_label = "Politique partisane"
        speech_acts_title = "Acte dominant"
        emotions_title = "Registre dominant"
        temporality_title = "Temporalité dominante"
        methodology = (
            f"Méthodologie : Analyse des {total_sentences} phrases justifiant directement la décision. "
            f"Dimensions : orientation temporelle, registre émotionnel, type de discours. N={total_sentences}."
        )
    else:
        title = "Resignation Justification"
        subtitle = "How Legault explains his decision to resign"
        quote_open, quote_close = '"', '"'
        excerpts_title = "The arguments"
        profile_title = "Rhetorical profile"
        content_title = "Justification basis"
        party_label = "Party politics"
        speech_acts_title = "Dominant act"
        emotions_title = "Dominant register"
        temporality_title = "Dominant temporality"
        methodology = (
            f"Methodology: Analysis of {total_sentences} sentences directly justifying the decision. "
            f"Dimensions: temporal orientation, emotional register, discourse type. N={total_sentences}."
        )

    sa_labels = labels.get('speech_act', {})
    emo_labels = labels.get('emotional_register', {})
    policy_labels = labels.get('policy_domain', {})

    # Temporality labels
    if lang == 'fr':
        temp_labels = {
            'PRESENT_SITUATION': 'Présent',
            'PRESENT_ANNOUNCEMENT': 'Annonce',
            'FUTURE_HOPE': 'Futur',
            'FUTURE_TRANSITION': 'Transition',
            'PAST_REFERENCE': 'Passé',
            'ATEMPORAL': 'Atemporel'
        }
    else:
        temp_labels = {
            'PRESENT_SITUATION': 'Present',
            'PRESENT_ANNOUNCEMENT': 'Announcement',
            'FUTURE_HOPE': 'Future',
            'FUTURE_TRANSITION': 'Transition',
            'PAST_REFERENCE': 'Past',
            'ATEMPORAL': 'Atemporal'
        }

    # Build excerpts HTML with all 4 labels
    excerpts_html = ''
    for i, item in enumerate(rationale_data):
        text = item['text']
        # Register
        emo = item['emotional_register']
        emo_label = emo_labels.get(emo, emo)
        emo_color = EMOTIONAL_REGISTER_COLORS.get(emo, '#6B7280')
        # Speech act
        speech_acts = item.get('speech_acts', [])
        primary_sa = speech_acts[0] if speech_acts else 'STATING'
        sa_label = sa_labels.get(primary_sa, primary_sa.replace('_', ' ').title())
        sa_color = SPEECH_ACT_COLORS.get(primary_sa, '#6B7280')
        # Temporality
        temps = item.get('temporality', [])
        primary_temp = temps[0] if temps else 'PRESENT_SITUATION'
        temp_label = temp_labels.get(primary_temp, primary_temp.replace('_', ' ').title())
        # Policy domain
        policy_domains = item.get('policy_domain', [])
        primary_policy = policy_domains[0] if policy_domains else 'NONE'
        policy_label = policy_labels.get(primary_policy, primary_policy.replace('_', ' ').title())
        policy_color = POLICY_DOMAIN_COLORS.get(primary_policy, '#6B7280')

        excerpts_html += f'''
        <div class="excerpt-card" style="border-left-color: {emo_color};">
            <div class="excerpt-tags">
                <span class="tag tag-register" style="background: {emo_color};">{html_lib.escape(emo_label)}</span>
                <span class="tag tag-act" style="background: {sa_color};">{html_lib.escape(sa_label)}</span>
                <span class="tag tag-temp">{html_lib.escape(temp_label)}</span>
                <span class="tag tag-policy" style="background: {policy_color};">{html_lib.escape(policy_label)}</span>
            </div>
            <p class="excerpt-text">{quote_open}{html_lib.escape(text)}{quote_close}</p>
        </div>
        '''

    # Compute 3-dimension scores (excluding partisan)
    orientation_score = justif_profile['orientation']  # future (+1) vs past (-1)
    register_score = justif_profile['register']  # constructive (+1) vs defensive (-1)

    # Action score: prescriptive (+1) vs diagnostic (-1)
    speech_acts_raw = raw.get('speech_acts', {})
    diagnostic_acts = ['STATING', 'DIAGNOSING', 'FRAMING']
    prescriptive_acts = ['PROPOSING', 'EXHORTING', 'COMMITTING', 'ANNOUNCING']
    diag_count = sum(speech_acts_raw.get(a, 0) for a in diagnostic_acts)
    presc_count = sum(speech_acts_raw.get(a, 0) for a in prescriptive_acts)
    total_acts = diag_count + presc_count
    action_score = (presc_count - diag_count) / total_acts if total_acts > 0 else 0

    # Build horizontal diverging gauges for 3 dimensions with label explanations
    if lang == 'fr':
        dimensions = [
            ("Orientation temporelle", "Passé", "Futur", orientation_score, "temporality"),
            ("Registre émotionnel", "Défensif", "Constructif", register_score, "emotional_register"),
            ("Type de discours", "Diagnostique", "Prescriptif", action_score, "speech_act"),
        ]
        # Labels used for each dimension
        dim_labels_used = {
            "temporality": "Futur, Présent, Passé",
            "emotional_register": "Optimiste, Solennel vs Préoccupé, Résigné",
            "speech_act": "Annonce, Souhait vs Diagnostic, Constat",
        }
    else:
        dimensions = [
            ("Temporal orientation", "Past", "Future", orientation_score, "temporality"),
            ("Emotional register", "Defensive", "Constructive", register_score, "emotional_register"),
            ("Discourse type", "Diagnostic", "Prescriptive", action_score, "speech_act"),
        ]
        dim_labels_used = {
            "temporality": "Future, Present, Past",
            "emotional_register": "Hopeful, Solemn vs Concerned, Resigned",
            "speech_act": "Announcing, Wishing vs Diagnosing, Stating",
        }

    gauges_html = '<div class="gauges">'
    for dim_name, neg_pole, pos_pole, score, dim_key in dimensions:
        color = POSITIVE_COLOR if score > 0 else NEGATIVE_COLOR if score < 0 else '#6B7280'
        # Position: -1 = 0%, 0 = 50%, +1 = 100%
        pos_pct = (score + 1) / 2 * 100
        # Fill width from center
        fill_width = abs(score) * 50  # 50% max from center

        if score < 0:
            fill_html = f'<div class="gauge-fill gauge-fill-neg" style="width: {fill_width:.1f}%; background: {color};"></div>'
        else:
            fill_html = f'<div class="gauge-fill gauge-fill-pos" style="width: {fill_width:.1f}%; background: {color};"></div>'

        labels_hint = dim_labels_used.get(dim_key, "")

        gauges_html += f'''
        <div class="gauge-row">
            <div class="gauge-header">
                <span class="gauge-dim">{html_lib.escape(dim_name)}</span>
                <span class="gauge-score" style="color: {color};">{score:+.2f}</span>
            </div>
            <div class="gauge-track">
                <span class="gauge-pole gauge-pole-left">{html_lib.escape(neg_pole)}</span>
                <div class="gauge-bar">
                    {fill_html}
                    <div class="gauge-center"></div>
                    <div class="gauge-dot" style="left: {pos_pct:.1f}%; background: {color};"></div>
                </div>
                <span class="gauge-pole gauge-pole-right">{html_lib.escape(pos_pole)}</span>
            </div>
            <div class="gauge-labels-hint">{html_lib.escape(labels_hint)}</div>
        </div>
        '''
    gauges_html += '</div>'

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
            padding: 44px 80px 36px;
            height: 100%;
            display: flex;
            flex-direction: column;
        }}

        /* Header */
        .header {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            padding-bottom: 14px;
            border-bottom: 2px solid var(--ink);
            margin-bottom: 24px;
            flex-shrink: 0;
        }}
        .main-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 54px;
            font-weight: 600;
            letter-spacing: -0.02em;
            line-height: 1.1;
        }}
        .subtitle {{
            font-size: 18px;
            color: var(--muted);
            margin-top: 6px;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }}

        /* Main 2-column layout */
        .main-content {{
            flex: 1;
            display: grid;
            grid-template-columns: 1.1fr 1fr;
            gap: 40px;
            min-height: 0;
            align-items: center;
        }}

        /* Left column: Excerpts - vertically centered */
        .left-col {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            height: 100%;
        }}
        .col-title {{
            font-size: 15px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--muted);
            margin-bottom: 20px;
        }}

        /* Excerpts with tags */
        .excerpts-list {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        .excerpt-card {{
            background: var(--card);
            border-radius: 14px;
            border: 1px solid var(--line);
            border-left: 7px solid var(--accent);
            padding: 18px 22px;
            box-shadow: var(--shadow-soft);
        }}
        .excerpt-tags {{
            display: flex;
            gap: 10px;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }}
        .tag {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            padding: 5px 12px;
            border-radius: 5px;
            color: white;
        }}
        .tag-temp {{
            background: var(--muted);
        }}
        .excerpt-text {{
            font-family: 'STIX Two Text', serif;
            font-size: 17px;
            line-height: 1.55;
            color: var(--ink);
        }}

        /* Right column: Profile + Key finding */
        .right-col {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 24px;
            height: 100%;
        }}

        /* Profile card with gauges */
        .profile-card {{
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            padding: 36px 40px;
            box-shadow: var(--shadow-soft);
        }}
        .profile-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 26px;
            font-weight: 600;
            margin-bottom: 28px;
            text-align: center;
            color: var(--ink);
        }}

        /* Dimension gauges */
        .gauges {{
            display: flex;
            flex-direction: column;
            gap: 28px;
        }}
        .gauge-row {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .gauge-header {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
        }}
        .gauge-dim {{
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--muted);
        }}
        .gauge-score {{
            font-family: 'STIX Two Text', serif;
            font-size: 32px;
            font-weight: 700;
        }}
        .gauge-track {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}
        .gauge-pole {{
            font-size: 14px;
            font-weight: 600;
            width: 100px;
            color: var(--muted);
        }}
        .gauge-pole-left {{ text-align: right; }}
        .gauge-pole-right {{ text-align: left; }}
        .gauge-bar {{
            flex: 1;
            height: 18px;
            background: var(--bg-deep);
            border-radius: 9px;
            position: relative;
            overflow: visible;
        }}
        .gauge-fill {{
            position: absolute;
            top: 3px;
            height: 12px;
            border-radius: 6px;
        }}
        .gauge-fill-neg {{
            right: 50%;
            border-radius: 6px 0 0 6px;
        }}
        .gauge-fill-pos {{
            left: 50%;
            border-radius: 0 6px 6px 0;
        }}
        .gauge-center {{
            position: absolute;
            left: 50%;
            top: -3px;
            width: 2px;
            height: 24px;
            background: var(--line);
            transform: translateX(-50%);
        }}
        .gauge-dot {{
            position: absolute;
            top: 50%;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            transform: translate(-50%, -50%);
            border: 3px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        .gauge-labels-hint {{
            font-size: 11px;
            color: var(--muted);
            font-style: italic;
            text-align: center;
            margin-top: 2px;
        }}

        /* Key finding callout */
        .key-finding {{
            background: linear-gradient(135deg, rgba(0, 61, 165, 0.08) 0%, rgba(0, 61, 165, 0.03) 100%);
            border: 2px solid {QUEBEC_BLUE};
            border-radius: 16px;
            padding: 32px 36px;
            text-align: center;
        }}
        .key-finding-label {{
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: {QUEBEC_BLUE};
            margin-bottom: 12px;
        }}
        .key-finding-stat {{
            font-family: 'STIX Two Text', serif;
            font-size: 84px;
            font-weight: 700;
            color: {QUEBEC_BLUE};
            line-height: 1;
            margin-bottom: 10px;
        }}
        .key-finding-text {{
            font-size: 19px;
            color: var(--ink);
            font-weight: 600;
        }}

        /* Footer */
        .methodology {{
            margin-top: auto;
            padding-top: 16px;
            flex-shrink: 0;
        }}
        .methodology-text {{
            font-size: 13px;
            color: var(--muted);
            border-top: 1px solid var(--line);
            padding-top: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div>
                <h1 class="main-title">{html_lib.escape(title)}</h1>
                <p class="subtitle">{html_lib.escape(subtitle)}</p>
            </div>
        </header>

        <div class="main-content">
            <!-- Left: Excerpts with tags -->
            <div class="left-col">
                <h2 class="col-title">{html_lib.escape(excerpts_title)} ({total_sentences})</h2>
                <div class="excerpts-list">
                    {excerpts_html}
                </div>
            </div>

            <!-- Right: Profile gauges + Key finding -->
            <div class="right-col">
                <div class="profile-card">
                    <h3 class="profile-title">{html_lib.escape(profile_title)}</h3>
                    {gauges_html}
                </div>

                <div class="key-finding">
                    <div class="key-finding-label">{html_lib.escape(content_title)}</div>
                    <div class="key-finding-stat">{party_pct}%</div>
                    <div class="key-finding-text">{html_lib.escape(party_label)}</div>
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
    """Generate resignation rationale figure."""
    if df is None:
        df = load_data()

    for lang in ['fr', 'en']:
        html_content = generate_html(df, lang)
        save_figure(html_content, OUTPUT_DIR, f'fig1b_resignation_rationale_{lang}', export_png=export_png)


if __name__ == '__main__':
    main()
