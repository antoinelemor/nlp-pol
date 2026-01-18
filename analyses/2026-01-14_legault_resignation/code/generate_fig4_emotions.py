#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig4_emotions.py

MAIN OBJECTIVE:
---------------
Generate emotional timeline figure for Legault's resignation speech.
Shows evolution of emotional tone throughout the speech with key moments.

Dependencies:
-------------
- config (colors, labels, weights)
- load_and_validate (data loading)
- html_utils (save_figure)

MAIN FEATURES:
--------------
1) SVG timeline with positive/negative zones
2) Rolling average of emotional tone
3) Peak detection (positive and negative extremes)
4) Curved connectors to quote bubbles
5) Quote bubbles with tone, speech act, and position

Author:
-------
Antoine Lemor
"""

import html as html_lib

from config import (
    get_labels, EMOTIONAL_REGISTER_COLORS, EMOTIONAL_REGISTER_WEIGHTS,
    POSITIVE_COLOR, NEGATIVE_COLOR
)
from load_and_validate import load_data, OUTPUT_DIR
from html_utils import save_figure


# =============================================================================
# DATA PREPARATION
# =============================================================================

def compute_rolling_tone(df, window=5):
    """
    Compute rolling average of emotional tone for each sentence.

    Args:
        df: DataFrame with emotional_register column
        window: Window size for rolling average

    Returns:
        List of tone values (one per sentence)
    """
    tone_values = []
    for _, row in df.iterrows():
        emotion = row.get('emotional_register', 'NEUTRAL')
        weight = EMOTIONAL_REGISTER_WEIGHTS.get(emotion, 0)
        tone_values.append(weight)

    # Apply rolling average
    if len(tone_values) < window:
        return tone_values

    rolling = []
    for i in range(len(tone_values)):
        start = max(0, i - window // 2)
        end = min(len(tone_values), i + window // 2 + 1)
        avg = sum(tone_values[start:end]) / (end - start)
        rolling.append(avg)

    return rolling


def detect_peaks(tone_values, n_peaks=4, min_distance=5, skip_first_n=3):
    """
    Detect local peaks (maxima and minima) in tone values.

    Args:
        tone_values: List of tone values
        n_peaks: Number of peaks to detect per category (positive/negative)
        min_distance: Minimum distance between peaks
        skip_first_n: Skip first N sentences (intro/greeting)

    Returns:
        Tuple of (positive_peaks, negative_peaks) - each a list of (index, value)
    """
    if len(tone_values) < 3:
        return [], []

    # Find all local maxima and minima (skip intro sentences)
    local_max = []
    local_min = []

    for i in range(max(1, skip_first_n), len(tone_values) - 1):
        # Check for local maximum
        if tone_values[i] > tone_values[i-1] and tone_values[i] > tone_values[i+1]:
            if tone_values[i] > 0:  # Only positive peaks
                local_max.append((i, tone_values[i]))
        # Check for local minimum
        if tone_values[i] < tone_values[i-1] and tone_values[i] < tone_values[i+1]:
            if tone_values[i] < 0:  # Only negative peaks
                local_min.append((i, tone_values[i]))

    # ALSO add the global minimum if it's negative (even if not a strict local min)
    # This ensures we capture the lowest negative point
    if len(tone_values) > skip_first_n:
        valid_values = [(i, tone_values[i]) for i in range(skip_first_n, len(tone_values))]
        global_min_idx, global_min_val = min(valid_values, key=lambda x: x[1])
        if global_min_val < 0:
            # Add if not already in local_min
            if not any(abs(idx - global_min_idx) < min_distance for idx, _ in local_min):
                local_min.append((global_min_idx, global_min_val))

    # Sort by absolute value (most extreme first)
    local_max.sort(key=lambda x: -x[1])
    local_min.sort(key=lambda x: x[1])

    # Filter peaks to ensure minimum distance
    def filter_peaks(peaks):
        filtered = []
        for idx, val in peaks:
            if all(abs(idx - f[0]) >= min_distance for f in filtered):
                filtered.append((idx, val))
                if len(filtered) >= n_peaks:
                    break
        return filtered

    pos_peaks = filter_peaks(local_max)
    neg_peaks = filter_peaks(local_min)

    # Sort by position for display
    pos_peaks.sort(key=lambda x: x[0])
    neg_peaks.sort(key=lambda x: x[0])

    return pos_peaks, neg_peaks


def get_peak_excerpts(df, peaks, lang='fr'):
    """
    Get excerpts for each peak position with context (sentence before and after).

    Args:
        df: DataFrame with text and annotations
        peaks: List of (index, value) tuples
        lang: Language for labels

    Returns:
        List of excerpt dictionaries
    """
    labels = get_labels(lang)
    excerpts = []

    for idx, value in peaks:
        if idx < len(df):
            row = df.iloc[idx]
            emotion = row.get('emotional_register', 'NEUTRAL')
            speech_acts = row.get('speech_act', [])
            policy_domains = row.get('policy_domain', ['NONE'])

            # Get speech act label
            if isinstance(speech_acts, list) and speech_acts:
                act = speech_acts[0]
                act_label = labels['speech_act'].get(act, act)
            else:
                act_label = ''

            # Get emotion label
            emotion_label = labels['emotional_register'].get(emotion, emotion)

            # Get policy domain label
            if isinstance(policy_domains, list) and policy_domains:
                domain = policy_domains[0]
                domain_label = labels.get('policy_domain', {}).get(domain, domain)
                if domain == 'NONE':
                    domain_label = ''
            else:
                domain_label = ''

            # Get text with context (sentence before + current + sentence after)
            text_parts = []

            # Add previous sentence for context if available
            if idx > 0:
                prev_text = df.iloc[idx - 1].get('text', '').strip()
                if prev_text and len(prev_text) > 20:
                    text_parts.append(prev_text)

            # Main sentence
            main_text = row.get('text', '').strip()
            text_parts.append(main_text)

            # Add next sentence for context if available
            if idx < len(df) - 1:
                next_text = df.iloc[idx + 1].get('text', '').strip()
                if next_text and len(next_text) > 20:
                    text_parts.append(next_text)

            # Combine with proper spacing
            text = ' '.join(text_parts)

            # Truncate if too long
            if len(text) > 400:
                text = text[:397] + '...'

            excerpts.append({
                'index': idx,
                'value': value,
                'text': text,
                'emotion': emotion,
                'emotion_label': emotion_label,
                'speech_act': act_label,
                'policy_domain': domain_label,
                'sentence_num': idx + 1
            })

    return excerpts


# =============================================================================
# SVG GENERATION
# =============================================================================

def generate_timeline_svg(tone_values, pos_peaks, neg_peaks,
                          width=1880, height=340, padding=40):
    """
    Generate SVG timeline with emotional tone curve.

    Args:
        tone_values: List of rolling tone values
        pos_peaks, neg_peaks: Peak positions
        width, height: SVG dimensions
        padding: Padding around the chart

    Returns:
        SVG string for the timeline
    """
    n = len(tone_values)
    if n == 0:
        return '<svg></svg>'

    # Chart dimensions
    chart_width = width - 2 * padding
    chart_height = height - 2 * padding

    # Normalize values to chart coordinates
    max_val = max(abs(min(tone_values)), abs(max(tone_values)), 1)
    zero_y = padding + chart_height / 2

    def to_x(idx):
        return padding + (idx / max(n-1, 1)) * chart_width

    def to_y(val):
        # Positive values go up (smaller y), negative go down (larger y)
        normalized = val / max_val
        return zero_y - normalized * (chart_height / 2 - 10)

    # Build SVG
    svg_parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']

    # Background zones
    pos_zone_height = chart_height / 2
    neg_zone_height = chart_height / 2

    svg_parts.append(f'''
    <!-- Background zones -->
    <rect x="{padding}" y="{padding}" width="{chart_width}" height="{pos_zone_height}"
          fill="#D1FAE5" opacity="0.5"/>
    <rect x="{padding}" y="{zero_y}" width="{chart_width}" height="{neg_zone_height}"
          fill="#FEE2E2" opacity="0.5"/>
    ''')

    # Zero line
    svg_parts.append(f'''
    <!-- Zero line -->
    <line x1="{padding}" y1="{zero_y}" x2="{width - padding}" y2="{zero_y}"
          stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="5,5"/>
    ''')

    # Build curve points
    points = [(to_x(i), to_y(v)) for i, v in enumerate(tone_values)]

    # Positive fill (area above zero)
    pos_fill_path = f"M {padding} {zero_y}"
    for x, y in points:
        pos_fill_path += f" L {x:.1f} {min(y, zero_y):.1f}"
    pos_fill_path += f" L {width - padding} {zero_y} Z"

    svg_parts.append(f'''
    <!-- Positive fill -->
    <path d="{pos_fill_path}" fill="{POSITIVE_COLOR}" opacity="0.15"/>
    ''')

    # Negative fill (area below zero)
    neg_fill_path = f"M {padding} {zero_y}"
    for x, y in points:
        neg_fill_path += f" L {x:.1f} {max(y, zero_y):.1f}"
    neg_fill_path += f" L {width - padding} {zero_y} Z"

    svg_parts.append(f'''
    <!-- Negative fill -->
    <path d="{neg_fill_path}" fill="{NEGATIVE_COLOR}" opacity="0.15"/>
    ''')

    # Main curve
    curve_path = f"M {points[0][0]:.1f} {points[0][1]:.1f}"
    for x, y in points[1:]:
        curve_path += f" L {x:.1f} {y:.1f}"

    svg_parts.append(f'''
    <!-- Main curve -->
    <path d="{curve_path}" fill="none" stroke="#475569" stroke-width="3" stroke-linecap="round"/>
    ''')

    svg_parts.append('</svg>')

    return '\n'.join(svg_parts), [(to_x(p[0]), to_y(p[1])) for p in pos_peaks], [(to_x(p[0]), to_y(p[1])) for p in neg_peaks]


def generate_markers_svg(pos_peaks, neg_peaks, pos_coords, neg_coords,
                         width=1880, height=340):
    """
    Generate SVG with peak markers.
    """
    svg_parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']

    # Negative peak markers
    svg_parts.append('<!-- Negative peak markers -->')
    for i, ((idx, val), (x, y)) in enumerate(zip(neg_peaks, neg_coords), 1):
        svg_parts.append(f'''
    <circle cx="{x:.1f}" cy="{y:.1f}" r="16" fill="{NEGATIVE_COLOR}" stroke="white" stroke-width="3"/>
    <text x="{x:.1f}" y="{y + 6:.1f}" text-anchor="middle" fill="white" font-size="14" font-weight="bold" font-family="Inter, sans-serif">{i}</text>
        ''')

    # Positive peak markers
    svg_parts.append('<!-- Positive peak markers -->')
    for i, ((idx, val), (x, y)) in enumerate(zip(pos_peaks, pos_coords), 1):
        svg_parts.append(f'''
    <circle cx="{x:.1f}" cy="{y:.1f}" r="16" fill="{POSITIVE_COLOR}" stroke="white" stroke-width="3"/>
    <text x="{x:.1f}" y="{y + 6:.1f}" text-anchor="middle" fill="white" font-size="14" font-weight="bold" font-family="Inter, sans-serif">{i}</text>
        ''')

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def generate_connectors_svg(pos_excerpts, neg_excerpts, pos_coords, neg_coords,
                            bubble_positions, width=1920, height=1080):
    """
    Generate SVG with curved connectors from peaks to bubbles.
    """
    svg_parts = [f'<svg class="connectors-layer" viewBox="0 0 {width} {height}">']

    # Negative connectors (go down to bottom bubbles)
    for i, (excerpt, (px, py), bubble_x) in enumerate(zip(neg_excerpts, neg_coords, bubble_positions['neg'])):
        # Adjust coordinates: timeline is at top=400px
        peak_x = px + 20  # Timeline container offset
        peak_y = py + 400  # Timeline container offset
        bubble_y = 875  # Top of bottom bubbles

        # Curved path
        ctrl_y = (peak_y + bubble_y) / 2
        path = f"M {peak_x:.1f} {peak_y:.1f} C {peak_x:.1f} {ctrl_y:.1f}, {bubble_x:.1f} {ctrl_y + 50:.1f}, {bubble_x:.1f} {bubble_y:.1f}"

        svg_parts.append(f'''
    <defs>
        <linearGradient id="grad_neg_{i}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:{NEGATIVE_COLOR};stop-opacity:0.7"/>
            <stop offset="100%" style="stop-color:{NEGATIVE_COLOR};stop-opacity:0.3"/>
        </linearGradient>
    </defs>
    <path d="{path}" fill="none" stroke="url(#grad_neg_{i})" stroke-width="2.5"
          stroke-linecap="round" stroke-linejoin="round"/>
        ''')

    # Positive connectors (go up to top bubbles)
    for i, (excerpt, (px, py), bubble_x) in enumerate(zip(pos_excerpts, pos_coords, bubble_positions['pos'])):
        peak_x = px + 20
        peak_y = py + 400
        bubble_y = 270  # Bottom of top bubbles

        ctrl_y = (peak_y + bubble_y) / 2
        path = f"M {peak_x:.1f} {peak_y:.1f} C {peak_x:.1f} {ctrl_y:.1f}, {bubble_x:.1f} {ctrl_y - 50:.1f}, {bubble_x:.1f} {bubble_y:.1f}"

        svg_parts.append(f'''
    <defs>
        <linearGradient id="grad_pos_{i}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:{POSITIVE_COLOR};stop-opacity:0.7"/>
            <stop offset="100%" style="stop-color:{POSITIVE_COLOR};stop-opacity:0.3"/>
        </linearGradient>
    </defs>
    <path d="{path}" fill="none" stroke="url(#grad_pos_{i})" stroke-width="2.5"
          stroke-linecap="round" stroke-linejoin="round"/>
        ''')

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


# =============================================================================
# HTML GENERATION
# =============================================================================

def generate_html(df, lang='fr'):
    """Generate emotional timeline HTML."""
    labels = get_labels(lang)

    # Filter out greeting/intro sentences at the start
    # Remove: "Bonjour à tous", "Oui, bonjour tout le monde", introduction by moderator
    df_filtered = df.copy()
    intro_mask = (
        df_filtered['text'].str.lower().str.contains('bonjour', na=False) |
        df_filtered['text'].str.lower().str.contains('laisse.*parole', na=False, regex=True)
    )
    df_filtered = df_filtered[~intro_mask].reset_index(drop=True)

    # Compute rolling tone
    tone_values = compute_rolling_tone(df_filtered, window=5)

    # Detect peaks (skip first 3 sentences which may still be intro material)
    pos_peaks, neg_peaks = detect_peaks(tone_values, n_peaks=4, min_distance=6, skip_first_n=0)

    # Get excerpts for peaks
    pos_excerpts = get_peak_excerpts(df_filtered, pos_peaks, lang)
    neg_excerpts = get_peak_excerpts(df_filtered, neg_peaks, lang)

    # Generate timeline SVG
    timeline_svg, pos_coords, neg_coords = generate_timeline_svg(
        tone_values, pos_peaks, neg_peaks
    )

    # Generate markers SVG
    markers_svg = generate_markers_svg(pos_peaks, neg_peaks, pos_coords, neg_coords)

    # Calculate bubble positions (evenly spaced)
    n_pos = len(pos_excerpts)
    n_neg = len(neg_excerpts)
    bubble_width = 450
    total_width = 1880

    def get_bubble_xs(n):
        if n == 0:
            return []
        if n == 1:
            return [total_width / 2]
        spacing = (total_width - bubble_width) / (n - 1) if n > 1 else 0
        return [20 + bubble_width / 2 + i * spacing for i in range(n)]

    pos_bubble_xs = get_bubble_xs(n_pos)
    neg_bubble_xs = get_bubble_xs(n_neg)

    # Generate connectors
    bubble_positions = {'pos': pos_bubble_xs, 'neg': neg_bubble_xs}
    connectors_svg = generate_connectors_svg(
        pos_excerpts, neg_excerpts, pos_coords, neg_coords, bubble_positions
    )

    # Title and labels
    if lang == 'fr':
        title = "L'évolution du discours : les moments clés"
        pos_zone_label = "ZONE POSITIVE"
        neg_zone_label = "ZONE NÉGATIVE"
        legend = "Les citations sont extraites des pics émotionnels identifiés sur la courbe (moyenne glissante sur 5 phrases)."
        tone_prefix = "Ton"
        act_prefix = "Acte"
        theme_prefix = "Thème"
        sentence_prefix = "Phrase"
        quote_open, quote_close = '«\u202F', '\u202F»'
    else:
        title = "Speech Evolution: Key Moments"
        pos_zone_label = "POSITIVE ZONE"
        neg_zone_label = "NEGATIVE ZONE"
        legend = "Quotes are extracted from emotional peaks identified on the curve (rolling average over 5 sentences)."
        tone_prefix = "Tone"
        act_prefix = "Act"
        theme_prefix = "Theme"
        sentence_prefix = "Sentence"
        quote_open, quote_close = '"', '"'

    # Build positive bubbles
    pos_bubbles_html = ''
    for i, (excerpt, x) in enumerate(zip(pos_excerpts, pos_bubble_xs)):
        left = x - bubble_width / 2
        theme_html = f'<span class="theme-badge">{theme_prefix}: {excerpt["policy_domain"]}</span>' if excerpt.get('policy_domain') else ''
        pos_bubbles_html += f'''
        <div class="bubble positive" style="left: {left:.0f}px; top: 80px;">
            <div class="bubble-header">
                <span class="badge" style="background: {POSITIVE_COLOR};">{i+1}</span>
                <span class="tone-label" style="color: {POSITIVE_COLOR};">{tone_prefix}: {excerpt['emotion_label']}</span>
                <span class="act-badge">{act_prefix}: {excerpt['speech_act']}</span>
                {theme_html}
                <span class="position">{sentence_prefix} {excerpt['sentence_num']}</span>
            </div>
            <div class="bubble-text">{quote_open}{html_lib.escape(excerpt['text'])}{quote_close}</div>
        </div>
        '''

    # Build negative bubbles
    neg_bubbles_html = ''
    for i, (excerpt, x) in enumerate(zip(neg_excerpts, neg_bubble_xs)):
        left = x - bubble_width / 2
        theme_html = f'<span class="theme-badge">{theme_prefix}: {excerpt["policy_domain"]}</span>' if excerpt.get('policy_domain') else ''
        neg_bubbles_html += f'''
        <div class="bubble negative" style="left: {left:.0f}px; top: 800px;">
            <div class="bubble-header">
                <span class="badge" style="background: {NEGATIVE_COLOR};">{i+1}</span>
                <span class="tone-label" style="color: {NEGATIVE_COLOR};">{tone_prefix}: {excerpt['emotion_label']}</span>
                <span class="act-badge">{act_prefix}: {excerpt['speech_act']}</span>
                {theme_html}
                <span class="position">{sentence_prefix} {excerpt['sentence_num']}</span>
            </div>
            <div class="bubble-text">{quote_open}{html_lib.escape(excerpt['text'])}{quote_close}</div>
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <title>{html_lib.escape(title)}</title>
    <link href="https://fonts.googleapis.com/css2?family=STIX+Two+Text:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            width: 1920px;
            height: 1080px;
            background: linear-gradient(135deg, #fbf8f2 0%, #f1ede6 100%);
            font-family: 'IBM Plex Sans', sans-serif;
            position: relative;
            overflow: hidden;
        }}

        .bottom-section {{
            position: absolute;
            bottom: 12px;
            left: 0;
            right: 0;
            text-align: center;
            z-index: 100;
        }}

        .main-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 44px;
            font-weight: 600;
            color: #1f1b16;
            letter-spacing: 0.5px;
            margin: 0 0 8px 0;
            text-shadow: 0 1px 2px rgba(0,0,0,0.08);
        }}

        .bottom-section .legend {{
            position: static;
            margin: 0;
        }}

        .infographic-container {{
            position: absolute;
            top: 0;
            left: 0;
            width: 1920px;
            height: 1080px;
        }}

        .timeline-container {{
            position: absolute;
            top: 400px;
            left: 20px;
            width: 1880px;
            height: 340px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            padding: 0;
            overflow: visible;
            z-index: 10;
        }}

        .timeline-container svg {{
            width: 100%;
            height: 100%;
        }}

        .connectors-layer {{
            position: absolute;
            top: 0;
            left: 0;
            width: 1920px;
            height: 1080px;
            pointer-events: none;
            z-index: 12;
        }}

        .markers-layer {{
            position: absolute;
            top: 0;
            left: 0;
            width: 1920px;
            height: 1080px;
            pointer-events: none;
            z-index: 20;
        }}

        .bubble {{
            z-index: 30;
            position: absolute;
            width: 450px;
            max-height: 260px;
            overflow: hidden;
            padding: 14px 16px;
            border-radius: 10px;
            border-left: 4px solid;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
        }}

        .bubble.positive {{
            background: #D1FAE5;
            border-color: {POSITIVE_COLOR};
        }}

        .bubble.negative {{
            background: #FEE2E2;
            border-color: {NEGATIVE_COLOR};
        }}

        .bubble-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }}

        .badge {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
            color: white;
            font-family: 'IBM Plex Sans', sans-serif;
            font-weight: 700;
            font-size: 13px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}

        .tone-label {{
            font-family: 'IBM Plex Sans', sans-serif;
            font-weight: 700;
            font-size: 15px;
            letter-spacing: 0.3px;
        }}

        .act-badge {{
            font-family: 'IBM Plex Sans', sans-serif;
            font-weight: 500;
            font-size: 12px;
            color: #475569;
            padding: 3px 10px;
            background: rgba(0,0,0,0.06);
            border-radius: 12px;
        }}

        .theme-badge {{
            font-family: 'IBM Plex Sans', sans-serif;
            font-weight: 600;
            font-size: 11px;
            color: #003DA5;
            padding: 3px 10px;
            background: rgba(0, 61, 165, 0.12);
            border-radius: 12px;
        }}

        .position {{
            margin-left: auto;
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 12px;
            color: #64748b;
            flex-shrink: 0;
        }}

        .bubble-text {{
            font-family: 'STIX Two Text', serif;
            font-size: 15px;
            line-height: 1.45;
            color: #1e293b;
            text-align: justify;
            hyphens: auto;
            display: -webkit-box;
            -webkit-line-clamp: 6;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        .zone-label {{
            position: absolute;
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 1px;
            opacity: 0.7;
        }}

        .zone-label.positive {{
            color: {POSITIVE_COLOR};
            top: 425px;
            right: 50px;
        }}

        .zone-label.negative {{
            color: {NEGATIVE_COLOR};
            top: 695px;
            right: 50px;
        }}

        .legend {{
            position: absolute;
            bottom: 15px;
            left: 0;
            right: 0;
            text-align: center;
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 12px;
            color: #64748b;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="infographic-container">
        <!-- Connectors SVG layer -->
        {connectors_svg}

        <!-- Timeline graph -->
        <div class="timeline-container">
            {timeline_svg}
        </div>

        <!-- Peak markers layer (on top of connectors) -->
        <svg class="markers-layer" viewBox="0 0 1880 340" style="position: absolute; top: 400px; left: 20px; width: 1880px; height: 340px;">
            {markers_svg.replace('<svg viewBox="0 0 1880 340" xmlns="http://www.w3.org/2000/svg">', '').replace('</svg>', '')}
        </svg>

        <!-- Zone labels -->
        <div class="zone-label positive">{pos_zone_label}</div>
        <div class="zone-label negative">{neg_zone_label}</div>

        <!-- Positive bubbles (top) -->
        {pos_bubbles_html}

        <!-- Negative bubbles (bottom) -->
        {neg_bubbles_html}

        <!-- Bottom section: title + legend -->
        <div class="bottom-section">
            <h1 class="main-title">{html_lib.escape(title)}</h1>
            <p class="legend">{html_lib.escape(legend)}</p>
        </div>
    </div>
</body>
</html>'''

    return html


# =============================================================================
# MAIN
# =============================================================================

def main(df=None, export_png=True):
    """Generate emotions timeline figure."""
    if df is None:
        df = load_data()

    for lang in ['fr', 'en']:
        html_content = generate_html(df, lang)
        save_figure(html_content, OUTPUT_DIR, f'fig4_emotions_{lang}', export_png=export_png)


if __name__ == '__main__':
    main()
