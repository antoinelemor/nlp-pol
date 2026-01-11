#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig3_actor_sentiment.py

MAIN OBJECTIVE:
---------------
Analyze and visualize the sentiment valence attributed to different actors
in Macron's speech. Maps positive, neutral, and negative mentions to
compute net sentiment scores per actor.

Dependencies:
-------------
- compute_indices (load_data, prepare_actor_sentiment_data)
- config (get_labels)
- html_utils (COLORS, POSITIVE_COLOR, NEGATIVE_COLOR, save_figure)

MAIN FEATURES:
--------------
1) Extract and aggregate actor mentions with valence annotations
2) Compute net sentiment score per actor: (positive - negative) / total
3) Display top actors ranked by mention frequency
4) Show representative positive/negative excerpts
5) Generate bilingual output (FR/EN)

Author:
-------
Antoine Lemor
"""

from pathlib import Path
import re
from compute_indices import load_data, prepare_actor_sentiment_data
from config import get_labels
from html_utils import COLORS, POSITIVE_COLOR, NEGATIVE_COLOR, save_figure

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output" / "figures"


def generate_html(data, lang='fr'):
    """Generate the actor sentiment HTML."""
    labels = get_labels(lang)
    actors = data['actors']

    if lang == 'fr':
        title = "Paysage de sentiment des acteurs"
        subtitle = "Qui reçoit quel traitement dans le discours de Macron ?"
        neg_label = "NÉGATIF"
        pos_label = "POSITIF"
        net_label = "Score net"
        cat_title = "Synthèse par catégorie"
        cat_labels = ['France & Alliés', 'Grandes puissances', 'Partenaires']
        quotes_title = "Extraits labellisés"
        pos_quote_label = "Positif"
        neg_quote_label = "Négatif"
        quotes_entities_label = "Extraits labellisés — entités"
        quotes_summary_label = "Extraits labellisés — synthèse"
        methodology = "Méthodologie : Chaque mention d'acteur est annotée avec une valence. Score net = (% positif − % négatif). +1 = toujours positif, −1 = toujours négatif."
    else:
        title = "Actor Sentiment Landscape"
        subtitle = "Who gets what treatment in Macron's speech?"
        neg_label = "NEGATIVE"
        pos_label = "POSITIVE"
        net_label = "Net score"
        cat_title = "Summary by category"
        cat_labels = ['France & Allies', 'Major Powers', 'Partners']
        quotes_title = "Labeled excerpts"
        pos_quote_label = "Positive"
        neg_quote_label = "Negative"
        quotes_entities_label = "Labeled excerpts — entities"
        quotes_summary_label = "Labeled excerpts — summary"
        methodology = "Methodology: Each actor mention is annotated with valence. Net score = (% positive − % negative). +1 = always positive, −1 = always negative."

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

    # Generate actor rows
    actor_rows = ""
    for a in actors[:12]:
        neg_width = a['neg_ratio'] * 100
        pos_width = a['pos_ratio'] * 100
        net = a['net_sentiment']

        if net > 0.1:
            net_color = POSITIVE_COLOR
        elif net < -0.1:
            net_color = NEGATIVE_COLOR
        else:
            net_color = '#b45309'

        actor_rows += f'''
        <div class="actor-row">
            <div class="actor-name">{a['actor']}</div>
            <div class="sentiment-bars">
                <div class="neg-bar-container">
                    <div class="neg-bar" style="width: {neg_width}%;"></div>
                </div>
                <div class="center-line"></div>
                <div class="pos-bar-container">
                    <div class="pos-bar" style="width: {pos_width}%;"></div>
                </div>
            </div>
            <div class="net-indicator" style="background: {net_color};">{net:+.2f}</div>
            <div class="count">n={a['total']}</div>
        </div>'''

    # Category summary
    categories = {
        'France & Allies': ['France', 'Europe/UE', 'Ambassadeurs', 'G7'],
        'Major Powers': ['États-Unis', 'Chine', 'Russie'],
        'Partners': ['Ukraine', 'Inde', 'Afrique'],
    }

    cat_sentiments = []
    all_actors = data['all_actors']
    for cat, members in categories.items():
        cat_pos = sum(a['positive'] for a in all_actors if a['actor'] in members)
        cat_neg = sum(a['negative'] for a in all_actors if a['actor'] in members)
        cat_total = sum(a['total'] for a in all_actors if a['actor'] in members)
        if cat_total > 0:
            cat_sentiments.append((cat_pos - cat_neg) / cat_total)
        else:
            cat_sentiments.append(0)

    cat_bars = ""
    for label, val in zip(cat_labels, cat_sentiments):
        color = POSITIVE_COLOR if val > 0 else NEGATIVE_COLOR
        width = min(abs(val) * 100, 100)
        direction = 'right' if val > 0 else 'left'
        cat_bars += f'''
        <div class="cat-row">
            <div class="cat-label">{label}</div>
            <div class="cat-bar-container">
                <div class="cat-center"></div>
                <div class="cat-bar cat-bar-{direction}" style="width: {width}%; background: {color};"></div>
            </div>
            <div class="cat-value" style="color: {color};">{val:+.2f}</div>
        </div>'''

    quotes = data.get('quotes', {})
    positive_quotes = quotes.get('positive', [])
    negative_quotes = quotes.get('negative', [])
    empty_quote = "Aucun extrait disponible." if lang == 'fr' else "No labeled excerpt available."

    def interleave_quotes(pos_items, neg_items, limit=4):
        combined = []
        for i in range(max(len(pos_items), len(neg_items))):
            if i < len(pos_items):
                combined.append({'tone': 'pos', **pos_items[i]})
            if i < len(neg_items):
                combined.append({'tone': 'neg', **neg_items[i]})
            if len(combined) >= limit:
                break
        return combined[:limit]

    def build_quote_cards(items, count=2):
        cards = ""
        for i in range(count):
            if i < len(items):
                item = items[i]
                tone = item.get('tone', 'pos')
                tone_class = f"quote-{tone}"
                tone_label = pos_quote_label if tone == 'pos' else neg_quote_label
                actor_label = item.get('actor', '').strip()
                actor_html = f'<div class="quote-actor">{actor_label}</div>' if actor_label else ''
                cards += f'''
                    <div class="quote-card {tone_class}">
                        <div class="quote-meta">
                            <span class="quote-tag {tone_class}">{tone_label}</span>
                        </div>
                        {actor_html}
                        <div class="quote-text">{format_quote(item.get('text', ''))}</div>
                    </div>'''
            else:
                cards += f'''
                    <div class="quote-card quote-empty">
                        <div class="quote-meta">
                            <span class="quote-tag quote-empty">{quotes_title}</span>
                        </div>
                        <div class="quote-text">{empty_quote}</div>
                    </div>'''
        return cards

    combined_quotes = interleave_quotes(positive_quotes, negative_quotes, limit=4)
    entity_quotes_html = build_quote_cards(combined_quotes[:2], count=2)
    summary_quotes_html = build_quote_cards(combined_quotes[2:4], count=2)

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
        .title-block {{
            max-width: 1100px;
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

        /* Main content */
        .main-content {{
            display: grid;
            grid-template-columns: 1.25fr 1fr;
            gap: 24px;
            flex: 1;
            min-height: 0;
        }}

        .column {{
            display: flex;
            flex-direction: column;
            gap: 18px;
            min-height: 0;
            height: 100%;
        }}

        /* Panels */
        .panel {{
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow-soft);
            padding: 22px 26px;
            flex: 0 0 auto;
        }}

        /* Header row */
        .header-row {{
            display: flex;
            align-items: center;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--line);
            margin-bottom: 12px;
        }}
        .header-row .actor-name {{ width: 150px; }}
        .header-row .sentiment-bars {{
            flex: 1;
            display: flex;
            justify-content: space-between;
            padding: 0 20px;
        }}
        .header-neg {{ color: {NEGATIVE_COLOR}; font-weight: 700; font-size: 14px; letter-spacing: 0.12em; text-transform: uppercase; }}
        .header-pos {{ color: {POSITIVE_COLOR}; font-weight: 700; font-size: 14px; letter-spacing: 0.12em; text-transform: uppercase; }}
        .header-net {{ width: 72px; text-align: center; font-weight: 700; font-size: 14px; letter-spacing: 0.12em; text-transform: uppercase; margin-left: 16px; }}
        .header-row .count {{ width: 60px; margin-left: 10px; }}

        .actor-row {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        .actor-name {{
            width: 150px;
            font-size: 18px;
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
            width: 72px;
            height: 26px;
            border-radius: 13px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 15px;
            font-weight: 700;
            margin-left: 16px;
        }}
        .count {{
            width: 60px;
            text-align: right;
            font-size: 15px;
            color: var(--muted);
            margin-left: 10px;
        }}

        /* Category panel */
        .panel-title {{
            font-size: 22px;
            font-weight: 700;
            color: var(--ink);
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 20px;
        }}
        .cat-row {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }}
        .cat-label {{
            width: 160px;
            font-size: 19px;
            font-weight: 600;
            color: var(--ink);
        }}
        .cat-bar-container {{
            flex: 1;
            height: 35px;
            background: var(--bg-deep);
            border-radius: 8px;
            position: relative;
        }}
        .cat-center {{
            position: absolute;
            left: 50%;
            top: 0;
            width: 2px;
            height: 100%;
            background: var(--ink);
        }}
        .cat-bar {{
            position: absolute;
            top: 0;
            height: 100%;
            border-radius: 6px;
        }}
        .cat-bar-right {{ left: 50%; }}
        .cat-bar-left {{ right: 50%; }}
        .cat-value {{
            width: 80px;
            text-align: right;
            font-family: 'STIX Two Text', serif;
            font-size: 28px;
            font-weight: 700;
        }}

        /* Quote panel */
        .quote-area {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            flex: 1;
            min-height: 0;
        }}
        .quote-stack {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
        }}
        .quote-area.entity-quotes .quote-stack {{
            width: 100%;
        }}
        .quote-area-label {{
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--muted);
            text-align: center;
        }}
        .quote-cards {{
            display: flex;
            flex-direction: column;
            gap: 12px;
            align-items: center;
        }}
        .quote-area.entity-quotes .quote-cards {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 16px;
            width: 100%;
        }}
        .quote-card {{
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 16px 18px;
            box-shadow: var(--shadow-soft);
            display: flex;
            flex-direction: column;
            gap: 10px;
            width: fit-content;
            max-width: 520px;
            position: relative;
        }}
        .quote-area.entity-quotes .quote-card {{
            width: 100%;
            max-width: 100%;
        }}
        .quote-card.quote-pos {{
            border-left: 8px solid {POSITIVE_COLOR};
        }}
        .quote-card.quote-neg {{
            border-left: 8px solid {NEGATIVE_COLOR};
        }}
        .quote-card.quote-empty {{
            border-left: 8px solid var(--line);
        }}
        .quote-meta {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .quote-tag {{
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            padding: 6px 10px;
            border-radius: 999px;
        }}
        .quote-tag.quote-pos {{
            color: {POSITIVE_COLOR};
            background: rgba(22, 163, 74, 0.12);
        }}
        .quote-tag.quote-neg {{
            color: {NEGATIVE_COLOR};
            background: rgba(220, 38, 38, 0.12);
        }}
        .quote-tag.quote-empty {{
            color: var(--muted);
            background: rgba(120, 113, 108, 0.12);
        }}
        .quote-actor {{
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 4px;
        }}
        .quote-card::before {{
            content: '"';
            position: absolute;
            top: 6px;
            right: 12px;
            font-family: 'STIX Two Text', serif;
            font-size: 26px;
            color: var(--line);
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
        </header>

        <div class="main-content">
            <div class="column">
                <div class="panel actor-panel">
                    <div class="header-row">
                        <div class="actor-name"></div>
                        <div class="sentiment-bars">
                            <span class="header-neg">{neg_label}</span>
                            <span class="header-pos">{pos_label}</span>
                        </div>
                        <div class="header-net">{net_label}</div>
                        <div class="count"></div>
                    </div>
                    {actor_rows}
                </div>

                <div class="quote-area entity-quotes">
                    <div class="quote-stack">
                        <div class="quote-area-label">{quotes_entities_label}</div>
                        <div class="quote-cards">
                            {entity_quotes_html}
                        </div>
                    </div>
                </div>
            </div>

            <div class="column">
                <div class="panel category-panel">
                    <div class="panel-title">{cat_title}</div>
                    {cat_bars}
                </div>

                <div class="quote-area summary-quotes">
                    <div class="quote-stack">
                        <div class="quote-area-label">{quotes_summary_label}</div>
                        <div class="quote-cards">
                            {summary_quotes_html}
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
    print("Generating Figure 3: Actor Sentiment Landscape")
    print("=" * 70)

    print("\nLoading data...")
    df = load_data()
    data = prepare_actor_sentiment_data(df)

    for lang in ['fr', 'en']:
        print(f"\n--- {lang.upper()} ---")
        html = generate_html(data, lang)
        save_figure(html, OUTPUT_DIR, f"fig3_actor_sentiment_{lang}")

    print("\nDone!")


if __name__ == "__main__":
    main()
