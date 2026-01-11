#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig8_diplomatic_positioning.py

MAIN OBJECTIVE:
---------------
Analyze Macron's diplomatic positioning through actor framing patterns.
Classifies actors into groups (Us/France & Europe, Close Allies, Major Powers,
Global South) and measures valence distribution to compute a Diplomatic Index.

Dependencies:
-------------
- compute_indices (load_data, select_excerpt_candidates)
- config (get_labels)
- html_utils (COLORS, POSITIVE_COLOR, NEGATIVE_COLOR, save_figure)

MAIN FEATURES:
--------------
1) Normalize and classify actors into geopolitical groups
2) Compute valence distribution (positive/neutral/negative) per group
3) Calculate Diplomatic Index: contrast between in-group and out-group framing
4) Display representative excerpts for each group
5) Generate bilingual output (FR/EN)

Author:
-------
Antoine Lemor
"""

import json
import re
from pathlib import Path
from collections import Counter, defaultdict
from compute_indices import load_data, select_excerpt_candidates
from config import get_labels
from html_utils import COLORS, POSITIVE_COLOR, NEGATIVE_COLOR, save_figure

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output" / "figures"

# =============================================================================
# ENTITY CLASSIFICATION
# =============================================================================

ENTITY_NORMALIZATION = {
    'France': 'France', 'France (nous)': 'France', 'France (nous/on)': 'France',
    'Français': 'France', 'nous': 'France', 'on': 'France',
    'Europe': 'Europe/UE', 'Europe/UE': 'Europe/UE', 'Union européenne': 'Europe/UE',
    'UE': 'Europe/UE', 'Européens': 'Europe/UE', 'Europe / Union européenne': 'Europe/UE',
    'Commission européenne': 'Commission européenne',
    'Ambassadeurs': 'Ambassadeurs', 'Ambassadeurs (vous)': 'Ambassadeurs',
    'Ambassadeurs (audience)': 'Ambassadeurs', 'Ambassades françaises': 'Ambassadeurs',
    'Diplomatie française': 'Diplomatie française',
    'Armées françaises': 'Forces françaises', 'Paris': 'Paris',
    'Coalition des volontaires': 'Coalition volontaires',
    'États-Unis': 'États-Unis', 'États-Unis d\'Amérique': 'États-Unis',
    'États-Unis / Américains': 'États-Unis', 'Américains': 'États-Unis',
    'USA': 'États-Unis', 'Washington': 'États-Unis',
    'Chine': 'Chine', 'Pékin': 'Chine', 'Chinois': 'Chine',
    'Russie': 'Russie', 'Moscou': 'Russie', 'Kremlin': 'Russie',
    'Inde': 'Inde', 'Ukraine': 'Ukraine', 'Canada': 'Canada',
    'Royaume-Uni': 'Royaume-Uni', 'G7': 'G7', 'OTAN': 'OTAN',
    'Afrique': 'Afrique', 'BRICS': 'BRICS',
}

ENTITY_GROUPS = {
    'NOUS': {'France', 'Europe/UE', 'Commission européenne', 'Ambassadeurs',
             'Diplomatie française', 'Forces françaises', 'Paris', 'Coalition volontaires'},
    'ALLIES': {'Ukraine', 'Inde', 'Canada', 'Royaume-Uni', 'G7', 'OTAN'},
    'PUISSANCES': {'États-Unis', 'Chine', 'Russie'},
    'SUD_GLOBAL': {'Afrique', 'BRICS'},
}

GROUP_INFO = {
    'NOUS': {'color': '#0055A4', 'label_fr': 'Nous (France & Europe)', 'label_en': 'Us (France & Europe)'},
    'ALLIES': {'color': '#059669', 'label_fr': 'Alliés proches', 'label_en': 'Close Allies'},
    'PUISSANCES': {'color': '#7C3AED', 'label_fr': 'Grandes puissances', 'label_en': 'Major Powers'},
    'SUD_GLOBAL': {'color': '#D97706', 'label_fr': 'Sud global', 'label_en': 'Global South'},
}

# Quotes to exclude from excerpt selection (partial match)
QUOTE_EXCLUSIONS = [
    "le sommet de Paris pour la prospérité des peuples",
    "Ce que je dis n'est rien d'autre, par exemple, que ce que font ensemble le Canada",
]


def extract_actor_data(df):
    """Extract and classify all actors with their valence."""
    actor_data = defaultdict(lambda: {'POSITIVE': 0, 'NEUTRAL': 0, 'NEGATIVE': 0, 'AMBIGUOUS': 0})
    quote_candidates = []

    for _, row in df.iterrows():
        val = row.get('actors')
        text = row.get('text', '')
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except:
                continue
        if isinstance(val, list):
            for a in val:
                if isinstance(a, dict):
                    raw_actor = a.get('actor', '')
                    valence = a.get('valence', 'NEUTRAL')
                    actor = ENTITY_NORMALIZATION.get(raw_actor, raw_actor)
                    actor_data[actor][valence] += 1
                    group = next((g for g, entities in ENTITY_GROUPS.items() if actor in entities), None)
                    if group and text:
                        quote_candidates.append({
                            'text': text,
                            'actor': actor,
                            'valence': valence,
                            'group': group,
                        })

    return actor_data, quote_candidates


def classify_actors(actor_data):
    """Classify actors into groups and compute metrics."""
    group_data = {}

    for group_name, entities in ENTITY_GROUPS.items():
        pos = sum(actor_data[e]['POSITIVE'] for e in entities if e in actor_data)
        neu = sum(actor_data[e]['NEUTRAL'] for e in entities if e in actor_data)
        neg = sum(actor_data[e]['NEGATIVE'] for e in entities if e in actor_data)
        total = pos + neu + neg
        score = (pos - neg) / total if total > 0 else 0

        top_entities = []
        for e in entities:
            if e in actor_data:
                e_total = sum(actor_data[e].values())
                if e_total > 0:
                    e_score = (actor_data[e]['POSITIVE'] - actor_data[e]['NEGATIVE']) / e_total
                    top_entities.append({
                        'entity': e, 'total': e_total,
                        'positive': actor_data[e]['POSITIVE'],
                        'negative': actor_data[e]['NEGATIVE'],
                        'neutral': actor_data[e]['NEUTRAL'],
                        'score': e_score,
                    })
        top_entities.sort(key=lambda x: x['total'], reverse=True)

        group_data[group_name] = {
            'positive': pos, 'neutral': neu, 'negative': neg,
            'total': total, 'score': score, 'entities': top_entities[:4],
        }

    return group_data


def compute_diplomatic_index(group_data):
    """Compute Diplomatic Framing Index."""
    nous_score = group_data['NOUS']['score']
    allies_score = group_data['ALLIES']['score'] if group_data['ALLIES']['total'] > 0 else 0
    puissances_score = group_data['PUISSANCES']['score'] if group_data['PUISSANCES']['total'] > 0 else 0
    in_group_avg = (nous_score + allies_score) / 2
    return (in_group_avg - puissances_score) / 2


def generate_html(group_data, diplomatic_index, quote_candidates, lang='fr'):
    """Generate the editorial-style diplomatic positioning HTML."""

    # Check if major powers are particularly targeted
    puissances_score = group_data['PUISSANCES']['score']
    puissances_targeted = puissances_score < -0.1

    if lang == 'fr':
        title = "Positionnement diplomatique : nous vs eux"
        subtitle = "Comment Macron cadre-t-il la France par rapport aux autres acteurs internationaux ?"
        index_label = "Indice de cadrage"
        index_desc = "Mesure le contraste entre le cadrage positif du 'nous' (France, Europe, alliés) et celui des puissances extérieures."
        pos_label, neu_label, neg_label = "Positif", "Neutre", "Négatif"
        mentions_label = "mentions"
        methodology = "Méthodologie : Chaque mention d'acteur est annotée avec une valence (positif/neutre/négatif). Score = (positif − négatif) / total mentions."
        excerpts_title = "Extraits labellisés"
        key_insight = "Grandes puissances particulièrement ciblées" if puissances_targeted else ""
        if diplomatic_index > 0.3:
            interp = "Très favorable au 'nous'"
        elif diplomatic_index > 0.1:
            interp = "Modérément favorable"
        else:
            interp = "Relativement équilibré"
    else:
        title = "Diplomatic Positioning: Us vs Them"
        subtitle = "How does Macron frame France relative to other international actors?"
        index_label = "Framing Index"
        index_desc = "Measures the contrast between positive 'us' framing (France, Europe, allies) and external powers framing."
        pos_label, neu_label, neg_label = "Positive", "Neutral", "Negative"
        mentions_label = "mentions"
        methodology = "Methodology: Each actor mention is annotated with valence (positive/neutral/negative). Score = (positive − negative) / total mentions."
        excerpts_title = "Labeled excerpts"
        key_insight = "Major powers particularly targeted" if puissances_targeted else ""
        if diplomatic_index > 0.3:
            interp = "Highly favorable to 'us'"
        elif diplomatic_index > 0.1:
            interp = "Moderately favorable"
        else:
            interp = "Relatively balanced"

    # Generate group cards
    group_cards_html = ""
    for group_id in ['NOUS', 'ALLIES', 'PUISSANCES', 'SUD_GLOBAL']:
        data = group_data[group_id]
        if data['total'] == 0:
            continue

        info = GROUP_INFO[group_id]
        color = info['color']
        label = info[f'label_{lang}']
        score = data['score']
        score_color = POSITIVE_COLOR if score > 0.15 else NEGATIVE_COLOR if score < -0.15 else '#78716c'

        pos_pct = data['positive'] / data['total'] * 100
        neu_pct = data['neutral'] / data['total'] * 100
        neg_pct = data['negative'] / data['total'] * 100

        entities_html = ""
        for ent in data['entities'][:3]:
            ent_color = POSITIVE_COLOR if ent['score'] > 0.15 else NEGATIVE_COLOR if ent['score'] < -0.15 else '#78716c'
            entities_html += f'''
            <div class="entity-row">
                <span class="entity-name">{ent['entity']}</span>
                <span class="entity-count">{ent['total']}</span>
                <span class="entity-score" style="color: {ent_color};">{ent['score']:+.2f}</span>
            </div>'''

        group_cards_html += f'''
        <div class="group-card">
            <div class="group-color-bar" style="background: {color};"></div>
            <div class="group-content">
                <div class="group-header">
                    <span class="group-label">{label}</span>
                    <span class="group-total">{data['total']} {mentions_label}</span>
                </div>
                <div class="group-score" style="color: {score_color};">{score:+.2f}</div>
                <div class="valence-bar">
                    <div class="valence-segment pos" style="width: {pos_pct}%;"></div>
                    <div class="valence-segment neu" style="width: {neu_pct}%;"></div>
                    <div class="valence-segment neg" style="width: {neg_pct}%;"></div>
                </div>
                <div class="valence-legend">
                    <span class="v-pos">{pos_label}: {data['positive']}</span>
                    <span class="v-neg">{neg_label}: {data['negative']}</span>
                </div>
                <div class="entities-list">{entities_html}</div>
            </div>
        </div>'''

    idx_color = POSITIVE_COLOR if diplomatic_index > 0.15 else '#78716c'

    def format_quote(text):
        cleaned = ' '.join(str(text).split())
        match = re.search(r'^(.*?[.!?])(?:\s|$)', cleaned)
        return match.group(1) if match else cleaned

    def build_quote_card(q, excerpts_title, lang):
        group_info = GROUP_INFO.get(q.get('group', ''), {})
        group_label = group_info.get('label_fr' if lang == 'fr' else 'label_en', q.get('group', ''))
        actor_label = q.get('actor', '')
        valence = q.get('valence', 'NEUTRAL')
        tone_class = 'quote-pos' if valence == 'POSITIVE' else 'quote-neg' if valence == 'NEGATIVE' else 'quote-neu'
        return f'''
            <div class="quote-card {tone_class}">
                <div class="quote-meta">
                    <span class="quote-label">{group_label}</span>
                </div>
                <div class="quote-actor">{actor_label}</div>
                <div class="quote-text">« {format_quote(q.get('text', ''))} »</div>
            </div>'''

    # Filter out excluded quotes
    def is_excluded(q):
        text = q.get('text', '')
        return any(excl in text for excl in QUOTE_EXCLUSIONS)

    # Get quotes for each group type (excluding blacklisted ones)
    puissances_quotes = [q for q in quote_candidates if q.get('group') == 'PUISSANCES' and not is_excluded(q)]
    sud_quotes = [q for q in quote_candidates if q.get('group') == 'SUD_GLOBAL' and not is_excluded(q)]
    nous_quotes = [q for q in quote_candidates if q.get('group') == 'NOUS' and not is_excluded(q)]
    allies_quotes = [q for q in quote_candidates if q.get('group') == 'ALLIES' and not is_excluded(q)]

    # Select best quotes from each group
    selected_quotes = []
    if puissances_quotes:
        candidates = select_excerpt_candidates(puissances_quotes, min_len=80, max_len=360, limit=2)
        selected_quotes.append(candidates[0] if candidates else puissances_quotes[0])
    if sud_quotes:
        candidates = select_excerpt_candidates(sud_quotes, min_len=80, max_len=360, limit=2)
        selected_quotes.append(candidates[0] if candidates else sud_quotes[0])
    if nous_quotes:
        # Use second quote for France if available for variety
        candidates = select_excerpt_candidates(nous_quotes, min_len=80, max_len=360, limit=3)
        selected_quotes.append(candidates[1] if len(candidates) > 1 else (candidates[0] if candidates else nous_quotes[0]))
    if allies_quotes:
        # Use second quote for Allies if available for variety
        candidates = select_excerpt_candidates(allies_quotes, min_len=80, max_len=360, limit=3)
        selected_quotes.append(candidates[1] if len(candidates) > 1 else (candidates[0] if candidates else allies_quotes[0]))

    quote_cards_html = ""
    for q in selected_quotes[:4]:
        quote_cards_html += build_quote_card(q, excerpts_title, lang)

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

        /* Index display */
        .index-box {{
            text-align: center;
            padding: 18px 26px;
            background: var(--card);
            border: 1px solid var(--line);
            border-left: 10px solid {idx_color};
            border-radius: 16px;
            box-shadow: var(--shadow-soft);
        }}
        .index-value {{
            font-family: 'STIX Two Text', serif;
            font-size: 60px;
            font-weight: 700;
            color: {idx_color};
            line-height: 1;
        }}
        .index-label {{
            font-size: 16px;
            font-weight: 600;
            color: var(--muted);
            margin-top: 8px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .index-interp {{
            font-size: 15px;
            color: {idx_color};
            font-weight: 600;
            margin-top: 4px;
        }}
        .key-insight {{
            margin-top: 10px;
            padding: 6px 12px;
            background: rgba(124, 58, 237, 0.15);
            border-radius: 999px;
            font-size: 13px;
            font-weight: 700;
            color: #7C3AED;
            letter-spacing: 0.06em;
        }}

        /* Main content */
        .main-content {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
            flex: 1;
            min-height: 0;
        }}

        /* Group cards */
        .group-card {{
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow-soft);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        .group-color-bar {{
            height: 6px;
        }}
        .group-content {{
            padding: 18px 20px;
            flex: 1;
            display: flex;
            flex-direction: column;
        }}
        .group-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .group-label {{
            font-size: 18px;
            font-weight: 700;
            color: var(--ink);
        }}
        .group-total {{
            font-size: 14px;
            color: var(--muted);
        }}
        .group-score {{
            font-family: 'STIX Two Text', serif;
            font-size: 44px;
            font-weight: 700;
            text-align: center;
            margin-bottom: 12px;
        }}

        /* Valence bar */
        .valence-bar {{
            display: flex;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 8px;
        }}
        .valence-segment.pos {{ background: {POSITIVE_COLOR}; }}
        .valence-segment.neu {{ background: #d6d3d1; }}
        .valence-segment.neg {{ background: {NEGATIVE_COLOR}; }}
        .valence-legend {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            margin-bottom: 14px;
        }}
        .v-pos {{ color: {POSITIVE_COLOR}; font-weight: 600; }}
        .v-neg {{ color: {NEGATIVE_COLOR}; font-weight: 600; }}

        /* Entities list */
        .entities-list {{
            border-top: 1px solid var(--line);
            padding-top: 12px;
            margin-top: auto;
        }}
        .entity-row {{
            display: flex;
            align-items: center;
            padding: 6px 0;
        }}
        .entity-name {{
            flex: 1;
            font-size: 15px;
            font-weight: 500;
            color: var(--ink);
        }}
        .entity-count {{
            font-size: 13px;
            color: var(--muted);
            margin-right: 12px;
        }}
        .entity-score {{
            font-family: 'STIX Two Text', serif;
            font-size: 18px;
            font-weight: 600;
        }}

        .excerpt-section {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .excerpt-label {{
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
        .quote-card.quote-pos {{ border-left: 8px solid {POSITIVE_COLOR}; }}
        .quote-card.quote-neg {{ border-left: 8px solid {NEGATIVE_COLOR}; }}
        .quote-card.quote-neu {{ border-left: 8px solid var(--line); }}
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
        .quote-actor {{
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--muted);
        }}
        .quote-text {{
            font-family: 'STIX Two Text', serif;
            font-size: 19px;
            line-height: 1.5;
            color: var(--ink);
        }}

        /* Description */
        .description {{
            margin-top: 10px;
            padding: 16px 24px;
            background: var(--card);
            border-radius: 14px;
            border: 1px solid var(--line);
            border-left: 8px solid #0055A4;
            box-shadow: var(--shadow-soft);
        }}
        .description-text {{
            font-size: 17px;
            color: var(--muted);
            line-height: 1.5;
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
            <div class="index-box">
                <div class="index-value">{diplomatic_index:+.2f}</div>
                <div class="index-label">{index_label}</div>
                <div class="index-interp">{interp}</div>
                {f'<div class="key-insight">{key_insight}</div>' if key_insight else ''}
            </div>
        </header>

        <div class="main-content">
            {group_cards_html}
        </div>

        <div class="excerpt-section">
            <div class="excerpt-label">{excerpts_title}</div>
            <div class="quote-cards">
                {quote_cards_html}
            </div>
        </div>

        <div class="description">
            <p class="description-text">{index_desc}</p>
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
    print("Generating Figure 8: Diplomatic Positioning")
    print("=" * 70)

    df = load_data()
    actor_data, quote_candidates = extract_actor_data(df)
    group_data = classify_actors(actor_data)
    diplomatic_index = compute_diplomatic_index(group_data)

    print(f"\nDiplomatic Framing Index: {diplomatic_index:+.2f}")
    for group_name, data in group_data.items():
        print(f"  {group_name}: n={data['total']}, score={data['score']:+.2f}")

    for lang in ['fr', 'en']:
        print(f"\n--- {lang.upper()} ---")
        html = generate_html(group_data, diplomatic_index, quote_candidates, lang)
        save_figure(html, OUTPUT_DIR, f"fig8_diplomatic_positioning_{lang}")

    print("\nDone!")


if __name__ == "__main__":
    main()
