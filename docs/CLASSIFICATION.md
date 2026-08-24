# Classification layers

Jung did not score responses; he sorted them. This app reproduces that as four layers, each feeding the next. Everything below is computed in `analyse()` / `classifyRule()` in `frontend/index.html`, optionally refined by `POST /api/classify`.

## Layer 1 — Stimulus (fixed per word)

From `shared/stimulus_words.json` → `meta[]`.

| field | values | source |
|---|---|---|
| `pos` | noun / adjective / verb | Jung alternated these deliberately |
| `loaded` | true/false | our reading of which words Jung placed as emotionally critical (death, money, morality, aggression, family, fear). 48 of 100. |
| `theme` | see `themes` map | our editorial clustering layer. Jung grouped disturbed stimuli by content when reading a sheet; he did not publish a fixed taxonomy. Edit freely. |

## Layer 2 — Association type (per response)

Jung & Riklin's categories from *Diagnostische Assoziationsstudien*:

| type | subtypes | what it means |
|---|---|---|
| **inner** | coordination, sub/superordination, contrast, predicate, definition | linked by meaning |
| **outer** | stock, coexistence, speech-habit, identity | linked by habit, co-occurrence, idiom, or synonymy |
| **clang** | rhyme, completion, sound | linked by sound only |
| **remainder** | indirect, meaningless, misunderstanding, repetition, failure | no usable link |
| **egocentric** | personal | refers to the subject themselves (Jung treated this as its own diagnostic category) |

Two tiers produce this:

1. **Rule tier** (always on, offline). Conservative and ordered: failure → repetition → personal pronoun → antonym table → stock-pair table → completion → rhyme → sound echo → definition pattern → sentence/evaluative → fall back to relatedness bands (≥0.45 inner, ≥0.15 outer, shared onset → clang/sound, else remainder/indirect). Without any scorer the fallback is skipped and the response is `unclassified` on purpose. Verdicts from the tables are `source: 'rule'`; relatedness-band verdicts are `source: 'rule-probable'`.
2. **LLM tier** (optional, `backend/main.py` with Ollama). Only replaces `rule-probable` verdicts; hard rule verdicts stand. Uses a ~0.5–1B instruct model with `format: json`.

Tables (`ANTONYMS`, `STOCK`, `EVALUATIVE`) are scoped to Jung's 100 words and are meant to be extended from real sessions.

## Layer 3 — Complex indicators (per response)

| flag | rule | Jung's indicator |
|---|---|---|
| `LONG_RT` | RT > subject's median | prolonged reaction time. Flags ~50% by construction; severity in `rtRatio` |
| `NO_RESPONSE` | empty / skipped / timeout | failure |
| `REPEATS_STIMULUS` | response = stimulus | repetition |
| `MULTI_WORD` | > 2 words | sentence reaction |
| `LOW_RELATEDNESS` | **disabled** (`flagLowRelatedness: false`); relatedness is recorded only | unusual / far-fetched reaction (proxy; over-fired in practice) |
| `CLANG` | type = clang | clang reaction |
| `EGOCENTRIC` | type = egocentric | egocentric / subjective reaction |
| `STEREOTYPY` | same response to ≥3 stimuli | stereotypy |
| `PERSEVERATION` | response matches previous stimulus or previous response, or relates to the previous stimulus ≥0.2 more than the current one | perseveration (the complex carries into the next reaction) |
| `PATTERN_BREAK` | type is clang/remainder/egocentric while a different type holds ≥50% of responses | sudden shift in reaction type, including defensive "flattening" |
| `INVESTIGATE_PREV` / `_NEXT` | neighbour of a *disturbed* response | product requirement / perseveration |

**Disturbed** (`item.disturbed`) is the working definition of "worth a look": any non-RT indicator, or `rtRatio ≥ 2`, or `LONG_RT` plus any other indicator. It drives the carmine rows, neighbour investigation, the "responses disturbed" count, and theme clustering. Plain `LONG_RT` renders grey.

## Layer 4 — Subject profile (per session)

- `typeShares`: proportion of inner / outer / clang / remainder / egocentric.
- `reactionType`, Jung's broad typology, decided in this order:
  - **egocentric** if egocentric ≥ 15%
  - **predicate** if predicate subtype ≥ 30% (Jung linked heavy evaluation to held-back affect)
  - **definition** if definition subtype ≥ 20% (pedantic / self-presenting)
  - **superficial** if outer + clang ≥ 50% (fatigue, distraction, or defence)
  - **objective** otherwise
- `themes[]`: per theme, `disturbed / total` and total indicator count, split into loaded vs neutral stimuli. A loaded theme with most of its stimuli disturbed is the closest thing to Jung's "constellation" and is where phase-2 follow-up should start.

Thresholds are guesses calibrated on nothing yet. Treat them as dials, not findings.

## What is still missing from Jung's scheme

- Misunderstanding of the stimulus (needs STT confidence or observer input)
- Reproduction faults (phase 1.5)
- Behavioural indicators: laughing, blushing, gesture, stammering (observer notes field)
- Sub/superordination vs coordination distinction without the LLM tier
