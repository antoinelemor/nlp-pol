#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig2_justifications.py

MAIN OBJECTIVE:
---------------
Generate figure analyzing how Legault justifies his decision and his record.
Shows justification categories with counts, percentages, and quotes under bars.

Dependencies:
-------------
- config (colors, labels)
- load_and_validate (data loading)
- compute_indices (aggregation, excerpts)
- html_utils (HTML generation, export)

MAIN FEATURES:
--------------
1) Justification categories with N (%) and bars
2) Quotes under each justification type
3) Focus index card showing record vs resignation balance
4) Justification targets breakdown

Author:
-------
Antoine Lemor
"""

import html as html_lib
from pathlib import Path

from config import (
    get_labels, JUSTIFICATION_COLORS, JUSTIFICATION_TARGET_COLORS,
    POSITIVE_COLOR, NEGATIVE_COLOR, QUEBEC_BLUE
)
from load_and_validate import load_data, OUTPUT_DIR, extract_justifications
from compute_indices import (
    aggregate_justification_categories,
    aggregate_justification_targets,
    compute_justification_balance_index,
    get_excerpts_for_category
)
from html_utils import save_figure


# =============================================================================
# EXCERPT EXTRACTION
# =============================================================================

# Keywords to find better representative excerpts for each category
# Keys must match actual annotation values (CIRCUMSTANCE_CLAIM, VALUES_APPEAL, COLLECTIVE_ACHIEVEMENT)
CATEGORY_KEYWORDS = {
    'RECORD_DEFENSE': ['réalisé', 'accompli', 'fait', 'réussi', 'bilan', 'fierté', 'fier'],
    'CIRCUMSTANCE_CLAIM': ['pandémie', 'crise', 'solidarité', 'période', 'monde', 'brouillard', 'coût de la vie'],
    'EFFORT_CLAIM': ['travaillé', 'effort', 'essayé', 'tenté', 'investi', 'j\'ai'],
    'VALUES_APPEAL': ['valeur', 'important', 'essentiel', 'fondamental', 'croire', 'conviction', 'avenir', 'génération'],
    'COLLECTIVE_ACHIEVEMENT': ['équipe', 'ensemble', 'collectif', 'nous avons', 'remercier', 'embarqués', 'aventure'],
    'DECISION_RATIONALE': ['décision', 'choisi', 'pourquoi', 'raison', 'changement', 'défis', 'élection'],
}

TARGET_KEYWORDS = {
    'OVERALL_RECORD': ['bilan', 'mandat', 'gouvernement', 'réalisations'],
    'IDENTITY_POLICY': ['français', 'langue', 'identité', 'culture', 'nation'],
    'PARTY_CREATION': ['CAQ', 'parti', 'fondé', 'créé'],
    'PERSONAL_CONDUCT': ['moi', 'j\'ai', 'personnellement'],
    'ECONOMIC_POLICY': ['économie', 'emploi', 'richesse', 'investissement'],
}


def get_justification_excerpts(df, category: str, limit: int = 1):
    """Get excerpts for a specific justification category with keyword prioritization."""
    just_df = extract_justifications(df)
    if just_df.empty:
        return []

    filtered = just_df[just_df['justification_category'] == category]
    if filtered.empty:
        return []

    texts = filtered['text'].tolist()
    keywords = CATEGORY_KEYWORDS.get(category, [])

    # First try to find text with relevant keywords
    for text in texts:
        if text and len(text) > 80:
            text_lower = text.lower()
            if any(kw in text_lower for kw in keywords):
                return [text]  # Return full text without truncation

    # Fallback: return first long enough text
    for text in texts:
        if text and len(text) > 80:
            return [text]  # Return full text without truncation
    return []


def get_target_excerpts(df, target: str, limit: int = 1):
    """Get excerpts for a specific justification target with keyword prioritization."""
    just_df = extract_justifications(df)
    if just_df.empty:
        return []

    filtered = just_df[just_df['justification_target'] == target]
    if filtered.empty:
        return []

    texts = filtered['text'].tolist()
    keywords = TARGET_KEYWORDS.get(target, [])

    # First try to find text with relevant keywords
    for text in texts:
        if text and len(text) > 60:
            text_lower = text.lower()
            if any(kw in text_lower for kw in keywords):
                return [text]  # Return full text without truncation

    # Fallback
    for text in texts:
        if text and len(text) > 60:
            return [text]  # Return full text without truncation
    return []


# =============================================================================
# FIGURE GENERATION
# =============================================================================

def generate_html(df, lang='fr'):
    """Generate justifications figure HTML for specified language."""
    labels = get_labels(lang)

    # Get aggregated data
    categories = aggregate_justification_categories(df)
    targets = aggregate_justification_targets(df)
    balance_idx, balance_meta = compute_justification_balance_index(df)

    # Calculate totals
    total_justifications = categories['count'].sum() if not categories.empty else 0
    total_targets = targets['count'].sum() if not targets.empty else 0

    # Title and subtitle
    resignation_count = balance_meta['resignation']
    record_count = balance_meta['record']

    if lang == 'fr':
        title = "Stratégies de justification"
        subtitle = "Comment Legault justifie sa décision et son bilan"
        section1_title = "Types de justification"
        section1_desc = "Stratégies argumentatives utilisées"
        section2_title = "Objets justifiés"
        section2_desc = "Ce qui est défendu ou expliqué"
        balance_question = "Parle-t-il surtout des raisons de sa démission ou de son bilan ?"
        balance_left = "Démission"
        balance_right = "Bilan"
        methodology = (
            f"Méthodologie : Classification de {total_justifications} segments de justification. "
            f"Focus = (bilan − démission) / total."
        )
        quote_open, quote_close = '«\u202F', '\u202F»'
    else:
        title = "Justification Strategies"
        subtitle = "How Legault justifies his decision and record"
        section1_title = "Justification types"
        section1_desc = "Argumentative strategies used"
        section2_title = "Targets justified"
        section2_desc = "What is being defended or explained"
        balance_question = "Does he focus on resignation reasons or his record?"
        balance_left = "Resignation"
        balance_right = "Record"
        methodology = (
            f"Methodology: Classification of {total_justifications} justification segments. "
            f"Focus = (record − resignation) / total."
        )
        quote_open, quote_close = '"', '"'

    cat_labels = labels['justification_category']
    target_labels = labels['justification_target']

    # Build categories HTML with quotes under bars
    categories_html = ''
    max_cat_count = categories['count'].max() if not categories.empty else 1

    for _, row in categories.head(6).iterrows():
        cat = row['justification_category']
        count = row['count']
        pct = round(count / total_justifications * 100, 1) if total_justifications > 0 else 0
        bar_width = (count / max_cat_count) * 100
        color = JUSTIFICATION_COLORS.get(cat, '#6B7280')
        label = cat_labels.get(cat, cat)

        # Get excerpt
        excerpts = get_justification_excerpts(df, cat, limit=1)
        quote_text = excerpts[0] if excerpts else ''

        quote_html = ''
        if quote_text:
            quote_html = f'''
            <blockquote class="item-quote" style="border-left-color: {color};">
                <span class="quote-text">{quote_open}{html_lib.escape(quote_text)}{quote_close}</span>
            </blockquote>
            '''

        categories_html += f'''
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

    # Build targets HTML with quotes
    targets_html = ''
    max_target_count = targets['count'].max() if not targets.empty else 1

    for _, row in targets.head(5).iterrows():
        target = row['justification_target']
        count = row['count']
        pct = round(count / total_targets * 100, 1) if total_targets > 0 else 0
        bar_width = (count / max_target_count) * 100
        color = JUSTIFICATION_TARGET_COLORS.get(target, '#6B7280')
        label = target_labels.get(target, target)

        # Get excerpt for target
        target_excerpts = get_target_excerpts(df, target, limit=1)
        quote_text = target_excerpts[0] if target_excerpts else ''

        quote_html = ''
        if quote_text:
            quote_html = f'''
            <blockquote class="item-quote-small" style="border-left-color: {color};">
                <span class="quote-text">{quote_open}{html_lib.escape(quote_text)}{quote_close}</span>
            </blockquote>
            '''

        targets_html += f'''
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

    # Balance visualization - tilt angle based on index (-15 to +15 degrees)
    tilt_angle = balance_idx * 15  # Negative = tilts left (resignation), Positive = tilts right (record)
    left_color = NEGATIVE_COLOR
    right_color = POSITIVE_COLOR

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

        /* Main content - two columns */
        .main-content {{
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 1.4fr;
            gap: 30px;
            min-height: 0;
            overflow: hidden;
        }}

        /* Left column - targets + balance */
        .left-column {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .targets-section {{
            flex: 1;
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
            margin-bottom: 8px;
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
            font-size: 18px;
            color: var(--ink);
            flex: 1;
        }}
        .item-stat {{
            font-family: 'STIX Two Text', serif;
            font-size: 20px;
            font-weight: 600;
            color: var(--ink);
        }}
        .item-pct {{
            font-size: 14px;
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
            font-size: 15px;
            color: var(--ink);
            line-height: 1.45;
            padding: 6px 12px 6px 14px;
            border-left: 4px solid var(--line);
            border-radius: 6px;
            background: var(--card);
            margin-top: 4px;
            margin-bottom: 8px;
        }}
        .item-quote .quote-text {{
            /* Show full quotes without truncation */
        }}
        .item-quote-small {{
            font-family: 'STIX Two Text', serif;
            font-size: 14px;
            color: var(--ink);
            line-height: 1.4;
            padding: 5px 10px 5px 12px;
            border-left: 3px solid var(--line);
            border-radius: 4px;
            background: var(--card);
            margin-top: 4px;
            margin-bottom: 6px;
        }}
        .item-quote-small .quote-text {{
            /* Show full quotes without truncation */
        }}

        /* Right column - categories + balance */
        .right-column {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .categories-section {{
            flex: 1;
        }}

        /* Balance visualization */
        .balance-card {{
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow-soft);
            padding: 24px 28px;
        }}
        .balance-question {{
            font-family: 'STIX Two Text', serif;
            font-size: 18px;
            font-weight: 600;
            color: var(--ink);
            text-align: center;
            margin-bottom: 20px;
        }}
        .balance-scale {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }}
        .balance-beam-container {{
            position: relative;
            width: 100%;
            height: 80px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .balance-beam {{
            position: relative;
            width: 280px;
            height: 8px;
            background: var(--ink);
            border-radius: 4px;
            transform: rotate({tilt_angle}deg);
            transform-origin: center;
            transition: transform 0.3s ease;
        }}
        .balance-pivot {{
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 16px solid transparent;
            border-right: 16px solid transparent;
            border-bottom: 24px solid var(--ink);
        }}
        .balance-plate {{
            position: absolute;
            top: -8px;
            width: 70px;
            height: 40px;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .balance-plate-left {{
            left: -20px;
            background: {left_color};
        }}
        .balance-plate-right {{
            right: -20px;
            background: {right_color};
        }}
        .plate-count {{
            font-family: 'STIX Two Text', serif;
            font-size: 22px;
            line-height: 1;
        }}
        .balance-labels {{
            display: flex;
            justify-content: space-between;
            width: 320px;
            margin-top: 16px;
        }}
        .balance-label {{
            font-size: 14px;
            font-weight: 600;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .balance-label-left {{
            color: {left_color};
        }}
        .balance-label-right {{
            color: {right_color};
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
                <div class="stat-number">{total_justifications}</div>
                <div class="stat-label">{"justifications" if lang == 'fr' else "justifications"}</div>
            </div>
        </header>

        <div class="main-content">
            <!-- Left: Balance + Targets (objets justifiés) -->
            <div class="left-column">
                <div class="balance-card">
                    <div class="balance-question">{html_lib.escape(balance_question)}</div>
                    <div class="balance-scale">
                        <div class="balance-beam-container">
                            <div class="balance-beam">
                                <div class="balance-plate balance-plate-left">
                                    <span class="plate-count">{resignation_count}</span>
                                </div>
                                <div class="balance-plate balance-plate-right">
                                    <span class="plate-count">{record_count}</span>
                                </div>
                            </div>
                            <div class="balance-pivot"></div>
                        </div>
                        <div class="balance-labels">
                            <span class="balance-label balance-label-left">{html_lib.escape(balance_left)}</span>
                            <span class="balance-label balance-label-right">{html_lib.escape(balance_right)}</span>
                        </div>
                    </div>
                </div>

                <div class="section targets-section">
                    <div class="section-header">
                        <h2 class="section-title">{html_lib.escape(section2_title)}</h2>
                        <p class="section-desc">{html_lib.escape(section2_desc)}</p>
                    </div>
                    {targets_html}
                </div>
            </div>

            <!-- Right: Justification types -->
            <div class="section">
                <div class="section-header">
                    <h2 class="section-title">{html_lib.escape(section1_title)}</h2>
                    <p class="section-desc">{html_lib.escape(section1_desc)}</p>
                </div>
                {categories_html}
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
    """Generate justifications figure."""
    if df is None:
        df = load_data()

    for lang in ['fr', 'en']:
        html_content = generate_html(df, lang)
        save_figure(html_content, OUTPUT_DIR, f'fig2_justifications_{lang}', export_png=export_png)


if __name__ == '__main__':
    main()
