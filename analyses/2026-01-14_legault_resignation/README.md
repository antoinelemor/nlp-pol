# Legault Resignation Speech Analysis

Discourse analysis of Quebec Premier François Legault's resignation speech (January 14, 2026).

## Presentations

- [French slides (PDF)](presentation/slides_fr.pdf)
- [English slides (PDF)](presentation/slides_en.pdf)

## Key Findings (n=122 sentences)

| Index | Value | Interpretation |
|-------|-------|----------------|
| **Emotional Tone** | +0.33 | Positive tone overall despite resignation |
| **Top Domain** | Party politics | 24 mentions (over healthcare, education) |
| **Legacy Emphasis** | 72% | 88/122 sentences dedicated to legacy construction |
| **Actor Sentiment** | +0.94 | Overwhelmingly positive (149 pos vs 5 neg) |
| **Identity Emphasis** | 16% | Quebec nationalism secondary to partisan themes |

## Data

| | |
|---|---|
| **Source** | CPAC video transcript ([YouTube](https://www.youtube.com/watch?v=bajLePwfbzo)) |
| **Context** | Resignation announcement, press conference, January 14, 2026 |
| **Sentences** | 122 |
| **Actor mentions** | 154 (149 positive, 5 negative) |
| **Annotation** | LLM with structured resignation discourse prompt (see `prompts/`) |

Each sentence is annotated with 10 dimensions:
- `speech_act`: Communicative function (THANKING, PRAISING, CLAIMING_ACHIEVEMENT, JUSTIFYING, ANNOUNCING, etc.)
- `justification_type`: Category and target (DECISION_RATIONALE, RECORD_DEFENSE, PERSONAL_CIRCUMSTANCES, etc.)
- `policy_domain`: Policy area using CAP categories (PARTY_POLITICS, HEALTHCARE, EDUCATION, ECONOMY, etc.)
- `emotional_register`: Emotional tone (GRATEFUL, PROUD, NOSTALGIC, SOLEMN, NEUTRAL, etc.)
- `actors`: Named entities with actor_type, valence (POSITIVE/NEGATIVE/NEUTRAL), and role
- `temporality`: Temporal orientation (PAST_ACHIEVEMENT, PRESENT_ANNOUNCEMENT, FUTURE_WISHES, etc.)
- `identity_themes`: Quebec identity themes with stance (FRENCH_LANGUAGE, NATIONAL_PRIDE, etc.)
- `rhetorical_devices`: Notable strategies (ENUMERATION, STATISTICS, PERSONAL_ANECDOTE, etc.)
- `legacy_framing`: How Legault positions his legacy (BUILDER, HISTORIC_ACHIEVEMENT, PRAGMATIST, etc.)
- `implicit_references`: References to events/contexts not explicitly named

---

## Composite Indices

### 1. Emotional Tone Index

**Range**: -1 (negative) to +1 (positive)

**Formula**:
```
tone_index = mean(emotion_weights) / max_weight
```

**Emotional register weights**:
| Register | Weight |
|----------|--------|
| GRATEFUL | +1.5 |
| PROUD | +1.5 |
| HOPEFUL | +1.0 |
| AFFECTIONATE | +1.0 |
| NOSTALGIC | +0.5 |
| SOLEMN | +0.5 |
| NEUTRAL | 0.0 |
| DETERMINED | 0.0 |
| HUMOROUS | 0.0 |
| RESIGNED | -0.5 |
| CONCERNED | -0.5 |
| DEFENSIVE | -1.0 |
| COMBATIVE | -1.5 |

---

### 2. Justification Balance Index

**Range**: -1 (resignation-focused) to +1 (record-focused)

**Formula**:
```
balance = (record_defense - resignation_rationale) / total_justifications
```

Where:
- **Resignation targets** = RESIGNATION
- **Record targets** = OVERALL_MANDATE, SPECIFIC_POLICY, PANDEMIC_RESPONSE, ECONOMIC_POLICY, IDENTITY_POLICY, PARTY_CREATION

---

### 3. Legacy Emphasis Index

**Range**: 0 (no legacy framing) to 1 (entirely legacy-focused)

**Formula**:
```
legacy_index = legacy_sentences / total_sentences
```

**Legacy framing values**: HISTORIC_ACHIEVEMENT, PERSONAL_SACRIFICE, PIONEERING, TRANSFORMATIVE, DEFENDER, BUILDER, PRAGMATIST

---

### 4. Identity Emphasis Index

**Range**: 0 to 1

**Formula**:
```
identity_index = identity_sentences / total_sentences
```

**Identity themes**: FRENCH_LANGUAGE, NATIONAL_PRIDE, CULTURAL_DISTINCTIVENESS, SECULARISM, HISTORICAL_MEMORY, VULNERABILITY, AUTONOMY, INTEGRATION

---

### 5. Gratitude Index

**Range**: 0 to 1

**Formula**:
```
gratitude_index = thanking_sentences / total_sentences
```

Proportion of speech dedicated to thanking supporters, staff, and collaborators.

---

### 6. Actor Sentiment Index

**Range**: -1 (negative) to +1 (positive)

**Formula**:
```
actor_index = (positive_mentions - negative_mentions) / total_mentions
```

---

## Figures

| Figure | Title | Description |
|--------|-------|-------------|
| Fig 1 | Resignation Dashboard | Overview of 5 composite indices with key metrics |
| Fig 1b | Resignation Rationale | Why Legault resigned: explicit justifications (horizontal bars) |
| Fig 2 | Justification Strategies | Justification categories by target (grouped bars) |
| Fig 3 | Policy Domains | Policy areas mentioned (sunburst chart, CAP categories) |
| Fig 3b | Domain × Speech Acts | Policy domains linked to speech acts (Sankey diagram) |
| Fig 4 | Emotional Landscape | Emotional register evolution through speech (matplotlib timeline with peak detection) |
| Fig 5 | Actor Sentiment | Who is mentioned and how (diverging horizontal bars by actor type) |
| Fig 6 | Identity & Nationalism | Quebec identity themes linked to stances (Sankey diagram) |
| Fig 7 | Rhetorical Strategy | Legacy framing and speech acts (dual donut charts) |

---

## Code

| File | Description |
|------|-------------|
| `generate_all.py` | Master script to generate all figures |
| `generate_fig1_dashboard.py` | Dashboard with 5 composite indices |
| `generate_fig1b_resignation_rationale.py` | Resignation rationale horizontal bars |
| `generate_fig2_justifications.py` | Justification categories grouped bars |
| `generate_fig3_policy_domains.py` | Policy domains sunburst chart |
| `generate_fig3b_domain_acts.py` | Domain × Speech Acts Sankey diagram |
| `generate_fig4_emotions.py` | Emotional timeline with scipy peak detection |
| `generate_fig5_actors.py` | Actor sentiment diverging bars |
| `generate_fig6_identity.py` | Identity themes Sankey diagram |
| `generate_fig7_combined.py` | Rhetorical strategy dual donut charts |
| `compute_indices.py` | Composite index calculations and excerpt selection |
| `load_and_validate.py` | Data loading, JSON parsing, extraction utilities |
| `html_utils.py` | HTML template utilities, Playwright PNG export |
| `config.py` | Colors, labels (FR/EN), matplotlib style, palettes |

**Run**:
```bash
cd code

# Generate all figures (FR + EN)
python generate_all.py
```

**Output**:
- `output/figures/fig{1,1b,2,3,3b,4,5,6,7}_*_{en,fr}.html` (HTML versions)
- `output/figures/fig{1,1b,2,3,3b,4,5,6,7}_*_{en,fr}.png` (PNG versions)

## Dependencies

- Python 3.10+
- pandas, numpy, matplotlib, scipy
- playwright (for HTML to PNG conversion)
