#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
compute_indices.py

MAIN OBJECTIVE:
---------------
Compute all composite indices for the Macron diplomacy speech analysis.
Provides reusable data processing functions separated from visualization
to ensure reproducibility and modularity.

Dependencies:
-------------
- pandas, numpy, scipy
- load_and_validate (load_annotated_data, parse_labels_column, extract_all_list_values)
- config (EMOTIONAL_REGISTER_WEIGHTS, get_labels)

MAIN FEATURES:
--------------
1) Data loading and validation from CSV annotations
2) Composite index computation:
   - Geopolitical Anxiety Index (worldview: threat vs opportunity + tone)
   - Agency Index (France positioning: active vs reactive)
   - Policy Ambition Index (specificity: concrete vs aspirational)
   - Diplomatic Tone Index (emotional register weights)
   - Action Orientation Index (speech acts: action vs descriptive)
3) Prepare structured data for each visualization
4) Excerpt selection with deduplication across figures

Author:
-------
Antoine Lemor
"""

import json
import re
import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from scipy.signal import find_peaks
from scipy.interpolate import make_interp_spline

from load_and_validate import load_annotated_data, parse_labels_column, extract_all_list_values
from config import EMOTIONAL_REGISTER_WEIGHTS, get_labels

# =============================================================================
# EXCERPT REGISTRY
# =============================================================================

USED_EXCERPTS = set()


def excerpt_key(text):
    """Return a normalized key for excerpt deduping."""
    cleaned = ' '.join(str(text).split())
    return first_sentence(cleaned).strip().lower()


def reserve_unique_texts(texts, limit=None, used_keys=None):
    """Reserve unique texts across figures (based on excerpt_key)."""
    if used_keys is None:
        used_keys = USED_EXCERPTS
    selected = []
    for t in texts:
        key = excerpt_key(t)
        if key and key not in used_keys:
            selected.append(t)
            used_keys.add(key)
        if limit is not None and len(selected) >= limit:
            break
    return selected


def select_excerpt_candidates(candidates, min_len=160, max_len=360, limit=3):
    """Select unique excerpt candidates with length filtering."""
    filtered = [c for c in candidates if min_len <= len(first_sentence(c.get('text', ''))) <= max_len]
    if len(filtered) < limit:
        filtered = candidates
    filtered.sort(key=lambda x: len(first_sentence(x.get('text', ''))))
    selected = []
    for c in filtered:
        key = excerpt_key(c.get('text', ''))
        if key and key not in USED_EXCERPTS:
            selected.append(c)
            USED_EXCERPTS.add(key)
        if len(selected) >= limit:
            break
    if len(selected) < limit:
        for c in candidates:
            key = excerpt_key(c.get('text', ''))
            if key and key not in USED_EXCERPTS:
                selected.append(c)
                USED_EXCERPTS.add(key)
            if len(selected) >= limit:
                break
    return selected
# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# =============================================================================
# DATA LOADING
# =============================================================================

def load_data(filepath=None):
    """Load and prepare annotated data."""
    if filepath is None:
        csv_files = list(DATA_DIR.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError("No CSV files found in data directory")
        filepath = csv_files[0]
    df = load_annotated_data(filepath)
    df = parse_labels_column(df)
    return df


def count_list_column(df, col):
    """Count all values in a list-type column."""
    all_values = []
    for val in df[col].dropna():
        values = extract_all_list_values(val)
        all_values.extend(values)
    return Counter(all_values)


def safe_json_parse(val):
    """Safely parse JSON."""
    if isinstance(val, (dict, list, tuple, np.ndarray)):
        if isinstance(val, np.ndarray):
            return val.tolist()
        if isinstance(val, tuple):
            return list(val)
        return val
    if pd.isna(val):
        return None
    try:
        return json.loads(val)
    except:
        return None


def get_text_column(df):
    """Return the first matching text column name."""
    for col in ['text', 'sentence', 'segment', 'utterance']:
        if col in df.columns:
            return col
    return None


def normalize_actor_name(name):
    """Normalize actor mentions to canonical labels."""
    if not name:
        return name
    if 'France' in name or name in ['nous', 'on']:
        return 'France'
    if 'Europe' in name or 'UE' in name or 'Européen' in name:
        return 'Europe/UE'
    if 'États-Unis' in name or 'USA' in name or 'Amérique' in name:
        return 'États-Unis'
    if 'Ambassadeur' in name:
        return 'Ambassadeurs'
    return name


def first_sentence(text):
    """Return the first sentence-like chunk for length checks."""
    if not text:
        return ""
    match = re.search(r'^(.*?[.!?])(?:\s|$)', str(text).strip())
    return match.group(1) if match else str(text).strip()


# =============================================================================
# COMPOSITE INDICES
# =============================================================================

def compute_worldview_components(df):
    """Return worldview components used for the combined index."""
    threat_frames = ['DISORDER', 'POWER_POLITICS', 'MULTILATERAL_DECLINE', 'EXISTENTIAL_THREAT',
                     'BRUTALIZATION', 'VASSALIZATION', 'RECOLONIZATION', 'FRAGMENTATION',
                     'REACTIONARY_INTERNATIONAL']
    opportunity_frames = ['OPPORTUNITY', 'RESILIENCE', 'COOPERATION', 'MULTILATERAL_RENEWAL',
                          'PROGRESS', 'SOLIDARITY', 'LEADERSHIP_OPPORTUNITY', 'STRATEGIC_ADVANTAGE',
                          'REFORM_MOMENTUM']

    frame_counts = count_list_column(df, 'geopolitical_frame')
    frame_counts.pop('NONE', None)

    threat = sum(frame_counts.get(f, 0) for f in threat_frames)
    opportunity = sum(frame_counts.get(f, 0) for f in opportunity_frames)

    frame_total = threat + opportunity
    if frame_total == 0:
        frame_balance = 0.0
    else:
        frame_balance = (opportunity - threat) / frame_total

    tone_index = compute_diplomatic_tone_index(df)
    if 'emotional_register' in df.columns:
        tone_total = int(df['emotional_register'].notna().sum())
    else:
        tone_total = 0

    evidence_total = frame_total + tone_total
    if evidence_total == 0:
        weight_frame = 0.0
        weight_tone = 0.0
        worldview_index = 0.0
    else:
        weight_frame = frame_total / evidence_total if frame_total else 0.0
        weight_tone = tone_total / evidence_total if tone_total else 0.0
        worldview_index = frame_balance * weight_frame + tone_index * weight_tone

    return {
        'frame_balance': frame_balance,
        'frame_total': frame_total,
        'tone_index': tone_index,
        'tone_total': tone_total,
        'weight_frame': weight_frame,
        'weight_tone': weight_tone,
        'worldview_index': worldview_index,
    }


def compute_geopolitical_anxiety_index(df):
    """
    Worldview index: -1 (pessimistic) to +1 (optimistic).
    Combines threat/opportunity balance with emotional tone (weighted by coverage).
    """
    return compute_worldview_components(df)['worldview_index']


def compute_agency_index(df):
    """
    Agency Index: 0 (passive) to 1 (highly active)
    Active positioning vs Passive/Reactive
    """
    active = ['ACTIVE_AGENT', 'LEADER', 'POWER', 'MODEL']
    passive = ['REACTIVE_AGENT', 'VICTIM']

    pos_counts = count_list_column(df, 'france_positioning')
    pos_counts.pop('NOT_APPLICABLE', None)

    active_count = sum(pos_counts.get(p, 0) for p in active)
    passive_count = sum(pos_counts.get(p, 0) for p in passive)
    partner_count = pos_counts.get('PARTNER', 0) + pos_counts.get('RELIABLE_ALLY', 0)

    total = active_count + passive_count + partner_count
    if total == 0:
        return 0.5

    # Active = 1, Partner = 0.7, Passive = 0.3
    return (active_count * 1.0 + partner_count * 0.7 + passive_count * 0.3) / total


def compute_policy_ambition_index(df):
    """
    Policy Ambition Index: 0 (vague) to 1 (concrete)
    Based on specificity of policy proposals
    """
    policies = []
    for val in df['policy_content'].dropna():
        p = safe_json_parse(val)
        if p and p.get('present'):
            policies.append(p.get('specificity'))

    if not policies:
        return 0.5

    weights = {'CONCRETE': 1.0, 'PROGRAMMATIC': 0.6, 'ASPIRATIONAL': 0.2}
    scores = [weights.get(p, 0.5) for p in policies if p]

    return np.mean(scores) if scores else 0.5


def compute_diplomatic_tone_index(df):
    """
    Diplomatic Tone Index: -1 (alarmist/combative) to +1 (confident/calm)
    """
    if 'emotional_register' not in df.columns:
        return 0.0

    weights = df['emotional_register'].map(EMOTIONAL_REGISTER_WEIGHTS).dropna()
    if len(weights) == 0:
        return 0.0

    raw = weights.mean()
    return raw / 2.0  # Normalize


def compute_action_orientation_index(df):
    """
    Action Orientation Index: 0 (descriptive) to 1 (action-oriented)
    Based on speech acts
    """
    action_acts = ['PROPOSING', 'EXHORTING', 'COMMITTING']
    descriptive_acts = ['STATING', 'DIAGNOSING', 'FRAMING']

    act_counts = count_list_column(df, 'speech_act')

    action = sum(act_counts.get(a, 0) for a in action_acts)
    descriptive = sum(act_counts.get(a, 0) for a in descriptive_acts)

    total = action + descriptive
    if total == 0:
        return 0.5

    return action / total


def compute_all_indices(df):
    """Compute all indices and return as dictionary."""
    return {
        'geopolitical_anxiety': compute_geopolitical_anxiety_index(df),
        'agency': compute_agency_index(df),
        'policy_ambition': compute_policy_ambition_index(df),
        'diplomatic_tone': compute_diplomatic_tone_index(df),
        'action_orientation': compute_action_orientation_index(df),
    }


# =============================================================================
# TIMELINE DATA
# =============================================================================

def prepare_timeline_data(df):
    """Prepare emotional timeline data with peak detection."""
    df = df.copy().reset_index(drop=True)
    df['tone_weight'] = df['emotional_register'].map(EMOTIONAL_REGISTER_WEIGHTS).fillna(0)
    df['tone_smooth'] = df['tone_weight'].rolling(window=10, center=True, min_periods=3).mean()

    smooth_vals = df['tone_smooth'].fillna(0).values
    n_points = len(df)

    # Smooth curve
    x = np.arange(n_points)
    y = smooth_vals
    valid = ~np.isnan(df['tone_smooth'].values)
    x_valid = x[valid]
    y_valid = y[valid]

    x_smooth = np.linspace(x_valid.min(), x_valid.max(), 400)
    spl = make_interp_spline(x_valid, y_valid, k=3)
    y_smooth = spl(x_smooth)

    # Find peaks
    neg_peaks, _ = find_peaks(-smooth_vals, prominence=0.25, distance=15)
    pos_peaks, _ = find_peaks(smooth_vals, prominence=0.25, distance=15)

    neg_peaks_sorted = sorted(neg_peaks, key=lambda x: smooth_vals[x])[:4]
    pos_peaks_sorted = sorted(pos_peaks, key=lambda x: -smooth_vals[x])[:4]

    # Calculate data range
    y_data_min = np.min(y_smooth)
    y_data_max = np.max(y_smooth)
    y_padding = (y_data_max - y_data_min) * 0.15

    return {
        'df': df,
        'n_points': n_points,
        'x_smooth': x_smooth,
        'y_smooth': y_smooth,
        'y_min': y_data_min - y_padding,
        'y_max': y_data_max + y_padding,
        'neg_peaks': neg_peaks_sorted,
        'pos_peaks': pos_peaks_sorted,
        'smooth_vals': smooth_vals,
    }


def extract_peak_excerpt(df, idx, is_positive=True):
    """Extract excerpt with context from a peak."""
    positive_registers = {'CONFIDENT', 'GRATEFUL', 'SOLEMN'}
    negative_registers = {'ALARMIST', 'COMBATIVE', 'INDIGNANT', 'DEFIANT', 'EXASPERATED'}
    neutral_registers = {'NEUTRAL', 'PRAGMATIC'}

    n = len(df)
    tone = df.iloc[idx]['emotional_register']
    if pd.isna(tone):
        tone = "NEUTRAL"

    target_registers = positive_registers if is_positive else negative_registers
    use_idx = idx

    # Search nearby if mismatched
    if tone in neutral_registers or (is_positive and tone in negative_registers) or (not is_positive and tone in positive_registers):
        for offset in [1, -1, 2, -2, 3, -3]:
            check_idx = idx + offset
            if 0 <= check_idx < n:
                check_tone = df.iloc[check_idx]['emotional_register']
                if check_tone in target_registers:
                    use_idx = check_idx
                    tone = check_tone
                    break

    before = str(df.iloc[use_idx-1]['text']).strip() if use_idx > 0 else ""
    main = str(df.iloc[use_idx]['text']).strip()
    after = str(df.iloc[use_idx+1]['text']).strip() if use_idx < n-1 else ""

    if len(before) < 10:
        before = ""

    # Get speech act
    speech_act = df.iloc[use_idx].get('speech_act', None)
    if pd.isna(speech_act):
        speech_act = None
    elif isinstance(speech_act, str):
        if speech_act.startswith('['):
            try:
                speech_act = json.loads(speech_act.replace("'", '"'))
            except:
                pass
    if isinstance(speech_act, list):
        speech_act = speech_act
    elif speech_act:
        speech_act = [speech_act]
    else:
        speech_act = []

    return {
        'idx': idx,
        'pos': use_idx + 1,
        'tone': tone,
        'speech_act': speech_act,
        'before': before if before != 'nan' else "",
        'main': main if main != 'nan' else "",
        'after': after if after != 'nan' else "",
    }


# =============================================================================
# GEOPOLITICAL FRAME DATA
# =============================================================================

def prepare_geopolitical_data(df):
    """Prepare geopolitical frame analysis data."""
    threat_frames = ['DISORDER', 'POWER_POLITICS', 'MULTILATERAL_DECLINE', 'EXISTENTIAL_THREAT',
                     'BRUTALIZATION', 'VASSALIZATION', 'RECOLONIZATION', 'FRAGMENTATION',
                     'REACTIONARY_INTERNATIONAL']
    opportunity_frames = ['OPPORTUNITY', 'RESILIENCE', 'COOPERATION', 'MULTILATERAL_RENEWAL',
                          'PROGRESS', 'SOLIDARITY', 'LEADERSHIP_OPPORTUNITY', 'STRATEGIC_ADVANTAGE',
                          'REFORM_MOMENTUM']

    frame_counts = count_list_column(df, 'geopolitical_frame')
    frame_counts.pop('NONE', None)

    threat_data = [(f, frame_counts.get(f, 0)) for f in threat_frames if frame_counts.get(f, 0) > 0]
    opp_data = [(f, frame_counts.get(f, 0)) for f in opportunity_frames if frame_counts.get(f, 0) > 0]

    threat_data.sort(key=lambda x: x[1], reverse=True)
    opp_data.sort(key=lambda x: x[1], reverse=True)

    text_col = get_text_column(df)
    threat_quotes = []
    opp_quotes = []
    if text_col:
        seen_threat = set()
        seen_opp = set()
        for _, row in df.iterrows():
            text = str(row.get(text_col, '')).strip()
            if not text or text.lower() == 'nan':
                continue
            frames = extract_all_list_values(safe_json_parse(row.get('geopolitical_frame')) or [])
            if not frames:
                continue
            threat_frame = next((f for f in frames if f in threat_frames), None)
            opp_frame = next((f for f in frames if f in opportunity_frames), None)
            if threat_frame and text not in seen_threat:
                threat_quotes.append({'frame': threat_frame, 'text': text})
                seen_threat.add(text)
            if opp_frame and text not in seen_opp:
                opp_quotes.append({'frame': opp_frame, 'text': text})
                seen_opp.add(text)

    def select_quotes(quotes, min_len=160, max_len=360, limit=3):
        filtered = [q for q in quotes if min_len <= len(first_sentence(q['text'])) <= max_len]
        if len(filtered) < limit:
            filtered = quotes
        filtered.sort(key=lambda x: len(first_sentence(x['text'])))
        selected = []
        for q in filtered:
            key = excerpt_key(q['text'])
            if key and key not in USED_EXCERPTS:
                selected.append(q)
                USED_EXCERPTS.add(key)
            if len(selected) >= limit:
                break
        if len(selected) < limit:
            for q in quotes:
                key = excerpt_key(q['text'])
                if key and key not in USED_EXCERPTS:
                    selected.append(q)
                    USED_EXCERPTS.add(key)
                if len(selected) >= limit:
                    break
        return selected

    worldview = compute_worldview_components(df)

    return {
        'threat_data': threat_data,
        'opportunity_data': opp_data,
        'threat_total': sum(x[1] for x in threat_data),
        'opportunity_total': sum(x[1] for x in opp_data),
        'gai': worldview['worldview_index'],
        'frame_balance': worldview['frame_balance'],
        'frame_total': worldview['frame_total'],
        'tone_index': worldview['tone_index'],
        'tone_total': worldview['tone_total'],
        'weight_frame': worldview['weight_frame'],
        'weight_tone': worldview['weight_tone'],
        'threat_quotes': select_quotes(threat_quotes),
        'opportunity_quotes': select_quotes(opp_quotes),
    }


# =============================================================================
# ACTOR SENTIMENT DATA
# =============================================================================

def prepare_actor_sentiment_data(df):
    """Prepare actor sentiment analysis data."""
    actor_data = defaultdict(lambda: {'POSITIVE': 0, 'NEUTRAL': 0, 'NEGATIVE': 0, 'AMBIGUOUS': 0})

    for val in df['actors'].dropna():
        actors = safe_json_parse(val)
        if not actors:
            continue
        for a in actors:
            name = normalize_actor_name(a.get('actor', ''))
            valence = a.get('valence', 'NEUTRAL')
            actor_data[name][valence] += 1

    actor_metrics = []
    for actor, counts in actor_data.items():
        total = sum(counts.values())
        if total < 3:
            continue
        pos = counts['POSITIVE']
        neg = counts['NEGATIVE']
        net = (pos - neg) / total
        actor_metrics.append({
            'actor': actor,
            'total': total,
            'positive': pos,
            'negative': neg,
            'neutral': counts['NEUTRAL'],
            'net_sentiment': net,
            'pos_ratio': pos / total,
            'neg_ratio': neg / total,
        })

    actor_metrics.sort(key=lambda x: x['total'], reverse=True)

    quotes = {'positive': [], 'negative': []}
    text_col = get_text_column(df)
    if text_col:
        seen_pos = set()
        seen_neg = set()
        for _, row in df.iterrows():
            text = str(row.get(text_col, '')).strip()
            if not text or text.lower() == 'nan':
                continue
            actors = safe_json_parse(row.get('actors'))
            if not actors:
                continue
            pos_added = False
            neg_added = False
            for a in actors:
                valence = a.get('valence')
                actor_name = normalize_actor_name(a.get('actor', ''))
                if valence == 'POSITIVE' and not pos_added and text not in seen_pos:
                    quotes['positive'].append({'text': text, 'actor': actor_name})
                    seen_pos.add(text)
                    pos_added = True
                if valence == 'NEGATIVE' and not neg_added and text not in seen_neg:
                    quotes['negative'].append({'text': text, 'actor': actor_name})
                    seen_neg.add(text)
                    neg_added = True
                if pos_added and neg_added:
                    break

    def select_actor_quotes(quotes_list, min_len=160, max_len=360, limit=3):
        filtered = [q for q in quotes_list if min_len <= len(first_sentence(q['text'])) <= max_len]
        if len(filtered) < limit:
            filtered = quotes_list
        filtered.sort(key=lambda x: len(first_sentence(x['text'])))
        selected = []
        for q in filtered:
            key = excerpt_key(q['text'])
            if key and key not in USED_EXCERPTS:
                selected.append(q)
                USED_EXCERPTS.add(key)
            if len(selected) >= limit:
                break
        if len(selected) < limit:
            for q in quotes_list:
                key = excerpt_key(q['text'])
                if key and key not in USED_EXCERPTS:
                    selected.append(q)
                    USED_EXCERPTS.add(key)
                if len(selected) >= limit:
                    break
        return selected

    return {
        'actors': actor_metrics[:12],
        'all_actors': actor_metrics,
        'quotes': {
            'positive': select_actor_quotes(quotes['positive']),
            'negative': select_actor_quotes(quotes['negative']),
        },
    }


# =============================================================================
# POLICY DATA
# =============================================================================

def prepare_policy_data(df):
    """Prepare policy analysis data."""
    policies = []
    for val in df['policy_content'].dropna():
        p = safe_json_parse(val)
        if p and p.get('present'):
            policies.append({
                'domain': p.get('domain'),
                'action': p.get('action_type'),
                'specificity': p.get('specificity'),
            })

    if not policies:
        return None

    policies_df = pd.DataFrame(policies)
    domain_counts = policies_df['domain'].value_counts().head(10)
    action_counts = policies_df['action'].value_counts()
    spec_counts = policies_df['specificity'].value_counts()

    return {
        'policies': policies,
        'domain_counts': domain_counts.to_dict(),
        'action_counts': action_counts.to_dict(),
        'specificity_counts': {
            'CONCRETE': spec_counts.get('CONCRETE', 0),
            'PROGRAMMATIC': spec_counts.get('PROGRAMMATIC', 0),
            'ASPIRATIONAL': spec_counts.get('ASPIRATIONAL', 0),
        },
        'ambition_index': compute_policy_ambition_index(df),
    }


# =============================================================================
# RHETORICAL DATA
# =============================================================================

def prepare_rhetorical_data(df):
    """Prepare rhetorical strategy data."""
    act_counts = count_list_column(df, 'speech_act')
    emo_counts = df['emotional_register'].value_counts().to_dict()

    top_acts = ['PROPOSING', 'EXHORTING', 'DIAGNOSING', 'STATING', 'REASSURING',
                'DENOUNCING', 'WARNING', 'COMMITTING', 'FRAMING']
    top_acts = [a for a in top_acts if a in act_counts]

    emo_order = ['PRAGMATIC', 'CONFIDENT', 'NEUTRAL', 'COMBATIVE', 'ALARMIST',
                 'GRATEFUL', 'EXASPERATED', 'DEFIANT', 'SOLEMN', 'INDIGNANT']
    emo_order = [e for e in emo_order if e in emo_counts]

    quotes = []
    text_col = get_text_column(df)
    if text_col:
        for _, row in df.iterrows():
            text = str(row.get(text_col, '')).strip()
            if not text or text.lower() == 'nan':
                continue
            acts = extract_all_list_values(safe_json_parse(row.get('speech_act')) or [])
            act = next((a for a in acts if a in top_acts), None)
            emo = row.get('emotional_register')
            if act:
                quotes.append({'text': text, 'label': act, 'kind': 'speech_act'})
            if emo in emo_order:
                quotes.append({'text': text, 'label': emo, 'kind': 'emotional_register'})

    return {
        'speech_acts': {a: act_counts.get(a, 0) for a in top_acts},
        'emotional_registers': {e: emo_counts.get(e, 0) for e in emo_order},
        'action_index': compute_action_orientation_index(df),
        'tone_index': compute_diplomatic_tone_index(df),
        'quotes': select_excerpt_candidates(quotes, min_len=160, max_len=360, limit=4),
    }


# =============================================================================
# AGENCY DATA
# =============================================================================

def prepare_agency_data(df):
    """Prepare France agency profile data."""
    pos_counts = count_list_column(df, 'france_positioning')
    pos_counts.pop('NOT_APPLICABLE', None)

    pos_order = ['ACTIVE_AGENT', 'PARTNER', 'REACTIVE_AGENT', 'LEADER', 'POWER',
                 'MODEL', 'RELIABLE_ALLY', 'VICTIM']
    pos_order = [p for p in pos_order if p in pos_counts]

    active = ['ACTIVE_AGENT', 'LEADER', 'POWER', 'MODEL']
    cooperative = ['PARTNER', 'RELIABLE_ALLY']
    reactive = ['REACTIVE_AGENT', 'VICTIM']

    quotes = []
    text_col = get_text_column(df)
    if text_col:
        for _, row in df.iterrows():
            text = str(row.get(text_col, '')).strip()
            if not text or text.lower() == 'nan':
                continue
            positions = extract_all_list_values(safe_json_parse(row.get('france_positioning')) or [])
            label = None
            if any(p in positions for p in active):
                label = 'ACTIVE'
            elif any(p in positions for p in cooperative):
                label = 'COOPERATIVE'
            elif any(p in positions for p in reactive):
                label = 'REACTIVE'
            if label:
                quotes.append({'text': text, 'label': label, 'kind': 'agency_level'})

    return {
        'positioning_counts': {p: pos_counts.get(p, 0) for p in pos_order},
        'categories': {
            'active': sum(pos_counts.get(p, 0) for p in active),
            'cooperative': sum(pos_counts.get(p, 0) for p in cooperative),
            'reactive': sum(pos_counts.get(p, 0) for p in reactive),
        },
        'agency_index': compute_agency_index(df),
        'quotes': select_excerpt_candidates(quotes, min_len=160, max_len=360, limit=4),
    }


# =============================================================================
# SUMMARY STATS
# =============================================================================

def compute_summary_stats(df):
    """Compute summary statistics for the speech."""
    n_sentences = len(df)

    n_policies = sum(1 for val in df['policy_content'].dropna()
                    if safe_json_parse(val) and safe_json_parse(val).get('present'))

    n_stances = sum(len(safe_json_parse(val) or []) for val in df['issue_stances'].dropna())
    n_actors = sum(len(safe_json_parse(val) or []) for val in df['actors'].dropna())

    frame_counts = count_list_column(df, 'geopolitical_frame')
    frame_counts.pop('NONE', None)
    n_frames = sum(frame_counts.values())

    return {
        'n_sentences': n_sentences,
        'n_policies': n_policies,
        'n_stances': n_stances,
        'n_actors': n_actors,
        'n_frames': n_frames,
    }


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    print("Loading data...")
    df = load_data()
    print(f"Loaded {len(df)} sentences")

    print("\nComputing indices...")
    indices = compute_all_indices(df)
    for name, value in indices.items():
        if 'anxiety' in name or 'tone' in name:
            print(f"  {name}: {value:+.2f}")
        else:
            print(f"  {name}: {value:.0%}")

    print("\nSummary stats:")
    stats = compute_summary_stats(df)
    for name, value in stats.items():
        print(f"  {name}: {value}")
