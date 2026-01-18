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
Compute composite indices and prepare data aggregations
for the Legault Resignation Speech analysis.

Dependencies:
-------------
- pandas (DataFrame operations)
- numpy (numerical computations)
- config (color palettes, weights)
- load_and_validate (data extraction functions)

MAIN FEATURES:
--------------
1) Compute Emotional Tone Index
2) Compute Justification Balance Index
3) Compute Legacy Emphasis Index
4) Prepare aggregated data for figures
5) Select representative excerpts

Author:
-------
Antoine Lemor
"""

import pandas as pd
import numpy as np
from collections import Counter
from typing import Dict, List, Tuple, Optional, Set

from config import EMOTIONAL_REGISTER_WEIGHTS, get_labels
from load_and_validate import (
    extract_speech_acts,
    extract_policy_domains,
    extract_justifications,
    extract_actors,
    extract_identity_themes,
    extract_emotional_register,
    extract_legacy_framing
)


# =============================================================================
# GLOBAL EXCERPT REGISTRY (for deduplication across figures)
# =============================================================================

USED_EXCERPTS: Set[str] = set()


def reset_excerpts():
    """Reset the excerpt registry (call at start of generation)."""
    global USED_EXCERPTS
    USED_EXCERPTS = set()


# =============================================================================
# COMPOSITE INDICES
# =============================================================================

def compute_emotional_tone_index(df: pd.DataFrame) -> Tuple[float, Dict]:
    """
    Compute overall emotional tone index.

    Formula:
        tone_index = mean(emotion_weights) / max_weight

    Range: [-1, +1] where -1 = negative, +1 = positive

    Returns:
        Tuple of (index_value, metadata_dict)
    """
    emotions = df['emotional_register'].dropna().tolist()
    if not emotions:
        return 0.0, {'n': 0, 'distribution': {}}

    weights = [EMOTIONAL_REGISTER_WEIGHTS.get(e, 0) for e in emotions]
    max_weight = max(abs(w) for w in EMOTIONAL_REGISTER_WEIGHTS.values())

    tone_index = np.mean(weights) / max_weight if max_weight > 0 else 0

    distribution = Counter(emotions)

    return float(tone_index), {
        'n': len(emotions),
        'distribution': dict(distribution),
        'mean_weight': float(np.mean(weights)),
        'formula': 'mean(emotion_weights) / max_weight'
    }


def compute_justification_balance_index(df: pd.DataFrame) -> Tuple[float, Dict]:
    """
    Compute balance between resignation justification vs record defense.

    Formula:
        balance = (record_defense - resignation_rationale) / total_justifications

    Range: [-1, +1] where -1 = focused on resignation, +1 = focused on record

    Returns:
        Tuple of (index_value, metadata_dict)
    """
    justifications_df = extract_justifications(df)

    if justifications_df.empty:
        return 0.0, {'n': 0, 'resignation': 0, 'record': 0}

    target_counts = justifications_df['justification_target'].value_counts()

    # Resignation-related targets
    resignation_targets = ['RESIGNATION']
    resignation_count = sum(target_counts.get(t, 0) for t in resignation_targets)

    # Record-related targets
    record_targets = ['OVERALL_MANDATE', 'SPECIFIC_POLICY', 'PANDEMIC_RESPONSE',
                      'ECONOMIC_POLICY', 'IDENTITY_POLICY', 'PARTY_CREATION']
    record_count = sum(target_counts.get(t, 0) for t in record_targets)

    total = resignation_count + record_count
    if total == 0:
        balance = 0.0
    else:
        balance = (record_count - resignation_count) / total

    return float(balance), {
        'n': int(total),
        'resignation': int(resignation_count),
        'record': int(record_count),
        'formula': '(record_defense - resignation_rationale) / total'
    }


def compute_legacy_emphasis_index(df: pd.DataFrame) -> Tuple[float, Dict]:
    """
    Compute how much the speech emphasizes legacy construction.

    Formula:
        legacy_index = legacy_sentences / total_sentences

    Range: [0, 1] where 0 = no legacy framing, 1 = entirely legacy-focused

    Returns:
        Tuple of (index_value, metadata_dict)
    """
    legacy_df = extract_legacy_framing(df)
    total = len(df)

    if total == 0:
        return 0.0, {'n': 0, 'total': 0}

    legacy_count = len(legacy_df)
    legacy_index = legacy_count / total

    distribution = Counter(legacy_df['legacy_framing'].tolist()) if not legacy_df.empty else {}

    return float(legacy_index), {
        'n': int(legacy_count),
        'total': int(total),
        'distribution': dict(distribution),
        'formula': 'legacy_sentences / total_sentences'
    }


def compute_identity_emphasis_index(df: pd.DataFrame) -> Tuple[float, Dict]:
    """
    Compute how much the speech emphasizes identity/nationalist themes.

    Formula:
        identity_index = identity_sentences / total_sentences

    Range: [0, 1]

    Returns:
        Tuple of (index_value, metadata_dict)
    """
    identity_df = extract_identity_themes(df)
    total = len(df)

    if total == 0:
        return 0.0, {'n': 0, 'total': 0}

    identity_count = len(identity_df['segment_id'].unique())
    identity_index = identity_count / total

    theme_dist = Counter(identity_df['identity_theme'].tolist()) if not identity_df.empty else {}
    stance_dist = Counter(identity_df['identity_stance'].dropna().tolist()) if not identity_df.empty else {}

    return float(identity_index), {
        'n': int(identity_count),
        'total': int(total),
        'theme_distribution': dict(theme_dist),
        'stance_distribution': dict(stance_dist),
        'formula': 'identity_sentences / total_sentences'
    }


def compute_gratitude_index(df: pd.DataFrame) -> Tuple[float, Dict]:
    """
    Compute proportion of speech dedicated to thanking.

    Formula:
        gratitude_index = thanking_sentences / total_sentences

    Returns:
        Tuple of (index_value, metadata_dict)
    """
    speech_acts_df = extract_speech_acts(df)
    total = len(df)

    if total == 0 or speech_acts_df.empty:
        return 0.0, {'n': 0, 'total': 0}

    thanking_count = len(speech_acts_df[speech_acts_df['speech_act'] == 'THANKING']['segment_id'].unique())
    gratitude_index = thanking_count / total

    return float(gratitude_index), {
        'n': int(thanking_count),
        'total': int(total),
        'formula': 'thanking_sentences / total_sentences'
    }


def compute_action_orientation_index(df: pd.DataFrame) -> Tuple[float, Dict]:
    """
    Compute action vs. descriptive orientation of the speech.

    Formula:
        action_index = (action_acts - descriptive_acts) / (action_acts + descriptive_acts)

    Range: [-1, +1] where -1 = descriptive, +1 = performative

    Returns:
        Tuple of (index_value, metadata_dict)
    """
    speech_acts_df = extract_speech_acts(df)

    if speech_acts_df.empty:
        return 0.0, {'n': 0, 'action': 0, 'descriptive': 0}

    action_acts = ['ANNOUNCING', 'COMMITTING', 'EXHORTING', 'APPEALING', 'PROPOSING']
    descriptive_acts = ['STATING', 'EXPLAINING', 'DIAGNOSING', 'FRAMING']

    act_counts = speech_acts_df['speech_act'].value_counts().to_dict()
    action_count = sum(act_counts.get(a, 0) for a in action_acts)
    descriptive_count = sum(act_counts.get(a, 0) for a in descriptive_acts)

    total = action_count + descriptive_count
    if total == 0:
        action_index = 0.0
    else:
        action_index = (action_count - descriptive_count) / total

    return float(action_index), {
        'n': int(total),
        'action': int(action_count),
        'descriptive': int(descriptive_count),
        'formula': '(action - descriptive) / total'
    }


# =============================================================================
# DATA AGGREGATION FUNCTIONS
# =============================================================================

def aggregate_speech_acts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate speech act counts.

    Returns:
        DataFrame with columns: speech_act, count, percentage
    """
    speech_acts_df = extract_speech_acts(df)
    if speech_acts_df.empty:
        return pd.DataFrame(columns=['speech_act', 'count', 'percentage'])

    counts = speech_acts_df['speech_act'].value_counts().reset_index()
    counts.columns = ['speech_act', 'count']
    counts['percentage'] = (counts['count'] / counts['count'].sum() * 100).round(1)
    return counts.sort_values('count', ascending=False)


def aggregate_policy_domains(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate policy domain counts.

    Returns:
        DataFrame with columns: policy_domain, count, percentage
    """
    domains_df = extract_policy_domains(df)
    if domains_df.empty:
        return pd.DataFrame(columns=['policy_domain', 'count', 'percentage'])

    counts = domains_df['policy_domain'].value_counts().reset_index()
    counts.columns = ['policy_domain', 'count']
    counts['percentage'] = (counts['count'] / counts['count'].sum() * 100).round(1)
    return counts.sort_values('count', ascending=False)


def aggregate_justification_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate justification category counts.

    Returns:
        DataFrame with columns: justification_category, count, percentage
    """
    just_df = extract_justifications(df)
    if just_df.empty:
        return pd.DataFrame(columns=['justification_category', 'count', 'percentage'])

    counts = just_df['justification_category'].value_counts().reset_index()
    counts.columns = ['justification_category', 'count']
    counts['percentage'] = (counts['count'] / counts['count'].sum() * 100).round(1)
    return counts.sort_values('count', ascending=False)


def aggregate_justification_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate justification target counts.

    Returns:
        DataFrame with columns: justification_target, count, percentage
    """
    just_df = extract_justifications(df)
    if just_df.empty:
        return pd.DataFrame(columns=['justification_target', 'count', 'percentage'])

    counts = just_df['justification_target'].value_counts().reset_index()
    counts.columns = ['justification_target', 'count']
    counts['percentage'] = (counts['count'] / counts['count'].sum() * 100).round(1)
    return counts.sort_values('count', ascending=False)


def aggregate_actors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate actor mentions by actor name and valence.

    Returns:
        DataFrame with columns: actor, actor_type, valence, count
    """
    actors_df = extract_actors(df)
    if actors_df.empty:
        return pd.DataFrame(columns=['actor', 'actor_type', 'valence', 'count'])

    counts = actors_df.groupby(['actor', 'actor_type', 'valence']).size().reset_index(name='count')
    return counts.sort_values('count', ascending=False)


def aggregate_actors_by_valence(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Group actors by valence (positive, negative, neutral, mixed).

    Returns:
        Dict with keys: 'POSITIVE', 'NEGATIVE', 'NEUTRAL', 'MIXED'
    """
    actors_df = extract_actors(df)
    result = {}

    for valence in ['POSITIVE', 'NEGATIVE', 'NEUTRAL', 'MIXED']:
        subset = actors_df[actors_df['valence'] == valence]
        if not subset.empty:
            counts = subset['actor'].value_counts().reset_index()
            counts.columns = ['actor', 'count']
            result[valence] = counts

    return result


def aggregate_emotional_register(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate emotional register counts.

    Returns:
        DataFrame with columns: emotional_register, count, percentage
    """
    emotions = df['emotional_register'].dropna().value_counts().reset_index()
    emotions.columns = ['emotional_register', 'count']
    emotions['percentage'] = (emotions['count'] / emotions['count'].sum() * 100).round(1)
    return emotions


def aggregate_identity_themes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate identity theme counts.

    Returns:
        DataFrame with columns: identity_theme, count, percentage
    """
    identity_df = extract_identity_themes(df)
    if identity_df.empty:
        return pd.DataFrame(columns=['identity_theme', 'count', 'percentage'])

    counts = identity_df['identity_theme'].value_counts().reset_index()
    counts.columns = ['identity_theme', 'count']
    counts['percentage'] = (counts['count'] / counts['count'].sum() * 100).round(1)
    return counts.sort_values('count', ascending=False)


def aggregate_legacy_framing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate legacy framing counts.

    Returns:
        DataFrame with columns: legacy_framing, count, percentage
    """
    legacy_df = extract_legacy_framing(df)
    if legacy_df.empty:
        return pd.DataFrame(columns=['legacy_framing', 'count', 'percentage'])

    counts = legacy_df['legacy_framing'].value_counts().reset_index()
    counts.columns = ['legacy_framing', 'count']
    counts['percentage'] = (counts['count'] / counts['count'].sum() * 100).round(1)
    return counts.sort_values('count', ascending=False)


# =============================================================================
# EXCERPT SELECTION
# =============================================================================

def select_excerpt_candidates(
    texts: List[str],
    min_len: int = 160,
    max_len: int = 360,
    limit: int = 3
) -> List[str]:
    """
    Select unique excerpts from candidates, filtered by length.

    Args:
        texts: List of candidate text excerpts.
        min_len: Minimum character length.
        max_len: Maximum character length.
        limit: Maximum number of excerpts to return.

    Returns:
        List of selected excerpts (added to USED_EXCERPTS registry).
    """
    global USED_EXCERPTS

    # Filter by length
    valid = [t for t in texts if min_len <= len(t) <= max_len]

    # Sort by length (prefer medium-length excerpts)
    valid = sorted(valid, key=lambda x: abs(len(x) - 250))

    # Filter out already used
    available = [t for t in valid if t not in USED_EXCERPTS]

    # Select and register
    selected = available[:limit]
    USED_EXCERPTS.update(selected)

    return selected


def get_excerpts_for_category(
    df: pd.DataFrame,
    category_col: str,
    category_value: str,
    limit: int = 2,
    min_len: int = 160,
    max_len: int = 360,
    fallback_any_length: bool = True
) -> List[Dict]:
    """
    Get representative excerpts for a specific category value.

    Args:
        df: DataFrame with parsed annotations.
        category_col: Column name to filter on.
        category_value: Value to filter for.
        limit: Maximum excerpts to return.
        min_len: Minimum character length for excerpts.
        max_len: Maximum character length for excerpts.
        fallback_any_length: If True and no excerpts found, try without length filter.

    Returns:
        List of dicts with 'text' and 'segment_id' keys.
    """
    # Handle different column types
    if category_col == 'emotional_register':
        mask = df[category_col] == category_value
    elif category_col == 'legacy_framing':
        mask = df[category_col] == category_value
    elif category_col in ['speech_act', 'policy_domain', 'temporality', 'rhetorical_devices']:
        mask = df[category_col].apply(
            lambda x: category_value in x if isinstance(x, list) else False
        )
    else:
        mask = pd.Series([False] * len(df))

    filtered = df[mask]
    if filtered.empty:
        return []

    texts = filtered['text'].tolist()
    selected = select_excerpt_candidates(texts, min_len=min_len, max_len=max_len, limit=limit)

    # Fallback: if no excerpts found due to length filter, try without length filter
    if not selected and fallback_any_length and texts:
        selected = select_excerpt_candidates(texts, min_len=0, max_len=10000, limit=limit)

    return [
        {'text': t, 'segment_id': filtered[filtered['text'] == t]['segment_id'].iloc[0]}
        for t in selected
        if t in filtered['text'].values
    ]


def get_excerpts_for_nested_category(
    df: pd.DataFrame,
    category_col: str,
    nested_key: str,
    category_value: str,
    limit: int = 2,
    min_len: int = 160,
    max_len: int = 360,
    fallback_any_length: bool = True
) -> List[Dict]:
    """
    Get excerpts for nested category structures (e.g., identity_themes.theme).

    Args:
        df: DataFrame with parsed annotations.
        category_col: Column containing the nested dict (e.g., 'identity_themes').
        nested_key: Key within the dict to check (e.g., 'theme').
        category_value: Value to filter for.
        limit: Maximum excerpts to return.
        min_len: Minimum character length for excerpts.
        max_len: Maximum character length for excerpts.
        fallback_any_length: If True and no excerpts found, try without length filter.

    Returns:
        List of dicts with 'text' and 'segment_id' keys.
    """
    def check_nested(row):
        val = row.get(category_col)
        if not isinstance(val, dict):
            return False
        nested_val = val.get(nested_key)
        if isinstance(nested_val, list):
            return category_value in nested_val
        return nested_val == category_value

    mask = df.apply(check_nested, axis=1)
    filtered = df[mask]

    if filtered.empty:
        return []

    texts = filtered['text'].tolist()
    selected = select_excerpt_candidates(texts, min_len=min_len, max_len=max_len, limit=limit)

    # Fallback: if no excerpts found due to length filter, try without length filter
    if not selected and fallback_any_length and texts:
        selected = select_excerpt_candidates(texts, min_len=0, max_len=10000, limit=limit)

    return [
        {'text': t, 'segment_id': filtered[filtered['text'] == t]['segment_id'].iloc[0]}
        for t in selected
        if t in filtered['text'].values
    ]


def limit_sentences(text: str, max_sentences: int = 2) -> str:
    """
    Limit text to a maximum number of sentences.

    Args:
        text: Input text.
        max_sentences: Maximum sentences to keep.

    Returns:
        Truncated text.
    """
    import re
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return ' '.join(parts[:max_sentences])


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == '__main__':
    from load_and_validate import load_data

    try:
        df = load_data()

        print("\n" + "="*60)
        print("COMPOSITE INDICES")
        print("="*60)

        tone, tone_meta = compute_emotional_tone_index(df)
        print(f"Emotional Tone Index: {tone:.3f} (n={tone_meta['n']})")

        balance, balance_meta = compute_justification_balance_index(df)
        print(f"Justification Balance: {balance:.3f} (n={balance_meta['n']})")

        legacy, legacy_meta = compute_legacy_emphasis_index(df)
        print(f"Legacy Emphasis: {legacy:.3f} (n={legacy_meta['n']})")

        identity, identity_meta = compute_identity_emphasis_index(df)
        print(f"Identity Emphasis: {identity:.3f} (n={identity_meta['n']})")

        gratitude, gratitude_meta = compute_gratitude_index(df)
        print(f"Gratitude Index: {gratitude:.3f} (n={gratitude_meta['n']})")

        print("\n" + "="*60)
        print("AGGREGATIONS")
        print("="*60)

        print("\nSpeech Acts:")
        print(aggregate_speech_acts(df).head(5))

        print("\nPolicy Domains:")
        print(aggregate_policy_domains(df).head(5))

        print("\nEmotional Register:")
        print(aggregate_emotional_register(df).head(5))

    except FileNotFoundError:
        print("No data file found yet. Waiting for annotation...")
