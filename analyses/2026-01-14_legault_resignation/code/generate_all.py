#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_all.py

MAIN OBJECTIVE:
---------------
Master script to generate all figures for the Legault Resignation analysis.
Orchestrates individual figure generators and manages excerpt deduplication.

Dependencies:
-------------
- load_and_validate (data loading)
- compute_indices (excerpt registry reset)
- All generate_fig*.py modules

MAIN FEATURES:
--------------
1) Load and validate annotated data
2) Reset excerpt registry for deduplication
3) Generate all figures in sequence (FR/EN)
4) Summary statistics output

Author:
-------
Antoine Lemor
"""

import sys
from pathlib import Path

# Add code directory to path
CODE_DIR = Path(__file__).parent
sys.path.insert(0, str(CODE_DIR))

from load_and_validate import load_data, OUTPUT_DIR
from compute_indices import reset_excerpts


# =============================================================================
# FIGURE GENERATORS (import when available)
# =============================================================================

FIGURE_MODULES = [
    'generate_fig1_dashboard',
    'generate_fig2_justifications',
    'generate_fig3_policy_domains',
    'generate_fig4_emotions',
    'generate_fig5_actors',
    'generate_fig6_identity',
    'generate_fig7_legacy',
    'generate_fig8_speech_acts',
]


def generate_all_figures(df, export_png=True):
    """
    Generate all figures from the loaded data.

    Args:
        df: Parsed annotation DataFrame.
        export_png: Whether to export PNG files.
    """
    print("\n" + "="*60)
    print("GENERATING ALL FIGURES")
    print("="*60)

    # Reset excerpt registry
    reset_excerpts()
    print("Reset excerpt registry for deduplication.")

    generated = []
    skipped = []

    for module_name in FIGURE_MODULES:
        try:
            module = __import__(module_name)
            if hasattr(module, 'main'):
                print(f"\n--- Generating {module_name} ---")
                module.main(df, export_png=export_png)
                generated.append(module_name)
            else:
                print(f"Warning: {module_name} has no main() function")
                skipped.append(module_name)
        except ImportError as e:
            print(f"Skipping {module_name}: not yet implemented ({e})")
            skipped.append(module_name)
        except Exception as e:
            print(f"Error in {module_name}: {e}")
            skipped.append(module_name)

    # Summary
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)
    print(f"Generated: {len(generated)} figures")
    for name in generated:
        print(f"  - {name}")
    if skipped:
        print(f"\nSkipped: {len(skipped)} figures")
        for name in skipped:
            print(f"  - {name}")

    print(f"\nOutput directory: {OUTPUT_DIR}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    print("="*60)
    print("NLP-POL: Legault Resignation Speech Analysis")
    print("="*60)

    # Load data
    try:
        df = load_data()
    except FileNotFoundError:
        print("\nERROR: No annotated data file found in data/ directory.")
        print("Please complete the annotation and place the CSV file in:")
        print(f"  {CODE_DIR.parent / 'data'}")
        print("\nExpected columns:")
        print("  segment_id, speaker, text, speech_act, justification_type,")
        print("  policy_domain, emotional_register, actors, temporality,")
        print("  identity_themes, rhetorical_devices, legacy_framing, implicit_references")
        return

    # Check for minimum required columns
    required = ['text', 'segment_id']
    missing = [col for col in required if col not in df.columns]
    if missing:
        print(f"\nERROR: Missing required columns: {missing}")
        return

    # Generate figures
    generate_all_figures(df, export_png=True)

    print("\nDone!")


if __name__ == '__main__':
    main()
