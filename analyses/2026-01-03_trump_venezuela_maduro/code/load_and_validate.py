#!/usr/bin/env python3
"""
PROJECT:
-------
NLP-POL - Political Discourse Analysis

TITLE:
------
01_load_and_validate.py

MAIN OBJECTIVE:
---------------
Load and validate LLM-annotated political discourse data.
Provides data cleaning, schema validation, and summary statistics.

Dependencies:
-------------
- pandas
- json
- pathlib
- typing

MAIN FEATURES:
--------------
1) Load annotated JSON/CSV data
2) Validate annotation schema
3) Compute basic statistics
4) Export cleaned dataset

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
# CONFIGURATION
# =============================================================================

EXPECTED_SCHEMA = {
    "utterance_type": ["question", "statement", "response"],
    "speaker_role": ["political_leader", "government_official", "journalist", "unknown"],
    "theme_primary": [
        "governance", "legal_justice", "military_operation", "diplomatic_relations",
        "humanitarian", "economic_resources", "security_threat", "domestic_politics",
        "personal_narrative", "meta_communication"
    ],
    "legitimation_frame": [
        "security_threat_neutralization", "legal_procedural", "economic_benefit",
        "humanitarian_liberation", "competence_demonstration", "historical_precedent", "null"
    ],
    "tone": [
        "triumphant", "threatening", "reassuring", "factual",
        "dismissive", "confrontational", "deferential"
    ],
    "response_type": ["direct", "partial", "pivot", "deflection", "attack", "null"]
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


def parse_labels_column(df: pd.DataFrame, labels_col: str = None) -> pd.DataFrame:
    """
    Parse JSON labels column into separate columns.

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

    def safe_parse(x):
        if pd.isna(x):
            return {}
        if isinstance(x, dict):
            return x
        try:
            return json.loads(x)
        except (json.JSONDecodeError, TypeError):
            return {}

    labels_df = df[labels_col].apply(safe_parse).apply(pd.Series)

    # Combine with original data
    result = pd.concat([df.drop(columns=[labels_col]), labels_df], axis=1)

    return result


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

        # Check for unexpected values
        actual_values = df[col].dropna().unique()
        invalid = [v for v in actual_values if v not in expected_values and v != "null"]

        if invalid:
            report["invalid_values"][col] = invalid

        # Count nulls
        null_count = df[col].isna().sum() + (df[col] == "null").sum()
        report["null_counts"][col] = null_count

        # Coverage per value
        report["coverage"][col] = df[col].value_counts(normalize=True).to_dict()

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
        "total_utterances": len(df),
        "by_speaker_role": {},
        "by_utterance_type": {},
        "by_theme": {},
        "by_tone": {},
        "by_legitimation": {},
        "by_response_type": {}
    }

    # Counts by category
    if "speaker_role" in df.columns:
        stats["by_speaker_role"] = df["speaker_role"].value_counts().to_dict()

    if "utterance_type" in df.columns:
        stats["by_utterance_type"] = df["utterance_type"].value_counts().to_dict()

    if "theme_primary" in df.columns:
        stats["by_theme"] = df["theme_primary"].value_counts().to_dict()

    if "tone" in df.columns:
        stats["by_tone"] = df["tone"].value_counts().to_dict()

    if "legitimation_frame" in df.columns:
        stats["by_legitimation"] = df["legitimation_frame"].value_counts().to_dict()

    if "response_type" in df.columns:
        stats["by_response_type"] = df["response_type"].value_counts().to_dict()

    return stats


def extract_themes_open(df: pd.DataFrame, col: str = "themes_open") -> Counter:
    """
    Extract and count all open themes.

    Args:
        df: DataFrame with themes_open column
        col: Column name

    Returns:
        Counter of all themes
    """
    all_themes = []

    if col not in df.columns:
        return Counter()

    for themes in df[col].dropna():
        if isinstance(themes, list):
            all_themes.extend(themes)
        elif isinstance(themes, str):
            try:
                parsed = json.loads(themes)
                if isinstance(parsed, list):
                    all_themes.extend(parsed)
            except json.JSONDecodeError:
                all_themes.append(themes)

    return Counter(all_themes)


def extract_entities(df: pd.DataFrame, col: str = "entities_mentioned") -> pd.DataFrame:
    """
    Extract all entities with their valences.

    Args:
        df: DataFrame with entities column
        col: Column name

    Returns:
        DataFrame with entity, type, valence, count
    """
    entities = []

    if col not in df.columns:
        return pd.DataFrame()

    for ent_list in df[col].dropna():
        if isinstance(ent_list, str):
            try:
                ent_list = json.loads(ent_list)
            except json.JSONDecodeError:
                continue

        if isinstance(ent_list, list):
            for ent in ent_list:
                if isinstance(ent, dict):
                    entities.append({
                        "entity": ent.get("entity", ""),
                        "type": ent.get("type", ""),
                        "valence": ent.get("valence", "neutral")
                    })

    if not entities:
        return pd.DataFrame()

    ent_df = pd.DataFrame(entities)
    ent_counts = ent_df.groupby(["entity", "type", "valence"]).size().reset_index(name="count")

    return ent_counts.sort_values("count", ascending=False)


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
    print(f"  Total utterances: {stats['total_utterances']}")
    print(f"  By speaker role: {stats['by_speaker_role']}")
    print(f"  By utterance type: {stats['by_utterance_type']}")

    # Save if requested
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"\nSaved cleaned data to {args.output}")
