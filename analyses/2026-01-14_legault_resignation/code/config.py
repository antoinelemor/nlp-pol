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
Configuration file for the Legault Resignation Speech analysis.
Contains color palettes, bilingual labels (FR/EN), and constants.

Dependencies:
-------------
- None (pure configuration)

MAIN FEATURES:
--------------
1) Color palettes for all annotation dimensions
2) Bilingual labels (French/English)
3) Constants for figure generation

Author:
-------
Antoine Lemor
"""

# =============================================================================
# GENERAL SETTINGS
# =============================================================================

OUTPUT_WIDTH = 1920
OUTPUT_HEIGHT = 1080

# =============================================================================
# CSS VARIABLES (NLP-POL Brand Identity)
# =============================================================================

CSS_VARS = """
:root {
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
}
"""

# =============================================================================
# SEMANTIC COLORS
# =============================================================================

POSITIVE_COLOR = '#059669'   # Green (success, positive)
NEGATIVE_COLOR = '#DC2626'   # Red (danger, negative)
NEUTRAL_COLOR = '#6B7280'    # Gray
WARNING_COLOR = '#F59E0B'    # Amber
PRIMARY_COLOR = '#2563EB'    # Blue
QUEBEC_BLUE = '#003DA5'      # Québec official blue (fleur-de-lys)

# =============================================================================
# SPEECH ACT COLORS
# =============================================================================

SPEECH_ACT_COLORS = {
    'ANNOUNCING': '#7C3AED',      # Purple - major declarations
    'THANKING': '#059669',        # Green - gratitude
    'PRAISING': '#10B981',        # Emerald - positive evaluation
    'JUSTIFYING': '#F59E0B',      # Amber - explanation/defense
    'CLAIMING_ACHIEVEMENT': '#2563EB',  # Blue - pride/accomplishment
    'DIAGNOSING': '#6366F1',      # Indigo - analysis
    'ACKNOWLEDGING': '#8B5CF6',   # Violet - admission
    'EXHORTING': '#DC2626',       # Red - call to action
    'EXPRESSING_EMOTION': '#EC4899',  # Pink - feelings
    'STATING': '#6B7280',         # Gray - neutral
    'WARNING': '#EF4444',         # Red - danger
    'WISHING': '#14B8A6',         # Teal - hopes
    'TRANSITIONAL': '#9CA3AF',    # Light gray - discourse markers
    'ANTICIPATION_CRITICISM': '#0891B2',  # Cyan - defensive anticipation
    'DEFENDING': '#F97316',       # Orange - defense
    'EXPLAINING': '#0EA5E9',      # Sky blue - explanation
}

# =============================================================================
# JUSTIFICATION TYPE COLORS
# =============================================================================

JUSTIFICATION_COLORS = {
    'DECISION_RATIONALE': '#7C3AED',    # Purple - why resign
    'POLICY_DEFENSE': '#2563EB',        # Blue - defending policies
    'RECORD_DEFENSE': '#0891B2',        # Cyan - defending record
    'EFFORT_CLAIM': '#059669',          # Green - personal effort
    'EXTERNAL_ATTRIBUTION': '#DC2626',  # Red - blaming others
    'CIRCUMSTANCE_CLAIM': '#F59E0B',    # Amber - circumstances
    'VALUES_APPEAL': '#8B5CF6',         # Violet - values
    'COLLECTIVE_ACHIEVEMENT': '#10B981', # Emerald - team credit
}

JUSTIFICATION_TARGET_COLORS = {
    'RESIGNATION': '#7C3AED',
    'OVERALL_MANDATE': '#2563EB',
    'SPECIFIC_POLICY': '#0891B2',
    'PARTY_CREATION': '#059669',
    'PANDEMIC_RESPONSE': '#DC2626',
    'ECONOMIC_POLICY': '#F59E0B',
    'IDENTITY_POLICY': '#003DA5',
    'PERSONAL_CONDUCT': '#6B7280',
}

# =============================================================================
# POLICY DOMAIN COLORS (CAP-based)
# =============================================================================

POLICY_DOMAIN_COLORS = {
    'MACROECONOMICS': '#2563EB',     # Blue
    'TAXATION': '#0891B2',           # Cyan
    'HEALTHCARE': '#DC2626',         # Red
    'EDUCATION': '#F59E0B',          # Amber
    'LABOR': '#6366F1',              # Indigo
    'IMMIGRATION': '#7C3AED',        # Purple
    'CULTURE_IDENTITY': '#003DA5',   # Québec blue
    'SECULARISM': '#8B5CF6',         # Violet
    'LANGUAGE_POLICY': '#0F766E',    # Teal
    'ENERGY': '#10B981',             # Emerald
    'HOUSING': '#A855F7',            # Purple
    'SENIORS': '#EC4899',            # Pink
    'INTERGOVERNMENTAL': '#6B7280',  # Gray
    'COST_OF_LIVING': '#EF4444',     # Red
    'PARTY_POLITICS': '#059669',     # Green
    'NONE': '#D1D5DB',               # Light gray
}

# =============================================================================
# EMOTIONAL REGISTER COLORS
# =============================================================================

EMOTIONAL_REGISTER_COLORS = {
    'PROUD': '#2563EB',        # Blue - pride
    'GRATEFUL': '#059669',     # Green - gratitude
    'NOSTALGIC': '#8B5CF6',    # Violet - nostalgia
    'AFFECTIONATE': '#EC4899', # Pink - warmth
    'DETERMINED': '#0891B2',   # Cyan - resolve
    'DEFENSIVE': '#F59E0B',    # Amber - defense
    'RESIGNED': '#6B7280',     # Gray - acceptance
    'HOPEFUL': '#10B981',      # Emerald - hope
    'CONCERNED': '#EF4444',    # Red - worry
    'COMBATIVE': '#DC2626',    # Dark red - fighting
    'SOLEMN': '#1F2937',       # Dark gray - gravity
    'HUMOROUS': '#14B8A6',     # Teal - humor
    'NEUTRAL': '#9CA3AF',      # Light gray
}

# Emotional weights for potential composite index
EMOTIONAL_REGISTER_WEIGHTS = {
    'PROUD': 1.5,
    'GRATEFUL': 1.0,
    'NOSTALGIC': 0.0,
    'AFFECTIONATE': 1.0,
    'DETERMINED': 1.0,
    'DEFENSIVE': -0.5,
    'RESIGNED': -1.0,
    'HOPEFUL': 1.0,
    'CONCERNED': -1.0,
    'COMBATIVE': -0.5,
    'SOLEMN': 0.0,
    'HUMOROUS': 0.5,
    'NEUTRAL': 0.0,
}

# =============================================================================
# ACTOR VALENCE COLORS
# =============================================================================

ACTOR_VALENCE_COLORS = {
    'POSITIVE': '#059669',
    'NEGATIVE': '#DC2626',
    'NEUTRAL': '#6B7280',
    'MIXED': '#F59E0B',
}

ACTOR_ROLE_COLORS = {
    'THANKED': '#059669',
    'PRAISED': '#10B981',
    'CREDITED': '#2563EB',
    'BLAMED': '#DC2626',
    'SUPPORTED': '#0891B2',
    'REFERENCED': '#6B7280',
    'OPPOSITION': '#EF4444',
}

# =============================================================================
# IDENTITY THEMES COLORS
# =============================================================================

IDENTITY_THEME_COLORS = {
    'FRENCH_LANGUAGE': '#0F766E',      # Teal
    'NATIONAL_PRIDE': '#003DA5',       # Québec blue
    'CULTURAL_DISTINCTIVENESS': '#7C3AED',  # Purple
    'SECULARISM': '#6366F1',           # Indigo
    'HISTORICAL_MEMORY': '#8B5CF6',    # Violet
    'VULNERABILITY': '#DC2626',        # Red
    'AUTONOMY': '#2563EB',             # Blue
    'INTEGRATION': '#F59E0B',          # Amber
}

IDENTITY_STANCE_COLORS = {
    'DEFENSIVE': '#F59E0B',
    'CELEBRATORY': '#059669',
    'CONCERNED': '#DC2626',
    'ASSERTIVE': '#2563EB',
}

# =============================================================================
# LEGACY FRAMING COLORS
# =============================================================================

LEGACY_FRAMING_COLORS = {
    'HISTORIC_ACHIEVEMENT': '#2563EB',  # Blue
    'PERSONAL_SACRIFICE': '#7C3AED',    # Purple
    'PIONEERING': '#059669',            # Green
    'TRANSFORMATIVE': '#0891B2',        # Cyan
    'DEFENDER': '#003DA5',              # Québec blue
    'BUILDER': '#10B981',               # Emerald
    'PRAGMATIST': '#F59E0B',            # Amber
    'NONE': '#D1D5DB',                  # Light gray
}

# =============================================================================
# BILINGUAL LABELS
# =============================================================================

LABELS = {
    'fr': {
        # Title elements
        'analysis_title': 'Analyse du discours de démission',
        'speaker': 'François Legault',
        'date': '14 janvier 2026',
        'subtitle': 'Premier ministre du Québec (2018-2026)',

        # Speech acts
        'speech_act': {
            'ANNOUNCING': 'Annonce',
            'THANKING': 'Remerciement',
            'PRAISING': 'Éloge',
            'JUSTIFYING': 'Justification',
            'CLAIMING_ACHIEVEMENT': 'Revendication',
            'DIAGNOSING': 'Diagnostic',
            'ACKNOWLEDGING': 'Reconnaissance',
            'EXHORTING': 'Exhortation',
            'EXPRESSING_EMOTION': 'Expression émotionnelle',
            'STATING': 'Constat',
            'WARNING': 'Avertissement',
            'WISHING': 'Souhait',
            'TRANSITIONAL': 'Transition',
            'ANTICIPATION_CRITICISM': 'Anticipation critique',
            'DEFENDING': 'Défense',
            'EXPLAINING': 'Explication',
        },

        # Justification types
        'justification_category': {
            'DECISION_RATIONALE': 'Raison de la décision',
            'POLICY_DEFENSE': 'Défense de politiques',
            'RECORD_DEFENSE': 'Défense du bilan',
            'EFFORT_CLAIM': "Revendication d'effort",
            'EXTERNAL_ATTRIBUTION': 'Attribution externe',
            'CIRCUMSTANCE_CLAIM': 'Circonstances',
            'VALUES_APPEAL': 'Appel aux valeurs',
            'COLLECTIVE_ACHIEVEMENT': 'Réussite collective',
        },

        # Justification targets
        'justification_target': {
            'RESIGNATION': 'Démission',
            'OVERALL_MANDATE': 'Bilan global',
            'SPECIFIC_POLICY': 'Politique spécifique',
            'PARTY_CREATION': 'Création du parti',
            'PANDEMIC_RESPONSE': 'Gestion pandémie',
            'ECONOMIC_POLICY': 'Politique économique',
            'IDENTITY_POLICY': 'Politique identitaire',
            'PERSONAL_CONDUCT': 'Conduite personnelle',
        },

        # Policy domains
        'policy_domain': {
            'MACROECONOMICS': 'Économie',
            'TAXATION': 'Fiscalité',
            'HEALTHCARE': 'Santé',
            'EDUCATION': 'Éducation',
            'LABOR': 'Travail',
            'IMMIGRATION': 'Immigration',
            'CULTURE_IDENTITY': 'Culture et identité',
            'SECULARISM': 'Laïcité',
            'LANGUAGE_POLICY': 'Politique linguistique',
            'ENERGY': 'Énergie',
            'HOUSING': 'Logement',
            'SENIORS': 'Aînés',
            'INTERGOVERNMENTAL': 'Relations intergouv.',
            'COST_OF_LIVING': 'Coût de la vie',
            'PARTY_POLITICS': 'Politique partisane',
            'NONE': 'Aucun',
        },

        # Emotional register
        'emotional_register': {
            'PROUD': 'Fier',
            'GRATEFUL': 'Reconnaissant',
            'NOSTALGIC': 'Nostalgique',
            'AFFECTIONATE': 'Affectueux',
            'DETERMINED': 'Déterminé',
            'DEFENSIVE': 'Défensif',
            'RESIGNED': 'Résigné',
            'HOPEFUL': 'Optimiste',
            'CONCERNED': 'Préoccupé',
            'COMBATIVE': 'Combatif',
            'SOLEMN': 'Solennel',
            'HUMOROUS': 'Humoristique',
            'NEUTRAL': 'Neutre',
        },

        # Identity themes
        'identity_theme': {
            'FRENCH_LANGUAGE': 'Langue française',
            'NATIONAL_PRIDE': 'Fierté nationale',
            'CULTURAL_DISTINCTIVENESS': 'Distinction culturelle',
            'SECULARISM': 'Laïcité',
            'HISTORICAL_MEMORY': 'Mémoire historique',
            'VULNERABILITY': 'Vulnérabilité',
            'AUTONOMY': 'Autonomie',
            'INTEGRATION': 'Intégration',
        },

        # Legacy framing
        'legacy_framing': {
            'HISTORIC_ACHIEVEMENT': 'Réalisation historique',
            'PERSONAL_SACRIFICE': 'Sacrifice personnel',
            'PIONEERING': 'Pionnier',
            'TRANSFORMATIVE': 'Transformateur',
            'DEFENDER': 'Défenseur',
            'BUILDER': 'Bâtisseur',
            'PRAGMATIST': 'Pragmatique',
            'NONE': 'Aucun',
        },

        # Figure titles
        'fig_titles': {
            'dashboard': 'Tableau de bord',
            'justifications': 'Justifications',
            'policy_domains': 'Domaines de politiques',
            'emotions': 'Registre émotionnel',
            'actors': 'Acteurs mentionnés',
            'identity': 'Thèmes identitaires',
            'legacy': 'Construction de l\'héritage',
            'timeline': 'Temporalité du discours',
        },

        # Common labels
        'sentences': 'phrases',
        'total': 'Total',
        'methodology': 'Méthodologie',
        'source': 'Source',
        'quote_open': '«\u202F',
        'quote_close': '\u202F»',
    },

    'en': {
        # Title elements
        'analysis_title': 'Resignation Speech Analysis',
        'speaker': 'François Legault',
        'date': 'January 14, 2026',
        'subtitle': 'Premier of Québec (2018-2026)',

        # Speech acts
        'speech_act': {
            'ANNOUNCING': 'Announcement',
            'THANKING': 'Thanking',
            'PRAISING': 'Praising',
            'JUSTIFYING': 'Justification',
            'CLAIMING_ACHIEVEMENT': 'Achievement claim',
            'DIAGNOSING': 'Diagnosis',
            'ACKNOWLEDGING': 'Acknowledgment',
            'EXHORTING': 'Exhortation',
            'EXPRESSING_EMOTION': 'Emotional expression',
            'STATING': 'Statement',
            'WARNING': 'Warning',
            'WISHING': 'Wish',
            'TRANSITIONAL': 'Transition',
            'ANTICIPATION_CRITICISM': 'Anticipating criticism',
            'DEFENDING': 'Defense',
            'EXPLAINING': 'Explanation',
        },

        # Justification types
        'justification_category': {
            'DECISION_RATIONALE': 'Decision rationale',
            'POLICY_DEFENSE': 'Policy defense',
            'RECORD_DEFENSE': 'Record defense',
            'EFFORT_CLAIM': 'Effort claim',
            'EXTERNAL_ATTRIBUTION': 'External attribution',
            'CIRCUMSTANCE_CLAIM': 'Circumstance claim',
            'VALUES_APPEAL': 'Values appeal',
            'COLLECTIVE_ACHIEVEMENT': 'Collective achievement',
        },

        # Justification targets
        'justification_target': {
            'RESIGNATION': 'Resignation',
            'OVERALL_MANDATE': 'Overall mandate',
            'SPECIFIC_POLICY': 'Specific policy',
            'PARTY_CREATION': 'Party creation',
            'PANDEMIC_RESPONSE': 'Pandemic response',
            'ECONOMIC_POLICY': 'Economic policy',
            'IDENTITY_POLICY': 'Identity policy',
            'PERSONAL_CONDUCT': 'Personal conduct',
        },

        # Policy domains
        'policy_domain': {
            'MACROECONOMICS': 'Economy',
            'TAXATION': 'Taxation',
            'HEALTHCARE': 'Healthcare',
            'EDUCATION': 'Education',
            'LABOR': 'Labor',
            'IMMIGRATION': 'Immigration',
            'CULTURE_IDENTITY': 'Culture & Identity',
            'SECULARISM': 'Secularism',
            'LANGUAGE_POLICY': 'Language policy',
            'ENERGY': 'Energy',
            'HOUSING': 'Housing',
            'SENIORS': 'Seniors',
            'INTERGOVERNMENTAL': 'Intergovernmental',
            'COST_OF_LIVING': 'Cost of living',
            'PARTY_POLITICS': 'Party politics',
            'NONE': 'None',
        },

        # Emotional register
        'emotional_register': {
            'PROUD': 'Proud',
            'GRATEFUL': 'Grateful',
            'NOSTALGIC': 'Nostalgic',
            'AFFECTIONATE': 'Affectionate',
            'DETERMINED': 'Determined',
            'DEFENSIVE': 'Defensive',
            'RESIGNED': 'Resigned',
            'HOPEFUL': 'Hopeful',
            'CONCERNED': 'Concerned',
            'COMBATIVE': 'Combative',
            'SOLEMN': 'Solemn',
            'HUMOROUS': 'Humorous',
            'NEUTRAL': 'Neutral',
        },

        # Identity themes
        'identity_theme': {
            'FRENCH_LANGUAGE': 'French language',
            'NATIONAL_PRIDE': 'National pride',
            'CULTURAL_DISTINCTIVENESS': 'Cultural distinctiveness',
            'SECULARISM': 'Secularism',
            'HISTORICAL_MEMORY': 'Historical memory',
            'VULNERABILITY': 'Vulnerability',
            'AUTONOMY': 'Autonomy',
            'INTEGRATION': 'Integration',
        },

        # Legacy framing
        'legacy_framing': {
            'HISTORIC_ACHIEVEMENT': 'Historic achievement',
            'PERSONAL_SACRIFICE': 'Personal sacrifice',
            'PIONEERING': 'Pioneering',
            'TRANSFORMATIVE': 'Transformative',
            'DEFENDER': 'Defender',
            'BUILDER': 'Builder',
            'PRAGMATIST': 'Pragmatist',
            'NONE': 'None',
        },

        # Figure titles
        'fig_titles': {
            'dashboard': 'Dashboard',
            'justifications': 'Justifications',
            'policy_domains': 'Policy Domains',
            'emotions': 'Emotional Register',
            'actors': 'Actors Mentioned',
            'identity': 'Identity Themes',
            'legacy': 'Legacy Construction',
            'timeline': 'Speech Timeline',
        },

        # Common labels
        'sentences': 'sentences',
        'total': 'Total',
        'methodology': 'Methodology',
        'source': 'Source',
        'quote_open': '"',
        'quote_close': '"',
    }
}


def get_labels(lang='fr'):
    """Get labels dictionary for specified language."""
    return LABELS.get(lang, LABELS['fr'])


def get_quote_marks(lang='fr'):
    """Get quote marks for specified language."""
    labels = get_labels(lang)
    return labels['quote_open'], labels['quote_close']
