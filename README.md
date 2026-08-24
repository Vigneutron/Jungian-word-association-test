# jung-wat

Phase-1 prototype of a word association test app built on Jung's 1904–1909 method. See `CLAUDE.md` for full project context and `docs/METHOD.md` for the psychology.

## Live demo
**https://vigneutron.github.io/Jungian-word-association-test/**

Published from this repo by `.github/workflows/pages.yml` on every push. The root `index.html` forwards to `frontend/`.

## Sharing the demo
Do not send `index.html` as a file attachment: iOS opens it in Quick Look, which does not run JavaScript, and the mic needs https. Share the Pages link above instead — https is also what the microphone permission requires.

## Run the prototype (no backend)
Open `frontend/index.html` in Chrome or Safari. Pick a stimulus set (Jung 1910 is the default; the Rapaport 1946 clinical list is explicit), choose mic or typing, press Begin.
Without a scorer URL, relatedness uses a placeholder heuristic and says so on the results screen.

## Run with the open-source scorer
```
cd backend
pip install -r requirements.txt        # first run downloads all-MiniLM-L6-v2 (~80 MB)
uvicorn main:app --reload --port 8000
python test_scorer.py                  # optional sanity check
```
Then in the prototype's setup screen set scorer URL to `http://localhost:8000`.

Optional LLM scorer instead of embeddings (needs Ollama running):
```
ollama pull qwen2.5:0.5b
SCORER=ollama uvicorn main:app --port 8000
```

## Export
Results screen → Export JSON. Schema documented in `CLAUDE.md`.
