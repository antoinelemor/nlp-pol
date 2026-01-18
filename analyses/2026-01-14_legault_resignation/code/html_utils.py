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
Shared HTML utilities for figure generation.
Includes base template, common components, and PNG export.

Dependencies:
-------------
- pathlib (Path handling)
- playwright (PNG export)
- config (CSS variables)

MAIN FEATURES:
--------------
1) Base HTML template with NLP-POL branding
2) Common HTML components (cards, bars, quotes)
3) Playwright-based PNG export
4) Figure saving utilities

Author:
-------
Antoine Lemor
"""

from pathlib import Path
from typing import Optional
import html

from config import CSS_VARS, get_labels, get_quote_marks, OUTPUT_WIDTH, OUTPUT_HEIGHT


# =============================================================================
# PATHS
# =============================================================================

ANALYSIS_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ANALYSIS_DIR / 'output' / 'figures'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# BASE HTML TEMPLATE
# =============================================================================

def get_base_template(
    title: str,
    subtitle: str,
    content: str,
    methodology: str,
    lang: str = 'fr'
) -> str:
    """
    Generate complete HTML document with NLP-POL branding.

    Args:
        title: Main figure title.
        subtitle: Subtitle/description.
        content: Main content HTML.
        methodology: Methodology note for footer.
        lang: Language code ('fr' or 'en').

    Returns:
        Complete HTML string.
    """
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <title>{html.escape(title)}</title>
    <link href="https://fonts.googleapis.com/css2?family=STIX+Two+Text:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        {CSS_VARS}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            width: {OUTPUT_WIDTH}px;
            height: {OUTPUT_HEIGHT}px;
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

        .header-left {{
            flex: 1;
        }}

        .main-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 62px;
            font-weight: 600;
            line-height: 1.1;
            letter-spacing: -0.02em;
            color: var(--ink);
        }}

        .subtitle {{
            font-size: 21px;
            color: var(--muted);
            margin-top: 8px;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }}

        .header-right {{
            text-align: right;
        }}

        .speaker-name {{
            font-family: 'STIX Two Text', serif;
            font-size: 28px;
            font-weight: 600;
            color: var(--ink);
        }}

        .speaker-title {{
            font-size: 16px;
            color: var(--muted);
            margin-top: 4px;
        }}

        /* Main content */
        .main-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 18px;
            overflow: hidden;
        }}

        /* Panels/Cards */
        .panel {{
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow-soft);
            padding: 22px 26px;
        }}

        .panel-header {{
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--muted);
            margin-bottom: 12px;
        }}

        /* Index cards */
        .index-card {{
            background: var(--card);
            border-radius: 16px;
            border: 1px solid var(--line);
            box-shadow: var(--shadow-soft);
            padding: 24px 28px;
            display: flex;
            flex-direction: column;
        }}

        .index-value {{
            font-family: 'STIX Two Text', serif;
            font-size: 72px;
            font-weight: 700;
            line-height: 1;
        }}

        .index-label {{
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            margin-top: 8px;
        }}

        .index-sublabel {{
            font-size: 13px;
            color: var(--muted);
            margin-top: 4px;
        }}

        /* Horizontal bars */
        .bar-container {{
            margin-bottom: 12px;
        }}

        .bar-label {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
            font-size: 14px;
        }}

        .bar-name {{
            font-weight: 500;
        }}

        .bar-value {{
            color: var(--muted);
        }}

        .bar-track {{
            height: 24px;
            background: var(--bg-deep);
            border-radius: 8px;
            overflow: hidden;
        }}

        .bar-fill {{
            height: 100%;
            border-radius: 8px;
            transition: width 0.3s ease;
        }}

        /* Quote cards */
        .quote-card {{
            background: var(--card);
            border-radius: 14px;
            border: 1px solid var(--line);
            padding: 16px 18px;
            margin-bottom: 12px;
        }}

        .quote-label {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 8px;
        }}

        .quote-text {{
            font-family: 'STIX Two Text', serif;
            font-size: 19px;
            line-height: 1.55;
            color: var(--ink);
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        /* Grid layouts */
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}

        .grid-3 {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
        }}

        .grid-4 {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }}

        .grid-5 {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
        }}

        /* Methodology footer */
        .methodology {{
            margin-top: auto;
            padding-top: 20px;
        }}

        .methodology-text {{
            font-size: 15px;
            color: var(--muted);
            border-top: 1px solid var(--line);
            padding-top: 16px;
            line-height: 1.5;
        }}

        /* Utility classes */
        .text-positive {{ color: #059669; }}
        .text-negative {{ color: #DC2626; }}
        .text-neutral {{ color: #6B7280; }}
        .text-warning {{ color: #F59E0B; }}
        .text-primary {{ color: #2563EB; }}

        .border-left-accent {{
            border-left: 8px solid var(--accent);
        }}

        .section-title {{
            font-size: 22px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 16px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="header-left">
                <h1 class="main-title">{html.escape(title)}</h1>
                <p class="subtitle">{html.escape(subtitle)}</p>
            </div>
            <div class="header-right">
                <p class="speaker-name">François Legault</p>
                <p class="speaker-title">Premier ministre du Québec (2018-2026)</p>
            </div>
        </header>
        <div class="main-content">
            {content}
        </div>
        <footer class="methodology">
            <p class="methodology-text">{html.escape(methodology)}</p>
        </footer>
    </div>
</body>
</html>'''


# =============================================================================
# COMPONENT GENERATORS
# =============================================================================

def make_bar_chart(
    items: list,
    color_map: dict,
    label_map: dict,
    max_value: Optional[float] = None
) -> str:
    """
    Generate horizontal bar chart HTML.

    Args:
        items: List of (name, value) tuples.
        color_map: Dict mapping names to colors.
        label_map: Dict mapping names to display labels.
        max_value: Maximum value for scaling (auto if None).

    Returns:
        HTML string for bar chart.
    """
    if not items:
        return '<p style="color: var(--muted);">No data available</p>'

    if max_value is None:
        max_value = max(v for _, v in items) if items else 1

    bars = []
    for name, value in items:
        color = color_map.get(name, '#6B7280')
        label = label_map.get(name, name)
        pct = (value / max_value * 100) if max_value > 0 else 0

        bars.append(f'''
        <div class="bar-container">
            <div class="bar-label">
                <span class="bar-name">{html.escape(label)}</span>
                <span class="bar-value">{value}</span>
            </div>
            <div class="bar-track">
                <div class="bar-fill" style="width: {pct}%; background: {color};"></div>
            </div>
        </div>
        ''')

    return '\n'.join(bars)


def make_index_card(
    value: float,
    label: str,
    sublabel: str = '',
    color: str = '#2563EB',
    format_str: str = '{:+.2f}'
) -> str:
    """
    Generate index card HTML.

    Args:
        value: Numeric index value.
        label: Main label text.
        sublabel: Secondary label text.
        color: Border and value color.
        format_str: Format string for value display.

    Returns:
        HTML string for index card.
    """
    formatted = format_str.format(value)
    return f'''
    <div class="index-card" style="border-left: 10px solid {color};">
        <span class="index-value" style="color: {color};">{formatted}</span>
        <span class="index-label">{html.escape(label)}</span>
        <span class="index-sublabel">{html.escape(sublabel)}</span>
    </div>
    '''


def make_quote_card(
    text: str,
    label: str,
    color: str = '#0f766e',
    lang: str = 'fr'
) -> str:
    """
    Generate quote card HTML.

    Args:
        text: Quote text.
        label: Category/theme label.
        color: Border color.
        lang: Language for quote marks.

    Returns:
        HTML string for quote card.
    """
    quote_open, quote_close = get_quote_marks(lang)
    return f'''
    <div class="quote-card" style="border-left: 8px solid {color};">
        <p class="quote-label" style="color: {color};">{html.escape(label)}</p>
        <p class="quote-text">{quote_open}{html.escape(text)}{quote_close}</p>
    </div>
    '''


def make_panel(
    title: str,
    content: str,
    border_color: Optional[str] = None
) -> str:
    """
    Generate panel/card HTML.

    Args:
        title: Panel header title.
        content: Inner HTML content.
        border_color: Optional left border color.

    Returns:
        HTML string for panel.
    """
    border_style = f'border-left: 8px solid {border_color};' if border_color else ''
    return f'''
    <div class="panel" style="{border_style}">
        <p class="panel-header">{html.escape(title)}</p>
        {content}
    </div>
    '''


# =============================================================================
# FIGURE SAVING
# =============================================================================

def save_figure(
    html_content: str,
    output_dir: Path,
    filename: str,
    export_png: bool = True
) -> None:
    """
    Save HTML figure and optionally export to PNG.

    Args:
        html_content: Complete HTML string.
        output_dir: Output directory path.
        filename: Base filename (without extension).
        export_png: Whether to also export PNG.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save HTML
    html_path = output_dir / f'{filename}.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Saved: {html_path}")

    # Export PNG
    if export_png:
        png_path = output_dir / f'{filename}.png'
        html_to_png(html_content, png_path)
        print(f"Saved: {png_path}")


def html_to_png(
    html_content: str,
    output_path: Path,
    width: int = OUTPUT_WIDTH,
    height: int = OUTPUT_HEIGHT
) -> None:
    """
    Export HTML to PNG using Playwright.

    Args:
        html_content: Complete HTML string.
        output_path: Output PNG path.
        width: Viewport width.
        height: Viewport height.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Warning: Playwright not installed. Skipping PNG export.")
        print("Install with: pip install playwright && playwright install chromium")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': width, 'height': height})
        page.set_content(html_content)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(800)  # Wait for Google Fonts
        page.screenshot(
            path=str(output_path),
            clip={'x': 0, 'y': 0, 'width': width, 'height': height}
        )
        browser.close()


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == '__main__':
    # Test template generation
    test_content = '''
    <div class="grid-2">
        <div class="panel">
            <p class="panel-header">Test Panel</p>
            <p>This is test content.</p>
        </div>
        <div class="panel">
            <p class="panel-header">Another Panel</p>
            <p>More test content here.</p>
        </div>
    </div>
    '''

    test_html = get_base_template(
        title="Test Figure",
        subtitle="Testing the template",
        content=test_content,
        methodology="Test methodology note.",
        lang='fr'
    )

    print("Template generated successfully!")
    print(f"HTML length: {len(test_html)} characters")
