#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
html_utils.py

MAIN OBJECTIVE:
---------------
Provide shared HTML/CSS utilities for figure generation.
Includes color constants, base HTML templates, SVG utilities,
and Playwright-based PNG export functionality.

Dependencies:
-------------
- pathlib
- playwright (optional, for PNG export)

MAIN FEATURES:
--------------
1) Shared color palette (primary, success, danger, etc.)
2) Base HTML template with responsive styling
3) SVG utilities for gauges and horizontal bars
4) Playwright integration for HTML-to-PNG conversion

Author:
-------
Antoine Lemor
"""

from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# =============================================================================
# COLORS
# =============================================================================

COLORS = {
    'primary': '#2563EB',
    'success': '#059669',
    'danger': '#DC2626',
    'warning': '#F59E0B',
    'neutral': '#64748B',
    'dark': '#1e293b',
    'light': '#f8fafc',
}

POSITIVE_COLOR = '#059669'
POSITIVE_LIGHT = '#D1FAE5'
NEGATIVE_COLOR = '#DC2626'
NEGATIVE_LIGHT = '#FEE2E2'

# =============================================================================
# BASE HTML TEMPLATE
# =============================================================================

def get_base_html(title, body_content, width=1920, height=1080, extra_styles=""):
    """Generate base HTML structure with common styles."""
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,500;0,600;1,400&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            width: {width}px;
            height: {height}px;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            font-family: 'Inter', sans-serif;
            position: relative;
            overflow: hidden;
        }}

        .container {{
            position: absolute;
            top: 0;
            left: 0;
            width: {width}px;
            height: {height}px;
            padding: 40px;
        }}

        .main-title {{
            font-family: 'Source Serif 4', Georgia, serif;
            font-size: 44px;
            font-weight: 600;
            color: #0f172a;
            text-align: center;
            margin-bottom: 8px;
            text-shadow: 0 1px 2px rgba(0,0,0,0.08);
        }}

        .subtitle {{
            font-size: 16px;
            color: #64748b;
            text-align: center;
            font-style: italic;
            margin-bottom: 30px;
        }}

        .card {{
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            padding: 24px;
        }}

        .card-title {{
            font-size: 18px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .legend {{
            position: absolute;
            bottom: 20px;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 13px;
            color: #64748b;
            font-style: italic;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}

        .stat-value {{
            font-size: 48px;
            font-weight: 700;
            color: {COLORS['primary']};
        }}

        .stat-label {{
            font-size: 14px;
            color: #64748b;
            margin-top: 4px;
        }}

        {extra_styles}
    </style>
</head>
<body>
    <div class="container">
        {body_content}
    </div>
</body>
</html>'''


# =============================================================================
# SVG UTILITIES
# =============================================================================

def create_gauge_svg(value, min_val=-1, max_val=1, width=200, height=120,
                     color_negative=NEGATIVE_COLOR, color_positive=POSITIVE_COLOR):
    """Create a gauge SVG element."""
    # Normalize value to 0-1 range
    normalized = (value - min_val) / (max_val - min_val)
    normalized = max(0, min(1, normalized))

    # Determine color
    if value < -0.2:
        color = color_negative
    elif value > 0.2:
        color = color_positive
    else:
        color = COLORS['warning']

    # Calculate needle angle (180 = left, 0 = right)
    angle = 180 - (normalized * 180)

    import math
    needle_x = 100 + 70 * math.cos(math.radians(angle))
    needle_y = 100 - 70 * math.sin(math.radians(angle))

    return f'''
    <svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <!-- Background arc -->
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#E5E7EB" stroke-width="20" stroke-linecap="round"/>

        <!-- Colored sections -->
        <path d="M 20 100 A 80 80 0 0 1 60 35" fill="none" stroke="{color_negative}" stroke-width="20" stroke-linecap="round" opacity="0.8"/>
        <path d="M 60 35 A 80 80 0 0 1 140 35" fill="none" stroke="{COLORS['warning']}" stroke-width="20" stroke-linecap="round" opacity="0.8"/>
        <path d="M 140 35 A 80 80 0 0 1 180 100" fill="none" stroke="{color_positive}" stroke-width="20" stroke-linecap="round" opacity="0.8"/>

        <!-- Needle -->
        <line x1="100" y1="100" x2="{needle_x}" y2="{needle_y}" stroke="#1a1a1a" stroke-width="4" stroke-linecap="round"/>
        <circle cx="100" cy="100" r="10" fill="#1a1a1a"/>
    </svg>
    '''


def create_horizontal_bar(value, max_value, width=300, height=24, color=COLORS['primary']):
    """Create a horizontal bar SVG."""
    bar_width = (value / max_value) * (width - 4) if max_value > 0 else 0
    return f'''
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="{width}" height="{height}" rx="4" fill="#E5E7EB"/>
        <rect x="2" y="2" width="{bar_width}" height="{height-4}" rx="3" fill="{color}"/>
    </svg>
    '''


# =============================================================================
# PLAYWRIGHT EXPORT
# =============================================================================

def html_to_png(html_content, output_path, width=1920, height=1080):
    """Convert HTML to PNG using Playwright."""
    if not HAS_PLAYWRIGHT:
        print("  [!] Playwright not installed. Skipping PNG export.")
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


def save_figure(html_content, output_dir, filename, width=1920, height=1080):
    """Save HTML and PNG versions of a figure."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save HTML
    html_path = output_dir / f"{filename}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"  Saved: {html_path.name}")

    # Save PNG
    png_path = output_dir / f"{filename}.png"
    if html_to_png(html_content, png_path, width, height):
        print(f"  Saved: {png_path.name}")

    return html_path, png_path
