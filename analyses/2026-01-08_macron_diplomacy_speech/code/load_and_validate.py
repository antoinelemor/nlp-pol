#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
load_and_validate.py

MAIN OBJECTIVE:
---------------
Load and validate LLM-annotated diplomatic discourse data.
Adapted for Macron Ambassadors Speech annotation schema (10 dimensions).

Dependencies:
-------------
- pandas
- json
- pathlib
- typing

MAIN FEATURES:
--------------
1) Load annotated JSON/CSV data
2) Parse complex nested annotation fields (actors, policy_content, issue_stances)
3) Validate annotation schema
4) Compute basic statistics

Author:
-------
Antoine Lemor
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import Counter


# =============================================================================
# EXPECTED SCHEMA (Macron Diplomatic Discourse)
# =============================================================================

EXPECTED_SCHEMA = {
    "speech_act": [
        "STATING", "DIAGNOSING", "DENOUNCING", "PROPOSING", "EXHORTING",
        "REASSURING", "FRAMING", "THANKING", "WARNING", "REJECTING", "COMMITTING"
    ],
    "geopolitical_frame": [
        # Threat frames
        "DISORDER", "POWER_POLITICS", "MULTILATERAL_DECLINE", "EXISTENTIAL_THREAT",
        "RECOLONIZATION", "FRAGMENTATION", "BRUTALIZATION", "VASSALIZATION",
        "REACTIONARY_INTERNATIONAL",
        # Opportunity frames
        "OPPORTUNITY", "RESILIENCE", "COOPERATION", "MULTILATERAL_RENEWAL",
        "PROGRESS", "SOLIDARITY", "LEADERSHIP_OPPORTUNITY", "STRATEGIC_ADVANTAGE",
        "REFORM_MOMENTUM",
        # Other
        "NONE"
    ],
    "france_positioning": [
        "ACTIVE_AGENT", "REACTIVE_AGENT", "VICTIM", "MODEL", "PARTNER",
        "LEADER", "RELIABLE_ALLY", "POWER", "NOT_APPLICABLE"
    ],
    "emotional_register": [
        "ALARMIST", "COMBATIVE", "CONFIDENT", "INDIGNANT", "PRAGMATIC",
        "SOLEMN", "DEFIANT", "GRATEFUL", "EXASPERATED", "NEUTRAL"
    ],
    "temporality": [
        "PAST_ACHIEVEMENT", "PAST_DIAGNOSIS", "PRESENT_CRISIS", "PRESENT_OBSERVATION",
        "FUTURE_ACTION", "FUTURE_RISK", "CONTINUITY", "RUPTURE", "ATEMPORAL"
    ],
}


# =============================================================================
# DATA LOADING
# =============================================================================

def load_annotated_data(filepath: Path) -> pd.DataFrame:
    """
    Load annotated data from CSV or JSON.

    Args:
        filepath: Path to the annotated data file

    Returns:
        DataFrame with annotations
    """
    filepath = Path(filepath)

    if filepath.suffix == '.csv':
        df = pd.read_csv(filepath)
    elif filepath.suffix == '.json':
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    elif filepath.suffix == '.jsonl':
        records = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                records.append(json.loads(line))
        df = pd.DataFrame(records)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")

    return df


def safe_json_parse(x):
    """Safely parse JSON strings."""
    if pd.isna(x):
        return {}
    if isinstance(x, dict):
        return x
    if isinstance(x, list):
        return x
    try:
        return json.loads(x)
    except (json.JSONDecodeError, TypeError):
        return {}


def parse_labels_column(df: pd.DataFrame, labels_col: str = None) -> pd.DataFrame:
    """
    Parse JSON labels column into separate columns.
    Handles the complex nested structure of diplomatic discourse annotations.

    Args:
        df: DataFrame with labels column
        labels_col: Name of the column containing JSON labels (auto-detects if None)

    Returns:
        DataFrame with expanded label columns
    """
    # Auto-detect labels column
    if labels_col is None:
        for col_name in ['labels', 'annotation', 'annotations']:
            if col_name in df.columns:
                labels_col = col_name
                break

    if labels_col is None or labels_col not in df.columns:
        return df

    # Parse the main annotation JSON
    labels_df = df[labels_col].apply(safe_json_parse).apply(pd.Series)

    # Combine with original data (drop the original labels column)
    result = pd.concat([df.drop(columns=[labels_col]), labels_df], axis=1)

    return result


def flatten_list_field(value):
    """
    Flatten list fields to single primary value (for analysis).
    If list, return first element. If string, return as-is.
    """
    if isinstance(value, list):
        return value[0] if value else None
    return value


def extract_all_list_values(value):
    """
    Extract all values from a list field.
    """
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except:
            pass
        return [value]
    return []


# =============================================================================
# ACTOR EXTRACTION
# =============================================================================

def extract_actors(df: pd.DataFrame, col: str = 'actors') -> pd.DataFrame:
    """
    Extract all actors with their mention types and valences.

    Args:
        df: DataFrame with actors column
        col: Column name

    Returns:
        DataFrame with actor, mention_type, valence, count
    """
    actors = []

    if col not in df.columns:
        return pd.DataFrame()

    for actor_list in df[col].dropna():
        if isinstance(actor_list, str):
            try:
                actor_list = json.loads(actor_list)
            except json.JSONDecodeError:
                continue

        if isinstance(actor_list, list):
            for actor in actor_list:
                if isinstance(actor, dict):
                    actors.append({
                        'actor': actor.get('actor', ''),
                        'mention_type': actor.get('mention_type', 'EXPLICIT'),
                        'valence': actor.get('valence', 'NEUTRAL')
                    })

    if not actors:
        return pd.DataFrame()

    actors_df = pd.DataFrame(actors)
    actor_counts = actors_df.groupby(['actor', 'mention_type', 'valence']).size().reset_index(name='count')

    return actor_counts.sort_values('count', ascending=False)


def extract_actor_valences(df: pd.DataFrame, col: str = 'actors') -> pd.DataFrame:
    """
    Extract actor valence summary (aggregated per actor).

    Returns:
        DataFrame with actor, positive, neutral, negative, total, net_score
    """
    actors = []

    if col not in df.columns:
        return pd.DataFrame()

    for actor_list in df[col].dropna():
        if isinstance(actor_list, str):
            try:
                actor_list = json.loads(actor_list)
            except json.JSONDecodeError:
                continue

        if isinstance(actor_list, list):
            for actor in actor_list:
                if isinstance(actor, dict):
                    actors.append({
                        'actor': actor.get('actor', ''),
                        'valence': actor.get('valence', 'NEUTRAL')
                    })

    if not actors:
        return pd.DataFrame()

    actors_df = pd.DataFrame(actors)

    # Pivot to get valence counts per actor
    pivot = actors_df.groupby(['actor', 'valence']).size().unstack(fill_value=0)

    # Ensure all valence columns exist
    for v in ['POSITIVE', 'NEUTRAL', 'NEGATIVE', 'AMBIGUOUS']:
        if v not in pivot.columns:
            pivot[v] = 0

    pivot['total'] = pivot.sum(axis=1)
    pivot['net_score'] = (pivot.get('POSITIVE', 0) - pivot.get('NEGATIVE', 0)) / pivot['total']

    return pivot.sort_values('total', ascending=False).reset_index()


# =============================================================================
# POLICY CONTENT EXTRACTION
# =============================================================================

def extract_policy_content(df: pd.DataFrame, col: str = 'policy_content') -> pd.DataFrame:
    """
    Extract policy content proposals.

    Returns:
        DataFrame with segment_id, domain, action_type, specificity, summary
    """
    policies = []

    if col not in df.columns:
        return pd.DataFrame()

    for idx, policy in df[col].items():
        if isinstance(policy, str):
            try:
                policy = json.loads(policy)
            except json.JSONDecodeError:
                continue

        if isinstance(policy, dict) and policy.get('present', False):
            policies.append({
                'segment_id': idx,
                'domain': policy.get('domain'),
                'action_type': policy.get('action_type'),
                'specificity': policy.get('specificity'),
                'summary': policy.get('summary')
            })

    return pd.DataFrame(policies)


# =============================================================================
# ISSUE STANCES EXTRACTION
# =============================================================================

def extract_issue_stances(df: pd.DataFrame, col: str = 'issue_stances') -> pd.DataFrame:
    """
    Extract issue stances.

    Returns:
        DataFrame with segment_id, issue, stance_type, stance_content, explicit
    """
    stances = []

    if col not in df.columns:
        return pd.DataFrame()

    for idx, stance_list in df[col].items():
        if isinstance(stance_list, str):
            try:
                stance_list = json.loads(stance_list)
            except json.JSONDecodeError:
                continue

        if isinstance(stance_list, list):
            for stance in stance_list:
                if isinstance(stance, dict):
                    stances.append({
                        'segment_id': idx,
                        'issue': stance.get('issue', ''),
                        'stance_type': stance.get('stance_type', ''),
                        'stance_content': stance.get('stance_content', ''),
                        'explicit': stance.get('explicit', True)
                    })

    return pd.DataFrame(stances)


# =============================================================================
# IMPLICIT REFERENCES EXTRACTION
# =============================================================================

def extract_implicit_references(df: pd.DataFrame, col: str = 'implicit_references') -> pd.DataFrame:
    """
    Extract implicit references to external events/actors.

    Returns:
        DataFrame with segment_id, reference_target, reference_type, confidence
    """
    refs = []

    if col not in df.columns:
        return pd.DataFrame()

    for idx, ref_data in df[col].items():
        if isinstance(ref_data, str):
            try:
                ref_data = json.loads(ref_data)
            except json.JSONDecodeError:
                continue

        if isinstance(ref_data, dict) and ref_data.get('present', False):
            targets = ref_data.get('targets', [])
            for target in targets:
                if isinstance(target, dict):
                    refs.append({
                        'segment_id': idx,
                        'reference_target': target.get('reference_target', ''),
                        'reference_type': target.get('reference_type', ''),
                        'confidence': target.get('confidence', 'MEDIUM')
                    })

    return pd.DataFrame(refs)


# =============================================================================
# VALIDATION
# =============================================================================

def validate_schema(df: pd.DataFrame, schema: Dict[str, List[str]] = EXPECTED_SCHEMA) -> Dict[str, Any]:
    """
    Validate that annotations conform to expected schema.

    Args:
        df: DataFrame with annotations
        schema: Expected schema dictionary

    Returns:
        Validation report dictionary
    """
    report = {
        "valid": True,
        "missing_columns": [],
        "invalid_values": {},
        "null_counts": {},
        "coverage": {}
    }

    for col, expected_values in schema.items():
        if col not in df.columns:
            report["missing_columns"].append(col)
            report["valid"] = False
            continue

        # Handle list columns (speech_act, geopolitical_frame, etc.)
        all_values = []
        for val in df[col].dropna():
            if isinstance(val, list):
                all_values.extend(val)
            elif isinstance(val, str):
                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, list):
                        all_values.extend(parsed)
                    else:
                        all_values.append(val)
                except:
                    all_values.append(val)
            else:
                all_values.append(val)

        # Check for unexpected values
        invalid = [v for v in set(all_values) if v not in expected_values]

        if invalid:
            report["invalid_values"][col] = invalid

        # Count nulls
        null_count = df[col].isna().sum()
        report["null_counts"][col] = null_count

        # Coverage per value
        coverage = Counter(all_values)
        total = sum(coverage.values())
        report["coverage"][col] = {k: v / total for k, v in coverage.items()} if total > 0 else {}

    return report


# =============================================================================
# STATISTICS
# =============================================================================

def compute_basic_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute basic statistics on the annotated dataset.

    Args:
        df: DataFrame with annotations

    Returns:
        Dictionary with statistics
    """
    stats = {
        "total_sentences": len(df),
        "by_speech_act": {},
        "by_geopolitical_frame": {},
        "by_france_positioning": {},
        "by_emotional_register": {},
        "by_temporality": {},
    }

    # Count list-type columns (flatten and count all values)
    list_columns = ['speech_act', 'geopolitical_frame', 'france_positioning', 'temporality']

    for col in list_columns:
        if col in df.columns:
            all_values = []
            for val in df[col].dropna():
                values = extract_all_list_values(val)
                all_values.extend(values)
            stats[f"by_{col}"] = dict(Counter(all_values))

    # Count single-value columns
    if 'emotional_register' in df.columns:
        stats['by_emotional_register'] = df['emotional_register'].value_counts().to_dict()

    return stats


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load and validate annotated data")
    parser.add_argument("input", type=str, help="Path to annotated data file")
    parser.add_argument("--output", type=str, help="Path to save cleaned data")

    args = parser.parse_args()

    # Load data
    print(f"Loading data from {args.input}...")
    df = load_annotated_data(args.input)

    # Parse labels if needed
    df = parse_labels_column(df)

    # Validate
    print("\nValidating schema...")
    report = validate_schema(df)

    if report["missing_columns"]:
        print(f"  Missing columns: {report['missing_columns']}")
    if report["invalid_values"]:
        print(f"  Invalid values: {report['invalid_values']}")

    # Stats
    print("\nBasic statistics:")
    stats = compute_basic_stats(df)
    print(f"  Total sentences: {stats['total_sentences']}")
    print(f"  Speech acts: {stats['by_speech_act']}")
    print(f"  Emotional register: {stats['by_emotional_register']}")

    # Extract complex fields
    print("\nExtracting complex fields...")
    actors_df = extract_actor_valences(df)
    if not actors_df.empty:
        print(f"  Top actors: {actors_df.head(5)['actor'].tolist()}")

    policies_df = extract_policy_content(df)
    print(f"  Policy proposals: {len(policies_df)}")

    stances_df = extract_issue_stances(df)
    print(f"  Issue stances: {len(stances_df)}")

    # Save if requested
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"\nSaved cleaned data to {args.output}")
