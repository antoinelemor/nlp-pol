#!/usr/bin/env python3
"""
Generate PDF versions of HTML presentations using Playwright.
Uses native PDF generation to preserve clickable links.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

PRESENTATION_DIR = Path(__file__).parent
SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080


async def generate_presentation_pdf(html_file: Path, output_file: Path):
    """Generate a multi-page PDF from fixed-size HTML slides with clickable links."""
    print(f"Generating PDF: {output_file.name}")

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

        # Inject CSS to format slides for PDF print
        await page.add_style_tag(content="""
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
            .nav-info {
                display: none !important;
            }
        """)

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

    print(f"  Saved: {output_file.name}")


async def main():
    print("=" * 60)
    print("GENERATING PRESENTATION PDFs")
    print("=" * 60)

    # Generate PDFs
    for lang in ['fr', 'en']:
        html_file = PRESENTATION_DIR / f'slides_{lang}.html'
        pdf_file = PRESENTATION_DIR / f'slides_{lang}.pdf'

        if html_file.exists():
            await generate_presentation_pdf(html_file, pdf_file)
        else:
            print(f"  Warning: {html_file.name} not found")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
