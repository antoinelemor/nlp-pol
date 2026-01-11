# NLP-POL

Weekly NLP analyses of political speeches and interventions, published on LinkedIn and blog.

## About

This project applies Natural Language Processing to political discourse analysis. Each analysis takes a political speech, press conference, or interview and produces:

- Sentence-level annotations (tone, theme, response patterns, entities)
- Quantitative metrics (posture index, evasion rates, animosity scores)
- Visualizations for each research question
- Bilingual presentations (EN/FR)

The goal is to reveal rhetorical patterns that are difficult to perceive when watching or reading political discourse in real-time.

## Methodology

1. **Transcription**: Audio/video → text using [Transcribe-tool](https://github.com/antoinelemor/Transcribe-tool)
2. **Tokenization**: Text → sentences (CSV format)
3. **Annotation**: Each sentence is annotated by LLM using [LLM_Tool](https://github.com/antoinelemor/LLM_Tool) with a structured prompt defining:
   - Speaker role (official, journalist)
   - Utterance type (statement, question, response)
   - Tone (threatening → deferential scale)
   - Theme (security, diplomacy, economy, etc.)
   - Response type (direct, partial, deflection, etc.)
   - Entities mentioned with sentiment valence
4. **Analysis**: Python scripts compute metrics and generate figures
5. **Presentation**: Beamer slides with key findings

See each analysis README for detailed calculations.

## Analyses

| Date | Topic | Method | Slides |
|------|-------|--------|--------|
| 2026-01-08 | [Macron Ambassadors Speech](analyses/2026-01-08_macron_diplomacy_speech/) | [README](analyses/2026-01-08_macron_diplomacy_speech/README.md) | [FR](analyses/2026-01-08_macron_diplomacy_speech/presentation/slides_fr.pdf) / [EN](analyses/2026-01-08_macron_diplomacy_speech/presentation/slides_en.pdf) |
| 2026-01-03 | [Trump Venezuela Press Conference](analyses/2026-01-03_trump_venezuela_maduro/) | [README](analyses/2026-01-03_trump_venezuela_maduro/README.md) | [FR](analyses/2026-01-03_trump_venezuela_maduro/presentation/slides_fr.pdf) / [EN](analyses/2026-01-03_trump_venezuela_maduro/presentation/slides_en.pdf) |

## Structure

```
analyses/
└── YYYY-MM-DD_topic/
    ├── README.md           # Detailed methodology
    ├── data/               # Annotated CSV
    ├── prompts/            # LLM annotation prompts
    ├── code/               # Python scripts
    ├── output/figures/     # Generated plots (EN/FR)
    └── presentation/       # Beamer slides (EN/FR)
```

## Tools

- [Transcribe-tool](https://github.com/antoinelemor/Transcribe-tool) — Audio/video transcription
- [LLM_Tool](https://github.com/antoinelemor/LLM_Tool) — Text annotation with LLMs

## Author

Antoine Lemor — [github.com/antoinelemor](https://github.com/antoinelemor)

## License

CC BY-NC 4.0
