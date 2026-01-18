#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig5_actors.py

MAIN OBJECTIVE:
---------------
Generate figure analyzing actors (people, organizations) mentioned in the speech.
Diverging bar chart showing positive vs negative sentiment per actor.

Dependencies:
-------------
- config (colors, labels)
- load_and_validate (data loading)
- compute_indices (aggregation)
- html_utils (HTML generation, export)

MAIN FEATURES:
--------------
1) Diverging bar chart per actor (positive/negative)
2) Net sentiment score per actor
3) Actor sentiment index
4) Quote cards for positive/negative examples

Author:
-------
Antoine Lemor
"""

import html as html_lib
from pathlib import Path
from collections import Counter
import pandas as pd

from config import (
    get_labels, POSITIVE_COLOR, NEGATIVE_COLOR, QUEBEC_BLUE
)
from load_and_validate import load_data, OUTPUT_DIR, extract_actors
from compute_indices import aggregate_actors, select_excerpt_candidates
from html_utils import save_figure


# =============================================================================
# ACTOR NAME NORMALIZATION
# =============================================================================

# Actors to exclude from the analysis
EXCLUDED_ACTORS = {
    'François Legault',
    'Premier ministre du Québec (François Legault)',
}

# Mapping of actor names to their canonical form
ACTOR_NAME_MAP = {
    # Martin variations
    'Martin Koskinen': 'Martin Koskinen',
    'Martin': 'Martin Koskinen',
    '« nous » (Legault et Martin)': 'Martin Koskinen',
    # CAQ variations
    'la CAQ': 'CAQ',
    'CAQ': 'CAQ',
    'mon parti (CAQ)': 'CAQ',
    'un nouveau parti (la CAQ, implicitement)': 'CAQ',
    'Parti (nouveau parti/CAQ implicitement)': 'CAQ',
    'le parti': 'CAQ',
    # Québec variations
    'Québec': 'Québec',
    'notre nation (Québec)': 'Québec',
    # Quebec people
    'Québécois': 'Québécois',
    # Audience / Implicit
    'tout le monde': 'Auditoire',
    'tous (audience)': 'Auditoire',
    'vous (audience)': 'Auditoire',
    'personne (tout le monde)': 'Auditoire',
    # Nous / on
    'nous': 'Nous (collectif)',
    'nous / on (collectif québécois)': 'Nous (collectif)',
    # Canada
    'Canada (reste du Canada)': 'Canada',
}


def normalize_actor_name(actor_name):
    """Normalize actor name to canonical form."""
    if actor_name in EXCLUDED_ACTORS:
        return None
    return ACTOR_NAME_MAP.get(actor_name, actor_name)


# =============================================================================
# DATA PREPARATION
# =============================================================================

def compute_actor_sentiment_index(df):
    """
    Compute overall sentiment index for actors.

    Formula: (positive - negative) / (positive + negative)
    Range: [-1, +1] where -1 = all negative, +1 = all positive
    """
    actors_df = extract_actors(df)
    if actors_df.empty:
        return 0.0, {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0}

    # Normalize actor names and filter out excluded actors
    actors_df['actor_normalized'] = actors_df['actor'].apply(normalize_actor_name)
    actors_df = actors_df[actors_df['actor_normalized'].notna()]

    valence_counts = actors_df['valence'].value_counts().to_dict()
    pos = valence_counts.get('POSITIVE', 0)
    neg = valence_counts.get('NEGATIVE', 0)
    neu = valence_counts.get('NEUTRAL', 0)
    total = pos + neg

    if total == 0:
        return 0.0, {'positive': pos, 'negative': neg, 'neutral': neu, 'total': len(actors_df)}

    index = (pos - neg) / total
    return float(index), {'positive': pos, 'negative': neg, 'neutral': neu, 'total': len(actors_df)}


def get_actor_sentiment_breakdown(df):
    """Get sentiment breakdown per actor with counts and percentages."""
    actors_df = extract_actors(df)
    if actors_df.empty:
        return []

    # Normalize actor names and filter out excluded actors
    actors_df['actor'] = actors_df['actor'].apply(normalize_actor_name)
    actors_df = actors_df[actors_df['actor'].notna()]

    # Group by normalized actor and valence
    grouped = actors_df.groupby(['actor', 'valence']).size().unstack(fill_value=0)

    # Calculate totals and percentages
    results = []
    for actor in grouped.index:
        pos = grouped.loc[actor].get('POSITIVE', 0)
        neg = grouped.loc[actor].get('NEGATIVE', 0)
        neu = grouped.loc[actor].get('NEUTRAL', 0)
        total = pos + neg + neu

        if total >= 2:  # Only include actors with at least 2 mentions
            net_score = (pos - neg) / total if total > 0 else 0
            results.append({
                'actor': actor,
                'positive': pos,
                'negative': neg,
                'neutral': neu,
                'total': total,
                'net_score': net_score,
                'pos_pct': pos / total * 100 if total > 0 else 0,
                'neg_pct': neg / total * 100 if total > 0 else 0
            })

    # Sort by total mentions
    results.sort(key=lambda x: x['total'], reverse=True)
    return results


def get_actor_excerpts(df, valence, limit=1):
    """Get excerpts for actors with specific valence."""
    actors_df = extract_actors(df)
    if actors_df.empty:
        return []

    filtered = actors_df[actors_df['valence'] == valence]
    if filtered.empty:
        return []

    # Get the segment texts
    segment_ids = filtered['segment_id'].unique()
    results = []

    for seg_id in segment_ids[:limit*3]:  # Check more to find good ones
        text = df[df['segment_id'] == seg_id]['text'].iloc[0] if seg_id in df['segment_id'].values else ''
        actor = filtered[filtered['segment_id'] == seg_id]['actor'].iloc[0]
        if len(text) >= 60 and len(text) <= 300:
            results.append({'text': text, 'actor': actor})
            if len(results) >= limit:
                break

    return results


# Constructed category actors (not real named entities)
CONSTRUCTED_ACTORS = {'Auditoire', 'Nous (collectif)'}


def get_excerpt_for_actor(df, actor_normalized, limit=1):
    """Get an excerpt where this actor is mentioned."""
    actors_df = extract_actors(df)
    if actors_df.empty:
        return None

    # Normalize all actors
    actors_df['actor_normalized'] = actors_df['actor'].apply(normalize_actor_name)

    # Filter to this actor
    filtered = actors_df[actors_df['actor_normalized'] == actor_normalized]
    if filtered.empty:
        return None

    # Get best excerpt (prefer longer texts)
    for _, row in filtered.iterrows():
        seg_id = row['segment_id']
        matching_rows = df[df['segment_id'] == seg_id]
        if not matching_rows.empty:
            text = matching_rows['text'].iloc[0]
            if len(text) >= 60:
                return text

    return None


# =============================================================================
# FIGURE GENERATION
# =============================================================================

def generate_html(df, lang='fr'):
    """Generate actors figure HTML for specified language."""
    labels = get_labels(lang)

    # Get data
    actor_sentiment_idx, sentiment_meta = compute_actor_sentiment_index(df)
    actor_breakdown = get_actor_sentiment_breakdown(df)

    total_mentions = sentiment_meta['total']
    pos_count = sentiment_meta['positive']
    neg_count = sentiment_meta['negative']

    # Separate named actors from constructed categories
    named_actors = [a for a in actor_breakdown if a['actor'] not in CONSTRUCTED_ACTORS]
    constructed_actors = [a for a in actor_breakdown if a['actor'] in CONSTRUCTED_ACTORS]

    # Title and content
    if lang == 'fr':
        title = "Tonalité envers les acteurs"
        subtitle = "Comment Legault parle-t-il des personnes et groupes qu'il mentionne ?"
        methodology = (
            f"Méthodologie : Chaque mention d'acteur est annotée avec une valence (positif, négatif, neutre). "
            f"Score net = (positif − négatif) / total. François Legault exclu de l'analyse."
        )
        header_neg = "NÉGATIF"
        header_pos = "POSITIF"
        header_net = "Score net"
        index_label = "Indice de sentiment"
        index_interp = "très positif" if actor_sentiment_idx > 0.5 else ("positif" if actor_sentiment_idx > 0.2 else "modéré")
        index_meta = f"Positifs: {pos_count} · Négatifs: {neg_count} · Total: {total_mentions}"
        constructed_title = "Catégories construites"
        constructed_desc = "Ces catégories regroupent des références implicites ou collectives"
        excerpts_title = "Extraits représentatifs"
        quote_open, quote_close = '«\u202F', '\u202F»'
    else:
        title = "Actor Sentiment Landscape"
        subtitle = "Who receives what treatment in Legault's speech?"
        methodology = (
            f"Methodology: Each actor mention is annotated with a valence (positive, negative, neutral). "
            f"Net score = (positive − negative) / total. François Legault excluded from analysis."
        )
        header_neg = "NEGATIVE"
        header_pos = "POSITIVE"
        header_net = "Net score"
        index_label = "Sentiment index"
        index_interp = "very positive" if actor_sentiment_idx > 0.5 else ("positive" if actor_sentiment_idx > 0.2 else "moderate")
        index_meta = f"Positive: {pos_count} · Negative: {neg_count} · Total: {total_mentions}"
        constructed_title = "Constructed categories"
        constructed_desc = "These categories group implicit or collective references"
        excerpts_title = "Representative excerpts"
        quote_open, quote_close = '"', '"'

    # Build actor rows with diverging bars (named actors only)
    actors_html = ''
    max_pct = max([max(a['pos_pct'], a['neg_pct']) for a in named_actors[:8]] or [1])

    for actor_data in named_actors[:8]:
        actor = actor_data['actor']
        pos_pct = actor_data['pos_pct']
        neg_pct = actor_data['neg_pct']
        total = actor_data['total']
        net_score = actor_data['net_score']

        # Scale bars relative to max
        pos_width = (pos_pct / max_pct) * 50 if max_pct > 0 else 0
        neg_width = (neg_pct / max_pct) * 50 if max_pct > 0 else 0

        # Net indicator color
        if net_score > 0.3:
            net_color = POSITIVE_COLOR
        elif net_score < -0.3:
            net_color = NEGATIVE_COLOR
        else:
            net_color = '#b45309'  # Amber

        actors_html += f'''
        <div class="actor-row">
            <div class="actor-name">{html_lib.escape(actor[:25])}</div>
            <div class="sentiment-bars">
                <div class="neg-bar-container">
                    <div class="neg-bar" style="width: {neg_width}%;"></div>
                </div>
                <div class="center-line"></div>
                <div class="pos-bar-container">
                    <div class="pos-bar" style="width: {pos_width}%;"></div>
                </div>
            </div>
            <div class="net-indicator" style="background: {net_color};">{net_score:+.2f}</div>
            <div class="count">n={total}</div>
        </div>
        '''

    # Build constructed categories section
    constructed_html = ''
    for actor_data in constructed_actors:
        actor = actor_data['actor']
        total = actor_data['total']
        net_score = actor_data['net_score']

        if net_score > 0.3:
            net_color = POSITIVE_COLOR
        elif net_score < -0.3:
            net_color = NEGATIVE_COLOR
        else:
            net_color = '#b45309'

        constructed_html += f'''
        <div class="constructed-item">
            <span class="constructed-name">{html_lib.escape(actor)}</span>
            <span class="constructed-score" style="color: {net_color};">{net_score:+.2f}</span>
            <span class="constructed-count">n={total}</span>
        </div>
        '''

    # Get excerpts for key actors (8 actors for 2 rows)
    excerpt_actors = [
        'Québec', 'Martin Koskinen', 'CAQ', 'Québécois',  # Row 1
        'Isabelle', 'Hydro-Québec', 'Canada', 'Brigitte'   # Row 2
    ]
    excerpts_html = ''

    for actor_name in excerpt_actors:
        excerpt_text = get_excerpt_for_actor(df, actor_name)
        if excerpt_text:
            # Determine color based on actor's sentiment
            actor_data = next((a for a in actor_breakdown if a['actor'] == actor_name), None)
            if actor_data:
                net_score = actor_data['net_score']
                if net_score > 0.3:
                    border_color = POSITIVE_COLOR
                elif net_score < -0.3:
                    border_color = NEGATIVE_COLOR
                else:
                    border_color = '#b45309'
            else:
                border_color = QUEBEC_BLUE

            excerpts_html += f'''
            <div class="excerpt-card" style="border-left-color: {border_color};">
                <span class="excerpt-actor">{html_lib.escape(actor_name)}</span>
                <p class="excerpt-text">{quote_open}{html_lib.escape(excerpt_text)}{quote_close}</p>
            </div>
            '''

    # Index color
    if actor_sentiment_idx > 0.3:
        idx_color = POSITIVE_COLOR
    elif actor_sentiment_idx < -0.3:
        idx_color = NEGATIVE_COLOR
    else:
        idx_color = '#b45309'

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
        }}

        /* Header */
        .header {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--ink);
            margin-bottom: 24px;
        }}
        .title-block {{ max-width: 1100px; }}
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

        /* Main content - two rows */
        .main-content {{
            display: flex;
            flex-direction: column;
            gap: 14px;
            flex: 1;
            min-height: 0;
            overflow: hidden;
        }}
        .top-section {{
            display: grid;
            grid-template-columns: 1.3fr 0.5fr;
            gap: 20px;
            flex: 0 0 auto;
        }}

        /* Actor panel */
        .panel {{
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow-soft);
            padding: 12px 20px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }}

        /* Right column */
        .right-column {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        /* Header row */
        .header-row {{
            display: flex;
            align-items: center;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--line);
            margin-bottom: 8px;
        }}
        .header-row .actor-name {{ width: 180px; }}
        .header-row .sentiment-bars {{
            flex: 1;
            display: flex;
            justify-content: space-between;
            padding: 0 30px;
        }}
        .header-neg {{ color: {NEGATIVE_COLOR}; font-weight: 700; font-size: 15px; letter-spacing: 0.12em; text-transform: uppercase; }}
        .header-pos {{ color: {POSITIVE_COLOR}; font-weight: 700; font-size: 15px; letter-spacing: 0.12em; text-transform: uppercase; }}
        .header-net {{ width: 80px; text-align: center; font-weight: 700; font-size: 14px; letter-spacing: 0.12em; text-transform: uppercase; margin-left: 20px; }}

        .actor-row {{
            display: flex;
            align-items: center;
            margin-bottom: 6px;
        }}
        .actor-name {{
            width: 180px;
            font-size: 17px;
            font-weight: 600;
            color: var(--ink);
        }}
        .sentiment-bars {{
            flex: 1;
            display: flex;
            align-items: center;
            height: 20px;
        }}
        .neg-bar-container {{
            flex: 1;
            display: flex;
            justify-content: flex-end;
            height: 100%;
        }}
        .neg-bar {{
            background: {NEGATIVE_COLOR};
            height: 100%;
            border-radius: 4px 0 0 4px;
        }}
        .center-line {{
            width: 3px;
            height: 100%;
            background: var(--ink);
        }}
        .pos-bar-container {{
            flex: 1;
            height: 100%;
        }}
        .pos-bar {{
            background: {POSITIVE_COLOR};
            height: 100%;
            border-radius: 0 4px 4px 0;
        }}
        .net-indicator {{
            width: 80px;
            height: 30px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 15px;
            font-weight: 700;
            margin-left: 20px;
        }}
        .count {{
            width: 60px;
            text-align: right;
            font-size: 14px;
            color: var(--muted);
            margin-left: 12px;
        }}

        /* Constructed categories */
        .constructed-section {{
            background: var(--card);
            border-radius: 12px;
            border: 1px solid var(--line);
            padding: 16px 20px;
            box-shadow: var(--shadow-soft);
        }}
        .constructed-title {{
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--ink);
            margin-bottom: 4px;
        }}
        .constructed-desc {{
            font-size: 12px;
            color: var(--muted);
            margin-bottom: 12px;
        }}
        .constructed-item {{
            display: flex;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid var(--line);
        }}
        .constructed-item:last-child {{
            border-bottom: none;
        }}
        .constructed-name {{
            flex: 1;
            font-size: 15px;
            font-weight: 600;
            color: var(--ink);
        }}
        .constructed-score {{
            font-family: 'STIX Two Text', serif;
            font-size: 18px;
            font-weight: 700;
            margin-right: 12px;
        }}
        .constructed-count {{
            font-size: 13px;
            color: var(--muted);
        }}

        /* Excerpts section - full width at bottom */
        .excerpts-section {{
            display: flex;
            flex-direction: column;
            flex: 1;
            min-height: 0;
        }}
        .excerpts-title {{
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--ink);
            margin-bottom: 8px;
        }}
        .excerpts-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            grid-template-rows: auto auto;
            gap: 10px 14px;
            align-items: start;
        }}
        .excerpt-card {{
            background: var(--card);
            border-radius: 10px;
            border: 1px solid var(--line);
            border-left: 5px solid var(--accent);
            padding: 10px 12px;
            box-shadow: var(--shadow-soft);
            height: fit-content;
        }}
        .excerpt-actor {{
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--muted);
            display: block;
            margin-bottom: 4px;
        }}
        .excerpt-text {{
            font-family: 'STIX Two Text', serif;
            font-size: 14px;
            line-height: 1.4;
            color: var(--ink);
        }}

        /* Index card */
        .index-card {{
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            border-left: 10px solid {idx_color};
            box-shadow: var(--shadow-soft);
            padding: 20px 24px;
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
            font-size: 64px;
            font-weight: 700;
            color: {idx_color};
            line-height: 1;
            margin-top: 12px;
        }}
        .index-label {{
            font-size: 17px;
            font-weight: 600;
            color: var(--muted);
            margin-top: 10px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .index-interp {{
            font-size: 17px;
            color: {idx_color};
            font-weight: 600;
            margin-top: 6px;
        }}
        .index-meta {{
            font-size: 13px;
            color: var(--muted);
            margin-top: 10px;
            line-height: 1.4;
        }}

        /* Footer */
        .methodology {{
            margin-top: auto;
            padding-top: 10px;
        }}
        .methodology-text {{
            font-size: 16px;
            color: var(--muted);
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

        <div class="main-content">
            <div class="top-section">
                <div class="panel actor-panel">
                    <div class="header-row">
                        <div class="actor-name"></div>
                        <div class="sentiment-bars">
                            <span class="header-neg">{header_neg}</span>
                            <span class="header-pos">{header_pos}</span>
                        </div>
                        <div class="header-net">{header_net}</div>
                        <div class="count"></div>
                    </div>
                    {actors_html}
                </div>

                <div class="right-column">
                    <div class="constructed-section">
                        <h3 class="constructed-title">{html_lib.escape(constructed_title)}</h3>
                        <p class="constructed-desc">{html_lib.escape(constructed_desc)}</p>
                        {constructed_html}
                    </div>

                    <div class="index-card">
                        <div class="index-kicker">Indice</div>
                        <div class="index-value">{actor_sentiment_idx:+.2f}</div>
                        <div class="index-label">{html_lib.escape(index_label)}</div>
                        <div class="index-interp">{html_lib.escape(index_interp)}</div>
                        <div class="index-meta">{html_lib.escape(index_meta)}</div>
                    </div>
                </div>
            </div>

            <div class="excerpts-section">
                <h3 class="excerpts-title">{html_lib.escape(excerpts_title)}</h3>
                <div class="excerpts-row">
                    {excerpts_html}
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
    """Generate actors figure."""
    if df is None:
        df = load_data()

    for lang in ['fr', 'en']:
        html_content = generate_html(df, lang)
        save_figure(html_content, OUTPUT_DIR, f'fig5_actors_{lang}', export_png=export_png)


if __name__ == '__main__':
    main()
