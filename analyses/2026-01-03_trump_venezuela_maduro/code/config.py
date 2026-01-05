#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
config.py

MAIN OBJECTIVE:
---------------
Shared configuration for professional visualizations.
Consistent color palettes, fonts, and styling.

Author:
-------
Antoine Lemor
"""

import matplotlib.pyplot as plt
import matplotlib as mpl

# =============================================================================
# PROFESSIONAL STYLE CONFIGURATION
# =============================================================================

def setup_style():
    """Configure matplotlib for professional publication-quality figures."""

    plt.style.use('seaborn-v0_8-whitegrid')

    mpl.rcParams.update({
        # Figure
        'figure.figsize': (12, 7),
        'figure.dpi': 150,
        'figure.facecolor': 'white',
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.facecolor': 'white',

        # Font
        'font.family': 'sans-serif',
        'font.sans-serif': ['Helvetica Neue', 'Helvetica', 'Arial', 'DejaVu Sans'],
        'font.size': 11,
        'axes.titlesize': 14,
        'axes.titleweight': 'bold',
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,

        # Axes
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.linewidth': 0.8,
        'axes.edgecolor': '#333333',
        'axes.labelcolor': '#333333',
        'axes.titlepad': 15,

        # Grid
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linewidth': 0.5,

        # Ticks
        'xtick.color': '#333333',
        'ytick.color': '#333333',

        # Legend
        'legend.frameon': True,
        'legend.framealpha': 0.9,
        'legend.edgecolor': '#cccccc',
    })


# =============================================================================
# COLOR PALETTES
# =============================================================================

# Main accent colors
COLORS = {
    'primary': '#2563EB',      # Blue
    'secondary': '#7C3AED',    # Purple
    'success': '#059669',      # Green
    'warning': '#D97706',      # Orange
    'danger': '#DC2626',       # Red
    'neutral': '#6B7280',      # Gray
    'dark': '#1F2937',         # Dark gray
    'light': '#F3F4F6',        # Light gray
}

# Legitimation frame palette
LEGITIMATION_PALETTE = {
    'security_threat_neutralization': '#DC2626',  # Red
    'legal_procedural': '#2563EB',                 # Blue
    'economic_benefit': '#059669',                 # Green
    'humanitarian_liberation': '#7C3AED',          # Purple
    'competence_demonstration': '#D97706',         # Orange
    'historical_precedent': '#92400E',             # Brown
}

# Tone palette (warm = aggressive, cool = peaceful)
TONE_PALETTE = {
    'triumphant': '#F59E0B',      # Amber
    'threatening': '#DC2626',      # Red
    'confrontational': '#BE185D',  # Pink
    'dismissive': '#9333EA',       # Purple
    'factual': '#6B7280',          # Gray
    'reassuring': '#059669',       # Green
    'deferential': '#0891B2',      # Cyan
}

# Tone weights for rhetorical posture index
# Negative = aggressive, Positive = peaceful, 0 = neutral
TONE_WEIGHTS = {
    'threatening': -2.0,
    'confrontational': -1.5,
    'dismissive': -1.0,
    'triumphant': -0.5,
    'factual': 0.0,
    'reassuring': 1.0,
    'deferential': 1.5,
}

# Response type palette
RESPONSE_PALETTE = {
    'direct': '#059669',       # Green
    'partial': '#F59E0B',      # Amber
    'pivot': '#F97316',        # Orange
    'deflection': '#DC2626',   # Red
    'attack': '#7C3AED',       # Purple
}

# Theme palette
THEME_PALETTE = {
    'military_operation': '#1E40AF',
    'security_threat': '#DC2626',
    'diplomatic_relations': '#7C3AED',
    'governance': '#0891B2',
    'economic_resources': '#059669',
    'legal_justice': '#2563EB',
    'humanitarian': '#DB2777',
    'domestic_politics': '#F59E0B',
    'meta_communication': '#6B7280',
    'personal_narrative': '#92400E',
}


# =============================================================================
# LABELS
# =============================================================================

LABELS_EN = {
    # Legitimation
    'security_threat_neutralization': 'Security Threat',
    'legal_procedural': 'Legal/Justice',
    'economic_benefit': 'Economic Benefit',
    'humanitarian_liberation': 'Humanitarian',
    'competence_demonstration': 'Competence/Success',
    'historical_precedent': 'Historical Comparison',

    # Tone
    'triumphant': 'Triumphant',
    'threatening': 'Threatening',
    'confrontational': 'Confrontational',
    'dismissive': 'Dismissive',
    'factual': 'Factual',
    'reassuring': 'Reassuring',
    'deferential': 'Deferential',

    # Response
    'direct': 'Direct Answer',
    'partial': 'Partial Answer',
    'pivot': 'Topic Pivot',
    'deflection': 'Evasion',
    'attack': 'Attack',

    # Theme
    'military_operation': 'Military Operation',
    'security_threat': 'Security Threat',
    'diplomatic_relations': 'Diplomacy',
    'governance': 'Governance',
    'economic_resources': 'Economy/Oil',
    'legal_justice': 'Legal/Justice',
    'humanitarian': 'Humanitarian',
    'domestic_politics': 'Domestic Politics',
    'meta_communication': 'Press Conference',
    'personal_narrative': 'Personal',
}

LABELS_FR = {
    # Legitimation
    'security_threat_neutralization': 'Menace sécuritaire',
    'legal_procedural': 'Légal/Justice',
    'economic_benefit': 'Bénéfice économique',
    'humanitarian_liberation': 'Humanitaire',
    'competence_demonstration': 'Compétence/Succès',
    'historical_precedent': 'Comparaison historique',

    # Tone
    'triumphant': 'Triomphant',
    'threatening': 'Menaçant',
    'confrontational': 'Confrontationnel',
    'dismissive': 'Dédaigneux',
    'factual': 'Factuel',
    'reassuring': 'Rassurant',
    'deferential': 'Déférent',

    # Response
    'direct': 'Réponse directe',
    'partial': 'Réponse partielle',
    'pivot': 'Changement de sujet',
    'deflection': 'Évitement',
    'attack': 'Attaque',

    # Theme
    'military_operation': 'Opération militaire',
    'security_threat': 'Menace sécuritaire',
    'diplomatic_relations': 'Diplomatie',
    'governance': 'Gouvernance',
    'economic_resources': 'Économie/Pétrole',
    'legal_justice': 'Légal/Justice',
    'humanitarian': 'Humanitaire',
    'domestic_politics': 'Politique intérieure',
    'meta_communication': 'Conf. de presse',
    'personal_narrative': 'Personnel',
}


def get_labels(lang='en'):
    """Get label dictionary for specified language."""
    return LABELS_EN if lang == 'en' else LABELS_FR
