#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
generate_fig5_policy_matrix.py

MAIN OBJECTIVE:
---------------
Analyze and visualize Macron's policy agenda by domain category.
Groups policy proposals into thematic categories (Security, Diplomacy,
Multilateralism, Economy, etc.) and measures specificity levels.

Dependencies:
-------------
- compute_indices (load_data, safe_json_parse, reserve_unique_texts, first_sentence)
- config (get_labels, POLICY_DOMAIN_PALETTE)
- html_utils (COLORS, POSITIVE_COLOR, NEGATIVE_COLOR, save_figure)

MAIN FEATURES:
--------------
1) Extract policy_content annotations with domain, action_type, specificity
2) Aggregate by thematic category with domain groupings
3) Compute Policy Ambition Index based on specificity distribution
4) Show representative policy excerpts per category
5) Generate bilingual output (FR/EN)

Author:
-------
Antoine Lemor
"""

from pathlib import Path
from collections import Counter, defaultdict
import json
from compute_indices import load_data, safe_json_parse, reserve_unique_texts, first_sentence
from config import get_labels, POLICY_DOMAIN_PALETTE
from html_utils import COLORS, POSITIVE_COLOR, NEGATIVE_COLOR, save_figure

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output" / "figures"

# =============================================================================
# DOMAIN CATEGORIES - Group domains thematically
# =============================================================================

DOMAIN_CATEGORIES = {
    'SECURITY_DEFENSE': {
        'label_fr': 'Sécurité & Défense',
        'label_en': 'Security & Defense',
        'color': '#B91C1C',
        'domains': ['DEFENSE_MILITARY', 'DEFENSE_INDUSTRY', 'STRATEGIC_AUTONOMY',
                    'UKRAINE_SUPPORT', 'PEACEKEEPING_OPERATIONS', 'INFORMATION_WARFARE',
                    'CYBERSECURITY', 'NUCLEAR_DETERRENCE', 'ARMS_CONTROL']
    },
    'DIPLOMACY_FOREIGN': {
        'label_fr': 'Diplomatie',
        'label_en': 'Diplomacy',
        'color': '#1D4ED8',
        'domains': ['DIPLOMATIC_METHOD', 'ALLIANCE_MANAGEMENT', 'BILATERAL_RELATIONS',
                    'CRISIS_MANAGEMENT', 'CONSULAR_AFFAIRS', 'CONFLICT_RESOLUTION']
    },
    'MULTILATERAL': {
        'label_fr': 'Multilatéralisme',
        'label_en': 'Multilateralism',
        'color': '#6D28D9',
        'domains': ['MULTILATERAL_INSTITUTIONS', 'UN_REFORM', 'INTERNATIONAL_LAW',
                    'GLOBAL_GOVERNANCE_ARCHITECTURE', 'DEVELOPMENT_FINANCE_REFORM']
    },
    'ECONOMY_TRADE': {
        'label_fr': 'Économie & Commerce',
        'label_en': 'Economy & Trade',
        'color': '#047857',
        'domains': ['TRADE_POLICY', 'ECONOMIC_PARTNERSHIPS', 'ECONOMIC_SOVEREIGNTY',
                    'INDUSTRIAL_POLICY', 'INVESTMENT', 'SANCTIONS']
    },
    'VALUES_SOFT_POWER': {
        'label_fr': 'Valeurs & Influence',
        'label_en': 'Values & Soft Power',
        'color': '#BE185D',
        'domains': ['CULTURAL_INFLUENCE', 'SCIENCE_TECHNOLOGY', 'HUMAN_RIGHTS',
                    'DEMOCRACY_PROMOTION', 'FRANCOPHONIE', 'EDUCATION', 'SOFT_POWER']
    },
    'DEVELOPMENT_CLIMATE': {
        'label_fr': 'Développement & Climat',
        'label_en': 'Development & Climate',
        'color': '#059669',
        'domains': ['CLIMATE_ENVIRONMENT', 'DEVELOPMENT_AID', 'HEALTH_GLOBAL',
                    'FOOD_SECURITY', 'MIGRATION']
    },
    'EUROPEAN': {
        'label_fr': 'Europe',
        'label_en': 'European Affairs',
        'color': '#D97706',
        'domains': ['EUROPEAN_INTEGRATION', 'EUROPEAN_ECONOMY', 'EUROPEAN_SOVEREIGNTY',
                    'EUROPEAN_DEFENSE', 'EUROZONE', 'ENLARGEMENT']
    },
    'REGIONAL': {
        'label_fr': 'Relations régionales',
        'label_en': 'Regional Relations',
        'color': '#0E7490',
        'domains': ['AFRICA_RELATIONS', 'INDO_PACIFIC_POLICY', 'MIDDLE_EAST_POLICY',
                    'EMERGING_POWERS_RELATIONS', 'AMERICAS', 'NEIGHBORHOOD_POLICY']
    },
}

ACTION_TYPES = {
    'REINFORCEMENT': {'label_fr': 'Renforcement', 'label_en': 'Reinforcement', 'color': '#1D4ED8'},
    'COALITION_BUILDING': {'label_fr': 'Coalitions', 'label_en': 'Coalition Building', 'color': '#059669'},
    'STRATEGIC_REPOSITIONING': {'label_fr': 'Repositionnement', 'label_en': 'Repositioning', 'color': '#7C3AED'},
    'ENGAGEMENT': {'label_fr': 'Engagement', 'label_en': 'Engagement', 'color': '#0891B2'},
    'RESISTANCE': {'label_fr': 'Résistance', 'label_en': 'Resistance', 'color': '#DC2626'},
    'DEFENSE_OF_EXISTING': {'label_fr': 'Défense acquis', 'label_en': 'Defend Status Quo', 'color': '#D97706'},
    'INSTITUTIONAL_REFORM': {'label_fr': 'Réforme', 'label_en': 'Reform', 'color': '#7C3AED'},
    'NEW_INITIATIVE': {'label_fr': 'Nouvelle initiative', 'label_en': 'New Initiative', 'color': '#047857'},
    'INNOVATION': {'label_fr': 'Innovation', 'label_en': 'Innovation', 'color': '#BE185D'},
}


def prepare_enhanced_policy_data(df):
    """Extract and enhance policy data with categorization and quotes."""
    policies = []
    quotes_by_cat = defaultdict(list)

    for idx, row in df.iterrows():
        val = row.get('policy_content')
        p = safe_json_parse(val)
        if p and p.get('present'):
            domain = p.get('domain', 'OTHER')
            action = p.get('action_type', 'OTHER')
            spec = p.get('specificity', 'PROGRAMMATIC')
            summary = p.get('summary', '')
            text = row.get('text', '')

            # Find category for domain
            category = 'OTHER'
            for cat_key, cat_info in DOMAIN_CATEGORIES.items():
                if domain in cat_info['domains']:
                    category = cat_key
                    break

            policies.append({
                'domain': domain,
                'category': category,
                'action': action,
                'specificity': spec,
                'summary': summary,
                'text': text,
            })

            # Store quotes for each category (prioritize concrete ones)
            max_quotes = 3
            if category == 'DIPLOMACY_FOREIGN':
                max_quotes = 8
            if spec == 'CONCRETE' and len(text) > 30:
                quotes_by_cat[category].insert(0, text)
            elif len(text) > 30 and len(quotes_by_cat[category]) < max_quotes:
                quotes_by_cat[category].append(text)

    if not policies:
        return None

    for category, quotes in quotes_by_cat.items():
        if category == 'DIPLOMACY_FOREIGN':
            prioritized = [q for q in quotes if 'diplom' in q.lower()]
            others = [q for q in quotes if 'diplom' not in q.lower()]
            quotes = prioritized + others
        quotes_by_cat[category] = reserve_unique_texts(quotes, limit=3)

    # Build aggregations
    n = len(policies)

    # By category
    cat_counts = Counter(p['category'] for p in policies)

    # By domain (top 10)
    domain_counts = Counter(p['domain'] for p in policies)
    top_domains = domain_counts.most_common(10)

    # By action
    action_counts = Counter(p['action'] for p in policies)

    # By specificity
    spec_counts = Counter(p['specificity'] for p in policies)

    # Ambition index
    spec_weights = {'CONCRETE': 1.0, 'PROGRAMMATIC': 0.6, 'ASPIRATIONAL': 0.2}
    total_weight = sum(spec_weights.get(p['specificity'], 0.5) for p in policies)
    ambition_idx = total_weight / n if n > 0 else 0

    # Action orientation: proactive vs defensive
    proactive = {'REINFORCEMENT', 'COALITION_BUILDING', 'NEW_INITIATIVE',
                 'STRATEGIC_REPOSITIONING', 'INSTITUTIONAL_REFORM', 'INNOVATION', 'ENGAGEMENT'}
    defensive = {'DEFENSE_OF_EXISTING', 'RESISTANCE'}
    pro_count = sum(1 for p in policies if p['action'] in proactive)
    def_count = sum(1 for p in policies if p['action'] in defensive)
    orientation_idx = (pro_count - def_count) / n if n > 0 else 0

    # Select best quotes per category (override diplomacy example)
    selected_quotes = {}
    for cat, quotes in quotes_by_cat.items():
        if not quotes:
            continue
        if cat == 'DIPLOMACY_FOREIGN':
            preferred = next((q for q in quotes if 'diplom' in q.lower()), None)
            if preferred:
                selected_quotes[cat] = preferred
            elif len(quotes) > 1:
                selected_quotes[cat] = quotes[1]
            else:
                selected_quotes[cat] = quotes[0]
        else:
            selected_quotes[cat] = quotes[0]

    return {
        'n_policies': n,
        'policies': policies,
        'category_counts': dict(cat_counts),
        'top_domains': top_domains,
        'action_counts': dict(action_counts),
        'specificity_counts': {
            'CONCRETE': spec_counts.get('CONCRETE', 0),
            'PROGRAMMATIC': spec_counts.get('PROGRAMMATIC', 0),
            'ASPIRATIONAL': spec_counts.get('ASPIRATIONAL', 0),
        },
        'ambition_index': ambition_idx,
        'orientation_index': orientation_idx,
        'quotes': selected_quotes,
    }


def generate_html(data, lang='fr'):
    """Generate the editorial-style policy matrix HTML."""
    if data is None:
        return None

    n_policies = data['n_policies']
    ambition_idx = data['ambition_index']
    orientation_idx = data['orientation_index']

    if lang == 'fr':
        title = "L'agenda diplomatique de Macron"
        subtitle = "Analyse stratégique des propositions politiques"
        stat_line = f"{n_policies} propositions identifiées"
        section_domains = "Répartition par domaine thématique"
        section_domains_desc = "Chaque proposition est classée dans un domaine stratégique selon son objet principal."
        section_actions = "Comment Macron entend-il agir ?"
        section_actions_desc = "Type d'action proposée pour chaque mesure : renforcer l'existant, bâtir des coalitions, se repositionner..."
        section_precision = "Degré de précision des propositions"
        section_precision_desc = "Concret = mesure opérationnelle. Programmatique = orientation générale. Aspirationnel = vision abstraite."
        spec_labels = {'CONCRETE': 'Concret', 'PROGRAMMATIC': 'Programmatique', 'ASPIRATIONAL': 'Aspirationnel'}
        ambition_label = "Indice d'ambition"
        ambition_desc = "Mesure la concrétude moyenne des propositions. Plus c'est haut, plus les propositions sont précises et opérationnelles."
        orientation_label = "Orientation stratégique"
        orientation_desc = "Posture proactive (renforcer, innover) vs défensive (résister, préserver)."
        pro_label = "Proactif"
        def_label = "Défensif"
        methodology = "Méthodologie : Chaque proposition est annotée selon son domaine, type d'action et niveau de précision. L'indice d'ambition pondère la précision (Concret=100%, Programmatique=60%, Aspirationnel=20%)."
        excerpts_label = "Extraits labellisés"
    else:
        title = "Macron's Diplomatic Agenda"
        subtitle = "Strategic analysis of policy proposals"
        stat_line = f"{n_policies} proposals identified"
        section_domains = "Distribution by thematic domain"
        section_domains_desc = "Each proposal is classified into a strategic domain based on its main subject."
        section_actions = "How does Macron intend to act?"
        section_actions_desc = "Type of action proposed: reinforce existing, build coalitions, reposition..."
        section_precision = "Precision level of proposals"
        section_precision_desc = "Concrete = operational measure. Programmatic = general direction. Aspirational = abstract vision."
        spec_labels = {'CONCRETE': 'Concrete', 'PROGRAMMATIC': 'Programmatic', 'ASPIRATIONAL': 'Aspirational'}
        ambition_label = "Ambition index"
        ambition_desc = "Measures average concreteness of proposals. Higher = more precise and operational proposals."
        orientation_label = "Strategic orientation"
        orientation_desc = "Proactive posture (reinforce, innovate) vs defensive (resist, preserve)."
        pro_label = "Proactive"
        def_label = "Defensive"
        methodology = "Methodology: Each proposal is annotated by domain, action type and precision level. Ambition index weights precision (Concrete=100%, Programmatic=60%, Aspirational=20%)."
        excerpts_label = "Labeled excerpts"

    def format_quote(text):
        cleaned = ' '.join(str(text).split())
        return first_sentence(cleaned)

    # Generate domain items with elegant styling
    sorted_cats = sorted(data['category_counts'].items(), key=lambda x: -x[1])
    max_cat = max(data['category_counts'].values()) if data['category_counts'] else 1

    domain_items_html = ""
    for idx, (cat_key, count) in enumerate(sorted_cats):
        if cat_key == 'OTHER':
            continue
        cat_info = DOMAIN_CATEGORIES.get(cat_key, {})
        label = cat_info.get(f'label_{lang}', cat_key)
        color = cat_info.get('color', '#475569')
        pct_of_total = count / n_policies * 100
        bar_width = (count / max_cat) * 100
        # Show quote for each category
        quote = data['quotes'].get(cat_key, '')

        domain_items_html += f'''
        <div class="domain-item">
            <div class="domain-header">
                <span class="domain-dot" style="background: {color};"></span>
                <span class="domain-name">{label}</span>
                <span class="domain-stat">{count} <span class="domain-pct">({pct_of_total:.0f}%)</span></span>
            </div>
            <div class="domain-bar-track">
                <div class="domain-bar" style="width: {bar_width}%; background: {color};"></div>
            </div>
            {f'<blockquote class="domain-quote"><span class="quote-text">« {format_quote(quote)} »</span></blockquote>' if quote else ''}
        </div>
        '''

    # Generate action bars (horizontal stacked representation)
    sorted_actions = sorted(data['action_counts'].items(), key=lambda x: -x[1])
    total_actions = sum(data['action_counts'].values())

    # Stacked bar segments
    action_segments_html = ""
    for action, count in sorted_actions:
        action_info = ACTION_TYPES.get(action, {})
        color = action_info.get('color', '#64748b')
        pct = count / total_actions * 100
        if pct >= 3:  # Only show segments >= 3%
            action_segments_html += f'<div class="action-segment" style="width: {pct}%; background: {color};" title="{action}: {pct:.0f}%"></div>'

    # Action legend items - show all actions that appear in the bar
    action_legend_html = ""
    for action, count in sorted_actions:
        pct = count / total_actions * 100
        if pct >= 3:  # Only show in legend if >= 3% (same as bar segments)
            action_info = ACTION_TYPES.get(action, {})
            label = action_info.get(f'label_{lang}', action.replace('_', ' ').title())
            color = action_info.get('color', '#64748b')
            action_legend_html += f'''
            <div class="action-legend-item">
                <div class="action-color" style="background: {color};"></div>
                <span class="action-label">{label}</span>
                <span class="action-pct">{pct:.0f}%</span>
            </div>
            '''

    # Specificity data
    spec_concrete = data['specificity_counts']['CONCRETE']
    spec_prog = data['specificity_counts']['PROGRAMMATIC']
    spec_aspir = data['specificity_counts']['ASPIRATIONAL']

    # Orientation position
    orientation_pct = (orientation_idx + 1) / 2 * 100

    # Ambition styling
    if ambition_idx >= 0.55:
        ambition_color = '#059669'
        ambition_bg = '#ecfdf5'
    elif ambition_idx >= 0.40:
        ambition_color = '#1D4ED8'
        ambition_bg = '#eff6ff'
    else:
        ambition_color = '#D97706'
        ambition_bg = '#fffbeb'

    html = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=STIX+Two+Text:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
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
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            width: 1920px;
            height: 1080px;
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
            gap: 18px;
        }}

        /* Header */
        .header {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--ink);
        }}

        .header-left {{
            flex: 1;
        }}

        .main-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 62px;
            font-weight: 600;
            letter-spacing: -0.02em;
            line-height: 1.1;
        }}

        .subtitle {{
            font-size: 21px;
            color: var(--muted);
            margin-top: 8px;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }}

        .header-stat {{
            text-align: right;
        }}

        .stat-number {{
            font-family: 'STIX Two Text', serif;
            font-size: 66px;
            font-weight: 700;
            color: var(--ink);
            line-height: 1;
        }}

        .stat-label {{
            font-size: 16px;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 4px;
        }}

        /* Main Grid */
        .main-grid {{
            display: grid;
            grid-template-columns: 1.1fr 1fr;
            gap: 30px;
            flex: 1;
            min-height: 0;
        }}

        /* Left column - Domains */
        .domains-column {{
            display: flex;
            flex-direction: column;
            overflow: hidden;
            min-width: 0;
        }}

        .section-header {{
            margin-bottom: 12px;
        }}

        .section-title {{
            font-family: 'STIX Two Text', serif;
            font-size: 24px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 4px;
        }}

        .section-desc {{
            font-size: 16px;
            color: var(--muted);
            line-height: 1.35;
        }}

        .domain-item {{
            margin-bottom: 6px;
            min-width: 0;
            overflow: hidden;
        }}

        .domain-header {{
            display: flex;
            align-items: center;
            margin-bottom: 3px;
        }}

        .domain-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }}

        .domain-name {{
            font-weight: 600;
            font-size: 16px;
            color: var(--ink);
            flex: 1;
        }}

        .domain-stat {{
            font-family: 'STIX Two Text', serif;
            font-size: 20px;
            font-weight: 600;
            color: var(--ink);
        }}

        .domain-pct {{
            font-size: 14px;
            font-weight: 400;
            color: var(--muted);
        }}

        .domain-bar-track {{
            height: 12px;
            background: var(--bg-deep);
            border-radius: 6px;
            margin-bottom: 3px;
        }}

        .domain-bar {{
            height: 100%;
            border-radius: 6px;
        }}

        .domain-quote {{
            font-family: 'STIX Two Text', serif;
            font-size: 14px;
            color: var(--ink);
            line-height: 1.4;
            padding: 6px 10px 6px 12px;
            border-left: 4px solid var(--line);
            border-radius: 6px;
            background: var(--card);
            margin-top: 4px;
            margin-bottom: 4px;
            overflow: hidden;
            max-width: 100%;
        }}
        .domain-quote .quote-text {{
            font-size: 14px;
            color: var(--ink);
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 100%;
        }}

        /* Right column */
        .right-column {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        /* Actions section */
        .actions-section {{
        }}

        .action-stacked-bar {{
            display: flex;
            height: 40px;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 14px;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
        }}

        .action-segment {{
            height: 100%;
            transition: opacity 0.2s;
        }}

        .action-segment:hover {{
            opacity: 0.85;
        }}

        .action-legend {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px 24px;
        }}

        .action-legend-item {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .action-color {{
            width: 18px;
            height: 18px;
            border-radius: 5px;
            flex-shrink: 0;
        }}

        .action-label {{
            font-size: 18px;
            font-weight: 500;
            color: var(--ink);
            flex: 1;
        }}

        .action-pct {{
            font-family: 'STIX Two Text', serif;
            font-size: 22px;
            font-weight: 600;
            color: var(--ink);
        }}

        /* Precision section */
        .precision-section {{
        }}

        .precision-bars {{
            display: flex;
            gap: 20px;
            margin-bottom: 8px;
        }}

        .precision-item {{
            flex: 1;
            text-align: center;
        }}

        .precision-bar-container {{
            height: 85px;
            display: flex;
            align-items: flex-end;
            justify-content: center;
            margin-bottom: 8px;
        }}

        .precision-bar {{
            width: 75px;
            border-radius: 8px 8px 0 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 45px;
            gap: 2px;
        }}

        .precision-value {{
            font-family: 'STIX Two Text', serif;
            font-size: 26px;
            font-weight: 700;
            color: white;
            line-height: 1;
        }}

        .precision-pct {{
            font-size: 14px;
            font-weight: 600;
            color: rgba(255,255,255,0.9);
        }}

        .precision-label {{
            font-size: 17px;
            font-weight: 600;
            color: var(--ink);
        }}

        /* Index cards */
        .index-cards {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }}

        .index-card {{
            padding: 18px 16px;
            border-radius: 12px;
        }}

        .index-card.ambition {{
            background: {ambition_bg};
            border: 2px solid {ambition_color}40;
        }}

        .index-card.orientation {{
            background: #f5f5f4;
            border: 2px solid #d6d3d1;
        }}

        .index-value {{
            font-family: 'STIX Two Text', serif;
            font-size: 52px;
            font-weight: 700;
            line-height: 1;
            text-align: center;
        }}

        .index-value.ambition {{
            color: {ambition_color};
        }}

        .index-label {{
            font-size: 18px;
            font-weight: 600;
            color: var(--ink);
            margin-top: 10px;
            text-align: center;
        }}

        .index-desc {{
            font-size: 14px;
            color: var(--muted);
            margin-top: 8px;
            text-align: center;
            line-height: 1.4;
        }}

        /* Orientation gauge */
        .orientation-gauge {{
            margin-top: 12px;
        }}

        .gauge-track {{
            height: 14px;
            background: linear-gradient(90deg, #dc2626 0%, #e5e5e5 50%, #059669 100%);
            border-radius: 7px;
            position: relative;
        }}

        .gauge-marker {{
            position: absolute;
            top: -5px;
            width: 24px;
            height: 24px;
            background: white;
            border: 3px solid #1c1917;
            border-radius: 50%;
            transform: translateX(-50%);
            box-shadow: 0 2px 4px rgba(0,0,0,0.15);
        }}

        .gauge-labels {{
            display: flex;
            justify-content: space-between;
            margin-top: 8px;
        }}

        .gauge-label {{
            font-size: 15px;
            color: var(--muted);
            font-weight: 500;
        }}

        /* Footer methodology */
        .methodology {{
            margin-top: auto;
            padding-top: 10px;
        }}

        .methodology-text {{
            font-size: 16px;
            color: var(--muted);
            text-align: left;
            border-top: 1px solid var(--line);
            padding-top: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="header-left">
                <h1 class="main-title">{title}</h1>
                <p class="subtitle">{subtitle}</p>
            </div>
            <div class="header-stat">
                <div class="stat-number">{n_policies}</div>
                <div class="stat-label">{stat_line.replace(str(n_policies), '').strip()}</div>
            </div>
        </header>

        <div class="main-grid">
            <div class="domains-column">
                <div class="section-header">
                    <h2 class="section-title">{section_domains}</h2>
                    <p class="section-desc">{section_domains_desc}</p>
                </div>
                {domain_items_html}
            </div>

            <div class="right-column">
                <div class="actions-section">
                    <div class="section-header">
                        <h2 class="section-title">{section_actions}</h2>
                        <p class="section-desc">{section_actions_desc}</p>
                    </div>
                    <div class="action-stacked-bar">
                        {action_segments_html}
                    </div>
                    <div class="action-legend">
                        {action_legend_html}
                    </div>
                </div>

                <div class="precision-section">
                    <div class="section-header">
                        <h2 class="section-title">{section_precision}</h2>
                        <p class="section-desc">{section_precision_desc}</p>
                    </div>
                    <div class="precision-bars">
                        <div class="precision-item">
                            <div class="precision-bar-container">
                                <div class="precision-bar" style="height: {min(max(spec_aspir/n_policies*140, 40), 85)}px; background: #D97706;">
                                    <span class="precision-value">{spec_aspir}</span>
                                    <span class="precision-pct">({spec_aspir/n_policies*100:.0f}%)</span>
                                </div>
                            </div>
                            <div class="precision-label">{spec_labels['ASPIRATIONAL']}</div>
                        </div>
                        <div class="precision-item">
                            <div class="precision-bar-container">
                                <div class="precision-bar" style="height: {min(max(spec_prog/n_policies*140, 40), 85)}px; background: #1D4ED8;">
                                    <span class="precision-value">{spec_prog}</span>
                                    <span class="precision-pct">({spec_prog/n_policies*100:.0f}%)</span>
                                </div>
                            </div>
                            <div class="precision-label">{spec_labels['PROGRAMMATIC']}</div>
                        </div>
                        <div class="precision-item">
                            <div class="precision-bar-container">
                                <div class="precision-bar" style="height: {min(max(spec_concrete/n_policies*140, 40), 85)}px; background: #059669;">
                                    <span class="precision-value">{spec_concrete}</span>
                                    <span class="precision-pct">({spec_concrete/n_policies*100:.0f}%)</span>
                                </div>
                            </div>
                            <div class="precision-label">{spec_labels['CONCRETE']}</div>
                        </div>
                    </div>
                </div>

                <div class="index-cards">
                    <div class="index-card ambition">
                        <div class="index-value ambition">{ambition_idx:.0%}</div>
                        <div class="index-label">{ambition_label}</div>
                        <div class="index-desc">{ambition_desc}</div>
                    </div>
                    <div class="index-card orientation">
                        <div class="index-value" style="color: #1c1917;">{orientation_idx:+.2f}</div>
                        <div class="index-label">{orientation_label}</div>
                        <div class="index-desc">{orientation_desc}</div>
                        <div class="orientation-gauge">
                            <div class="gauge-track">
                                <div class="gauge-marker" style="left: {orientation_pct}%;"></div>
                            </div>
                            <div class="gauge-labels">
                                <span class="gauge-label">{def_label}</span>
                                <span class="gauge-label">{pro_label}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer class="methodology">
            <p class="methodology-text">{methodology}</p>
        </footer>
    </div>
</body>
</html>'''

    return html


def main():
    print("=" * 70)
    print("Generating Figure 5: Policy Agenda Analysis")
    print("=" * 70)

    print("\nLoading data...")
    df = load_data()
    data = prepare_enhanced_policy_data(df)

    if data is None:
        print("No policy data found. Skipping.")
        return

    print(f"\nPolicy analysis:")
    print(f"  Total proposals: {data['n_policies']}")
    print(f"  Ambition index: {data['ambition_index']:.1%}")
    print(f"  Orientation index: {data['orientation_index']:+.2f}")
    print(f"\n  By category:")
    for cat, count in sorted(data['category_counts'].items(), key=lambda x: -x[1]):
        print(f"    {cat}: {count}")
    print(f"\n  Quotes extracted: {len(data['quotes'])}")

    for lang in ['fr', 'en']:
        print(f"\n--- {lang.upper()} ---")
        html = generate_html(data, lang)
        if html:
            save_figure(html, OUTPUT_DIR, f"fig5_policy_matrix_{lang}")

    print("\nDone!")


if __name__ == "__main__":
    main()
