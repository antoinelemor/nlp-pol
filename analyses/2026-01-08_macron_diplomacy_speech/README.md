# Macron Ambassadors Speech Analysis

Diplomatic discourse analysis of President Macron's annual address to French ambassadors (January 2026).

## Presentations

- [French slides (PDF)](presentation/slides_fr.pdf)
- [English slides (PDF)](presentation/slides_en.pdf)

## Key Findings (n=359 sentences)

| Index | Value | Interpretation |
|-------|-------|----------------|
| **Geopolitical Anxiety** | +0.08 | Slightly optimistic worldview |
| **Agency** | 85% | Highly proactive positioning |
| **Policy Ambition** | 45% | Mostly programmatic (56%) |
| **Diplomatic Tone** | -0.01 | Neutral/pragmatic overall |
| **Action Orientation** | 43% | Balanced diagnostic/action |

## Data

| | |
|---|---|
| **Source** | French presidential transcript |
| **Context** | Annual conference of ambassadors, Elysee Palace |
| **Sentences** | 359 |
| **Policy mentions** | 119 |
| **Actor mentions** | 560 |
| **Geopolitical frames** | 264 |
| **Annotation** | LLM with structured diplomatic discourse prompt (see `prompts/`) |

Each sentence is annotated with 10 dimensions:
- `speech_act`: Communicative function (STATING, DIAGNOSING, PROPOSING, DENOUNCING, etc.)
- `geopolitical_frame`: Interpretive frame (DISORDER, POWER_POLITICS, RESILIENCE, etc.)
- `actors`: Named entities with mention type and valence
- `france_positioning`: How France is positioned (ACTIVE_AGENT, LEADER, PARTNER, etc.)
- `emotional_register`: Emotional tone (ALARMIST, COMBATIVE, CONFIDENT, PRAGMATIC, etc.)
- `temporality`: Temporal orientation (PAST_ACHIEVEMENT, PRESENT_CRISIS, FUTURE_ACTION, etc.)
- `implicit_references`: References to external events/actors not explicitly named
- `policy_content`: Policy proposals with domain, action type, and specificity
- `issue_stances`: Positions on specific issues
- `rhetorical_devices`: Notable rhetorical strategies employed

---

## Composite Indices

### 1. Geopolitical Anxiety Index (GAI)

**Range**: -1 (pessimistic) to +1 (optimistic)

**Formula**:
```
GAI = frame_balance * weight_frame + tone_index * weight_tone
```

Where:
- `frame_balance = (opportunity_frames - threat_frames) / total_frames`
- `tone_index = mean(emotional_register_weights) / 2.0`
- Weights are proportional to evidence counts

**Threat frames**: DISORDER, POWER_POLITICS, MULTILATERAL_DECLINE, EXISTENTIAL_THREAT, BRUTALIZATION, VASSALIZATION, RECOLONIZATION, FRAGMENTATION, REACTIONARY_INTERNATIONAL

**Opportunity frames**: OPPORTUNITY, RESILIENCE, COOPERATION, MULTILATERAL_RENEWAL, PROGRESS, SOLIDARITY, LEADERSHIP_OPPORTUNITY, STRATEGIC_ADVANTAGE, REFORM_MOMENTUM

---

### 2. Agency Index

**Range**: 0 (passive) to 1 (highly active)

**Formula**:
```
Agency = (Active*1.0 + Partner*0.7 + Passive*0.3) / Total
```

Where:
- **Active** = ACTIVE_AGENT + LEADER + POWER + MODEL
- **Partner** = PARTNER + RELIABLE_ALLY
- **Passive** = REACTIVE_AGENT + VICTIM

---

### 3. Policy Ambition Index

**Range**: 0 (vague) to 1 (concrete)

**Formula**:
```
Ambition = Mean(specificity_weights)
```

Where:
- CONCRETE = 1.0
- PROGRAMMATIC = 0.6
- ASPIRATIONAL = 0.2

---

### 4. Diplomatic Tone Index

**Range**: -1 (alarmist/combative) to +1 (confident/calm)

**Formula**:
```
Tone = Mean(emotional_register_weights) / 2.0
```

**Emotional register weights**:
| Register | Weight |
|----------|--------|
| ALARMIST | -2.0 |
| COMBATIVE | -1.5 |
| INDIGNANT | -1.5 |
| DEFIANT | -1.0 |
| EXASPERATED | -0.5 |
| PRAGMATIC | 0.0 |
| NEUTRAL | 0.0 |
| SOLEMN | +0.5 |
| GRATEFUL | +1.0 |
| CONFIDENT | +1.5 |

---

### 5. Action Orientation Index

**Range**: 0 (descriptive) to 1 (action-oriented)

**Formula**:
```
Action = action_acts / (action_acts + descriptive_acts)
```

Where:
- **Action acts** = PROPOSING + EXHORTING + COMMITTING
- **Descriptive acts** = STATING + DIAGNOSING + FRAMING

---

## Figures

| Figure | Title | Description |
|--------|-------|-------------|
| Fig 1 | Diplomatic Doctrine Dashboard | Overview of all 5 composite indices |
| Fig 2 | Geopolitical Worldview | Threat vs opportunity frame distribution |
| Fig 3 | Actor Sentiment Landscape | How actors are portrayed (sentiment) |
| Fig 4 | Emotional Timeline | Tone evolution through the speech |
| Fig 5 | Policy Ambition Matrix | Policy domains and specificity |
| Fig 6 | Rhetorical Strategy | Speech acts and emotional registers |
| Fig 7 | France Agency Profile | France positioning breakdown |
| Fig 8 | Diplomatic Positioning | Actor groups and sentiment |

---

## Code

| File | Description |
|------|-------------|
| `generate_all.py` | Master script to generate all 8 figures |
| `generate_fig{1-8}_*.py` | Individual figure generators (HTML/CSS + PNG) |
| `compute_indices.py` | Composite index calculations and data preparation |
| `load_and_validate.py` | Data loading, JSON parsing, extraction utilities |
| `config.py` | Colors, labels, matplotlib style, palettes |

**Run**:
```bash
cd code

# Generate all figures (FR + EN)
python generate_all.py

# Generate specific figure
python generate_all.py --fig 1

# Generate for specific language
python generate_all.py --lang fr

# Print comprehensive analysis report
python generate_all.py --full-report
```

**Output**:
- `output/figures/fig{1-8}_*_{en,fr}.html` (HTML versions)
- `output/figures/fig{1-8}_*_{en,fr}.png` (PNG versions)

## Dependencies

- Python 3.10+
- pandas, numpy, matplotlib, scipy
- playwright (for HTML to PNG conversion)
