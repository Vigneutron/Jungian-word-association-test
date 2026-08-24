"""
Relatedness scorer for the word association protocol.

Scores how semantically related a subject's response is to its stimulus word.
Everything here is open source and runs locally; no proprietary model is involved.

Default scorer: sentence-transformers / all-MiniLM-L6-v2 (Apache-2.0, ~22M params, ~80MB).
    Cosine similarity of the two embeddings, rescaled to 0..1.
Optional scorer: a small instruction-tuned LLM via Ollama (e.g. qwen2.5:0.5b, llama3.2:1b),
    asked to rate relatedness 0..1. Slower, but handles idiom and association better than
    raw embedding distance. Enable with SCORER=ollama.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

API:
    GET  /api/health                        -> {"ok": true, "scorer": "..."}
    POST /api/score {"pairs":[{"stimulus":"head","response":"hair"}]}
                                            -> {"scores":[0.61], "scorer":"all-MiniLM-L6-v2"}
    POST /api/classify {"items":[{"index":1,"stimulus":"head","response":"hair"}]}
                                            -> {"classifications":[{"index":1,"type":"outer","subtype":"stock","reason":"..."}],
                                                "classifier":"ollama:qwen2.5:0.5b"}
                                               (or {"classifications": null, "classifier": "none"} if no LLM is configured;
                                                the frontend's rule tier then stands on its own)
    GET  /api/words                         -> Jung 1910 list + meta (legacy)
    GET  /api/sets                          -> all five stimulus sets with per-word meta
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

SCORER = os.getenv("SCORER", "minilm")  # "minilm" | "ollama"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
WORDS_PATH = Path(__file__).resolve().parent.parent / "shared" / "stimulus_words.json"
SETS_PATH = Path(__file__).resolve().parent.parent / "shared" / "stimulus_sets.json"

app = FastAPI(title="jung-wat scorer")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Pair(BaseModel):
    stimulus: str
    response: str


class ScoreRequest(BaseModel):
    pairs: list[Pair]


class ClassifyItem(BaseModel):
    index: int
    stimulus: str
    response: str


class ClassifyRequest(BaseModel):
    items: list[ClassifyItem]


# Jung & Riklin association categories, as the LLM is asked to apply them.
TYPES = {
    "inner": ["coordination", "subordination", "superordination", "contrast", "predicate", "definition"],
    "outer": ["stock", "coexistence", "speech-habit", "identity"],
    "clang": ["rhyme", "completion", "sound"],
    "remainder": ["indirect", "meaningless", "misunderstanding", "repetition", "failure"],
    "egocentric": ["personal"],
}
CLASSIFY_PROMPT = """You are classifying responses from Jung's word-association test using Jung & Riklin's scheme.
Categories (type / subtype):
- inner: the link is by meaning. coordination (same class: head->arm), subordination (bird->sparrow), superordination (bird->animal), contrast (cold->warm), predicate (a judgement or property: water->deep, money->evil), definition (explains the word: pride->feeling superior)
- outer: the link is habit or co-occurrence, not meaning. stock (bread->butter, needle->thread), coexistence (lamp->table), speech-habit (an idiom or compound: head->ache), identity (a synonym)
- clang: sound only. rhyme, completion (stem->stemming), sound (similar sound, unrelated meaning)
- remainder: indirect (far-fetched, link only via an unstated middle term), meaningless, misunderstanding (answers a different word), repetition (repeats the stimulus), failure
- egocentric: personal reference (I, my, a person's name, my own experience)
Reply with ONLY a JSON object: {"type": "...", "subtype": "...", "reason": "<8 words max>"}
Stimulus: {stimulus}
Response: {response}"""


# ---------------------------------------------------------------- scorers
_model = None


def _minilm():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def _norm(w: str) -> str:
    # Jung's verbs are listed as "to sing"; the infinitive marker adds no meaning to the embedding.
    w = w.strip().lower()
    return w[3:] if w.startswith("to ") else w


def score_minilm(pairs: list[Pair]) -> list[float]:
    from sentence_transformers import util
    m = _minilm()
    a = m.encode([_norm(p.stimulus) for p in pairs], normalize_embeddings=True)
    b = m.encode([_norm(p.response) for p in pairs], normalize_embeddings=True)
    cos = util.cos_sim(a, b).diagonal().tolist()
    # cosine of unrelated short words tends to sit around 0.0-0.2; clamp negatives and return 0..1
    return [max(0.0, min(1.0, float(c))) for c in cos]


def score_ollama(pairs: list[Pair]) -> list[float]:
    import httpx
    out = []
    for p in pairs:
        prompt = (
            "You are scoring a word-association test. Rate how strongly the response is associated "
            "with the stimulus word, where 1.0 means a very common association (e.g. bread -> butter) "
            "and 0.0 means no discernible connection. Reply with only a number between 0 and 1.\n"
            f"Stimulus: {p.stimulus}\nResponse: {p.response}\nScore:"
        )
        r = httpx.post(f"{OLLAMA_URL}/api/generate", json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0}}, timeout=60)
        r.raise_for_status()
        txt = r.json().get("response", "").strip()
        try:
            val = float(txt.split()[0].strip("., "))
        except (ValueError, IndexError):
            val = 0.5
        out.append(max(0.0, min(1.0, val)))
    return out


SCORERS = {"minilm": ("all-MiniLM-L6-v2", score_minilm), "ollama": (f"ollama:{OLLAMA_MODEL}", score_ollama)}

CLASSIFIER = os.getenv("CLASSIFIER", "ollama")  # "ollama" | "none"


def _ollama_available() -> bool:
    import httpx
    try:
        return httpx.get(f"{OLLAMA_URL}/api/tags", timeout=2).status_code == 200
    except Exception:
        return False


def classify_ollama(items: list[ClassifyItem]) -> list[dict]:
    import httpx
    out = []
    for it in items:
        prompt = CLASSIFY_PROMPT.replace("{stimulus}", it.stimulus).replace("{response}", it.response)
        try:
            r = httpx.post(f"{OLLAMA_URL}/api/generate", json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0}}, timeout=60)
            r.raise_for_status()
            d = json.loads(r.json().get("response", "{}"))
            t = d.get("type") if d.get("type") in TYPES else None
            st = d.get("subtype") if t and d.get("subtype") in TYPES[t] else (TYPES[t][0] if t else None)
            if t:
                out.append({"index": it.index, "type": t, "subtype": st, "reason": str(d.get("reason", ""))[:80]})
        except Exception:
            continue
    return out


# ---------------------------------------------------------------- routes
@app.get("/api/health")
def health():
    return {"ok": True, "scorer": SCORERS[SCORER][0]}


@app.post("/api/score")
def score(req: ScoreRequest):
    name, fn = SCORERS[SCORER]
    return {"scores": fn(req.pairs), "scorer": name}


@app.post("/api/classify")
def classify(req: ClassifyRequest):
    if CLASSIFIER == "ollama" and _ollama_available():
        return {"classifications": classify_ollama(req.items), "classifier": f"ollama:{OLLAMA_MODEL}"}
    return {"classifications": None, "classifier": "none"}


@app.get("/api/words")
def words():
    return json.loads(WORDS_PATH.read_text())


@app.get("/api/sets")
def sets():
    return json.loads(SETS_PATH.read_text())
