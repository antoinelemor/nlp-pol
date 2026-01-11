#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_pdf.py

MAIN OBJECTIVE:
---------------
Generate PDF versions of HTML presentations using Playwright.
Two methods available:
- PNG-based (default): Screenshots each slide as PNG, then assembles into PDF.
  Better visual quality and readability.
- Direct PDF: Native browser PDF export. Preserves clickable links but may have
  rendering issues.

Dependencies:
-------------
- asyncio
- pathlib
- playwright
- Pillow (PIL) for PNG-to-PDF conversion

Author:
-------
Antoine Lemor
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
from playwright.async_api import async_playwright

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

PRESENTATION_DIR = Path(__file__).parent
SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080


def pngs_to_pdf(png_files: list, output_path: Path, dpi: int = 150):
    """
    Assemble PNG images into a single PDF.

    Parameters
    ----------
    png_files : list
        List of Path objects to PNG files (in order)
    output_path : Path
        Output PDF path
    dpi : int
        Resolution for the PDF (default: 150)
    """
    if not HAS_PIL:
        raise ImportError("Pillow is required for PNG-to-PDF conversion. Install with: pip install Pillow")

    images = []
    for png_file in png_files:
        img = Image.open(png_file)
        # Convert to RGB if necessary (PNG might have alpha channel)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        images.append(img)

    if images:
        # Save first image and append the rest
        images[0].save(
            output_path,
            'PDF',
            resolution=dpi,
            save_all=True,
            append_images=images[1:] if len(images) > 1 else []
        )


async def generate_pdf_from_pngs(html_file: Path, output_file: Path, dpi: int = 150, keep_pngs: bool = False):
    """
    Generate PDF by screenshotting each slide as PNG then assembling.

    Parameters
    ----------
    html_file : Path
        Path to the HTML presentation file
    output_file : Path
        Path for the output PDF
    dpi : int
        Resolution for the PDF (default: 150)
    keep_pngs : bool
        Whether to keep the intermediate PNG files (default: False)
    """
    print(f"Generating PDF (PNG method): {output_file.name}")

    # Create temp directory for PNGs
    temp_dir = Path(tempfile.mkdtemp(prefix='slides_'))
    png_files = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={'width': SLIDE_WIDTH, 'height': SLIDE_HEIGHT})

            # Load the HTML file
            await page.goto(f'file://{html_file.absolute()}')
            await page.wait_for_load_state('networkidle')

            # Wait for fonts to load
            await page.wait_for_timeout(1500)

            # Hide navigation elements
            await page.evaluate("""
                document.querySelectorAll('.nav-info, .slide-counter, .nav-container, .toc-toggle, .toc-sidebar, .keyboard-hint, .progress-bar').forEach(el => {
                    if (el) el.style.display = 'none';
                });
            """)

            # Get all slides
            slides = await page.query_selector_all('.slide')
            total_slides = len(slides)
            print(f"  Found {total_slides} slides")

            # Screenshot each slide
            for i, slide in enumerate(slides):
                png_path = temp_dir / f'slide_{i:03d}.png'

                # Scroll slide into view and wait
                await slide.scroll_into_view_if_needed()
                await page.wait_for_timeout(200)

                # Get slide bounding box
                box = await slide.bounding_box()

                if box:
                    # Screenshot the slide area
                    await page.screenshot(
                        path=str(png_path),
                        clip={
                            'x': box['x'],
                            'y': box['y'],
                            'width': SLIDE_WIDTH,
                            'height': SLIDE_HEIGHT
                        }
                    )
                    png_files.append(png_path)
                    print(f"  Captured slide {i + 1}/{total_slides}")

            await browser.close()

        # Assemble PNGs into PDF
        if png_files:
            print(f"  Assembling {len(png_files)} slides into PDF...")
            pngs_to_pdf(png_files, output_file, dpi=dpi)

            # Report file size
            size_mb = output_file.stat().st_size / 1024 / 1024
            print(f"  Saved: {output_file.name} ({size_mb:.1f} MB)")

        # Optionally keep PNGs
        if keep_pngs:
            png_output_dir = output_file.parent / f'{output_file.stem}_slides'
            png_output_dir.mkdir(exist_ok=True)
            for png_file in png_files:
                shutil.copy(png_file, png_output_dir / png_file.name)
            print(f"  PNGs saved to: {png_output_dir.name}/")

    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


async def generate_pdf_direct(html_file: Path, output_file: Path, simplify: bool = True):
    """
    Generate PDF using native browser PDF export (preserves links).

    Parameters
    ----------
    html_file : Path
        Path to the HTML presentation file
    output_file : Path
        Path for the output PDF
    simplify : bool
        Whether to simplify visual effects for better PDF readability (default: True)
    """
    print(f"Generating PDF (direct method): {output_file.name}")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': SLIDE_WIDTH, 'height': SLIDE_HEIGHT})

        # Load the HTML file
        await page.goto(f'file://{html_file.absolute()}')
        await page.wait_for_load_state('networkidle')

        # Wait for fonts to load
        await page.wait_for_timeout(1500)

        # Hide navigation info
        await page.evaluate("document.body.classList.add('hide-for-capture')")

        # Base CSS for PDF formatting
        pdf_css = """
            @page {
                size: 1920px 1080px;
                margin: 0;
            }
            body {
                background: white !important;
            }
            .slide {
                width: 1920px !important;
                height: 1080px !important;
                margin: 0 !important;
                page-break-after: always;
                page-break-inside: avoid;
                break-after: page;
                break-inside: avoid;
            }
            .slide:last-of-type {
                page-break-after: auto;
            }
            .nav-info, .slide-counter, .nav-container, .toc-toggle, .toc-sidebar, .keyboard-hint, .progress-bar {
                display: none !important;
            }
        """

        # Additional CSS to simplify visual effects for better PDF readability
        if simplify:
            pdf_css += """
            /* Remove complex gradients - use solid backgrounds */
            .slide {
                background: #fbf8f2 !important;
            }

            /* Simplify card shadows */
            .card, .col-card, .metric, .section-box, .tool-card, .pipeline-step, .insight-box {
                box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
            }

            /* Remove text shadows */
            * {
                text-shadow: none !important;
            }

            /* Ensure solid borders instead of gradient borders */
            .card, .col-card, .metric, .insight-box {
                border: 1px solid #e7e1d8 !important;
            }

            /* Simplify table styling */
            .data-table {
                border-collapse: collapse !important;
            }
            .data-table th {
                background: #f5f3ef !important;
            }
            .data-table tr:hover td {
                background: transparent !important;
            }

            /* Remove backdrop filters */
            * {
                backdrop-filter: none !important;
                -webkit-backdrop-filter: none !important;
            }

            /* Ensure text is crisp */
            * {
                -webkit-font-smoothing: antialiased !important;
                -moz-osx-font-smoothing: grayscale !important;
            }

            /* Remove animations */
            *, *::before, *::after {
                animation: none !important;
                transition: none !important;
            }

            /* Ensure all elements are fully opaque */
            .card, .col-card, .metric, .section-box, .pipeline-step, .tool-card,
            .insight-box, .table-container, .cards-grid .card, .metrics-row .metric {
                opacity: 1 !important;
                transform: none !important;
            }

            /* Simplify hover states (won't apply in PDF but just in case) */
            *:hover {
                transform: none !important;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
            }
        """

        await page.add_style_tag(content=pdf_css)

        # Get slide count
        slides = await page.query_selector_all('.slide')
        print(f"  Found {len(slides)} slides")

        # Generate PDF with native Playwright PDF (preserves links)
        await page.pdf(
            path=str(output_file),
            width='1920px',
            height='1080px',
            print_background=True,
            margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'},
            prefer_css_page_size=True
        )

        await browser.close()

    size_mb = output_file.stat().st_size / 1024 / 1024
    print(f"  Saved: {output_file.name} ({size_mb:.1f} MB)")


async def main():
    """
    Generate PDF versions of both French and English presentations.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate PDF presentations from HTML slides',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Methods:
  direct (default)  Native browser PDF export. Preserves clickable links.
                    Visual effects are simplified for better readability.
  png               Screenshot each slide as PNG, then assemble into PDF.
                    Best visual fidelity but no clickable links.

Examples:
  python generate_pdf.py                    # Direct method with simplified visuals
  python generate_pdf.py --no-simplify      # Keep all visual effects (may render poorly)
  python generate_pdf.py --method png       # PNG method, 150 DPI
  python generate_pdf.py --method png --dpi 200  # Higher quality PNG
        """
    )
    parser.add_argument('--method', choices=['direct', 'png'], default='direct',
                        help='PDF generation method (default: direct)')
    parser.add_argument('--no-simplify', action='store_true',
                        help='Keep complex visual effects (direct method only)')
    parser.add_argument('--dpi', type=int, default=150,
                        help='PDF resolution for PNG method (default: 150)')
    parser.add_argument('--keep-pngs', action='store_true',
                        help='Keep intermediate PNG files (PNG method only)')
    parser.add_argument('--lang', choices=['fr', 'en', 'both'], default='both',
                        help='Language version to generate (default: both)')
    args = parser.parse_args()

    print("=" * 60)
    print("GENERATING PRESENTATION PDFs")
    print(f"  Method: {args.method}")
    if args.method == 'direct':
        print(f"  Simplified visuals: {not args.no_simplify}")
    else:
        print(f"  DPI: {args.dpi}")
    print("=" * 60)

    # Determine languages to process
    languages = ['fr', 'en'] if args.lang == 'both' else [args.lang]

    # Generate PDFs
    for lang in languages:
        html_file = PRESENTATION_DIR / f'slides_{lang}.html'
        pdf_file = PRESENTATION_DIR / f'slides_{lang}.pdf'

        if html_file.exists():
            if args.method == 'png':
                await generate_pdf_from_pngs(
                    html_file,
                    pdf_file,
                    dpi=args.dpi,
                    keep_pngs=args.keep_pngs
                )
            else:
                await generate_pdf_direct(
                    html_file,
                    pdf_file,
                    simplify=not args.no_simplify
                )
        else:
            print(f"  Warning: {html_file.name} not found")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
