# Roadmap

## Phase 1 — capture (this repo)
- [x] 100 words, Jung's order, shared JSON source of truth
- [x] Mic (Web Speech API) and typing input, voice-onset / first-keystroke timing
- [x] Optional spoken stimulus (TTS), clock starts at utterance onset
- [x] Per-item record: response, reactionMs, completionMs, relatedness, flags
- [x] Flags: LONG_RT, LOW_RELATEDNESS, NO_RESPONSE, REPEATS_STIMULUS, MULTI_WORD, INVESTIGATE_PREV/NEXT
- [x] Open-source scorer backend (MiniLM), optional Ollama LLM scorer
- [x] Protocol-sheet results view, JSON export
- [x] Stimulus meta layer (POS, theme, loaded)
- [x] Jung & Riklin association types: rule tier + optional Ollama tier
- [x] Extra indicators: CLANG, EGOCENTRIC, STEREOTYPY, PERSEVERATION, PATTERN_BREAK
- [x] Subject profile (reaction type, type shares) and theme clustering on the results sheet
- [x] Import a saved session straight into analysis (file or pasted JSON)
- [x] Five stimulus sets (Jung 1910 ×3 variants, Kent & Rosanoff 1910, Rapaport/Gill/Schafer 1946), optional shuffle
- [x] One-tap correction chips for misheard spoken responses, flow uninterrupted
- [ ] Commonality score against association norms (Small World of Words / USF) as a replacement for embedding relatedness
- [ ] Session persistence (IndexedDB or SQLite)
- [ ] Replace Web Speech API with on-device STT (whisper-web / whisper.cpp / Vosk)
- [x] Client-side MiniLM via transformers.js so the app can ship with no backend (opt-in checkbox, default on)
- [ ] Category-run detection (several responses from one semantic field across unrelated stimuli, e.g. a run of animal names) via the semantic tier
- [ ] Observer notes field per item (laugh, hesitation, gesture)
- [ ] Calibrate relatedness threshold against ~50 hand-labelled pairs

## Phase 1.5 — reproduction test
- [ ] After the main run, re-present each word and ask for the earlier response
- [ ] Record `reproduced: true|false|altered` and the second reaction time
- [ ] Add `REPRODUCTION_FAULT` flag; Jung rated this among the strongest indicators

## Phase 2 — analysis
- [ ] Refine theme clustering: embed stimuli + responses, find clusters the fixed theme tags miss
- [ ] Cross-indicator scoring: an item with 2+ indicators outranks one with 1
- [ ] Session drift: plot RT over index to separate fatigue from true prolongation
- [ ] Guided follow-up: for each flagged cluster, generate open, non-leading interview prompts (open-source LLM, local)
- [ ] Report export (PDF/HTML protocol sheet with annotations)
- [ ] Multi-session comparison for the same subject

## Shipping checklist
- [ ] Decide platform: PWA (simplest, mic works in Safari/Chrome), or native shell (Capacitor/Tauri) for on-device STT
- [ ] Privacy statement: what audio/text is processed where. Target: everything on device.
- [ ] Mic permission UX and fallback to typing
- [ ] Accessibility: keyboard-only run, reduced motion (already respected), screen-reader labels on the trial screen
- [ ] Consent screen: this is not a diagnostic instrument
- [ ] Licensing audit: MiniLM (Apache-2.0), sentence-transformers (Apache-2.0), whisper (MIT), Vosk (Apache-2.0)
