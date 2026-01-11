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
Shared configuration for diplomatic discourse visualizations.
Palettes, fonts, and styling tailored for Macron Ambassadors Speech analysis.

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
    'primary': '#2563EB',      # Blue (France)
    'secondary': '#7C3AED',    # Purple
    'success': '#059669',      # Green
    'warning': '#D97706',      # Orange
    'danger': '#DC2626',       # Red
    'neutral': '#6B7280',      # Gray
    'dark': '#1F2937',         # Dark gray
    'light': '#F3F4F6',        # Light gray
    'france': '#0055A4',       # French blue
    'france_red': '#EF4135',   # French red
}

# Speech Act palette
SPEECH_ACT_PALETTE = {
    'STATING': '#6B7280',          # Gray - neutral observation
    'DIAGNOSING': '#F59E0B',       # Amber - analysis
    'DENOUNCING': '#DC2626',       # Red - criticism
    'PROPOSING': '#2563EB',        # Blue - action
    'EXHORTING': '#7C3AED',        # Purple - mobilization
    'REASSURING': '#059669',       # Green - confidence
    'FRAMING': '#64748B',          # Slate - meta
    'THANKING': '#10B981',         # Emerald - gratitude
    'WARNING': '#EA580C',          # Orange - alert
    'REJECTING': '#BE185D',        # Pink - refusal
    'COMMITTING': '#0891B2',       # Cyan - pledge
}

# Geopolitical Frame palette (warm = negative/threat, cool = positive/opportunity)
GEOPOLITICAL_FRAME_PALETTE = {
    # Threat frames (reds, oranges, purples)
    'DISORDER': '#DC2626',             # Red
    'POWER_POLITICS': '#B91C1C',       # Dark red
    'MULTILATERAL_DECLINE': '#F97316', # Orange
    'EXISTENTIAL_THREAT': '#7F1D1D',   # Very dark red
    'RECOLONIZATION': '#9333EA',       # Purple
    'FRAGMENTATION': '#E11D48',        # Rose
    'BRUTALIZATION': '#991B1B',        # Dark red
    'VASSALIZATION': '#6D28D9',        # Violet
    'REACTIONARY_INTERNATIONAL': '#7C3AED',  # Purple
    # Opportunity frames (greens, teals, blues)
    'OPPORTUNITY': '#059669',          # Green
    'RESILIENCE': '#0D9488',           # Teal
    'COOPERATION': '#10B981',          # Emerald
    'MULTILATERAL_RENEWAL': '#0891B2', # Cyan
    'PROGRESS': '#22C55E',             # Light green
    'SOLIDARITY': '#14B8A6',           # Teal
    'LEADERSHIP_OPPORTUNITY': '#2563EB', # Blue
    'STRATEGIC_ADVANTAGE': '#0EA5E9',  # Sky blue
    'REFORM_MOMENTUM': '#06B6D4',      # Cyan
    # Other
    'NONE': '#9CA3AF',                 # Gray
}

# France Positioning palette
FRANCE_POSITIONING_PALETTE = {
    'ACTIVE_AGENT': '#2563EB',     # Blue - proactive
    'REACTIVE_AGENT': '#F59E0B',   # Amber - responding
    'VICTIM': '#DC2626',           # Red - suffering
    'MODEL': '#8B5CF6',            # Violet - exemplary
    'PARTNER': '#10B981',          # Emerald - cooperative
    'LEADER': '#0055A4',           # French blue - leading
    'RELIABLE_ALLY': '#059669',    # Green - trustworthy
    'POWER': '#1E3A8A',            # Dark blue - strong
    'NOT_APPLICABLE': '#9CA3AF',   # Gray
}

# Emotional Register palette
EMOTIONAL_REGISTER_PALETTE = {
    'ALARMIST': '#DC2626',      # Red
    'COMBATIVE': '#EA580C',     # Orange
    'CONFIDENT': '#059669',     # Green
    'INDIGNANT': '#BE185D',     # Pink
    'PRAGMATIC': '#6B7280',     # Gray
    'SOLEMN': '#1F2937',        # Dark gray
    'DEFIANT': '#9333EA',       # Purple
    'GRATEFUL': '#10B981',      # Emerald
    'EXASPERATED': '#F97316',   # Orange
    'NEUTRAL': '#9CA3AF',       # Light gray
}

# Emotional register weights for diplomatic tone index
# Negative = alarm/combative, Positive = confident/calm
EMOTIONAL_REGISTER_WEIGHTS = {
    'ALARMIST': -2.0,
    'COMBATIVE': -1.5,
    'INDIGNANT': -1.5,
    'DEFIANT': -1.0,
    'EXASPERATED': -0.5,
    'PRAGMATIC': 0.0,
    'NEUTRAL': 0.0,
    'SOLEMN': 0.5,
    'GRATEFUL': 1.0,
    'CONFIDENT': 1.5,
}

# Temporality palette
TEMPORALITY_PALETTE = {
    'PAST_ACHIEVEMENT': '#059669',     # Green
    'PAST_DIAGNOSIS': '#0891B2',       # Cyan
    'PRESENT_CRISIS': '#DC2626',       # Red
    'PRESENT_OBSERVATION': '#6B7280',  # Gray
    'FUTURE_ACTION': '#2563EB',        # Blue
    'FUTURE_RISK': '#F97316',          # Orange
    'CONTINUITY': '#8B5CF6',           # Violet
    'RUPTURE': '#E11D48',              # Rose
    'ATEMPORAL': '#9CA3AF',            # Light gray
}

# Policy Domain palette (grouped by category)
POLICY_DOMAIN_PALETTE = {
    # Defense & Security
    'DEFENSE_MILITARY': '#1E3A8A',
    'STRATEGIC_AUTONOMY': '#1D4ED8',
    'PEACEKEEPING_OPERATIONS': '#3B82F6',
    'NUCLEAR_DETERRENCE': '#0F172A',
    'DEFENSE_INDUSTRY': '#1E40AF',
    # Economic & Development
    'DEVELOPMENT_AID': '#059669',
    'TRADE_POLICY': '#10B981',
    'ECONOMIC_PARTNERSHIPS': '#34D399',
    'DEVELOPMENT_FINANCE_REFORM': '#047857',
    'SANCTIONS_POLICY': '#065F46',
    # International Governance
    'UN_REFORM': '#7C3AED',
    'SECURITY_COUNCIL': '#6D28D9',
    'MULTILATERAL_INSTITUTIONS': '#8B5CF6',
    'GLOBAL_GOVERNANCE_ARCHITECTURE': '#5B21B6',
    'INTERNATIONAL_LAW': '#4C1D95',
    # European Affairs
    'EUROPEAN_INTEGRATION': '#2563EB',
    'EUROPEAN_SOVEREIGNTY': '#1D4ED8',
    'EUROPEAN_DEFENSE': '#1E40AF',
    'EUROPEAN_ECONOMY': '#3B82F6',
    # Regional & Bilateral
    'AFRICA_RELATIONS': '#D97706',
    'EMERGING_POWERS_RELATIONS': '#F59E0B',
    'TRANSATLANTIC_RELATIONS': '#0891B2',
    'INDO_PACIFIC_POLICY': '#06B6D4',
    'MIDDLE_EAST_POLICY': '#EA580C',
    'UKRAINE_SUPPORT': '#FBBF24',
    'RUSSIA_POLICY': '#DC2626',
    # Cross-cutting
    'INFORMATION_WARFARE': '#9333EA',
    'SCIENCE_TECHNOLOGY': '#6366F1',
    'CULTURAL_INFLUENCE': '#A855F7',
    'COUNTER_NEOCOLONIALISM': '#7C3AED',
    'DIPLOMATIC_METHOD': '#64748B',
    'ALLIANCE_MANAGEMENT': '#475569',
    'CLIMATE_ENVIRONMENT': '#22C55E',
}

# Stance Type palette
STANCE_TYPE_PALETTE = {
    'CRITICISM': '#DC2626',
    'SUPPORT': '#059669',
    'AMBIVALENT': '#F59E0B',
    'DISTANCING': '#9333EA',
    'CALL_FOR_ACTION': '#2563EB',
    'DEFENSE': '#0891B2',
    'CONDITIONAL_SUPPORT': '#10B981',
    'REFRAMING': '#7C3AED',
}

# Actor Valence palette
ACTOR_VALENCE_PALETTE = {
    'POSITIVE': '#059669',
    'NEUTRAL': '#6B7280',
    'NEGATIVE': '#DC2626',
    'AMBIGUOUS': '#F59E0B',
}


# =============================================================================
# LABELS (ENGLISH & FRENCH)
# =============================================================================

LABELS_EN = {
    # Speech Acts
    'STATING': 'Stating',
    'DIAGNOSING': 'Diagnosing',
    'DENOUNCING': 'Denouncing',
    'PROPOSING': 'Proposing',
    'EXHORTING': 'Exhorting',
    'REASSURING': 'Reassuring',
    'FRAMING': 'Framing',
    'THANKING': 'Thanking',
    'WARNING': 'Warning',
    'REJECTING': 'Rejecting',
    'COMMITTING': 'Committing',

    # Geopolitical Frames - Threat
    'DISORDER': 'World Disorder',
    'POWER_POLITICS': 'Power Politics',
    'MULTILATERAL_DECLINE': 'Multilateral Decline',
    'EXISTENTIAL_THREAT': 'Existential Threat',
    'RECOLONIZATION': 'Recolonization',
    'FRAGMENTATION': 'Fragmentation',
    'BRUTALIZATION': 'Brutalization',
    'VASSALIZATION': 'Vassalization',
    'REACTIONARY_INTERNATIONAL': 'Reactionary Intl.',
    # Geopolitical Frames - Opportunity
    'OPPORTUNITY': 'Opportunity',
    'RESILIENCE': 'Resilience',
    'COOPERATION': 'Cooperation',
    'MULTILATERAL_RENEWAL': 'Multilateral Renewal',
    'PROGRESS': 'Progress',
    'SOLIDARITY': 'Solidarity',
    'LEADERSHIP_OPPORTUNITY': 'Leadership Opportunity',
    'STRATEGIC_ADVANTAGE': 'Strategic Advantage',
    'REFORM_MOMENTUM': 'Reform Momentum',
    'NONE': 'None',

    # France Positioning
    'ACTIVE_AGENT': 'Active Agent',
    'REACTIVE_AGENT': 'Reactive Agent',
    'VICTIM': 'Victim',
    'MODEL': 'Model/Exemplar',
    'PARTNER': 'Partner',
    'LEADER': 'Leader',
    'RELIABLE_ALLY': 'Reliable Ally',
    'POWER': 'Power',
    'NOT_APPLICABLE': 'N/A',

    # Emotional Register
    'ALARMIST': 'Alarmist',
    'COMBATIVE': 'Combative',
    'CONFIDENT': 'Confident',
    'INDIGNANT': 'Indignant',
    'PRAGMATIC': 'Pragmatic',
    'SOLEMN': 'Solemn',
    'DEFIANT': 'Defiant',
    'GRATEFUL': 'Grateful',
    'EXASPERATED': 'Exasperated',
    'NEUTRAL': 'Neutral',

    # Temporality
    'PAST_ACHIEVEMENT': 'Past Achievement',
    'PAST_DIAGNOSIS': 'Past Diagnosis',
    'PRESENT_CRISIS': 'Present Crisis',
    'PRESENT_OBSERVATION': 'Present Observation',
    'FUTURE_ACTION': 'Future Action',
    'FUTURE_RISK': 'Future Risk',
    'CONTINUITY': 'Continuity',
    'RUPTURE': 'Rupture',
    'ATEMPORAL': 'Atemporal',

    # Policy Domains (abbreviated)
    'DEFENSE_MILITARY': 'Defense/Military',
    'STRATEGIC_AUTONOMY': 'Strategic Autonomy',
    'PEACEKEEPING_OPERATIONS': 'Peacekeeping',
    'NUCLEAR_DETERRENCE': 'Nuclear',
    'DEFENSE_INDUSTRY': 'Defense Industry',
    'DEVELOPMENT_AID': 'Development Aid',
    'TRADE_POLICY': 'Trade Policy',
    'ECONOMIC_PARTNERSHIPS': 'Economic Partners',
    'DEVELOPMENT_FINANCE_REFORM': 'Dev. Finance Reform',
    'SANCTIONS_POLICY': 'Sanctions',
    'UN_REFORM': 'UN Reform',
    'SECURITY_COUNCIL': 'Security Council',
    'MULTILATERAL_INSTITUTIONS': 'Multilateral Inst.',
    'GLOBAL_GOVERNANCE_ARCHITECTURE': 'Global Governance',
    'INTERNATIONAL_LAW': 'Intl. Law',
    'EUROPEAN_INTEGRATION': 'EU Integration',
    'EUROPEAN_SOVEREIGNTY': 'EU Sovereignty',
    'EUROPEAN_DEFENSE': 'EU Defense',
    'EUROPEAN_ECONOMY': 'EU Economy',
    'AFRICA_RELATIONS': 'Africa Relations',
    'EMERGING_POWERS_RELATIONS': 'Emerging Powers',
    'TRANSATLANTIC_RELATIONS': 'Transatlantic',
    'INDO_PACIFIC_POLICY': 'Indo-Pacific',
    'MIDDLE_EAST_POLICY': 'Middle East',
    'UKRAINE_SUPPORT': 'Ukraine Support',
    'RUSSIA_POLICY': 'Russia Policy',
    'INFORMATION_WARFARE': 'Info Warfare',
    'SCIENCE_TECHNOLOGY': 'Science/Tech',
    'CULTURAL_INFLUENCE': 'Cultural Influence',
    'COUNTER_NEOCOLONIALISM': 'Counter Neo-colonialism',
    'DIPLOMATIC_METHOD': 'Diplomatic Method',
    'ALLIANCE_MANAGEMENT': 'Alliance Mgmt.',
    'CLIMATE_ENVIRONMENT': 'Climate/Environment',

    # Stance Types
    'CRITICISM': 'Criticism',
    'SUPPORT': 'Support',
    'AMBIVALENT': 'Ambivalent',
    'DISTANCING': 'Distancing',
    'CALL_FOR_ACTION': 'Call for Action',
    'DEFENSE': 'Defense',
    'CONDITIONAL_SUPPORT': 'Conditional Support',
    'REFRAMING': 'Reframing',

    # Actor Valence
    'POSITIVE': 'Positive',
    'NEUTRAL': 'Neutral',
    'NEGATIVE': 'Negative',
    'AMBIGUOUS': 'Ambiguous',
}

LABELS_FR = {
    # Speech Acts
    'STATING': 'Constat',
    'DIAGNOSING': 'Diagnostic',
    'DENOUNCING': 'Dénonciation',
    'PROPOSING': 'Proposition',
    'EXHORTING': 'Exhortation',
    'REASSURING': 'Rassurer',
    'FRAMING': 'Cadrage',
    'THANKING': 'Remerciement',
    'WARNING': 'Mise en garde',
    'REJECTING': 'Rejet',
    'COMMITTING': 'Engagement',

    # Geopolitical Frames - Threat
    'DISORDER': 'Désordre mondial',
    'POWER_POLITICS': 'Politique de puissance',
    'MULTILATERAL_DECLINE': 'Déclin multilatéral',
    'EXISTENTIAL_THREAT': 'Menace existentielle',
    'RECOLONIZATION': 'Recolonisation',
    'FRAGMENTATION': 'Fragmentation',
    'BRUTALIZATION': 'Brutalisation',
    'VASSALIZATION': 'Vassalisation',
    'REACTIONARY_INTERNATIONAL': 'Internationale réact.',
    # Geopolitical Frames - Opportunity
    'OPPORTUNITY': 'Opportunité',
    'RESILIENCE': 'Résilience',
    'COOPERATION': 'Coopération',
    'MULTILATERAL_RENEWAL': 'Renouveau multilatéral',
    'PROGRESS': 'Progrès',
    'SOLIDARITY': 'Solidarité',
    'LEADERSHIP_OPPORTUNITY': 'Opportunité de leadership',
    'STRATEGIC_ADVANTAGE': 'Avantage stratégique',
    'REFORM_MOMENTUM': 'Élan de réforme',
    'NONE': 'Aucun',

    # France Positioning
    'ACTIVE_AGENT': 'Agent actif',
    'REACTIVE_AGENT': 'Agent réactif',
    'VICTIM': 'Victime',
    'MODEL': 'Modèle/Exemple',
    'PARTNER': 'Partenaire',
    'LEADER': 'Leader',
    'RELIABLE_ALLY': 'Allié fiable',
    'POWER': 'Puissance',
    'NOT_APPLICABLE': 'N/A',

    # Emotional Register
    'ALARMIST': 'Alarmiste',
    'COMBATIVE': 'Combatif',
    'CONFIDENT': 'Confiant',
    'INDIGNANT': 'Indigné',
    'PRAGMATIC': 'Pragmatique',
    'SOLEMN': 'Solennel',
    'DEFIANT': 'Défiant',
    'GRATEFUL': 'Reconnaissant',
    'EXASPERATED': 'Exaspéré',
    'NEUTRAL': 'Neutre',

    # Temporality
    'PAST_ACHIEVEMENT': 'Réalisation passée',
    'PAST_DIAGNOSIS': 'Diagnostic passé',
    'PRESENT_CRISIS': 'Crise présente',
    'PRESENT_OBSERVATION': 'Observation présente',
    'FUTURE_ACTION': 'Action future',
    'FUTURE_RISK': 'Risque futur',
    'CONTINUITY': 'Continuité',
    'RUPTURE': 'Rupture',
    'ATEMPORAL': 'Atemporel',

    # Policy Domains (abbreviated)
    'DEFENSE_MILITARY': 'Défense/Militaire',
    'STRATEGIC_AUTONOMY': 'Autonomie stratégique',
    'PEACEKEEPING_OPERATIONS': 'Maintien de la paix',
    'NUCLEAR_DETERRENCE': 'Nucléaire',
    'DEFENSE_INDUSTRY': 'Industrie défense',
    'DEVELOPMENT_AID': 'Aide au développement',
    'TRADE_POLICY': 'Politique commerciale',
    'ECONOMIC_PARTNERSHIPS': 'Partenariats éco.',
    'DEVELOPMENT_FINANCE_REFORM': 'Réforme fin. dév.',
    'SANCTIONS_POLICY': 'Sanctions',
    'UN_REFORM': 'Réforme ONU',
    'SECURITY_COUNCIL': 'Conseil de sécurité',
    'MULTILATERAL_INSTITUTIONS': 'Inst. multilatérales',
    'GLOBAL_GOVERNANCE_ARCHITECTURE': 'Gouv. mondiale',
    'INTERNATIONAL_LAW': 'Droit international',
    'EUROPEAN_INTEGRATION': 'Intégration UE',
    'EUROPEAN_SOVEREIGNTY': 'Souveraineté UE',
    'EUROPEAN_DEFENSE': 'Défense UE',
    'EUROPEAN_ECONOMY': 'Économie UE',
    'AFRICA_RELATIONS': 'Relations Afrique',
    'EMERGING_POWERS_RELATIONS': 'Puissances émergentes',
    'TRANSATLANTIC_RELATIONS': 'Transatlantique',
    'INDO_PACIFIC_POLICY': 'Indo-Pacifique',
    'MIDDLE_EAST_POLICY': 'Moyen-Orient',
    'UKRAINE_SUPPORT': 'Soutien Ukraine',
    'RUSSIA_POLICY': 'Politique Russie',
    'INFORMATION_WARFARE': 'Guerre info.',
    'SCIENCE_TECHNOLOGY': 'Science/Tech',
    'CULTURAL_INFLUENCE': 'Influence culturelle',
    'COUNTER_NEOCOLONIALISM': 'Contre néo-colonialisme',
    'DIPLOMATIC_METHOD': 'Méthode diplomatique',
    'ALLIANCE_MANAGEMENT': 'Gestion alliances',
    'CLIMATE_ENVIRONMENT': 'Climat/Environnement',

    # Stance Types
    'CRITICISM': 'Critique',
    'SUPPORT': 'Soutien',
    'AMBIVALENT': 'Ambivalent',
    'DISTANCING': 'Distanciation',
    'CALL_FOR_ACTION': 'Appel à l\'action',
    'DEFENSE': 'Défense',
    'CONDITIONAL_SUPPORT': 'Soutien conditionnel',
    'REFRAMING': 'Recadrage',

    # Actor Valence
    'POSITIVE': 'Positif',
    'NEUTRAL': 'Neutre',
    'NEGATIVE': 'Négatif',
    'AMBIGUOUS': 'Ambigu',
}


def get_labels(lang='en'):
    """Get label dictionary for specified language."""
    return LABELS_EN if lang == 'en' else LABELS_FR


# =============================================================================
# ACTOR CATEGORIES (for grouping in visualizations)
# =============================================================================

ACTOR_CATEGORIES = {
    'FRANCE_ALLIES': {
        'France', 'Europe', 'UE', 'European Union', 'Allemagne', 'Germany',
        'G7', 'NATO', 'OTAN', 'Occidentaux', 'Ambassadeurs', 'FINUL'
    },
    'MAJOR_POWERS': {
        'États-Unis', 'United States', 'Chine', 'China', 'Russie', 'Russia'
    },
    'REGIONAL_ACTORS': {
        'Afrique', 'Africa', 'Indo-Pacifique', 'Moyen-Orient', 'Middle East',
        'Ukraine', 'Iran', 'Liban', 'Lebanon', 'Israel', 'Palestine'
    },
    'INTERNATIONAL_ORG': {
        'ONU', 'UN', 'BRICS', 'G20', 'AFD'
    },
    'IDEOLOGICAL': {
        'Sud global', 'Global South', 'pays émergents'
    }
}
