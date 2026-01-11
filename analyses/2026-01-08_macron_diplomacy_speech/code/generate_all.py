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
Master script to generate all figures for the Macron diplomacy speech analysis.
Orchestrates the execution of individual figure generators and produces a
comprehensive analysis report with all computed indices.

Usage:
------
    python generate_all.py              # Generate all figures
    python generate_all.py --lang fr    # Generate French only
    python generate_all.py --fig 1      # Generate figure 1 only
    python generate_all.py --full-report # Print comprehensive analysis

Dependencies:
-------------
- compute_indices (all index computation functions)
- config (EMOTIONAL_REGISTER_WEIGHTS)
- generate_fig[1-8]_*.py (individual figure generators)

MAIN FEATURES:
--------------
1) Load and validate annotated data
2) Compute all composite indices with detailed breakdowns
3) Generate 8 figures in HTML + PNG format
4) Support bilingual output (FR/EN) and selective generation

Author:
-------
Antoine Lemor
"""

import argparse
import sys
from pathlib import Path

# Add code directory to path
CODE_DIR = Path(__file__).parent
sys.path.insert(0, str(CODE_DIR))

from compute_indices import (
    load_data, compute_all_indices, compute_summary_stats,
    compute_worldview_components, count_list_column,
    prepare_geopolitical_data, prepare_actor_sentiment_data,
    prepare_policy_data, prepare_rhetorical_data, prepare_agency_data
)
from config import EMOTIONAL_REGISTER_WEIGHTS


def print_header():
    print("=" * 70)
    print("MACRON DIPLOMACY SPEECH ANALYSIS - FIGURE GENERATION")
    print("HTML/CSS figures for web integration")
    print("=" * 70)


def print_full_analysis(df):
    """Print comprehensive analysis with all values - rigorous and scientific."""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE ANALYSIS REPORT")
    print("=" * 70)

    # =========================================================================
    # 1. SUMMARY STATISTICS
    # =========================================================================
    stats = compute_summary_stats(df)
    print("\n" + "-" * 50)
    print("1. SUMMARY STATISTICS")
    print("-" * 50)
    print(f"  Total sentences:        {stats['n_sentences']}")
    print(f"  Policy mentions:        {stats['n_policies']}")
    print(f"  Issue stances:          {stats['n_stances']}")
    print(f"  Actor mentions:         {stats['n_actors']}")
    print(f"  Geopolitical frames:    {stats['n_frames']}")

    # =========================================================================
    # 2. COMPOSITE INDICES
    # =========================================================================
    indices = compute_all_indices(df)
    worldview = compute_worldview_components(df)

    print("\n" + "-" * 50)
    print("2. COMPOSITE INDICES")
    print("-" * 50)

    print("\n  2.1 Geopolitical Anxiety Index (GAI)")
    print(f"      Value:          {indices['geopolitical_anxiety']:+.4f}")
    print(f"      Interpretation: [-1 = pessimistic, +1 = optimistic]")
    print(f"      Components:")
    print(f"        - Frame Balance:    {worldview['frame_balance']:+.4f} (weight: {worldview['weight_frame']:.2%})")
    print(f"        - Tone Index:       {worldview['tone_index']:+.4f} (weight: {worldview['weight_tone']:.2%})")
    print(f"        - Frame Total:      {worldview['frame_total']} frames")
    print(f"        - Tone Total:       {worldview['tone_total']} sentences")

    print("\n  2.2 Agency Index")
    print(f"      Value:          {indices['agency']:.4f} ({indices['agency']:.1%})")
    print(f"      Interpretation: [0 = passive, 1 = highly active]")
    print(f"      Formula: (Active*1.0 + Partner*0.7 + Passive*0.3) / Total")

    print("\n  2.3 Policy Ambition Index")
    print(f"      Value:          {indices['policy_ambition']:.4f} ({indices['policy_ambition']:.1%})")
    print(f"      Interpretation: [0 = vague, 1 = concrete]")
    print(f"      Formula: Mean(Concrete*1.0 + Programmatic*0.6 + Aspirational*0.2)")

    print("\n  2.4 Diplomatic Tone Index")
    print(f"      Value:          {indices['diplomatic_tone']:+.4f}")
    print(f"      Interpretation: [-1 = alarmist/combative, +1 = confident/calm]")
    print(f"      Formula: Mean(emotional_register_weights) / 2.0")

    print("\n  2.5 Action Orientation Index")
    print(f"      Value:          {indices['action_orientation']:.4f} ({indices['action_orientation']:.1%})")
    print(f"      Interpretation: [0 = descriptive, 1 = action-oriented]")
    print(f"      Formula: Action_acts / (Action_acts + Descriptive_acts)")

    # =========================================================================
    # 3. GEOPOLITICAL FRAMES DISTRIBUTION
    # =========================================================================
    geo_data = prepare_geopolitical_data(df)

    print("\n" + "-" * 50)
    print("3. GEOPOLITICAL FRAMES DISTRIBUTION")
    print("-" * 50)

    print(f"\n  Total Threat Frames:      {geo_data['threat_total']}")
    print(f"  Total Opportunity Frames: {geo_data['opportunity_total']}")
    print(f"  Ratio (Threat:Opp):       {geo_data['threat_total']}:{geo_data['opportunity_total']}")

    print("\n  Threat Frames (detail):")
    for frame, count in geo_data['threat_data']:
        pct = count / geo_data['frame_total'] * 100 if geo_data['frame_total'] > 0 else 0
        print(f"    - {frame:30} {count:3} ({pct:5.1f}%)")

    print("\n  Opportunity Frames (detail):")
    for frame, count in geo_data['opportunity_data']:
        pct = count / geo_data['frame_total'] * 100 if geo_data['frame_total'] > 0 else 0
        print(f"    - {frame:30} {count:3} ({pct:5.1f}%)")

    # =========================================================================
    # 4. ACTOR SENTIMENT ANALYSIS
    # =========================================================================
    actor_data = prepare_actor_sentiment_data(df)

    print("\n" + "-" * 50)
    print("4. ACTOR SENTIMENT ANALYSIS")
    print("-" * 50)

    print(f"\n  Total actors analyzed: {len(actor_data['all_actors'])}")
    print("\n  Top actors by mention count:")
    print(f"    {'Actor':<25} {'Total':>6} {'Pos':>5} {'Neg':>5} {'Net':>8}")
    print(f"    {'-'*25} {'-'*6} {'-'*5} {'-'*5} {'-'*8}")
    for a in actor_data['actors'][:15]:
        print(f"    {a['actor']:<25} {a['total']:>6} {a['positive']:>5} {a['negative']:>5} {a['net_sentiment']:>+8.2f}")

    # =========================================================================
    # 5. SPEECH ACT DISTRIBUTION
    # =========================================================================
    rhetorical_data = prepare_rhetorical_data(df)

    print("\n" + "-" * 50)
    print("5. SPEECH ACT DISTRIBUTION")
    print("-" * 50)

    total_acts = sum(rhetorical_data['speech_acts'].values())
    print(f"\n  Total speech acts: {total_acts}")
    print("\n  Distribution:")
    sorted_acts = sorted(rhetorical_data['speech_acts'].items(), key=lambda x: x[1], reverse=True)
    for act, count in sorted_acts:
        pct = count / total_acts * 100 if total_acts > 0 else 0
        bar = '#' * int(pct / 2)
        print(f"    {act:<15} {count:>4} ({pct:5.1f}%) {bar}")

    # =========================================================================
    # 6. EMOTIONAL REGISTER DISTRIBUTION
    # =========================================================================
    print("\n" + "-" * 50)
    print("6. EMOTIONAL REGISTER DISTRIBUTION")
    print("-" * 50)

    total_emo = sum(rhetorical_data['emotional_registers'].values())
    print(f"\n  Total tagged sentences: {total_emo}")
    print("\n  Distribution (with tone weights):")
    sorted_emo = sorted(rhetorical_data['emotional_registers'].items(), key=lambda x: x[1], reverse=True)
    for emo, count in sorted_emo:
        pct = count / total_emo * 100 if total_emo > 0 else 0
        weight = EMOTIONAL_REGISTER_WEIGHTS.get(emo, 0)
        bar = '#' * int(pct / 2)
        print(f"    {emo:<15} {count:>4} ({pct:5.1f}%) [w={weight:+.1f}] {bar}")

    # =========================================================================
    # 7. FRANCE POSITIONING (AGENCY PROFILE)
    # =========================================================================
    agency_data = prepare_agency_data(df)

    print("\n" + "-" * 50)
    print("7. FRANCE POSITIONING (AGENCY PROFILE)")
    print("-" * 50)

    print(f"\n  Agency Index: {agency_data['agency_index']:.4f} ({agency_data['agency_index']:.1%})")
    print("\n  Category breakdown:")
    print(f"    Active (ACTIVE_AGENT, LEADER, POWER, MODEL):     {agency_data['categories']['active']:>4}")
    print(f"    Cooperative (PARTNER, RELIABLE_ALLY):           {agency_data['categories']['cooperative']:>4}")
    print(f"    Reactive (REACTIVE_AGENT, VICTIM):              {agency_data['categories']['reactive']:>4}")

    total_pos = sum(agency_data['positioning_counts'].values())
    print(f"\n  Detailed positioning (n={total_pos}):")
    sorted_pos = sorted(agency_data['positioning_counts'].items(), key=lambda x: x[1], reverse=True)
    for pos, count in sorted_pos:
        pct = count / total_pos * 100 if total_pos > 0 else 0
        print(f"    {pos:<20} {count:>4} ({pct:5.1f}%)")

    # =========================================================================
    # 8. POLICY CONTENT ANALYSIS
    # =========================================================================
    policy_data = prepare_policy_data(df)

    print("\n" + "-" * 50)
    print("8. POLICY CONTENT ANALYSIS")
    print("-" * 50)

    if policy_data:
        print(f"\n  Policy Ambition Index: {policy_data['ambition_index']:.4f} ({policy_data['ambition_index']:.1%})")

        print("\n  Specificity distribution:")
        spec_total = sum(policy_data['specificity_counts'].values())
        for spec, count in sorted(policy_data['specificity_counts'].items(), key=lambda x: x[1], reverse=True):
            pct = count / spec_total * 100 if spec_total > 0 else 0
            print(f"    {spec:<15} {count:>4} ({pct:5.1f}%)")

        print("\n  Top policy domains:")
        sorted_domains = sorted(policy_data['domain_counts'].items(), key=lambda x: x[1], reverse=True)[:10]
        for domain, count in sorted_domains:
            print(f"    {domain:<35} {count:>4}")

        print("\n  Action type distribution:")
        for action, count in sorted(policy_data['action_counts'].items(), key=lambda x: x[1], reverse=True):
            print(f"    {action:<20} {count:>4}")
    else:
        print("\n  No policy content found.")

    print("\n" + "=" * 70)
    print("END OF COMPREHENSIVE ANALYSIS REPORT")
    print("=" * 70 + "\n")


def print_indices(df):
    """Print computed indices (legacy short version)."""
    indices = compute_all_indices(df)
    stats = compute_summary_stats(df)

    print(f"\nData: {stats['n_sentences']} sentences")
    print("\nKey Indices:")
    print(f"  Geopolitical Anxiety: {indices['geopolitical_anxiety']:+.2f}")
    print(f"  Agency:               {indices['agency']:.0%}")
    print(f"  Policy Ambition:      {indices['policy_ambition']:.0%}")
    print(f"  Diplomatic Tone:      {indices['diplomatic_tone']:+.2f}")
    print(f"  Action Orientation:   {indices['action_orientation']:.0%}")


def generate_fig1(lang=None):
    """Generate Figure 1: Dashboard."""
    from generate_fig1_dashboard import main as gen_fig1
    print("\n" + "-" * 50)
    print("Figure 1: Diplomatic Doctrine Dashboard")
    print("-" * 50)
    gen_fig1()


def generate_fig2(lang=None):
    """Generate Figure 2: Geopolitical Anxiety."""
    from generate_fig2_geopolitical import main as gen_fig2
    print("\n" + "-" * 50)
    print("Figure 2: Geopolitical Anxiety Index")
    print("-" * 50)
    gen_fig2()


def generate_fig3(lang=None):
    """Generate Figure 3: Actor Sentiment."""
    from generate_fig3_actor_sentiment import main as gen_fig3
    print("\n" + "-" * 50)
    print("Figure 3: Actor Sentiment Landscape")
    print("-" * 50)
    gen_fig3()


def generate_fig4(lang=None):
    """Generate Figure 4: Emotional Timeline."""
    from generate_fig4_emotional_timeline import main as gen_fig4
    print("\n" + "-" * 50)
    print("Figure 4: Emotional Timeline Infographic")
    print("-" * 50)
    gen_fig4()


def generate_fig5(lang=None):
    """Generate Figure 5: Policy Matrix."""
    from generate_fig5_policy_matrix import main as gen_fig5
    print("\n" + "-" * 50)
    print("Figure 5: Policy Ambition Matrix")
    print("-" * 50)
    gen_fig5()


def generate_fig6(lang=None):
    """Generate Figure 6: Rhetorical Strategy."""
    from generate_fig6_rhetorical_strategy import main as gen_fig6
    print("\n" + "-" * 50)
    print("Figure 6: Rhetorical Strategy")
    print("-" * 50)
    gen_fig6()


def generate_fig7(lang=None):
    """Generate Figure 7: Agency Profile."""
    from generate_fig7_agency_profile import main as gen_fig7
    print("\n" + "-" * 50)
    print("Figure 7: Agency Profile")
    print("-" * 50)
    gen_fig7()


def generate_fig8(lang=None):
    """Generate Figure 8: Diplomatic Positioning."""
    from generate_fig8_diplomatic_positioning import main as gen_fig8
    print("\n" + "-" * 50)
    print("Figure 8: Diplomatic Positioning")
    print("-" * 50)
    gen_fig8()


FIGURE_GENERATORS = {
    1: generate_fig1,
    2: generate_fig2,
    3: generate_fig3,
    4: generate_fig4,
    5: generate_fig5,
    6: generate_fig6,
    7: generate_fig7,
    8: generate_fig8,
}


def main():
    parser = argparse.ArgumentParser(description="Generate all analysis figures")
    parser.add_argument("--fig", type=int, choices=range(1, 9),
                       help="Generate specific figure (1-8)")
    parser.add_argument("--lang", choices=["fr", "en"],
                       help="Generate for specific language only")
    parser.add_argument("--full-report", action="store_true",
                       help="Print comprehensive analysis report")
    args = parser.parse_args()

    print_header()

    # Load data and show indices
    print("\nLoading data...")
    df = load_data()

    # Print full report if requested, otherwise short summary
    if args.full_report:
        print_full_analysis(df)
    else:
        print_indices(df)

    # Generate figures
    if args.fig:
        # Generate specific figure
        FIGURE_GENERATORS[args.fig](args.lang)
    else:
        # Generate all figures
        for fig_num in sorted(FIGURE_GENERATORS.keys()):
            FIGURE_GENERATORS[fig_num](args.lang)

    print("\n" + "=" * 70)
    print("DONE! All figures saved to output/figures/")
    print("  - HTML files: Ready for web integration")
    print("  - PNG files: Ready for presentations")
    print("=" * 70)


if __name__ == "__main__":
    main()
