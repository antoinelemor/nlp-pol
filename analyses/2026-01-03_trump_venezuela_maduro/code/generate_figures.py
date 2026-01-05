#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_figures.py

MAIN OBJECTIVE:
---------------
Generate figures for the Trump Venezuela press conference analysis.
Produces 7 bilingual figures (EN/FR) from LLM-annotated discourse data.

Dependencies:
-------------
- pandas
- numpy
- matplotlib
- scipy
- pathlib
- json

MAIN FEATURES:
--------------
1) Fig 1: Rhetorical posture index by speaker (weighted tone average)
2) Fig 2: Posture evolution timeline (rolling average)
3) Fig 3: Response types distribution (direct/partial/pivot/deflection/attack)
4) Fig 4: Evasion analysis by topic
5) Fig 5: Progressive theme focus (journalist questions vs Trump responses)
6) Fig 6: Topic distribution by speaker
7) Fig 7: Us vs Them entity sentiment analysis (animosity index)

Author:
-------
Antoine Lemor
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

from load_and_validate import load_annotated_data, parse_labels_column
from config import (
    setup_style, COLORS, LEGITIMATION_PALETTE, TONE_PALETTE, TONE_WEIGHTS,
    RESPONSE_PALETTE, THEME_PALETTE, get_labels
)

setup_style()

# =============================================================================
# SPEAKER CONFIGURATION
# =============================================================================

# Known speakers and their roles
KNOWN_SPEAKERS = {
    'Trump': {'role': 'President', 'color': '#DC2626'},
    'Marco Rubio': {'role': 'Secretary of State', 'color': '#2563EB'},
    'Pete Hegseth': {'role': 'Secretary of Defense', 'color': '#059669'},
    'Dan Caine': {'role': 'Chairman Joint Chiefs', 'color': '#7C3AED'},
}

def get_speaker_type(speaker):
    """Classify speaker as official or journalist."""
    if speaker in KNOWN_SPEAKERS:
        return 'official'
    elif speaker.startswith('SPEAKER_'):
        return 'journalist'
    return 'unknown'

def is_journalist(row):
    """Check if row is from a journalist (using speaker_role annotation)."""
    return row.get('speaker_role') == 'journalist'

def is_trump(row):
    """Check if row is from Trump (must be political_leader, not journalist)."""
    return (row['speaker'] == 'Trump' and
            row.get('speaker_role') in ['political_leader', 'government_official'])

def is_official(row):
    """Check if row is from a government official (political_leader or government_official)."""
    return (row['speaker'] in KNOWN_SPEAKERS and
            row.get('speaker_role') in ['political_leader', 'government_official'])


# =============================================================================
# DATA LOADING
# =============================================================================

def load_data(filepath):
    df = load_annotated_data(filepath)
    df = parse_labels_column(df)
    # Add helper columns (speaker_role takes precedence over speaker name)
    df['is_journalist'] = df.apply(is_journalist, axis=1)
    df['is_trump'] = df.apply(is_trump, axis=1)
    df['is_official'] = df.apply(is_official, axis=1)
    return df


# Themes to exclude from analysis (meta/procedural)
EXCLUDED_THEMES = ['meta_communication']


def compute_posture_index(df, speaker=None):
    """
    Compute rhetorical posture index.
    Negative = aggressive, Positive = peaceful, 0 = neutral.
    Range: [-2, +1.5]
    """
    if speaker:
        # Filter by speaker name + official role (political_leader or government_official)
        data = df[(df['speaker'] == speaker) &
                  (df['speaker_role'].isin(['political_leader', 'government_official']))]
    else:
        data = df

    tones = data['tone'].dropna()
    if len(tones) == 0:
        return 0.0

    weights = [TONE_WEIGHTS.get(t, 0.0) for t in tones]
    return np.mean(weights)


# =============================================================================
# FIGURE 1: RHETORICAL POSTURE INDEX
# =============================================================================

def fig_posture_index(df, output_dir, lang='en'):
    """
    Rhetorical posture index visualization.
    Uses semicircle gauge charts with GridSpec layout.
    """
    from matplotlib.patches import Wedge, Rectangle, FancyBboxPatch
    import matplotlib.patches as mpatches

    main_speakers = ['Trump', 'Marco Rubio', 'Pete Hegseth', 'Dan Caine']

    # Compute index for each speaker
    indices = {s: compute_posture_index(df, s) for s in main_speakers}

    # =========================================================================
    #  FIGURE DESIGN
    # =========================================================================

    fig = plt.figure(figsize=(18, 10), facecolor='white')

    # GridSpec layout: 2x2 for speaker gauges + bottom row for comparison
    gs = fig.add_gridspec(2, 4, height_ratios=[1.1, 0.9], hspace=-0.15, wspace=0.25,
                          left=0.05, right=0.95, top=0.92, bottom=0.12)

    # Color palette based on posture value
    def get_posture_color(val):
        if val < -0.8:
            return '#B71C1C'   # Deep red (very aggressive)
        elif val < -0.4:
            return '#D32F2F'   # Red (aggressive)
        elif val < 0:
            return '#F57C00'   # Orange (slightly aggressive)
        else:
            return '#607D8B'   # Blue-grey (neutral)

    def get_posture_label(val, lang):
        if lang == 'en':
            if val < -0.5:
                return 'Aggressive'
            elif val < 0:
                return 'Slightly Aggressive'
            else:
                return 'Neutral'
        else:
            if val < -0.5:
                return 'Agressif'
            elif val < 0:
                return 'Légèrement agressif'
            else:
                return 'Neutre'

    # -------------------------------------------------------------------------
    # TOP ROW: Speaker Gauge Charts (semicircle style)
    # -------------------------------------------------------------------------
    for idx, speaker in enumerate(main_speakers):
        ax = fig.add_subplot(gs[0, idx])

        val = indices[speaker]
        color = get_posture_color(val)
        label = get_posture_label(val, lang)

        # Create semicircle gauge background
        # Scale: -2 to +1.5 mapped to 180° to 0°
        scale_min, scale_max = -2.0, 1.5
        angle_range = 180  # degrees

        # Background arc (gray)
        bg_wedge = Wedge((0, 0), 1, 0, 180, width=0.35,
                         facecolor='#E0E0E0', edgecolor='white', linewidth=2)
        ax.add_patch(bg_wedge)

        # Value arc (colored)
        # Map value to angle: -2 -> 180°, +1.5 -> 0°
        val_clamped = max(scale_min, min(scale_max, val))
        val_normalized = (val_clamped - scale_min) / (scale_max - scale_min)
        val_angle = 180 - (val_normalized * angle_range)

        if val >= 0:
            # Positive: arc from 90° (center) to val_angle
            wedge = Wedge((0, 0), 1, val_angle, 90, width=0.35,
                         facecolor=color, edgecolor='white', linewidth=2)
        else:
            # Negative: arc from val_angle to 90° (center)
            wedge = Wedge((0, 0), 1, 90, val_angle, width=0.35,
                         facecolor=color, edgecolor='white', linewidth=2)
        ax.add_patch(wedge)

        # Center line (neutral position at 0)
        ax.plot([0, 0], [0.55, 1.05], color='#333333', linewidth=2, zorder=5)

        # Value needle
        needle_angle = np.radians(val_angle)
        needle_x = 0.85 * np.cos(needle_angle)
        needle_y = 0.85 * np.sin(needle_angle)
        ax.annotate('', xy=(needle_x, needle_y), xytext=(0, 0),
                    arrowprops=dict(arrowstyle='->', color='#1a1a1a', lw=2.5))

        # Center circle
        center_circle = plt.Circle((0, 0), 0.15, color='#1a1a1a', zorder=10)
        ax.add_patch(center_circle)

        # Value text below gauge (lowered further)
        ax.text(0, -0.35, f'{val:+.2f}', ha='center', va='center',
                fontsize=36, fontweight='bold', color=color)
        ax.text(0, -0.58, label, ha='center', va='center',
                fontsize=18, fontweight='medium', color=color)

        # Speaker name and role
        role = KNOWN_SPEAKERS[speaker]['role']
        ax.set_title(speaker, fontsize=22, fontweight='bold',
                    color=KNOWN_SPEAKERS[speaker]['color'], pad=8)
        ax.text(0, 1.25, role, ha='center', va='center',
                fontsize=13, color='#666666', style='italic')

        # Scale labels
        ax.text(-1.1, 0.1, '-2', ha='center', fontsize=12, color='#999999')
        ax.text(0, 1.15, '0', ha='center', fontsize=12, color='#999999')
        ax.text(1.1, 0.1, '+1.5', ha='center', fontsize=12, color='#999999')

        ax.set_xlim(-1.4, 1.4)
        ax.set_ylim(-0.8, 1.3)
        ax.set_aspect('equal')
        ax.axis('off')

    # -------------------------------------------------------------------------
    # BOTTOM ROW: Horizontal Comparison Bar Chart
    # -------------------------------------------------------------------------
    ax_bar = fig.add_subplot(gs[1, :])

    y_pos = np.arange(len(main_speakers))
    values = [indices[s] for s in main_speakers]
    bar_colors = [get_posture_color(v) for v in values]

    # Reference lines
    ax_bar.axvline(x=0, color='#333333', linewidth=2, linestyle='-', zorder=1)
    ax_bar.axvline(x=-1, color='#E0E0E0', linewidth=1, linestyle='--', zorder=1)
    ax_bar.axvline(x=1, color='#E0E0E0', linewidth=1, linestyle='--', zorder=1)

    # Background zones
    ax_bar.axvspan(-2.2, 0, alpha=0.05, color=COLORS['danger'], zorder=0)
    ax_bar.axvspan(0, 1.7, alpha=0.05, color=COLORS['neutral'], zorder=0)

    # Bars
    bars = ax_bar.barh(y_pos, values, color=bar_colors, edgecolor='white',
                       height=0.55, linewidth=2, zorder=3)

    # Labels
    ax_bar.set_yticks(y_pos)
    ax_bar.set_yticklabels(main_speakers, fontsize=16, fontweight='bold')
    ax_bar.invert_yaxis()

    # Value annotations
    for bar, val in zip(bars, values):
        x_pos = val + 0.08 if val >= 0 else val - 0.08
        ha = 'left' if val >= 0 else 'right'
        ax_bar.text(x_pos, bar.get_y() + bar.get_height()/2,
                   f'{val:+.2f}', va='center', ha=ha, fontsize=16, fontweight='bold',
                   color=get_posture_color(val))

    ax_bar.set_xlim(-2.2, 1.7)

    # Spectrum labels (below the x-axis)
    if lang == 'en':
        ax_bar.text(-2.1, 4.3, 'AGGRESSIVE', ha='left', fontsize=16,
                   color=COLORS['danger'], fontweight='bold')
        ax_bar.text(1.6, 4.3, 'NEUTRAL', ha='right', fontsize=16,
                   color=COLORS['neutral'], fontweight='bold')
    else:
        ax_bar.text(-2.1, 4.3, 'AGRESSIF', ha='left', fontsize=16,
                   color=COLORS['danger'], fontweight='bold')
        ax_bar.text(1.6, 4.3, 'NEUTRE', ha='right', fontsize=16,
                   color=COLORS['neutral'], fontweight='bold')

    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_visible(False)
    ax_bar.spines['bottom'].set_color('#E0E0E0')
    ax_bar.spines['left'].set_visible(False)
    ax_bar.tick_params(left=False, colors='#666666')

    # -------------------------------------------------------------------------
    # Main titles and methodology note
    # -------------------------------------------------------------------------
    if lang == 'en':
        fig.suptitle('Rhetorical Posture Index by Speaker',
                     fontsize=24, fontweight='bold', y=0.99, color='#1a1a1a')
        fig.text(0.5, 0.945, 'Weighted average of tone annotations (−2 = aggressive, +1.5 = neutral)',
                ha='center', fontsize=14, color='#666666', style='italic')
        # Reading guide - prominent box
        note_text = ('Reading guide: Each sentence is annotated by LLM for tone (7 categories). Index = weighted average of all sentences.\n'
                    'Scale: threatening (−2), confrontational (−1.5), dismissive (−1), triumphant (−0.5), factual (0), reassuring (+1), deferential (+1.5).')
        fig.text(0.5, 0.035, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))
    else:
        fig.suptitle('Indice de posture rhétorique par locuteur',
                     fontsize=24, fontweight='bold', y=0.99, color='#1a1a1a')
        fig.text(0.5, 0.945, 'Moyenne pondérée des annotations de ton (−2 = agressif, +1.5 = neutre)',
                ha='center', fontsize=14, color='#666666', style='italic')
        # Guide de lecture - encadré visible
        note_text = ('Guide de lecture : Chaque phrase est annotée par LLM pour le ton (7 catégories). Indice = moyenne pondérée de toutes les phrases.\n'
                    'Échelle : menaçant (−2), confrontationnel (−1.5), dédaigneux (−1), triomphant (−0.5), factuel (0), rassurant (+1), déférent (+1.5).')
        fig.text(0.5, 0.035, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))

    fig.savefig(output_dir / f'fig1_posture_index_{lang}.png', dpi=300,
                bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"  fig1_posture_index_{lang}.png")


# =============================================================================
# FIGURE 2: POSTURE EVOLUTION TIMELINE
# =============================================================================

def fig_posture_timeline(df, output_dir, lang='en'):
    """
    Timeline visualization of rhetorical posture evolution.
    Features gradient coloring and speaker annotations.
    """
    from matplotlib.collections import LineCollection
    from matplotlib.patches import Rectangle

    # Limit to statements before Q&A (segment 399)
    df_timeline = df.iloc[:399].copy()
    df_timeline['tone_weight'] = df_timeline['tone'].map(TONE_WEIGHTS).fillna(0)
    df_timeline['position'] = range(len(df_timeline))

    # Rolling average (window of 15 sentences for smoothing)
    window = 15
    df_timeline['posture_smooth'] = df_timeline['tone_weight'].rolling(
        window=window, center=True, min_periods=5
    ).mean()

    # =========================================================================
    # FIGURE DESIGN
    # =========================================================================

    fig = plt.figure(figsize=(16, 8), facecolor='white')

    # Single full-width panel (no summary panel)
    ax_main = fig.add_subplot(111)

    # Color functions
    def get_line_color(val):
        if val < -0.5:
            return '#C62828'   # Red (aggressive)
        elif val < -0.2:
            return '#F57C00'   # Orange (slightly aggressive)
        else:
            return '#607D8B'   # Grey (neutral)

    # -------------------------------------------------------------------------
    # MAIN TIMELINE PANEL
    # -------------------------------------------------------------------------

    # Background gradient zones
    ax_main.axhspan(0, 1.5, alpha=0.06, color=COLORS['neutral'], zorder=0)
    ax_main.axhspan(-2, 0, alpha=0.06, color=COLORS['danger'], zorder=0)

    # Reference lines
    ax_main.axhline(y=0, color='#333333', linewidth=1.5, linestyle='-', alpha=0.4, zorder=1)
    ax_main.axhline(y=0.5, color='#E0E0E0', linewidth=0.8, linestyle='--', alpha=0.5, zorder=1)
    ax_main.axhline(y=-0.5, color='#E0E0E0', linewidth=0.8, linestyle='--', alpha=0.5, zorder=1)

    # Get valid data points
    valid = df_timeline['posture_smooth'].notna()
    x = df_timeline.loc[valid, 'position'].values
    y = df_timeline.loc[valid, 'posture_smooth'].values

    # Create colored line segments
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    colors_line = []
    for i in range(len(y) - 1):
        val = (y[i] + y[i+1]) / 2
        colors_line.append(get_line_color(val))

    lc = LineCollection(segments, colors=colors_line, linewidth=3.5, zorder=3,
                        capstyle='round', joinstyle='round')
    ax_main.add_collection(lc)

    # Add subtle fill under the curve
    ax_main.fill_between(x, y, 0, where=(y >= 0), alpha=0.15,
                         color=COLORS['neutral'], zorder=2)
    ax_main.fill_between(x, y, 0, where=(y < 0), alpha=0.15,
                         color=COLORS['danger'], zorder=2)

    # Speaker change annotations
    current_speaker = None
    speaker_changes = []
    for idx, row in df_timeline.iterrows():
        pos = row['position']
        speaker = row['speaker']

        if pos >= 352 and speaker != 'Marco Rubio':
            continue

        if speaker != current_speaker and speaker in KNOWN_SPEAKERS:
            speaker_changes.append({
                'position': pos,
                'speaker': speaker,
                'role': KNOWN_SPEAKERS[speaker]['role'],
                'color': KNOWN_SPEAKERS[speaker]['color']
            })
            current_speaker = speaker

    # Draw speaker regions with subtle background
    for i, change in enumerate(speaker_changes):
        next_pos = speaker_changes[i+1]['position'] if i+1 < len(speaker_changes) else len(df_timeline)
        ax_main.axvspan(change['position'], next_pos, alpha=0.03,
                       color=change['color'], zorder=0)

        # Vertical marker line
        ax_main.axvline(x=change['position'], color=change['color'], linewidth=2,
                       linestyle='-', alpha=0.6, zorder=2)

        # Speaker label (at top)
        ax_main.text(change['position'] + 3, 1.35, change['speaker'],
                    fontsize=9, fontweight='bold', color=change['color'],
                    ha='left', va='bottom', zorder=5)

    # Axis styling
    ax_main.set_xlim(0, len(df_timeline))
    ax_main.set_ylim(-1.6, 1.5)

    # Y-axis with labels
    ax_main.set_yticks([-1.5, -1, -0.5, 0, 0.5, 1, 1.5])

    if lang == 'en':
        ax_main.set_ylabel('Posture Index', fontsize=12, fontweight='medium', color='#333333')
        ax_main.set_xlabel('Statement Segment (before Q&A session)', fontsize=12,
                          fontweight='medium', color='#333333')
        # Zone labels
        ax_main.text(len(df_timeline) + 5, 0.75, 'NEUTRAL', fontsize=14, rotation=90,
                    va='center', ha='left', color=COLORS['neutral'], fontweight='bold')
        ax_main.text(len(df_timeline) + 5, -0.75, 'AGGRESSIVE', fontsize=14, rotation=90,
                    va='center', ha='left', color=COLORS['danger'], fontweight='bold')
    else:
        ax_main.set_ylabel('Indice de posture', fontsize=14, fontweight='medium', color='#333333')
        ax_main.set_xlabel('Segment de déclaration (avant session Q&R)', fontsize=14,
                          fontweight='medium', color='#333333')
        ax_main.text(len(df_timeline) + 5, 0.75, 'NEUTRE', fontsize=14, rotation=90,
                    va='center', ha='left', color=COLORS['neutral'], fontweight='bold')
        ax_main.text(len(df_timeline) + 5, -0.75, 'AGRESSIF', fontsize=14, rotation=90,
                    va='center', ha='left', color=COLORS['danger'], fontweight='bold')

    ax_main.spines['top'].set_visible(False)
    ax_main.spines['right'].set_visible(False)
    ax_main.spines['left'].set_color('#CCCCCC')
    ax_main.spines['bottom'].set_color('#CCCCCC')
    ax_main.tick_params(colors='#666666')
    ax_main.grid(True, axis='x', alpha=0.2, linestyle='-', linewidth=0.5)

    # Speaker legend at bottom right
    from matplotlib.patches import Patch
    legend_patches = [Patch(facecolor=info['color'], edgecolor='white',
                            label=speaker) for speaker, info in KNOWN_SPEAKERS.items()]
    ax_main.legend(handles=legend_patches, loc='lower right', frameon=True,
                   framealpha=0.9, edgecolor='#CCCCCC', fontsize=9)

    # -------------------------------------------------------------------------
    # Main titles and methodology note
    # -------------------------------------------------------------------------
    if lang == 'en':
        fig.suptitle('Rhetorical Posture Evolution During Press Conference',
                     fontsize=22, fontweight='bold', y=0.97, color='#1a1a1a')
        fig.text(0.5, 0.905, f'Rolling average (window = {window} sentences) of tone-weighted posture index',
                ha='center', fontsize=12, color='#666666', style='italic')
        # Reading guide - prominent box
        note_text = ('Reading guide: Smoothed curve (rolling avg. of 15 sentences) of posture index over time.\n'
                    'Below 0 = aggressive zone, above 0 = neutral zone. Vertical lines = speaker changes. Statements only (before Q&A).')
        fig.text(0.5, 0.03, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))
    else:
        fig.suptitle('Évolution de la posture rhétorique pendant la conférence',
                     fontsize=22, fontweight='bold', y=0.97, color='#1a1a1a')
        fig.text(0.5, 0.905, f'Moyenne glissante (fenêtre = {window} phrases) de l\'indice de posture pondéré',
                ha='center', fontsize=12, color='#666666', style='italic')
        # Guide de lecture - encadré visible
        note_text = ('Guide de lecture : Courbe lissée (moy. glissante de 15 phrases) de l\'indice de posture dans le temps.\n'
                    'Sous 0 = zone agressive, au-dessus de 0 = zone neutre. Lignes verticales = changements de locuteur. Déclarations uniquement (avant Q&R).')
        fig.text(0.5, 0.03, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))

    fig.savefig(output_dir / f'fig2_posture_timeline_{lang}.png', dpi=300,
                bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"  fig2_posture_timeline_{lang}.png")


# =============================================================================
# FIGURE 3: RESPONSE TYPES
# =============================================================================

def fig_response_types(df, output_dir, lang='en'):
    """
    Visualization of Trump's response patterns.
    Donut chart with detailed breakdown.
    """
    labels = get_labels(lang)

    # Trump responses to questions
    responses = df[df['is_trump'] &
                   (df['utterance_type'] == 'response') &
                   df['response_type'].notna() &
                   (df['response_type'] != 'null')]

    counts = responses['response_type'].value_counts()
    total = counts.sum()

    # Professional color palette
    pro_colors = {
        'direct': '#2E7D32',      # Deep green
        'partial': '#F9A825',     # Amber
        'pivot': '#E65100',       # Deep orange
        'deflection': '#C62828',  # Deep red
        'attack': '#6A1B9A',      # Purple
    }

    # Order by response quality (direct first)
    response_order = ['direct', 'partial', 'pivot', 'deflection', 'attack']
    ordered_types = [r for r in response_order if r in counts.index]
    ordered_counts = [counts[r] for r in ordered_types]
    ordered_colors = [pro_colors.get(r, COLORS['neutral']) for r in ordered_types]
    ordered_labels = [labels.get(r, r) for r in ordered_types]

    # Create figure with GridSpec
    fig = plt.figure(figsize=(14, 9), facecolor='white')
    gs = fig.add_gridspec(1, 2, width_ratios=[1.1, 1], wspace=0.15,
                          left=0.05, right=0.95, top=0.82, bottom=0.12)

    # --- Panel 1: Donut Chart ---
    ax1 = fig.add_subplot(gs[0])

    # Create donut
    wedges, texts, autotexts = ax1.pie(
        ordered_counts,
        colors=ordered_colors,
        autopct='%1.0f%%',
        startangle=90,
        pctdistance=0.75,
        wedgeprops=dict(width=0.5, edgecolor='white', linewidth=3),
        textprops={'fontsize': 12, 'fontweight': 'bold', 'color': 'white'}
    )

    # Style autotexts
    for autotext in autotexts:
        autotext.set_fontweight('bold')
        autotext.set_fontsize(11)

    # Center text
    center_text = f"{total}"
    if lang == 'en':
        center_label = "segments"
    else:
        center_label = "segments"

    ax1.text(0, 0.05, center_text, ha='center', va='center',
             fontsize=40, fontweight='bold', color='#1a1a1a')
    ax1.text(0, -0.15, center_label, ha='center', va='center',
             fontsize=14, color='#666666')

    # Legend below donut
    legend = ax1.legend(wedges, ordered_labels,
                        loc='upper center', bbox_to_anchor=(0.5, -0.02),
                        ncol=len(ordered_types), fontsize=12, frameon=False,
                        columnspacing=1.5)

    ax1.set_aspect('equal')

    # --- Panel 2: Horizontal Bar Breakdown ---
    ax2 = fig.add_subplot(gs[1])

    y_pos = np.arange(len(ordered_types))
    bar_height = 0.6

    # Calculate percentages
    pcts = [c / total * 100 for c in ordered_counts]

    # Draw bars
    bars = ax2.barh(y_pos, pcts, color=ordered_colors, height=bar_height,
                    edgecolor='white', linewidth=2, zorder=3)

    # Add percentage labels
    for bar, val, count in zip(bars, pcts, ordered_counts):
        # Inside bar for large values
        if val > 15:
            ax2.text(val - 2, bar.get_y() + bar.get_height()/2,
                    f'{val:.0f}%', ha='right', va='center',
                    fontsize=14, fontweight='bold', color='white', zorder=4)
        else:
            ax2.text(val + 1.5, bar.get_y() + bar.get_height()/2,
                    f'{val:.0f}%', ha='left', va='center',
                    fontsize=14, fontweight='bold', color='#333333', zorder=4)

        # Count annotation at the end
        ax2.text(max(pcts) * 1.08, bar.get_y() + bar.get_height()/2,
                f'n={count}', ha='left', va='center',
                fontsize=11, color='#888888', style='italic')

    # Y-axis labels
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(ordered_labels, fontsize=14, fontweight='medium', color='#333333')

    # X-axis
    ax2.set_xlim(0, max(pcts) * 1.25)
    ax2.set_xlabel('')

    # Add quality zones (background)
    ax2.axhspan(-0.5, 0.5, alpha=0.08, color='#2E7D32', zorder=0)  # Direct = good
    ax2.axhspan(0.5, 1.5, alpha=0.05, color='#F9A825', zorder=0)   # Partial = ok
    ax2.axhspan(1.5, len(ordered_types) - 0.5, alpha=0.05, color='#C62828', zorder=0)  # Rest = evasive

    # Subtle grid
    ax2.xaxis.grid(True, alpha=0.15, linestyle='-', linewidth=0.5, zorder=0)
    ax2.set_axisbelow(True)

    # Clean spines
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_color('#E5E5E5')
    ax2.spines['left'].set_visible(False)
    ax2.tick_params(left=False, bottom=True, colors='#999999', labelsize=9)

    # Panel title
    if lang == 'en':
        ax2.set_title('Response Quality Breakdown', fontsize=13, fontweight='bold',
                     pad=15, loc='left', color='#1a1a1a')
    else:
        ax2.set_title('Répartition par qualité de réponse', fontsize=13, fontweight='bold',
                     pad=15, loc='left', color='#1a1a1a')

    # Calculate key metrics
    direct_pct = counts.get('direct', 0) / total * 100 if total > 0 else 0
    evasive_pct = (counts.get('pivot', 0) + counts.get('deflection', 0)) / total * 100 if total > 0 else 0

    # Add insight box
    if lang == 'en':
        insight_text = f"Direct answers: {direct_pct:.0f}%\nEvasive responses: {evasive_pct:.0f}%"
    else:
        insight_text = f"Réponses directes: {direct_pct:.0f}%\nRéponses évasives: {evasive_pct:.0f}%"

    ax2.text(0.98, 0.02, insight_text, transform=ax2.transAxes,
            ha='right', va='bottom', fontsize=9, color='#666666',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#F5F5F5',
                     edgecolor='#E0E0E0', alpha=0.9))

    # Main title with more space
    if lang == 'en':
        fig.suptitle("How Did Trump Respond to Journalists' Questions?",
                     fontsize=20, fontweight='bold', y=0.98, color='#1a1a1a')
        fig.text(0.5, 0.92, 'Analysis of response patterns during Q&A session',
                ha='center', fontsize=11, color='#666666', style='italic')
        # Reading guide - prominent box
        note_text = ('Reading guide: Trump\'s response sentences during Q&A, classified by LLM into 5 types.\n'
                    'Direct = answers the question. Partial = incomplete answer. Pivot/deflection = avoids. Attack = criticizes questioner.')
        fig.text(0.5, 0.03, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))
    else:
        fig.suptitle('Comment Trump a-t-il répondu aux questions des journalistes ?',
                     fontsize=20, fontweight='bold', y=0.98, color='#1a1a1a')
        fig.text(0.5, 0.92, 'Analyse des patterns de réponse pendant la session Q&R',
                ha='center', fontsize=11, color='#666666', style='italic')
        # Guide de lecture - encadré visible
        note_text = ('Guide de lecture : Phrases de réponse de Trump pendant le Q&R, classées par LLM en 5 types.\n'
                    'Direct = répond à la question. Partiel = réponse incomplète. Pivot/évitement = esquive. Attaque = critique le questionneur.')
        fig.text(0.5, 0.03, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))

    # Save
    fig.savefig(output_dir / f'fig3_responses_{lang}.png', dpi=300,
                bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"  fig3_responses_{lang}.png")


# =============================================================================
# Q&A BLOCK EXTRACTION
# =============================================================================

def extract_qa_blocks(df):
    """
    Extract Q&A blocks: consecutive journalist questions + Trump responses.
    Returns list of blocks with aggregated themes and response metrics.
    """
    df_reset = df.reset_index(drop=True)
    qa_blocks = []

    i = 0
    while i < len(df_reset):
        row = df_reset.iloc[i]

        # Start of a question block?
        if row.get('speaker_role') == 'journalist' and row.get('utterance_type') == 'question':
            # Collect all consecutive journalist questions
            question_themes = []
            question_start = i

            while i < len(df_reset):
                r = df_reset.iloc[i]
                if r.get('speaker_role') == 'journalist' and r.get('utterance_type') == 'question':
                    theme = r.get('theme_primary')
                    if theme and theme not in EXCLUDED_THEMES:
                        question_themes.append(theme)
                    i += 1
                else:
                    break

            # Now collect Trump's responses until next journalist question
            trump_responses = []
            trump_themes = []

            while i < len(df_reset):
                r = df_reset.iloc[i]

                # New journalist question = end of this block
                if r.get('speaker_role') == 'journalist' and r.get('utterance_type') == 'question':
                    break

                # Trump speaking
                if (r['speaker'] == 'Trump' and
                    r.get('speaker_role') in ['political_leader', 'government_official'] and
                    r.get('utterance_type') in ['response', 'statement']):

                    resp_type = r.get('response_type')
                    resp_theme = r.get('theme_primary')

                    if resp_type and resp_type != 'null':
                        trump_responses.append(resp_type)
                    if resp_theme:
                        trump_themes.append(resp_theme)

                i += 1

            # Save this Q&A block
            if question_themes and trump_responses:
                qa_blocks.append({
                    'position': question_start,
                    'question_themes': question_themes,
                    'trump_themes': trump_themes,
                    'response_types': trump_responses,
                })
        else:
            i += 1

    return qa_blocks


def compute_directness_score(response_types):
    """Compute directness score from response types. Range: 0 (evasive) to 1 (direct)."""
    if not response_types:
        return 0.5

    scores = {
        'direct': 1.0,
        'partial': 0.5,
        'pivot': 0.0,
        'deflection': 0.0,
        'attack': 0.25,
    }
    return np.mean([scores.get(rt, 0.5) for rt in response_types])


# =============================================================================
# FIGURE 4: EVASION ANALYSIS BY TOPIC
# =============================================================================

def fig_evasion_by_topic(df, output_dir, lang='en'):
    """Analyze response type distribution by topic (questions asked to Trump)."""
    labels = get_labels(lang)

    # Extract Q&A blocks
    qa_blocks = extract_qa_blocks(df)

    if not qa_blocks:
        print(f"  Skipped fig4_evasion_{lang}.png (no Q&A blocks)")
        return

    # Build analysis data: for each block, distribute weight across question themes
    question_analyses = []
    for block in qa_blocks:
        q_themes = block['question_themes']
        resp_types = block['response_types']

        # Weight per question theme in this block
        theme_weight = 1.0 / len(q_themes) if q_themes else 0

        for q_theme in q_themes:
            # Weight per response type
            resp_weight = 1.0 / len(resp_types) if resp_types else 0
            for rt in resp_types:
                question_analyses.append({
                    'question_theme': q_theme,
                    'response_type': rt,
                    'weight': theme_weight * resp_weight
                })

    qa_df = pd.DataFrame(question_analyses)

    # Aggregate with weights
    theme_response = qa_df.groupby(['question_theme', 'response_type'])['weight'].sum().unstack(fill_value=0)
    theme_response.index.name = 'theme_primary'

    # Calculate total for sorting
    response_cols = [c for c in theme_response.columns if c in ['direct', 'partial', 'pivot', 'deflection', 'attack']]
    theme_response['total'] = theme_response[response_cols].sum(axis=1)

    # Include all themes with any data, sort by total mentions
    theme_response = theme_response[theme_response['total'] > 0]
    theme_response = theme_response.sort_values('total', ascending=True)

    if len(theme_response) == 0:
        print(f"  Skipped fig4_evasion_{lang}.png (not enough data)")
        return

    # Professional color palette
    response_colors = {
        'direct': '#2E7D32',      # Deep green
        'partial': '#F9A825',     # Amber
        'pivot': '#E65100',       # Deep orange
        'deflection': '#C62828',  # Deep red
        'attack': '#6A1B9A',      # Purple
    }

    # Create figure - single panel
    fig = plt.figure(figsize=(12, 8), facecolor='white')
    ax = fig.add_subplot(111)

    themes = theme_response.index
    n_themes = len(themes)
    y_pos = np.arange(n_themes)

    # Stacked bar of response types (horizontal)
    response_order = ['direct', 'partial', 'pivot', 'deflection', 'attack']
    response_order = [r for r in response_order if r in theme_response.columns]

    # Convert to percentages
    theme_pct = theme_response[response_order].div(theme_response['total'], axis=0) * 100

    left = np.zeros(n_themes)
    bar_height = 0.6

    for resp in response_order:
        if resp in theme_pct.columns:
            values = theme_pct[resp].values
            color = response_colors.get(resp, COLORS['neutral'])
            bars = ax.barh(y_pos, values, left=left, color=color,
                           label=labels.get(resp, resp), height=bar_height,
                           edgecolor='white', linewidth=1.5)

            # Add percentage labels inside bars if wide enough
            for i, (bar, val) in enumerate(zip(bars, values)):
                if val > 12:  # Only show if bar is wide enough
                    ax.text(left[i] + val/2, bar.get_y() + bar.get_height()/2,
                            f'{val:.0f}%', ha='center', va='center',
                            fontsize=12, fontweight='bold', color='white')
            left += values

    # Theme labels on y-axis
    ax.set_yticks(y_pos)
    theme_labels = [labels.get(t, t) for t in themes]
    ax.set_yticklabels(theme_labels, fontsize=13, fontweight='medium')

    ax.set_xlim(0, 100)
    ax.set_xlabel('')

    # Add subtle grid
    ax.xaxis.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)

    # Legend at bottom
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.08),
              ncol=len(response_order), fontsize=12, frameon=False,
              columnspacing=1.5)

    # Clean spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#CCCCCC')
    ax.spines['left'].set_visible(False)
    ax.tick_params(left=False, bottom=True, colors='#666666')

    # Main title with subtitle
    if lang == 'en':
        fig.suptitle('How Did Trump Respond to Questions by Topic?',
                     fontsize=20, fontweight='bold', y=0.96, color='#1a1a1a')
        fig.text(0.5, 0.90, 'Response type distribution by topic during Q&A session',
                ha='center', fontsize=11, color='#666666', style='italic')
        # Reading guide - prominent box
        note_text = ('Reading guide: For each topic asked by journalists, shows how Trump responded (% of response types).\n'
                    'Green = direct. Yellow = partial. Orange = pivot. Red = deflection. Purple = attack. Sorted by question volume.')
        fig.text(0.5, 0.03, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))
    else:
        fig.suptitle('Comment Trump a-t-il répondu aux questions par thème ?',
                     fontsize=20, fontweight='bold', y=0.96, color='#1a1a1a')
        fig.text(0.5, 0.90, 'Répartition des types de réponse par thème pendant la session Q&R',
                ha='center', fontsize=11, color='#666666', style='italic')
        # Guide de lecture - encadré visible
        note_text = ('Guide de lecture : Pour chaque thème demandé par les journalistes, montre comment Trump a répondu (% de types de réponse).\n'
                    'Vert = direct. Jaune = partiel. Orange = pivot. Rouge = évitement. Violet = attaque. Trié par volume de questions.')
        fig.text(0.5, 0.03, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))

    plt.tight_layout(rect=[0, 0.08, 1, 0.88])

    fig.savefig(output_dir / f'fig4_evasion_{lang}.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"  fig4_evasion_{lang}.png")


# =============================================================================
# FIGURE 5: PROGRESSIVE THEME FOCUS
# =============================================================================

def fig_progressive_analysis(df, output_dir, lang='en'):
    """
    Journalist vs Trump theme focus over Q&A session.
    Smoothed curves, clean design.
    """
    from scipy.interpolate import make_interp_spline
    labels = get_labels(lang)

    # Extract Q&A blocks
    qa_blocks = extract_qa_blocks(df)

    if len(qa_blocks) < 5:
        print(f"  Skipped fig5_progressive_{lang}.png (not enough Q&A blocks)")
        return

    # Build cumulative data
    all_themes = list(THEME_PALETTE.keys())

    journalist_themes_cum = {t: 0 for t in all_themes}
    trump_themes_cum = {t: 0 for t in all_themes}

    journalist_series = {t: [] for t in all_themes}
    trump_series = {t: [] for t in all_themes}

    for block in qa_blocks:
        for t in block['question_themes']:
            if t in journalist_themes_cum:
                journalist_themes_cum[t] += 1

        for t in block['trump_themes']:
            if t in trump_themes_cum:
                trump_themes_cum[t] += 1

        for t in all_themes:
            journalist_series[t].append(journalist_themes_cum[t])
            trump_series[t].append(trump_themes_cum[t])

    # Get all themes with data (sorted by final count)
    top_journalist = sorted(journalist_themes_cum.items(), key=lambda x: x[1], reverse=True)
    top_trump = sorted(trump_themes_cum.items(), key=lambda x: x[1], reverse=True)
    top_j_themes = [t[0] for t in top_journalist if t[1] > 0]
    top_t_themes = [t[0] for t in top_trump if t[1] > 0]

    # Smoothing function
    def smooth_curve(y_vals, x_vals, num_points=200):
        if len(x_vals) < 4:
            return x_vals, y_vals
        try:
            x_smooth = np.linspace(min(x_vals), max(x_vals), num_points)
            spl = make_interp_spline(x_vals, y_vals, k=3)
            y_smooth = spl(x_smooth)
            y_smooth = np.maximum(y_smooth, 0)  # No negative values
            return x_smooth, y_smooth
        except:
            return x_vals, y_vals

    x_raw = np.array(range(1, len(qa_blocks) + 1))

    # Create figure with professional styling
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    fig.patch.set_facecolor('white')

    # Custom color palette (more muted, professional) - all themes
    pro_colors = {
        'diplomatic_relations': '#4C78A8',
        'governance': '#54A24B',
        'military_operation': '#E45756',
        'security_threat': '#F58518',
        'legal_justice': '#72B7B2',
        'economic_resources': '#EECA3B',
        'humanitarian': '#B279A2',
        'domestic_politics': '#FF9DA6',
        'personal_narrative': '#9D755D',
        'historical_precedent': '#BAB0AC',
    }

    # --- Panel 1: Journalist Questions ---
    for theme in top_j_themes:
        y_raw = np.array(journalist_series[theme])
        x_smooth, y_smooth = smooth_curve(y_raw, x_raw)
        color = pro_colors.get(theme, COLORS['neutral'])

        # Smoothed line
        ax1.plot(x_smooth, y_smooth, '-', color=color, linewidth=2.5, alpha=0.9)
        # Subtle markers at actual data points
        ax1.scatter(x_raw, y_raw, color=color, s=30, alpha=0.6, zorder=5)
        # End label
        ax1.annotate(labels.get(theme, theme),
                     xy=(x_raw[-1], y_raw[-1]),
                     xytext=(8, 0), textcoords='offset points',
                     fontsize=11, fontweight='medium', color=color,
                     va='center')

    # Styling
    ax1.set_xlim(0.5, len(qa_blocks) + 5)
    ax1.set_ylim(0, max(journalist_themes_cum.values()) * 1.15)
    ax1.set_xlabel('Q&A Exchange' if lang == 'en' else 'Échange Q&R', fontsize=13, fontweight='medium')
    ax1.set_ylabel('Cumulative Mentions' if lang == 'en' else 'Mentions cumulées', fontsize=13, fontweight='medium')

    title1 = 'Journalist Questions' if lang == 'en' else 'Questions des journalistes'
    ax1.set_title(title1, fontsize=16, fontweight='bold', pad=15)

    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color('#CCCCCC')
    ax1.spines['bottom'].set_color('#CCCCCC')
    ax1.tick_params(colors='#666666', labelsize=11)
    ax1.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)

    # --- Panel 2: Trump Responses ---
    for theme in top_t_themes:
        y_raw = np.array(trump_series[theme])
        x_smooth, y_smooth = smooth_curve(y_raw, x_raw)
        color = pro_colors.get(theme, COLORS['neutral'])

        ax2.plot(x_smooth, y_smooth, '-', color=color, linewidth=2.5, alpha=0.9)
        ax2.scatter(x_raw, y_raw, color=color, s=30, alpha=0.6, zorder=5)
        ax2.annotate(labels.get(theme, theme),
                     xy=(x_raw[-1], y_raw[-1]),
                     xytext=(8, 0), textcoords='offset points',
                     fontsize=11, fontweight='medium', color=color,
                     va='center')

    ax2.set_xlim(0.5, len(qa_blocks) + 5)
    ax2.set_ylim(0, max(trump_themes_cum.values()) * 1.15)
    ax2.set_xlabel('Q&A Exchange' if lang == 'en' else 'Échange Q&R', fontsize=13, fontweight='medium')
    ax2.set_ylabel('Cumulative Mentions' if lang == 'en' else 'Mentions cumulées', fontsize=13, fontweight='medium')

    title2 = "Trump's Responses" if lang == 'en' else 'Réponses de Trump'
    ax2.set_title(title2, fontsize=16, fontweight='bold', pad=15)

    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color('#CCCCCC')
    ax2.spines['bottom'].set_color('#CCCCCC')
    ax2.tick_params(colors='#666666')
    ax2.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)

    # Main title
    if lang == 'en':
        fig.suptitle('Theme Focus Evolution During Q&A Session',
                     fontsize=18, fontweight='bold', y=1.02, color='#1a1a1a')
        # Reading guide - prominent box
        note_text = ('Reading guide: Left panel = themes (LLM-annotated) in journalist questions. Right panel = themes in Trump\'s responses.\n'
                    'Cumulative curves: topics accumulating over Q&A exchanges. Divergence between panels = thematic mismatch.')
        fig.text(0.5, -0.02, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))
    else:
        fig.suptitle('Évolution du focus thématique pendant la session Q&R',
                     fontsize=18, fontweight='bold', y=1.02, color='#1a1a1a')
        # Guide de lecture - encadré visible
        note_text = ('Guide de lecture : Panneau gauche = thèmes (annotés par LLM) des questions journalistes. Panneau droit = thèmes des réponses de Trump.\n'
                    'Courbes cumulatives : thèmes s\'accumulant au fil des échanges Q&R. Divergence entre panneaux = décalage thématique.')
        fig.text(0.5, -0.02, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))

    plt.tight_layout()
    fig.savefig(output_dir / f'fig5_progressive_{lang}.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"  fig5_progressive_{lang}.png")


# =============================================================================
# FIGURE 6: TOPICS BY SPEAKER
# =============================================================================

def fig_topics_by_speaker(df, output_dir, lang='en'):
    """
    Visualization of topic distribution by speaker.
    Shows proportions (%) of each speaker's interventions by theme.
    """
    labels = get_labels(lang)

    # Main speakers
    main_speakers = ['Trump', 'Marco Rubio', 'Pete Hegseth', 'Dan Caine']

    # Professional color palette for themes (consistent, muted)
    pro_colors = {
        'military_operation': '#1E3A5F',      # Dark blue
        'security_threat': '#DC2626',          # Red
        'diplomatic_relations': '#5B21B6',     # Purple
        'governance': '#0891B2',               # Cyan
        'economic_resources': '#059669',       # Green
        'legal_justice': '#2563EB',            # Blue
        'humanitarian': '#DB2777',             # Pink
        'domestic_politics': '#EA580C',        # Orange
        'personal_narrative': '#78716C',       # Stone
        'historical_precedent': '#92400E',     # Brown
    }

    # Collect data for all speakers
    speaker_data = {}
    all_themes = set()

    for speaker in main_speakers:
        data = df[(df['speaker'] == speaker) &
                  (df['speaker_role'].isin(['political_leader', 'government_official'])) &
                  (~df['theme_primary'].isin(EXCLUDED_THEMES)) &
                  (df['theme_primary'].notna())]
        counts = data['theme_primary'].value_counts()
        total = counts.sum()
        pcts = (counts / total * 100) if total > 0 else counts
        speaker_data[speaker] = pcts
        all_themes.update(pcts.index)

    # Get top themes across all speakers for consistent ordering
    theme_totals = {}
    for theme in all_themes:
        theme_totals[theme] = sum(speaker_data[s].get(theme, 0) for s in main_speakers)
    top_themes = sorted(theme_totals.keys(), key=lambda x: theme_totals[x], reverse=True)[:8]

    # Create figure
    fig = plt.figure(figsize=(16, 9), facecolor='white')

    # Use GridSpec for sophisticated layout
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.25,
                          left=0.08, right=0.92, top=0.88, bottom=0.08)

    for idx, speaker in enumerate(main_speakers):
        row, col = idx // 2, idx % 2
        ax = fig.add_subplot(gs[row, col])

        pcts = speaker_data[speaker]

        # Get themes in order (top themes first)
        ordered_themes = [t for t in top_themes if t in pcts.index]
        ordered_pcts = [pcts.get(t, 0) for t in ordered_themes]

        # Create horizontal bars
        y_pos = np.arange(len(ordered_themes))
        bar_height = 0.65

        # Gradient colors based on percentage
        colors = [pro_colors.get(t, COLORS['neutral']) for t in ordered_themes]

        bars = ax.barh(y_pos, ordered_pcts, color=colors, height=bar_height,
                       edgecolor='white', linewidth=1.5, zorder=3)

        # Add percentage labels
        for bar, val, theme in zip(bars, ordered_pcts, ordered_themes):
            if val > 3:  # Only show if bar is wide enough
                # Inside bar for large values
                if val > 15:
                    ax.text(val - 1.5, bar.get_y() + bar.get_height()/2,
                           f'{val:.0f}%', ha='right', va='center',
                           fontsize=12, fontweight='bold', color='white', zorder=4)
                else:
                    # Outside bar
                    ax.text(val + 1, bar.get_y() + bar.get_height()/2,
                           f'{val:.0f}%', ha='left', va='center',
                           fontsize=12, fontweight='bold', color='#333333', zorder=4)

        # Y-axis labels (theme names)
        ax.set_yticks(y_pos)
        ax.set_yticklabels([labels.get(t, t) for t in ordered_themes],
                          fontsize=12, fontweight='medium', color='#333333')

        # X-axis
        ax.set_xlim(0, max(ordered_pcts) * 1.2 if ordered_pcts else 50)
        ax.set_xlabel('')

        # Subtle grid
        ax.xaxis.grid(True, alpha=0.15, linestyle='-', linewidth=0.5, zorder=0)
        ax.set_axisbelow(True)

        # Clean spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#E5E5E5')
        ax.spines['left'].set_visible(False)
        ax.tick_params(left=False, bottom=True, colors='#999999', labelsize=11)

        # Speaker title with role and total count
        role = KNOWN_SPEAKERS[speaker]['role']
        total_interventions = int(speaker_data[speaker].sum() / 100 * df[(df['speaker'] == speaker) &
                  (df['speaker_role'].isin(['political_leader', 'government_official'])) &
                  (~df['theme_primary'].isin(EXCLUDED_THEMES))].shape[0]) if speaker in speaker_data else 0

        # Calculate actual total
        actual_total = df[(df['speaker'] == speaker) &
                         (df['speaker_role'].isin(['political_leader', 'government_official'])) &
                         (~df['theme_primary'].isin(EXCLUDED_THEMES)) &
                         (df['theme_primary'].notna())].shape[0]

        # Title with speaker color
        speaker_color = KNOWN_SPEAKERS[speaker]['color']
        ax.set_title(f'{speaker}', fontsize=13, fontweight='bold',
                    color=speaker_color, pad=12, loc='left')

        # Subtitle with role and n
        n_label = f'n = {actual_total}' if lang == 'en' else f'n = {actual_total}'
        ax.text(1.0, 1.02, f'{role} · {n_label}',
               transform=ax.transAxes, ha='right', fontsize=9,
               color='#666666', style='italic')

        # Add colored accent bar at top
        ax.axhline(y=len(ordered_themes) - 0.5 + 0.5, color=speaker_color,
                  linewidth=3, xmin=0, xmax=0.15, zorder=5, clip_on=False)

    # Main title
    if lang == 'en':
        fig.suptitle('Topic Distribution by Speaker',
                     fontsize=20, fontweight='bold', y=0.97, color='#1a1a1a')
        fig.text(0.5, 0.93, 'Proportion of each speaker\'s interventions by theme',
                ha='center', fontsize=11, color='#666666', style='italic')
        # Reading guide - prominent box
        note_text = ('Reading guide: Each bar = % of that speaker\'s sentences with that theme (LLM-annotated). Top 8 themes shown.\n'
                    'Shows what each official talked about most. n = total sentences analyzed for that speaker.')
        fig.text(0.5, 0.02, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))
    else:
        fig.suptitle('Distribution thématique par locuteur',
                     fontsize=20, fontweight='bold', y=0.97, color='#1a1a1a')
        fig.text(0.5, 0.93, 'Proportion des interventions de chaque locuteur par thème',
                ha='center', fontsize=11, color='#666666', style='italic')
        # Guide de lecture - encadré visible
        note_text = ('Guide de lecture : Chaque barre = % des phrases de ce locuteur avec ce thème (annoté par LLM). Top 8 thèmes affichés.\n'
                    'Montre de quoi chaque officiel a le plus parlé. n = total des phrases analysées pour ce locuteur.')
        fig.text(0.5, 0.02, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))

    # Save
    fig.savefig(output_dir / f'fig6_topics_speakers_{lang}.png', dpi=300,
                bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"  fig6_topics_speakers_{lang}.png")


# =============================================================================
# FIGURE 7: IN-GROUP VS OUT-GROUP ENTITY ANALYSIS
# =============================================================================

def fig_us_vs_them(df, output_dir, lang='en'):
    """
    Analyze in-group (US) vs out-group (foreign) entity portrayal.
    Computes sentiment scores and animosity index from entity valence.
    """
    from matplotlib.patches import Rectangle
    from collections import Counter

    # Filter to US officials only (Trump, Rubio, Hegseth)
    officials = df[
        (df['speaker'].isin(['Trump', 'Pete Hegseth', 'Marco Rubio'])) &
        (df['speaker_role'].isin(['political_leader', 'government_official']))
    ]

    # =================================================================
    # ENTITY NORMALIZATION - Merge variants into canonical forms
    # =================================================================
    ENTITY_NORMALIZATION = {
        # United States variants
        'United States': 'United States',
        'United States of America': 'United States',
        'U.S.': 'United States',
        'America': 'United States',
        'American': 'United States',
        'us': 'United States',
        'united states': 'United States',

        # Trump variants
        'Trump': 'Trump',
        'President Trump': 'Trump',
        'Trump administration': 'Trump Admin',
        'President': 'Trump',
        'President of the United States': 'Trump',

        # Maduro variants
        'Maduro': 'Maduro',
        'Nicolas Maduro': 'Maduro',
        'Maduro regime': 'Maduro',
        'Cecilia Maduro': 'Maduro',

        # Biden variants
        'Biden': 'Biden',
        'Joe Biden': 'Biden',
        'Biden administration': 'Biden Admin',
        'Joe Biden administration': 'Biden Admin',

        # Venezuela variants
        'Venezuela': 'Venezuela',
        'Venezuelan': 'Venezuela',
        'Venezuelans': 'Venezuela',
        'venezuela': 'Venezuela',
        'Venezuelan people': 'Venezuela',

        # Cuba variants
        'Cuba': 'Cuba',
        'Cubans': 'Cuba',
        'Havana': 'Cuba',

        # Rubio variants
        'Marco': 'Rubio',
        'Marco Rubio': 'Rubio',
        'Rubio': 'Rubio',
        'Secretary Rubio': 'Rubio',

        # Hegseth variants
        'Pete': 'Hegseth',
        'Pete Hegseth': 'Hegseth',
        'Hegseth': 'Hegseth',
        'Secretary Hegseth': 'Hegseth',

        # Kerry variants
        'Kerry': 'Kerry',
        'SECRETARY KERRY': 'Kerry',
        'Secretary Kerry': 'Kerry',

        # Washington variants
        'Washington': 'Washington',
        'Washington, D.C.': 'Washington',
        'Washington, DC': 'Washington',

        # Ukraine variants
        'Ukraine': 'Ukraine',
        'Kyiv': 'Ukraine',
        'Kiev': 'Ukraine',
        'Zelensky': 'Zelensky',

        # Witkoff variants
        'Witkoff': 'Witkoff',
        'Mr. Witkoff': 'Witkoff',

        # Military variants
        'United States military': 'US Military',
        'U.S. military': 'US Military',
        'our military': 'US Military',
        'United States Armed Forces': 'US Military',
        'National Guard': 'National Guard',
        'Air National Guard': 'National Guard',

        # Monroe Doctrine variants
        'Monroe Doctrine': 'Monroe Doctrine',
        'Donro Doctrine': 'Monroe Doctrine',

        # Raisin-Kane variants
        'Dan Raisin-Kane': 'Gen. Raisin-Kane',
        'Chairman Raisin-Kane': 'Gen. Raisin-Kane',
        'General Raisin Cane': 'Gen. Raisin-Kane',

        # Pompeo variants
        'Pompeo': 'Pompeo',
        'Secretary Pompeo': 'Pompeo',

        # Flores variants
        'Celia Flores': 'Celia Flores',
        'Flores': 'Celia Flores',

        # Nauert variants
        'Nauert': 'Nauert',
        'MS NAUERT': 'Nauert',

        # Department of War variants
        'Department of War': 'Dept. of War',
        'United States War Department': 'Dept. of War',
        'Secretary of War': 'Dept. of War',

        # Western Hemisphere variants
        'Western Hemisphere': 'Western Hemisphere',
        'Western hemisphere': 'Western Hemisphere',

        # Memphis variants
        'Memphis': 'Memphis',
        'Memphis, Tennessee': 'Memphis',
    }

    # =================================================================
    # ENTITY CLASSIFICATION
    # "US" = United States (nation, institutions, officials, places)
    # "THEM" = Rest of the world (all foreign entities)
    # =================================================================

    US_ENTITIES = {
        # US Country/Nation
        'United States',

        # US Officials (current administration)
        'Trump', 'Trump Admin', 'Rubio', 'Hegseth', 'Kerry',
        'Gen. Raisin-Kane', 'Pompeo', 'Jay Clayton', 'Witkoff', 'Nauert',

        # US Officials (past administration)
        'Biden', 'Biden Admin', 'Jimmy Carter',

        # US Military & Security
        'National Guard', 'US Military', 'Dept. of War',
        'US law enforcement', 'Midnight Hammer',
        'United States Marines', 'United States Navy', 'United States Air Force',
        'Joint Force', 'America\'s joint force', 'joint force', 'U.S. forces',
        'CIA', 'NSA', 'NGA', 'Space Comm', 'Cyber Comm',

        # US Government institutions
        'Congress', 'Department of Justice', 'Southern District of New York',
        'American justice',

        # US Geographic locations
        'Washington', 'New York', 'Los Angeles', 'Houston', 'Miami', 'Chicago',
        'New Orleans', 'Memphis', 'Florida', 'Louisiana', 'Tennessee', 'Colorado',

        # US Doctrine/Policy
        'Monroe Doctrine',

        # American people/victims
        'Jocelyn Nungary',

        # Media
        'Fox & Friends',
    }

    THEM_ENTITIES = {
        # Venezuela
        'Venezuela', 'Maduro', 'Celia Flores', 'Caracas', 'Machado',

        # Cuba
        'Cuba', 'Diaz-Canel',

        # Iran
        'Iran', 'Soleimani',

        # Russia
        'Russia', 'Putin',

        # Ukraine
        'Ukraine', 'Zelensky',

        # Other countries/regions
        'Afghanistan', 'Middle East', 'Argentina', 'Chile', 'Honduras',
        'Thailand', 'Cambodia', 'Lausanne', 'Colombia', 'China',
        'South America', 'Gustavo Petro',

        # International organizations
        'NATO', 'European Union',

        # Foreign criminal organizations
        'Tren de Aragua', 'Cartel de las Solas',

        # Foreign terrorists
        'al-Baghdadi',

        # Hemispheric references
        'Western Hemisphere',
    }

    # =================================================================
    # EXTRACT AND CLASSIFY ENTITIES
    # =================================================================
    us_data = {'positive': 0, 'neutral': 0, 'negative': 0}
    them_data = {'positive': 0, 'neutral': 0, 'negative': 0}
    us_entity_counts = Counter()
    them_entity_counts = Counter()
    unclassified_count = 0

    for ent_list in officials['entities_mentioned'].dropna():
        if isinstance(ent_list, str):
            try:
                ent_list = json.loads(ent_list)
            except:
                continue
        if isinstance(ent_list, list):
            for ent in ent_list:
                if isinstance(ent, dict):
                    raw_entity = ent.get('entity', '')
                    valence = ent.get('valence', 'neutral')

                    # Normalize entity name
                    entity = ENTITY_NORMALIZATION.get(raw_entity, raw_entity)

                    if entity in US_ENTITIES:
                        us_data[valence] += 1
                        us_entity_counts[entity] += 1
                    elif entity in THEM_ENTITIES:
                        them_data[valence] += 1
                        them_entity_counts[entity] += 1
                    else:
                        unclassified_count += 1

    # Calculate scores
    us_total = us_data['positive'] + us_data['neutral'] + us_data['negative']
    them_total = them_data['positive'] + them_data['neutral'] + them_data['negative']

    if us_total == 0 or them_total == 0:
        print(f"  Skipped fig7_us_vs_them_{lang}.png (insufficient data)")
        return

    # Sentiment scores: +1 = positive portrayal, -1 = negative portrayal
    us_score = (us_data['positive'] - us_data['negative']) / us_total
    them_score = (them_data['positive'] - them_data['negative']) / them_total

    # Animosity Index: NEGATIVE values indicate hostility/animosity toward out-group
    # Formula: (them_score - us_score) / 2
    # - Negative: praising us while demonizing them (hostile discourse)
    # - Positive: balanced or conciliatory toward them
    animosity_index = (them_score - us_score) / 2

    # =================================================================
    # FIGURE DESIGN
    # =================================================================

    fig = plt.figure(figsize=(16, 10), facecolor='white')

    # GridSpec layout: 2 rows, 3 columns
    gs = fig.add_gridspec(2, 3, height_ratios=[1.2, 1], width_ratios=[1.2, 0.5, 1.2],
                          hspace=0.35, wspace=0.2,
                          left=0.06, right=0.94, top=0.85, bottom=0.1)

    # Color palettes
    valence_colors = ['#2E7D32', '#78909C', '#C62828']  # green, grey, red
    us_accent = '#1565C0'
    them_accent = '#C62828'

    # -------------------------------------------------------------------------
    # PANEL 1: "US" Donut Chart (top-left)
    # -------------------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])

    us_vals = [us_data['positive'], us_data['neutral'], us_data['negative']]
    us_pcts = [v / us_total * 100 for v in us_vals]
    valence_labels = ['Positive', 'Neutral', 'Negative'] if lang == 'en' else ['Positif', 'Neutre', 'Négatif']

    wedges1, _ = ax1.pie(us_vals, colors=valence_colors, startangle=90,
                         wedgeprops=dict(width=0.35, edgecolor='white', linewidth=2))

    # Center score
    score_color = '#2E7D32' if us_score > 0 else '#C62828'
    ax1.text(0, 0.05, f'{us_score:+.2f}', ha='center', va='center',
             fontsize=26, fontweight='bold', color=score_color)
    ax1.text(0, -0.15, 'score', ha='center', va='center',
             fontsize=9, color='#666666')

    # Title
    title_us = '"US" - United States' if lang == 'en' else '"NOUS" - États-Unis'
    ax1.set_title(title_us, fontsize=15, fontweight='bold', color=us_accent, pad=15)

    # Legend outside donut (right side)
    for i, (label, pct, val) in enumerate(zip(valence_labels, us_pcts, us_vals)):
        y_pos = 0.3 - i * 0.25
        ax1.add_patch(Rectangle((1.15, y_pos - 0.08), 0.12, 0.12,
                                 facecolor=valence_colors[i], edgecolor='white',
                                 transform=ax1.transData, clip_on=False))
        ax1.text(1.35, y_pos, f'{label}: {pct:.0f}% (n={val})',
                 ha='left', va='center', fontsize=9, color='#333333',
                 transform=ax1.transData)

    ax1.set_xlim(-1.2, 2.0)
    ax1.set_ylim(-0.9, 0.9)

    # -------------------------------------------------------------------------
    # PANEL 2: Central Animosity Index (top-center)
    # -------------------------------------------------------------------------
    ax_center = fig.add_subplot(gs[0, 1])
    ax_center.axis('off')

    # Animosity index color and label (negative = hostile)
    if animosity_index < -0.4:
        idx_color = '#C62828'
        idx_label = 'High Animosity' if lang == 'en' else 'Animosité élevée'
    elif animosity_index < -0.2:
        idx_color = '#F57C00'
        idx_label = 'Moderate' if lang == 'en' else 'Modéré'
    elif animosity_index < 0:
        idx_color = '#FFA726'
        idx_label = 'Low' if lang == 'en' else 'Faible'
    else:
        idx_color = '#2E7D32'
        idx_label = 'Conciliatory' if lang == 'en' else 'Conciliant'

    # Box title
    box_title = 'ANIMOSITY\nINDEX' if lang == 'en' else 'INDICE\nD\'ANIMOSITE'
    ax_center.text(0.5, 0.92, box_title, ha='center', va='center',
                   fontsize=12, fontweight='bold', color='#333333',
                   transform=ax_center.transAxes)

    # Index value (enlarged)
    ax_center.text(0.5, 0.58, f'{animosity_index:+.2f}', ha='center', va='center',
                   fontsize=48, fontweight='bold', color=idx_color,
                   transform=ax_center.transAxes)

    # Interpretation label (prominent)
    ax_center.text(0.5, 0.32, idx_label, ha='center', va='center',
                   fontsize=13, fontweight='bold', color=idx_color,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                            edgecolor=idx_color, linewidth=1.5, alpha=0.9),
                   transform=ax_center.transAxes)

    # Scale (ASCII-compatible)
    ax_center.text(0.5, 0.15, '-1 <-- 0 --> +1', ha='center', va='center',
                   fontsize=10, color='#666666', fontfamily='monospace',
                   transform=ax_center.transAxes)
    scale_label = 'hostile              conciliatory' if lang == 'en' else 'hostile              conciliant'
    ax_center.text(0.5, 0.06, scale_label, ha='center', va='center',
                   fontsize=9, color='#888888', style='italic',
                   transform=ax_center.transAxes)

    # -------------------------------------------------------------------------
    # PANEL 3: "THEM" Donut Chart (top-right)
    # -------------------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 2])

    them_vals = [them_data['positive'], them_data['neutral'], them_data['negative']]
    them_pcts = [v / them_total * 100 for v in them_vals]

    wedges2, _ = ax2.pie(them_vals, colors=valence_colors, startangle=90,
                         wedgeprops=dict(width=0.35, edgecolor='white', linewidth=2))

    # Center score
    score_color = '#2E7D32' if them_score > 0 else '#C62828'
    ax2.text(0, 0.05, f'{them_score:+.2f}', ha='center', va='center',
             fontsize=26, fontweight='bold', color=score_color)
    ax2.text(0, -0.15, 'score', ha='center', va='center',
             fontsize=9, color='#666666')

    # Title
    title_them = '"THEM" - Foreign Entities' if lang == 'en' else '"EUX" - Entités étrangères'
    ax2.set_title(title_them, fontsize=15, fontweight='bold', color=them_accent, pad=15)

    # Legend outside donut (right side)
    for i, (label, pct, val) in enumerate(zip(valence_labels, them_pcts, them_vals)):
        y_pos = 0.3 - i * 0.25
        ax2.add_patch(Rectangle((1.15, y_pos - 0.08), 0.12, 0.12,
                                 facecolor=valence_colors[i], edgecolor='white',
                                 transform=ax2.transData, clip_on=False))
        ax2.text(1.35, y_pos, f'{label}: {pct:.0f}% (n={val})',
                 ha='left', va='center', fontsize=9, color='#333333',
                 transform=ax2.transData)

    ax2.set_xlim(-1.2, 2.0)
    ax2.set_ylim(-0.9, 0.9)

    # -------------------------------------------------------------------------
    # PANEL 4: Top US Entities (bottom-left)
    # -------------------------------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])

    top_us_data = us_entity_counts.most_common(6)
    if top_us_data:
        entities = [e for e, c in top_us_data]
        counts = [c for e, c in top_us_data]
        y_pos = np.arange(len(entities))

        bars = ax3.barh(y_pos, counts, color=us_accent, height=0.55,
                       edgecolor='white', linewidth=1.5, alpha=0.9)

        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(entities, fontsize=10)
        ax3.invert_yaxis()

        for bar, count in zip(bars, counts):
            ax3.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    str(count), ha='left', va='center', fontsize=10,
                    fontweight='bold', color=us_accent)

        ax3.set_xlim(0, max(counts) * 1.2)

    title3 = 'Top "US" Entities' if lang == 'en' else 'Principales entités "NOUS"'
    ax3.set_title(title3, fontsize=12, fontweight='bold', color=us_accent, pad=10)
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.spines['left'].set_visible(False)
    ax3.tick_params(left=False, colors='#666666')
    ax3.xaxis.grid(True, alpha=0.2)
    ax3.set_axisbelow(True)

    # -------------------------------------------------------------------------
    # PANEL 5: Top THEM Entities (bottom-right, spanning center+right)
    # -------------------------------------------------------------------------
    ax4 = fig.add_subplot(gs[1, 1:])

    top_them_data = them_entity_counts.most_common(6)
    if top_them_data:
        entities = [e for e, c in top_them_data]
        counts = [c for e, c in top_them_data]
        y_pos = np.arange(len(entities))

        bars = ax4.barh(y_pos, counts, color=them_accent, height=0.55,
                       edgecolor='white', linewidth=1.5, alpha=0.9)

        ax4.set_yticks(y_pos)
        ax4.set_yticklabels(entities, fontsize=10)
        ax4.invert_yaxis()

        for bar, count in zip(bars, counts):
            ax4.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    str(count), ha='left', va='center', fontsize=10,
                    fontweight='bold', color=them_accent)

        ax4.set_xlim(0, max(counts) * 1.2)

    title4 = 'Top "THEM" Entities' if lang == 'en' else 'Principales entités "EUX"'
    ax4.set_title(title4, fontsize=12, fontweight='bold', color=them_accent, pad=10)
    ax4.spines['top'].set_visible(False)
    ax4.spines['right'].set_visible(False)
    ax4.spines['left'].set_visible(False)
    ax4.tick_params(left=False, colors='#666666')
    ax4.xaxis.grid(True, alpha=0.2)
    ax4.set_axisbelow(True)

    # -------------------------------------------------------------------------
    # Main titles and methodology note
    # -------------------------------------------------------------------------
    total_mentions = us_total + them_total + unclassified_count

    if lang == 'en':
        fig.suptitle('"Us" vs "Them": Named Entity Sentiment Analysis',
                     fontsize=20, fontweight='bold', y=0.97, color='#1a1a1a')
        fig.text(0.5, 0.905, 'Named entities = people, countries, and institutions mentioned by name in the speech',
                ha='center', fontsize=14, color='#333333', fontweight='medium')
        # Methodology note - prominent box at bottom (two lines)
        note_text = ('Reading guide: Each named entity is classified as "US" (United States, officials, military) '
                    'or "THEM" (foreign: Venezuela, Maduro, Cuba...).\n'
                    'LLM annotates valence (positive/neutral/negative) per mention. Score = (positive − negative) / total. '
                    'Animosity < 0 = hostile to out-group.')
        fig.text(0.5, 0.035, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))
    else:
        fig.suptitle('"Nous" vs "Eux" : Analyse du sentiment des entités nommées',
                     fontsize=20, fontweight='bold', y=0.97, color='#1a1a1a')
        fig.text(0.5, 0.905, 'Entités nommées = personnes, pays et institutions mentionnés par leur nom dans le discours',
                ha='center', fontsize=14, color='#333333', fontweight='medium')
        # Methodology note - prominent box at bottom (two lines)
        note_text = ('Guide de lecture : Chaque entité nommée est classée "NOUS" (États-Unis, officiels, militaires) '
                    'ou "EUX" (étranger : Venezuela, Maduro, Cuba...).\n'
                    'Le LLM annote la valence (positif/neutre/négatif) par mention. Score = (positif − négatif) / total. '
                    'Animosité < 0 = hostile à l\'exogroupe.')
        fig.text(0.5, 0.035, note_text, ha='center', fontsize=11, color='#333333',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F0F0', edgecolor='#AAAAAA', linewidth=1.5))

    fig.savefig(output_dir / f'fig7_us_vs_them_{lang}.png', dpi=300,
                bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"  fig7_us_vs_them_{lang}.png")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("Generating figures (v2 - using speaker names)")
    print("=" * 60)

    # Use absolute paths based on script location
    script_dir = Path(__file__).parent
    data_path = script_dir / '../data/20260103_Trump_Venezuela.csv'
    output_dir = script_dir / '../output/figures'
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nLoading {data_path}...")
    df = load_data(data_path)

    # Quick stats
    print(f"\nData summary:")
    print(f"  Total rows: {len(df)}")
    print(f"  Trump: {df['is_trump'].sum()}")
    print(f"  Journalists: {df['is_journalist'].sum()}")

    for lang in ['en', 'fr']:
        print(f"\n--- {lang.upper()} ---")
        fig_posture_index(df, output_dir, lang)        # fig1
        fig_posture_timeline(df, output_dir, lang)     # fig2
        fig_response_types(df, output_dir, lang)       # fig3
        fig_evasion_by_topic(df, output_dir, lang)     # fig4
        fig_progressive_analysis(df, output_dir, lang) # fig5
        fig_topics_by_speaker(df, output_dir, lang)    # fig6
        fig_us_vs_them(df, output_dir, lang)           # fig7

    print("\n" + "=" * 60)
    print("Done!")


if __name__ == "__main__":
    main()
