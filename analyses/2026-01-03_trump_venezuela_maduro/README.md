# Trump Venezuela Press Conference Analysis

White House press conference, January 3, 2026, following the US military operation in Venezuela.

## Presentations

- [French slides (PDF)](presentation/slides_fr.pdf)
- [English slides (PDF)](presentation/slides_en.pdf)

## Data

| | |
|---|---|
| **Source** | Associated Press video transcript ([YouTube](https://www.youtube.com/watch?v=ezYNnFETXk0)) |
| **Corpus** | 858 sentences |
| **Speakers** | Trump, Rubio, Hegseth, Caine + journalists |
| **Annotation** | LLM with structured prompt (see `prompts/discourse_analysis.txt`) |

Each sentence is annotated with:
- `speaker` and `speaker_role` (political_leader, government_official, journalist)
- `utterance_type` (statement, question, response)
- `tone` (threatening, confrontational, dismissive, triumphant, factual, reassuring, deferential)
- `theme_primary` (military_operation, security_threat, diplomatic_relations, etc.)
- `response_type` (direct, partial, pivot, deflection, attack)
- `entities_mentioned` with valence (positive, neutral, negative)

---

## Methodology

### Fig 1: Rhetorical Posture Index

**What it measures**: Overall rhetorical aggressiveness of each speaker.

**Calculation**:
1. Each sentence has a `tone` annotation
2. Tones are mapped to weights:
   | Tone | Weight |
   |------|--------|
   | threatening | -2.0 |
   | confrontational | -1.5 |
   | dismissive | -1.0 |
   | triumphant | -0.5 |
   | factual | 0.0 |
   | reassuring | +1.0 |
   | deferential | +1.5 |
3. Posture index = mean of weights for all sentences by speaker
4. Scale: -2 (aggressive) to +1.5 (neutral)

---

### Fig 2: Posture Timeline

**What it measures**: Evolution of rhetorical posture over time.

**Calculation**:
1. Limit to statement section (segments 1-399, before Q&A)
2. Map each sentence's tone to weight (same as Fig 1)
3. Apply rolling average with window = 15 sentences, centered
4. Plot smoothed curve with speaker change markers

---

### Fig 3: Response Types

**What it measures**: How Trump responds to journalist questions.

**Calculation**:
1. Filter to Trump's responses during Q&A (`utterance_type` = response)
2. Count each `response_type`:
   - `direct`: answers the question
   - `partial`: partially addresses the question
   - `pivot`: redirects to another topic
   - `deflection`: avoids the question
   - `attack`: attacks the question or questioner
3. Display as donut chart with percentages

---

### Fig 4: Evasion by Topic

**What it measures**: Response quality by topic of journalist questions.

**Calculation**:
1. Extract Q&A blocks: consecutive journalist questions + Trump responses
2. For each block, link question themes to response types
3. When a question spans multiple themes, weight is distributed equally
4. Aggregate response type distribution per theme
5. Display as stacked horizontal bar chart (% per theme)

---

### Fig 5: Progressive Theme Focus

**What it measures**: Thematic divergence between journalists and Trump over time.

**Calculation**:
1. Extract Q&A blocks (same as Fig 4)
2. For each block, record:
   - Themes in journalist questions
   - Themes in Trump's responses
3. Compute cumulative count per theme over exchanges
4. Apply spline smoothing (k=3)
5. Display side-by-side: journalist themes vs Trump themes

---

### Fig 6: Topics by Speaker

**What it measures**: What each speaker talks about.

**Calculation**:
1. Filter to officials (Trump, Rubio, Hegseth, Caine)
2. Exclude `meta_communication` theme
3. Count `theme_primary` per speaker
4. Convert to percentages
5. Display top 8 themes per speaker as horizontal bars

---

### Fig 7: Us vs Them

**What it measures**: In-group vs out-group portrayal in discourse.

**Entity classification**:
- **"US"**: United States entities (nation, officials, military, institutions, US cities)
- **"THEM"**: Foreign entities (Venezuela, Maduro, Cuba, Russia, etc.)

**Calculation**:
1. Extract `entities_mentioned` from Trump, Rubio, Hegseth sentences
2. Normalize entity names (e.g., "U.S." → "United States")
3. Classify each entity as US or THEM
4. Count valence (positive, neutral, negative) for each group

**Scores**:
- Sentiment score = (positive - negative) / total
- Animosity index = (THEM_score - US_score) / 2

**Interpretation**:
- Animosity < 0: hostile discourse (praising US, demonizing THEM)
- Animosity > 0: conciliatory discourse

---

## Code

| File | Description |
|------|-------------|
| `generate_figures.py` | Generates all 7 figures (EN + FR) |
| `load_and_validate.py` | Data loading and JSON parsing |
| `config.py` | Colors, labels, matplotlib style |

**Run**:
```bash
cd code
python generate_figures.py
```

**Output**: `output/figures/fig{1-7}_*_{en,fr}.png`

## Dependencies

- Python 3.10+
- pandas, numpy, matplotlib, scipy
