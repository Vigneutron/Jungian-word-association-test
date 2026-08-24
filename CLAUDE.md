# jung-wat — Word Association Test app

An app built on C. G. Jung's word association experiment (Burghölzli, 1904–1909). Phase 1 (this repo) captures the protocol: present 100 stimulus words in order, record the subject's first-word response, reaction time, and a relatedness score, then flag complex indicators. Phase 2 (not started) is interpretation of the flagged material.

## Hard constraints

- **Open source only for the ML.** Relatedness scoring must run on an open-source model we can ship (currently `sentence-transformers/all-MiniLM-L6-v2`, Apache-2.0). Do not wire in Anthropic, OpenAI, or any proprietary API for scoring. Claude is used to *build* the app, not inside it.
- **Method fidelity.** Default set is Jung's 100 words in his order. Five sets are available (`shared/stimulus_sets.json`): Jung (1910); Jung (1910) critical words only; Jung (1910) modern English; Kent & Rosanoff (1910); Rapaport, Gill & Schafer (1946, explicit clinical list). Label sets by authors and year. Shuffle exists as an option but is off by default because the published order carries meaning. Timing is stored in ms. **Display seconds as the primary unit** (e.g. `1.2 s`) with fifths of a second (Jung's unit) as a small secondary label; showing fifths alone reads as a 5x-fast clock.
- **Reaction time = stimulus delivery → response onset**, not → response submit. Mic: voice-activity onset from a Web Audio analyser on the persistent stream (fallback: recognizer `onspeechstart`, then first interim result). Typing: first keystroke. If the stimulus is spoken via TTS, the clock starts at `utterance.onstart` and the mic ignores input until the utterance ends + 250 ms.
- **The microphone opens once and stays open for the whole session** (`Mic` module in index.html). Never restart recognition per word; continuous mode with auto-restart on `onend`. Results arriving with no active trial, or during TTS playback, are discarded.
- **Two core metrics per response:** `reactionMs` and `relatedness` (0–1), plus an **association type** in Jung & Riklin's scheme (`assoc.type/subtype`). Flags derive from these. All of it lives in `classifyRule()` / `analyse()`; keep it in one place and explainable. See `docs/CLASSIFICATION.md`.

## Repo layout

```
CLAUDE.md                     this file
README.md                     run instructions
shared/stimulus_sets.json     five stimulus sets, each word tagged pos/theme/loaded (single source of truth)
shared/stimulus_words.json    Jung 1910 only; legacy, kept for old imports
frontend/index.html           phase-1 prototype, single file, no build step. Works standalone.
backend/main.py               FastAPI scorer (MiniLM default, Ollama optional)
backend/requirements.txt
backend/test_scorer.py        prints scores for a few known pairs
docs/METHOD.md                Jung's procedure, complex indicators, how we map them
docs/CLASSIFICATION.md        the four classification layers (stimulus meta, association type, flags, subject profile)
docs/ROADMAP.md               phase 2 and shipping checklist
```

## Data model (session export, `schema: jung-wat/session/v2`)

```json
{
  "subject": "S-01", "recordedAt": "...", "inputMode": "mic", "spokenStimulus": true,
  "summary": {"medianMs": 1400, "rtCutoffMs": 1400, "scorer": "all-MiniLM-L6-v2", "classifier": "rules only",
              "reactionType": "objective", "dominantType": "inner", "typeShares": {...}, "themes": [...], "config": {...}},
  "items": [{
    "index": 5, "stimulus": "dead", "stimulusPos": "adjective", "theme": "death_illness", "loaded": true,
    "response": "grandfather",
    "reactionMs": 3120, "reactionFifths": 15.6, "completionMs": 3900, "rtRatio": 2.23,
    "inputMode": "mic", "relatedness": 0.21, "relatednessPrev": 0.05, "scorer": "all-MiniLM-L6-v2",
    "assoc": {"type": "remainder", "subtype": "indirect", "evidence": ["semantically distant"], "source": "rule-probable"},
    "flags": ["LONG_RT", "LOW_RELATEDNESS"], "disturbed": true, "indicatorCount": 2
  }]
}
```

`index` is 1-based **presentation order** (neighbour analysis runs on this). `listPosition` is the word's position in its source set, which differs from `index` when shuffled or when a subset is run. Top-level export carries `set`, `setLabel`, `shuffled`. Schema is `jung-wat/session/v3`; import accepts v1–v3. Neighbour flags (`INVESTIGATE_PREV`, `INVESTIGATE_NEXT`) are applied to adjacent items, not the flagged item.

## Flag rules

Full table in `docs/CLASSIFICATION.md`. Summary: `LONG_RT` (> subject median, Jung's rule, ~50% by construction), `NO_RESPONSE`, `REPEATS_STIMULUS`, `MULTI_WORD`, `CLANG`, `EGOCENTRIC`, `STEREOTYPY`, `PERSEVERATION`, `PATTERN_BREAK`, and neighbour flags `INVESTIGATE_PREV` (on by default, product requirement) / `INVESTIGATE_NEXT` (Jung's forward perseveration, off by default).

`LOW_RELATEDNESS` is **off** (`CONFIG.flagLowRelatedness=false`): it over-fired. Relatedness is still scored and exported for phase-2 analysis; don't re-enable the flag without calibrating.

`item.disturbed` = any non-RT indicator, or `rtRatio ≥ 2`, or `LONG_RT` + another indicator. That, not raw flag count, drives carmine rows, neighbour investigation, and theme clustering.

## Classifier contract

`POST /api/classify` with `{"items":[{"index","stimulus","response"}]}` returns `{"classifications":[{"index","type","subtype","reason"}], "classifier":"name"}` or `{"classifications": null, "classifier": "none"}`. The frontend's rule tier always runs; the LLM only replaces `source: 'rule-probable'` verdicts. Needs Ollama with a small instruct model (`ollama pull qwen2.5:0.5b`).

## Spoken-response correction

Recognizer runs with `maxAlternatives = 5`. After each spoken response the test advances, but a strip shows the previous word, what was heard, and the alternative transcripts as one-tap chips, plus a free-text fix. `correctLast()` replaces `response`, keeps the original in `rawResponse`, sets `corrected: true`, and re-scores. Reaction time is never touched: it was measured at voice onset. While the fix box has focus the mic ignores input so keyboard taps aren't recorded as the next response.

## Import

Setup screen → "Saved session": file picker or pasted JSON → `importSession()` → straight to the results sheet. Accepts `jung-wat/session/v1` and `v2`; fills missing fields from `META`, recomputes classification and flags with current rules, and re-scores against the backend if a scorer URL is set and the session was scored by the placeholder. This is the entry point for phase-2 analysis of stored sessions.

## On-device scorer

`Local` module in index.html loads `Xenova/all-MiniLM-L6-v2` through transformers.js (jsdelivr CDN, ~23 MB, browser-cached) when "Score on this device" is checked and no scorer URL is set. Same model and cosine scale as the Python backend, so thresholds and relatedness bands carry over. It cannot load inside the chat preview (CDN blocked); on a hosted page it is the default path and removes the "unplaced" problem. If the import fails it falls back to the lexical placeholder and says so. For a native build, bundle the ONNX model instead of fetching it.

## Scorer contract

`POST /api/score` with `{"pairs":[{"stimulus","response"}]}` returns `{"scores":[0..1], "scorer":"name"}`. The frontend batches one pair per call right now; batch the whole session at the end if latency matters. If no backend URL is configured the frontend uses a trigram-overlap placeholder labelled `lexical-heuristic`. That placeholder is not a measure of anything; never ship it as the default.

## Known gaps / things to fix when productionising

0. **Unplaced responses** happen whenever no scorer is available: the rule tier refuses to guess. That's intended; the on-device scorer or backend is what fills them in.
1. **Speech recognition.** The prototype uses the Web Speech API (continuous mode), which in Chrome sends audio to Google. For a shippable, private app, replace with on-device STT: whisper.cpp / `whisper-web` (transformers.js) in the browser, or Vosk/Whisper in a native shell. The `Mic` module already owns a raw `MediaStream` and analyser, so an on-device recognizer can consume the same stream. Keep the analyser-based voice-onset timestamp; that's the measurement, independent of which recognizer produces the transcript.
1. **Speaker echo.** When TTS reads the word and the mic is open, the recognizer may catch the tail of the word. `Mic.clean()` strips a leading stimulus from the transcript and the analyser is muted until utterance end + 250 ms. Headphones fix it properly; a native build should use AEC.
2. **Embedded mic / file sharing.** The prototype can't access the mic inside a chat iframe, and an .html sent as an attachment opens in iOS Quick Look with JS disabled. It must be served over https (Netlify Drop, GitHub Pages; root `index.html` forwards to `frontend/`). Typing mode always works once served.
3. **Inline word list.** `frontend/index.html` inlines the 100 words so it runs as a single file. When moving to a framework, import from `shared/stimulus_words.json` and delete the inline copy.
4. **Duplicate "to cook"** at positions 11 and 20 is faithful to the 1910 English list; the modern-English set replaces the second with "to bake".
4. **Rule tables** (`ANTONYMS`, `STOCK`) are keyed by stimulus word and were written for Jung's list. They cover overlapping words in the other sets; extend them per set when those sets get real use.
4. **Rapaport list** is reconstructed from secondary sources; verify wording and order against the 1968 Holt edition before shipping.
5. **Persistence.** Nothing is stored between sessions. Add local storage (IndexedDB) or a `sessions` table; the export JSON is the intended record format.
6. **Relatedness calibration.** Word-level cosine on MiniLM is noisy for short strings (e.g. antonyms score high). Options in order of effort: keep MiniLM and tune the threshold against a small labelled set; switch to the Ollama scorer (`SCORER=ollama`) with a ~0.5–1B instruct model; run MiniLM client-side via transformers.js so no backend is needed at all.
7. **Classification thresholds** (`reactionType` cutoffs, `patternBreakShare`, relatedness bands) are uncalibrated guesses. Collect a few real sessions and tune.
8. **Reproduction test.** Jung re-ran the list afterwards and asked the subject to reproduce each earlier answer; failures to reproduce are a strong indicator. Not implemented. See ROADMAP.

## Commands

```
# backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000
python test_scorer.py

# frontend
open frontend/index.html    # set scorer URL to http://localhost:8000 in setup
```

## Style

Plain, small, readable. The prototype is intentionally framework-free. If you move to React/Vite, keep the three screens (setup / trial / protocol sheet), the fifths-of-a-second readout, and the carmine flag colour. UI palette and type are documented in the `<style>` block.
