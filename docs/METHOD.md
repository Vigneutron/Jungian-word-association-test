# Jung's association method, and how this app maps to it

Source texts: *Diagnostische Assoziationsstudien* (1904–1906, with Riklin, Bleuler et al.) and "The Association Method", Clark University lectures (1909, published 1910). This app follows the 1910 description.

## Procedure as Jung ran it

1. The experimenter reads a stimulus word aloud. The subject answers as quickly as possible with the first word that occurs to them. Jung instructs: do not deliberate.
2. A stopwatch runs from the end of the spoken stimulus to the onset of the reply. Recorded in fifths of a second.
3. The experimenter writes the response and time on a protocol sheet, plus any behavioural observations (laughing, blushing, gesture, hesitation).
4. After all 100 words, the list is read again (**reproduction test**). The subject is asked to repeat their earlier response. Whether they can is recorded.
5. Jung computed the subject's *probable mean* (median) reaction time and used it as that subject's own baseline. Educated adults averaged around 1.8 s (≈9 fifths); Jung treated anything clearly above the individual's mean as prolonged.

## Complex indicators (Jung, 1910) and the app's coverage

| Indicator | Phase 1 status |
|---|---|
| Prolonged reaction time | `LONG_RT` |
| No reaction / failure | `NO_RESPONSE` |
| Repetition of the stimulus word | `REPEATS_STIMULUS` |
| Reaction with several words or a sentence | `MULTI_WORD` |
| Unusual / far-fetched / meaningless response | approximated by `LOW_RELATEDNESS` |
| Perseveration (the *following* response is disturbed) | `INVESTIGATE_NEXT` (available, off by default) |
| Disturbance in the preceding word | `INVESTIGATE_PREV` (product requirement, on by default) |
| Misunderstanding the stimulus | not captured (needs human observation or STT confidence) |
| Faults in reproduction | not implemented, phase 2 |
| Laughing, blushing, movement, stammering | not captured; could add optional observer notes per item |
| Rhyming / sound associations ("clang") | not captured; cheap to add via phonetic similarity |
| Stereotyped responses (same answer repeatedly) | not captured; trivial to add in analysis |

## Notes on measurement choices

- **Why response onset, not submit.** Jung's stopwatch stops when the subject starts speaking. Typing "grandfather" takes longer than typing "hair" regardless of any complex; first-keystroke timing removes that confound. The full completion time is kept separately as `completionMs`.
- **Why the median.** Reaction-time distributions are right-skewed; the median is robust to the few long outliers that are exactly what we're trying to detect.
- **Why an absolute floor (2.5 s) on top of the ratio.** A fast subject with a 0.8 s median would otherwise be flagged at 1.2 s, which is noise.
- **What relatedness actually measures.** Embedding cosine captures semantic closeness (head→hair high, head→Tuesday low). It does not know common *associative* pairs that aren't semantic neighbours (bread→butter is fine, but lamp→mother scores low even though it may be a perfectly ordinary personal association). Treat `LOW_RELATEDNESS` as "worth a look", not as proof of anything. An instruct LLM rating association strength (the Ollama scorer) is closer to what Jung meant by an unusual reaction.

## Things Jung would warn us about

- The test says where the disturbances are; it does not say what they mean. Phase 2 needs a human (or a very careful interviewer flow), not a verdict generator.
- Fatigue and practice effects across 100 words are real. Consider recording elapsed session time and letting analysis control for drift.
- A single flagged word means little. Jung looked for *clusters* across indicators and across semantically linked stimuli (e.g. dead, to die, sick, anxiety all disturbed).
