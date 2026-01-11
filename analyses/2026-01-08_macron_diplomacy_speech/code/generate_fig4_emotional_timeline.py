#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig4_emotional_timeline.py

MAIN OBJECTIVE:
---------------
Generate an emotional timeline visualization tracking the evolution of
Macron's tone throughout the speech. Uses smoothed tone values and
peak detection to identify key emotional moments.

Dependencies:
-------------
- pandas, numpy, scipy (signal processing, interpolation)
- load_and_validate (load_annotated_data, parse_labels_column)
- config (EMOTIONAL_REGISTER_WEIGHTS, get_labels)
- playwright (optional, for PNG export)

MAIN FEATURES:
--------------
1) Compute rolling average of emotional register weights
2) Detect positive and negative peaks using scipy.signal.find_peaks
3) Extract representative excerpts at peak locations
4) Render interactive SVG timeline with annotation labels
5) Generate bilingual output (FR/EN)

Author:
-------
Antoine Lemor
"""

import json
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from scipy.interpolate import make_interp_spline
from pathlib import Path
from textwrap import wrap

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

from load_and_validate import load_annotated_data, parse_labels_column
from config import EMOTIONAL_REGISTER_WEIGHTS, get_labels

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# COLORS
# =============================================================================

NEGATIVE_COLOR = '#DC2626'
NEGATIVE_LIGHT = '#FEE2E2'
POSITIVE_COLOR = '#059669'
POSITIVE_LIGHT = '#D1FAE5'

# =============================================================================
# DATA
# =============================================================================

def load_data():
    csv_files = list(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError("No CSV files found")
    df = load_annotated_data(csv_files[0])
    df = parse_labels_column(df)
    return df


def prepare_data(df):
    """Prepare timeline data and extract peaks with excerpts."""
    df = df.copy().reset_index(drop=True)
    df['tone_weight'] = df['emotional_register'].map(EMOTIONAL_REGISTER_WEIGHTS).fillna(0)
    df['tone_smooth'] = df['tone_weight'].rolling(window=10, center=True, min_periods=3).mean()

    smooth_vals = df['tone_smooth'].fillna(0).values
    n_points = len(df)

    # Smooth curve for SVG
    x = np.arange(n_points)
    y = smooth_vals
    valid = ~np.isnan(df['tone_smooth'].values)
    x_valid = x[valid]
    y_valid = y[valid]

    # Interpolate for smoother curve
    x_smooth = np.linspace(x_valid.min(), x_valid.max(), 400)
    spl = make_interp_spline(x_valid, y_valid, k=3)
    y_smooth = spl(x_smooth)

    # Find peaks
    neg_peaks, _ = find_peaks(-smooth_vals, prominence=0.25, distance=15)
    pos_peaks, _ = find_peaks(smooth_vals, prominence=0.25, distance=15)

    neg_peaks_sorted = sorted(neg_peaks, key=lambda x: smooth_vals[x])[:4]
    pos_peaks_sorted = sorted(pos_peaks, key=lambda x: -smooth_vals[x])[:4]

    # Registers that don't match zones (should be replaced if in wrong zone)
    positive_registers = {'CONFIDENT', 'GRATEFUL', 'SOLEMN'}
    negative_registers = {'ALARMIST', 'COMBATIVE', 'INDIGNANT', 'DEFIANT', 'EXASPERATED'}
    neutral_registers = {'NEUTRAL', 'PRAGMATIC'}

    def extract_excerpt(idx, is_positive=True):
        """Extract excerpt, only searching nearby if current sentence is mismatched."""
        n = len(df)
        tone = df.iloc[idx]['emotional_register']
        if pd.isna(tone):
            tone = "NEUTRAL"

        # Check if tone matches the zone
        target_registers = positive_registers if is_positive else negative_registers
        use_idx = idx

        # Only search nearby if current is neutral/mismatched
        if tone in neutral_registers or (is_positive and tone in negative_registers) or (not is_positive and tone in positive_registers):
            # Search in small window for better match
            for offset in [1, -1, 2, -2, 3, -3]:
                check_idx = idx + offset
                if 0 <= check_idx < n:
                    check_tone = df.iloc[check_idx]['emotional_register']
                    if check_tone in target_registers:
                        use_idx = check_idx
                        tone = check_tone
                        break

        before = str(df.iloc[use_idx-1]['text']).strip() if use_idx > 0 else ""
        main = str(df.iloc[use_idx]['text']).strip()
        after = str(df.iloc[use_idx+1]['text']).strip() if use_idx < n-1 else ""

        if len(before) < 10:
            before = ""

        # Get additional annotations - handle list or JSON string
        speech_act = df.iloc[use_idx].get('speech_act', None)
        if pd.isna(speech_act):
            speech_act = None
        elif isinstance(speech_act, str):
            # Try to parse as JSON if it looks like a list
            if speech_act.startswith('['):
                try:
                    speech_act = json.loads(speech_act.replace("'", '"'))
                except:
                    pass
        # Keep as list for display
        if isinstance(speech_act, list):
            speech_act = speech_act  # Keep all values
        elif speech_act:
            speech_act = [speech_act]  # Wrap single value in list
        else:
            speech_act = []

        france_pos = df.iloc[use_idx].get('france_positioning', None)
        if pd.isna(france_pos):
            france_pos = None
        elif isinstance(france_pos, list) and france_pos:
            france_pos = france_pos[0]

        return {
            'idx': idx,  # Keep original peak idx for connector position
            'pos': use_idx + 1,
            'tone': tone,
            'speech_act': speech_act,
            'france_positioning': france_pos,
            'value': smooth_vals[idx],
            'before': before if before != 'nan' else "",
            'main': main if main != 'nan' else "",
            'after': after if after != 'nan' else "",
        }

    negative_excerpts = [extract_excerpt(idx, is_positive=False) for idx in neg_peaks_sorted]
    positive_excerpts = [extract_excerpt(idx, is_positive=True) for idx in pos_peaks_sorted]

    # Calculate actual data range for better scaling
    y_data_min = np.min(y_smooth)
    y_data_max = np.max(y_smooth)
    y_padding = (y_data_max - y_data_min) * 0.15

    return {
        'n_points': n_points,
        'x_smooth': x_smooth,
        'y_smooth': y_smooth,
        'y_min': y_data_min - y_padding,
        'y_max': y_data_max + y_padding,
        'negative_excerpts': negative_excerpts,
        'positive_excerpts': positive_excerpts,
    }


# =============================================================================
# SVG GENERATION
# =============================================================================

def generate_svg_timeline(data, width=1400, height=350):
    """Generate SVG for the timeline graph."""
    x_smooth = data['x_smooth']
    y_smooth = data['y_smooth']
    n_points = data['n_points']
    y_min, y_max = data['y_min'], data['y_max']

    # Margins
    margin_left = 40
    margin_right = 40
    plot_width = width - margin_left - margin_right
    plot_height = height - 40

    def to_svg_x(x_val):
        return margin_left + (x_val / n_points) * plot_width

    def to_svg_y(y_val):
        # Invert Y axis for SVG
        normalized = (y_val - y_min) / (y_max - y_min)
        return height - 20 - normalized * plot_height

    # Build path for the curve
    path_points = []
    for i, (x, y) in enumerate(zip(x_smooth, y_smooth)):
        sx, sy = to_svg_x(x), to_svg_y(y)
        if i == 0:
            path_points.append(f"M {sx:.1f} {sy:.1f}")
        else:
            path_points.append(f"L {sx:.1f} {sy:.1f}")

    curve_path = ' '.join(path_points)

    # Fill paths (positive and negative areas)
    zero_y = to_svg_y(0)

    # Create fill area for positive
    pos_fill_points = [f"M {to_svg_x(x_smooth[0]):.1f} {zero_y:.1f}"]
    for x, y in zip(x_smooth, y_smooth):
        y_clamped = max(y, 0)
        pos_fill_points.append(f"L {to_svg_x(x):.1f} {to_svg_y(y_clamped):.1f}")
    pos_fill_points.append(f"L {to_svg_x(x_smooth[-1]):.1f} {zero_y:.1f} Z")
    pos_fill_path = ' '.join(pos_fill_points)

    # Create fill area for negative
    neg_fill_points = [f"M {to_svg_x(x_smooth[0]):.1f} {zero_y:.1f}"]
    for x, y in zip(x_smooth, y_smooth):
        y_clamped = min(y, 0)
        neg_fill_points.append(f"L {to_svg_x(x):.1f} {to_svg_y(y_clamped):.1f}")
    neg_fill_points.append(f"L {to_svg_x(x_smooth[-1]):.1f} {zero_y:.1f} Z")
    neg_fill_path = ' '.join(neg_fill_points)

    # Peak markers
    neg_markers = []
    for i, exc in enumerate(data['negative_excerpts']):
        cx = to_svg_x(exc['idx'])
        cy = to_svg_y(exc['value'])
        neg_markers.append({
            'cx': cx, 'cy': cy, 'num': i + 1,
            'idx': exc['idx'], 'value': exc['value']
        })

    pos_markers = []
    for i, exc in enumerate(data['positive_excerpts']):
        cx = to_svg_x(exc['idx'])
        cy = to_svg_y(exc['value'])
        pos_markers.append({
            'cx': cx, 'cy': cy, 'num': i + 1,
            'idx': exc['idx'], 'value': exc['value']
        })

    svg = f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
    <!-- Background zones -->
    <rect x="{margin_left}" y="20" width="{plot_width}" height="{to_svg_y(0) - 20}"
          fill="{POSITIVE_LIGHT}" opacity="0.5"/>
    <rect x="{margin_left}" y="{to_svg_y(0)}" width="{plot_width}" height="{height - 20 - to_svg_y(0)}"
          fill="{NEGATIVE_LIGHT}" opacity="0.5"/>

    <!-- Zero line -->
    <line x1="{margin_left}" y1="{zero_y}" x2="{width - margin_right}" y2="{zero_y}"
          stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="5,5"/>

    <!-- Positive fill -->
    <path d="{pos_fill_path}" fill="{POSITIVE_COLOR}" opacity="0.15"/>

    <!-- Negative fill -->
    <path d="{neg_fill_path}" fill="{NEGATIVE_COLOR}" opacity="0.15"/>

    <!-- Main curve -->
    <path d="{curve_path}" fill="none" stroke="#475569" stroke-width="3" stroke-linecap="round"/>
</svg>'''

    # Markers SVG (separate layer)
    markers_svg = f'''
    <!-- Negative peak markers -->
    {"".join([f'''
    <circle cx="{m['cx']}" cy="{m['cy']}" r="16" fill="{NEGATIVE_COLOR}" stroke="white" stroke-width="3"/>
    <text x="{m['cx']}" y="{m['cy'] + 6}" text-anchor="middle" fill="white" font-size="14" font-weight="bold" font-family="Inter, sans-serif">{m['num']}</text>
    ''' for m in neg_markers])}

    <!-- Positive peak markers -->
    {"".join([f'''
    <circle cx="{m['cx']}" cy="{m['cy']}" r="16" fill="{POSITIVE_COLOR}" stroke="white" stroke-width="3"/>
    <text x="{m['cx']}" y="{m['cy'] + 6}" text-anchor="middle" fill="white" font-size="14" font-weight="bold" font-family="Inter, sans-serif">{m['num']}</text>
    ''' for m in pos_markers])}
    '''

    return svg, neg_markers, pos_markers, markers_svg


def generate_connector_svg(start_x, start_y, end_x, end_y, color, connector_id, is_above=True):
    """Generate SVG path for connector - smooth curve from peak to bubble."""
    gradient_id = f"grad_{connector_id}"

    # Smooth bezier curve with control points for elegant connection
    if is_above:
        # Going UP: curve from peak to bubble
        ctrl1_x = start_x
        ctrl1_y = start_y - abs(start_y - end_y) * 0.5
        ctrl2_x = end_x
        ctrl2_y = end_y + abs(start_y - end_y) * 0.3
        path = f"M {start_x} {start_y} C {ctrl1_x} {ctrl1_y}, {ctrl2_x} {ctrl2_y}, {end_x} {end_y}"
    else:
        # Going DOWN: curve from peak to bubble
        ctrl1_x = start_x
        ctrl1_y = start_y + abs(end_y - start_y) * 0.5
        ctrl2_x = end_x
        ctrl2_y = end_y - abs(end_y - start_y) * 0.3
        path = f"M {start_x} {start_y} C {ctrl1_x} {ctrl1_y}, {ctrl2_x} {ctrl2_y}, {end_x} {end_y}"

    return f'''
    <defs>
        <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:{color};stop-opacity:0.7"/>
            <stop offset="100%" style="stop-color:{color};stop-opacity:0.3"/>
        </linearGradient>
    </defs>
    <path d="{path}"
          fill="none" stroke="url(#{gradient_id})" stroke-width="2.5"
          stroke-linecap="round" stroke-linejoin="round"/>'''


# =============================================================================
# HTML GENERATION
# =============================================================================

def format_excerpt(exc):
    """Format excerpt text with guillemets around all - full text."""
    parts = []
    if exc['before']:
        parts.append(exc['before'])
    parts.append(exc['main'])
    if exc['after']:
        parts.append(exc['after'])
    full_text = ' '.join(parts)

    return f'« {full_text} »'


def format_excerpt_with_bold(exc):
    """Format excerpt with bold main sentence."""
    parts = []
    if exc['before']:
        parts.append(exc['before'])
    # Main sentence in bold
    parts.append(f'<strong>{exc["main"]}</strong>')
    if exc['after']:
        parts.append(exc['after'])
    full_text = ' '.join(parts)

    return f'« {full_text} »'


def generate_html(data, lang='fr'):
    """Generate complete HTML with SVG timeline and connected bubbles."""

    labels = get_labels(lang)

    if lang == 'fr':
        title = "L'évolution du discours : les moments clés"
        zone_positive = "ZONE CONFIANTE"
        zone_negative = "ZONE ALARMISTE"
        legend_text = "Indice de tonalité calculé sur moyenne glissante (10 phrases)."
    else:
        title = "The Evolution of the Speech: Key Moments"
        zone_positive = "CONFIDENT ZONE"
        zone_negative = "ALARMIST ZONE"
        legend_text = "Tone index based on rolling average (10 sentences)."

    # Generate SVG timeline - LARGER graph
    svg_width = 1880
    svg_height = 340
    svg_timeline, neg_markers, pos_markers, markers_svg = generate_svg_timeline(data, svg_width, svg_height)

    # Bubble positions (in pixels, relative to container) - 4 bubbles
    bubble_width = 450
    bubble_gap = 22
    start_x = 20
    top_y = 55
    bottom_y = 710  # Move UP to be closer to graph
    bubble_positions_top = [
        (start_x, top_y),
        (start_x + bubble_width + bubble_gap, top_y),
        (start_x + 2 * (bubble_width + bubble_gap), top_y),
        (start_x + 3 * (bubble_width + bubble_gap), top_y),
    ]
    bubble_positions_bottom = [
        (start_x, bottom_y),
        (start_x + bubble_width + bubble_gap, bottom_y),
        (start_x + 2 * (bubble_width + bubble_gap), bottom_y),
        (start_x + 3 * (bubble_width + bubble_gap), bottom_y),
    ]

    # SVG panel position - closer to boxes
    svg_top = 310
    svg_left = 20
    bubble_height_approx = 250

    # Generate connector SVGs - connect to CENTER of bubbles (will pass underneath)
    connectors_svg = []

    # Negative connectors (from peak down to CENTER of bubble)
    for i, (marker, bubble_pos) in enumerate(zip(neg_markers, bubble_positions_bottom)):
        start_x = svg_left + marker['cx']
        start_y = svg_top + marker['cy']
        end_x = bubble_pos[0] + bubble_width / 2
        end_y = bubble_pos[1] + bubble_height_approx / 2  # Center of bubble
        connectors_svg.append(generate_connector_svg(start_x, start_y, end_x, end_y, NEGATIVE_COLOR, f"neg_{i}", is_above=False))

    # Positive connectors (from peak up to CENTER of bubble)
    for i, (marker, bubble_pos) in enumerate(zip(pos_markers, bubble_positions_top)):
        start_x = svg_left + marker['cx']
        start_y = svg_top + marker['cy']
        end_x = bubble_pos[0] + bubble_width / 2
        end_y = bubble_pos[1] + bubble_height_approx / 2  # Center of bubble
        connectors_svg.append(generate_connector_svg(start_x, start_y, end_x, end_y, POSITIVE_COLOR, f"pos_{i}", is_above=True))

    # Labels prefixes
    if lang == 'fr':
        tone_prefix = "Ton"
        act_prefix = "Acte"
    else:
        tone_prefix = "Tone"
        act_prefix = "Act"

    # Generate bubble HTML
    def bubble_html(exc, num, is_negative, pos):
        color = NEGATIVE_COLOR if is_negative else POSITIVE_COLOR

        # Normalize tone label
        tone_raw = exc.get('tone', 'NEUTRAL')
        tone = labels.get(tone_raw, tone_raw.replace('_', ' ').title())

        # Normalize act label(s) - handle list
        act_raw = exc.get('speech_act', '')
        if isinstance(act_raw, list):
            act_parts = [labels.get(a, a.replace('_', ' ').title()) for a in act_raw if a]
            act = ', '.join(act_parts)
        elif act_raw:
            act = labels.get(act_raw, act_raw.replace('_', ' ').title())
        else:
            act = ''

        # Format excerpt with bold main sentence
        text = format_excerpt_with_bold(exc)

        # Truncate if too long
        max_chars = 380
        if len(text) > max_chars:
            text = text[:max_chars].rsplit(' ', 1)[0] + ' (...) »'

        # Position label
        pos_label = f"Phrase {exc['pos']}" if lang == 'fr' else f"Sentence {exc['pos']}"

        # Act badge HTML (if available)
        act_html = f'<span class="act-badge">{act_prefix}: {act}</span>' if act else ''

        return f'''
        <div class="bubble {'negative' if is_negative else 'positive'}" style="left: {pos[0]}px; top: {pos[1]}px;">
            <div class="bubble-header">
                <span class="badge" style="background: {color};">{num}</span>
                <span class="tone-label" style="color: {color};">{tone_prefix}: {tone.upper()}</span>
                {act_html}
                <span class="position">{pos_label}</span>
            </div>
            <div class="bubble-text">{text}</div>
        </div>
        '''

    positive_bubbles = ''.join([
        bubble_html(exc, i+1, False, bubble_positions_top[i])
        for i, exc in enumerate(data['positive_excerpts'][:4])
    ])

    negative_bubbles = ''.join([
        bubble_html(exc, i+1, True, bubble_positions_bottom[i])
        for i, exc in enumerate(data['negative_excerpts'][:4])
    ])

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
            font-size: 46px;
            font-weight: 600;
            color: var(--ink);
            letter-spacing: -0.01em;
            margin: 0 0 8px 0;
            text-shadow: 0 1px 2px rgba(31, 27, 22, 0.08);
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
            top: {svg_top}px;
            left: {svg_left}px;
            width: {svg_width}px;
            height: {svg_height}px;
            background: var(--card);
            border-radius: 18px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow);
            padding: 0;
            overflow: visible;
        }}

        .timeline-container svg {{
            width: 100%;
            height: 100%;
        }}

        .timeline-container {{
            z-index: 10;
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
            width: {bubble_width}px;
            max-height: 260px;
            overflow: hidden;
            padding: 14px 16px;
            border-radius: 12px;
            border-left: 6px solid;
            box-shadow: var(--shadow-soft);
        }}

        .bubble.positive {{
            background: {POSITIVE_LIGHT};
            border-color: {POSITIVE_COLOR};
        }}

        .bubble.negative {{
            background: {NEGATIVE_LIGHT};
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
            color: var(--muted);
            padding: 3px 10px;
            background: rgba(31, 27, 22, 0.06);
            border-radius: 12px;
        }}

        .position {{
            margin-left: auto;
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 12px;
            color: var(--muted);
            flex-shrink: 0;
        }}

        .bubble-text {{
            font-size: 15px;
            line-height: 1.45;
            color: var(--ink);
            text-align: justify;
            hyphens: auto;
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
            top: {svg_top + 25}px;
            right: 50px;
        }}

        .zone-label.negative {{
            color: {NEGATIVE_COLOR};
            top: {svg_top + svg_height - 45}px;
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
            color: var(--muted);
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="infographic-container">
        <!-- Connectors SVG layer -->
        <svg class="connectors-layer" viewBox="0 0 1920 1080">
            {chr(10).join(connectors_svg)}
        </svg>

        <!-- Timeline graph -->
        <div class="timeline-container">
            {svg_timeline}
        </div>

        <!-- Peak markers layer (on top of connectors) -->
        <svg class="markers-layer" viewBox="0 0 {svg_width} {svg_height}" style="position: absolute; top: {svg_top}px; left: {svg_left}px; width: {svg_width}px; height: {svg_height}px;">
            {markers_svg}
        </svg>

        <!-- Zone labels -->
        <div class="zone-label positive">{zone_positive}</div>
        <div class="zone-label negative">{zone_negative}</div>

        <!-- Positive bubbles (top) -->
        {positive_bubbles}

        <!-- Negative bubbles (bottom) -->
        {negative_bubbles}

        <!-- Bottom section: title + legend -->
        <div class="bottom-section">
            <h1 class="main-title">{title}</h1>
            <p class="legend">{legend_text}</p>
        </div>
    </div>
</body>
</html>
'''
    return html


# =============================================================================
# PNG EXPORT
# =============================================================================

def html_to_png(html_content, output_path, width=1920, height=1080):
    """Convert HTML to PNG using Playwright."""
    if not HAS_PLAYWRIGHT:
        print("  [!] Playwright not installed.")
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': width, 'height': height})
        page.set_content(html_content)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(800)  # Wait for fonts
        page.screenshot(path=str(output_path), clip={'x': 0, 'y': 0, 'width': width, 'height': height})
        browser.close()
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("Generating Integrated Infographic (HTML/CSS + SVG)")
    print("=" * 70)

    print("\nLoading data...")
    df = load_data()

    print("Preparing data...")
    data = prepare_data(df)

    for lang in ['fr', 'en']:
        print(f"\n--- {lang.upper()} ---")

        print("  Generating HTML...")
        html = generate_html(data, lang)

        # Save HTML
        html_path = OUTPUT_DIR / f"fig4_emotional_timeline_{lang}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  Saved: {html_path.name}")

        # Convert to PNG
        print("  Converting to PNG...")
        png_path = OUTPUT_DIR / f"fig4_emotional_timeline_{lang}.png"
        if html_to_png(html, png_path):
            print(f"  Saved: {png_path.name}")

    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()
