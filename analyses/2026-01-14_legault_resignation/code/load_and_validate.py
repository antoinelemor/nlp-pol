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
Load annotated CSV data and parse JSON annotation fields.
Validate annotation schema and provide clean dataframes.

Dependencies:
-------------
- pandas (DataFrame operations)
- json (JSON parsing)
- pathlib (Path handling)

MAIN FEATURES:
--------------
1) Load annotated CSV with proper encoding
2) Parse JSON annotation columns
3) Validate annotation schema
4) Extract nested fields (actors, identity_themes, etc.)

Author:
-------
Antoine Lemor
"""

import json
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any


# =============================================================================
# DATA PATHS
# =============================================================================

ANALYSIS_DIR = Path(__file__).parent.parent
DATA_DIR = ANALYSIS_DIR / 'data'
OUTPUT_DIR = ANALYSIS_DIR / 'output' / 'figures'


# =============================================================================
# ANNOTATION SCHEMA
# =============================================================================

EXPECTED_COLUMNS = [
    'segment_id', 'speaker', 'text', 'video_id', 'title', 'date', 'channel',
    'speech_act', 'justification_type', 'policy_domain', 'emotional_register',
    'actors', 'temporality', 'identity_themes', 'rhetorical_devices',
    'legacy_framing', 'implicit_references'
]

LIST_FIELDS = ['speech_act', 'policy_domain', 'temporality', 'rhetorical_devices']
DICT_FIELDS = ['justification_type', 'identity_themes', 'implicit_references']
NESTED_LIST_FIELDS = ['actors']
STRING_FIELDS = ['emotional_register', 'legacy_framing']


# =============================================================================
# LOADING FUNCTIONS
# =============================================================================

def load_annotated_data(filename: Optional[str] = None) -> pd.DataFrame:
    """
    Load annotated CSV file from data directory.

    Args:
        filename: Name of CSV file. If None, loads the first CSV in data dir.

    Returns:
        DataFrame with raw data.
    """
    if filename is None:
        csv_files = list(DATA_DIR.glob('*.csv'))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")
        filepath = csv_files[0]
    else:
        filepath = DATA_DIR / filename

    df = pd.read_csv(filepath, encoding='utf-8')
    print(f"Loaded {len(df)} sentences from {filepath.name}")
    return df


def parse_json_field(value: Any) -> Any:
    """
    Parse a JSON string field, handling edge cases.

    Args:
        value: String containing JSON or already parsed value.

    Returns:
        Parsed JSON object (dict, list, or original value).
    """
    if pd.isna(value):
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def parse_annotations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse all JSON annotation columns in the dataframe.

    Handles two formats:
    1. Unified 'annotation' column containing full JSON
    2. Separate columns for each annotation field

    Args:
        df: DataFrame with raw annotation strings.

    Returns:
        DataFrame with parsed JSON fields.
    """
    df = df.copy()

    # Check if we have a unified 'annotation' column (from LLM_Tool)
    if 'annotation' in df.columns:
        # Parse the unified annotation column and expand to separate columns
        annotation_fields = LIST_FIELDS + DICT_FIELDS + NESTED_LIST_FIELDS + STRING_FIELDS

        def expand_annotation(row):
            """Expand annotation JSON into separate fields."""
            ann = parse_json_field(row.get('annotation'))
            if isinstance(ann, dict):
                for field in annotation_fields:
                    row[field] = ann.get(field)
            return row

        df = df.apply(expand_annotation, axis=1)
    else:
        # Parse individual columns (legacy format)
        # Parse list fields
        for col in LIST_FIELDS:
            if col in df.columns:
                df[col] = df[col].apply(parse_json_field)

        # Parse dict fields
        for col in DICT_FIELDS:
            if col in df.columns:
                df[col] = df[col].apply(parse_json_field)

        # Parse nested list fields (list of dicts)
        for col in NESTED_LIST_FIELDS:
            if col in df.columns:
                df[col] = df[col].apply(parse_json_field)

    return df


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def extract_speech_acts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Explode speech_act column to get counts per speech act type.

    Returns:
        DataFrame with columns: segment_id, speech_act
    """
    records = []
    for _, row in df.iterrows():
        acts = row.get('speech_act', [])
        if isinstance(acts, list):
            for act in acts:
                records.append({
                    'segment_id': row['segment_id'],
                    'text': row['text'],
                    'speech_act': act
                })
    return pd.DataFrame(records)


def extract_policy_domains(df: pd.DataFrame) -> pd.DataFrame:
    """
    Explode policy_domain column to get counts per domain.

    Returns:
        DataFrame with columns: segment_id, policy_domain
    """
    records = []
    for _, row in df.iterrows():
        domains = row.get('policy_domain', [])
        if isinstance(domains, list):
            for domain in domains:
                if domain != 'NONE':
                    records.append({
                        'segment_id': row['segment_id'],
                        'text': row['text'],
                        'policy_domain': domain
                    })
    return pd.DataFrame(records)


def extract_justifications(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract justification information from justification_type dict.

    Returns:
        DataFrame with columns: segment_id, present, category, targets
    """
    records = []
    for _, row in df.iterrows():
        just = row.get('justification_type', {})
        if isinstance(just, dict) and just.get('present', False):
            targets = just.get('target', [])
            if isinstance(targets, str):
                targets = [targets]
            for target in targets:
                records.append({
                    'segment_id': row['segment_id'],
                    'text': row['text'],
                    'justification_category': just.get('justification_category'),
                    'justification_target': target
                })
    return pd.DataFrame(records)


def extract_actors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract actor mentions from actors list.

    Returns:
        DataFrame with columns: segment_id, actor, actor_type, valence, role
    """
    records = []
    for _, row in df.iterrows():
        actors = row.get('actors', [])
        if isinstance(actors, list):
            for actor in actors:
                if isinstance(actor, dict):
                    records.append({
                        'segment_id': row['segment_id'],
                        'text': row['text'],
                        'actor': actor.get('actor'),
                        'actor_type': actor.get('actor_type'),
                        'valence': actor.get('valence'),
                        'role': actor.get('role')
                    })
    return pd.DataFrame(records)


def extract_identity_themes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract identity theme information.

    Returns:
        DataFrame with columns: segment_id, theme, stance
    """
    records = []
    for _, row in df.iterrows():
        identity = row.get('identity_themes', {})
        if isinstance(identity, dict) and identity.get('present', False):
            themes = identity.get('theme', [])
            stance = identity.get('stance')
            if isinstance(themes, str):
                themes = [themes]
            for theme in themes:
                records.append({
                    'segment_id': row['segment_id'],
                    'text': row['text'],
                    'identity_theme': theme,
                    'identity_stance': stance
                })
    return pd.DataFrame(records)


def extract_emotional_register(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract emotional register (already a single value per sentence).

    Returns:
        DataFrame with columns: segment_id, emotional_register
    """
    records = []
    for _, row in df.iterrows():
        emotion = row.get('emotional_register')
        if emotion and emotion != 'NEUTRAL':
            records.append({
                'segment_id': row['segment_id'],
                'text': row['text'],
                'emotional_register': emotion
            })
    return pd.DataFrame(records)


def extract_legacy_framing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract legacy framing (already a single value per sentence).

    Returns:
        DataFrame with columns: segment_id, legacy_framing
    """
    records = []
    for _, row in df.iterrows():
        legacy = row.get('legacy_framing')
        if legacy and legacy != 'NONE':
            records.append({
                'segment_id': row['segment_id'],
                'text': row['text'],
                'legacy_framing': legacy
            })
    return pd.DataFrame(records)


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_annotations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate annotation data and return summary statistics.

    Returns:
        Dictionary with validation results and statistics.
    """
    results = {
        'total_sentences': len(df),
        'missing_fields': {},
        'field_coverage': {},
        'errors': []
    }

    # Check for missing fields
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            results['missing_fields'][col] = 'Column missing'

    # Calculate coverage for each annotation field
    annotation_cols = LIST_FIELDS + DICT_FIELDS + NESTED_LIST_FIELDS + STRING_FIELDS
    for col in annotation_cols:
        if col in df.columns:
            non_null = df[col].notna().sum()
            results['field_coverage'][col] = {
                'count': int(non_null),
                'percentage': round(100 * non_null / len(df), 1)
            }

    return results


def print_validation_report(validation: Dict[str, Any]) -> None:
    """Print a formatted validation report."""
    print("\n" + "="*60)
    print("ANNOTATION VALIDATION REPORT")
    print("="*60)
    print(f"Total sentences: {validation['total_sentences']}")

    if validation['missing_fields']:
        print("\nMissing fields:")
        for field, msg in validation['missing_fields'].items():
            print(f"  - {field}: {msg}")

    print("\nField coverage:")
    for field, stats in validation['field_coverage'].items():
        print(f"  - {field}: {stats['count']} ({stats['percentage']}%)")

    if validation['errors']:
        print("\nErrors:")
        for error in validation['errors']:
            print(f"  - {error}")

    print("="*60 + "\n")


# =============================================================================
# MAIN LOADING FUNCTION
# =============================================================================

def load_data(filename: Optional[str] = None, validate: bool = True) -> pd.DataFrame:
    """
    Main function to load and parse annotated data.

    Args:
        filename: Optional specific filename to load.
        validate: Whether to run validation and print report.

    Returns:
        Parsed DataFrame ready for analysis.
    """
    df = load_annotated_data(filename)
    df = parse_annotations(df)

    if validate:
        validation = validate_annotations(df)
        print_validation_report(validation)

    return df


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == '__main__':
    # Test loading
    try:
        df = load_data()
        print(f"Successfully loaded {len(df)} sentences")
        print(f"Columns: {list(df.columns)}")
    except FileNotFoundError as e:
        print(f"No data file found yet: {e}")
        print("Waiting for annotation to complete...")
