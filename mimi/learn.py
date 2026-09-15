"""Auto-learn loop via multi-AI consensus.

Flow:
  1. Sakib asks a question
  2. N providers answer (parallel)
  3. Each answer scored by judges (the same or other providers)
  4. Best answer saved to knowledge base
  5. Future queries check knowledge first

Safety:
  - Only FACTS are learned, not code
  - Every learned item is audited
  - Sakib can review/delete any item
"""
from datetime import datetime
from .database import execute, fetch_one, fetch_all
from .guardian import audit
from .multi_ai import available_providers, ask, ask_many, PROVIDERS


def ensure_tables():
    execute("""CREATE TABLE IF NOT EXISTS knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        sources TEXT,
        confidence REAL DEFAULT 0,
        learned_at TEXT DEFAULT CURRENT_TIMESTAMP,
        reviewed INTEGER DEFAULT 0,
        use_count INTEGER DEFAULT 0)""")
    execute("""CREATE INDEX IF NOT EXISTS idx_knowledge_topic
               ON knowledge(topic)""")
    execute("""CREATE INDEX IF NOT EXISTS idx_knowledge_q
               ON knowledge(question)""")


def _providers():
    return available_providers()


JUDGE_PROMPT = """You are judging AI answers to this question:

QUESTION: {question}

ANSWER A: {a}

ANSWER B: {b}

Which answer is better — A or B? Consider:
- Accuracy
- Clarity
- Completeness
- Not being evasive

Reply with exactly ONE letter: A or B."""


def _judge_pair(judge_provider, question, a_text, b_text):
    """Ask one provider to judge A vs B. Return 'A', 'B', or None."""
    if not judge_provider:
        return None
    prompt = JUDGE_PROMPT.format(question=question, a=a_text[:800], b=b_text[:800])
    try:
        r = ask(prompt, provider=judge_provider, max_tokens=10, temperature=0.1)
        r = str(r).strip().upper()
        if r.startswith("A"):
            return "A"
        if r.startswith("B"):
            return "B"
    except Exception:
        pass
    return None


def score_answers(question, replies, judge_providers=None):
    """Round-robin pairwise scoring. Returns ranked list of (provider, score)."""
    judge_providers = judge_providers or list(replies.keys())
    items = list(replies.items())
    if len(items) < 2:
        return items

    scores = {p: 0 for p, _ in items}
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            p_a, a_text = items[i]
            p_b, b_text = items[j]
            # pick a judge that is NOT one of the two
            judge = None
            for jp in judge_providers:
                if jp != p_a and jp != p_b:
                    judge = jp
                    break
            if not judge:
                continue
            verdict = _judge_pair(judge, question, a_text, b_text)
            if verdict == "A":
                scores[p_a] += 1
            elif verdict == "B":
                scores[p_b] += 1
            else:
                scores[p_a] += 0.5
                scores[p_b] += 0.5

    ranked = sorted(items, key=lambda x: -scores[x[0]])
    return [(p, scores[p], text) for p, text in ranked]


def learn_question(question, topic=None, providers=None):
    """Ask all providers, score, save best answer."""
    ensure_tables()
    providers = providers or _providers()
    if not providers:
        return {"ok": False, "error": "no providers available"}

    replies = ask_many(question, providers=providers, temperature=0.4)
    if not replies:
        return {"ok": False, "error": "no replies"}

    ranked = score_answers(question, replies, judge_providers=providers)
    if not ranked:
        return {"ok": False, "error": "scoring failed"}

    top_provider, top_score, top_text = ranked[0]
    sources = ",".join(f"{p}:{s}" for p, s, _ in ranked)
    confidence = top_score / max(1, len(providers) - 1)

    cur = execute(
        """INSERT INTO knowledge
           (topic, question, answer, sources, confidence)
           VALUES (?, ?, ?, ?, ?)""",
        (topic or question.split()[:3] and " ".join(question.split()[:3]),
         question, top_text, sources, confidence))
    kid = cur.lastrowid if hasattr(cur, "lastrowid") else None

    audit.log("knowledge_learned", actor="learn",
              payload={"kid": kid, "topic": topic,
                       "winner": top_provider,
                       "score": top_score})
    return {
        "ok": True,
        "id": kid,
        "winner": top_provider,
        "score": top_score,
        "confidence": round(confidence, 2),
        "answer": top_text,
        "ranking": [{"provider": p, "score": s} for p, s, _ in ranked],
    }


def recall(question, limit=3):
    """Search knowledge base for a matching question."""
    ensure_tables()
    rows = fetch_all(
        """SELECT * FROM knowledge
           WHERE question LIKE ?
           ORDER BY confidence DESC, use_count DESC LIMIT ?""",
        (f"%{question[:60]}%", limit))
    out = [dict(r) for r in rows]
    # bump use count
    for r in out:
        execute("UPDATE knowledge SET use_count = use_count + 1 WHERE id=?",
                (r["id"],))
    return out


def all_knowledge(limit=50):
    ensure_tables()
    rows = fetch_all(
        """SELECT id, topic, question, substr(answer,1,80) AS snippet,
                  confidence, use_count, learned_at
           FROM knowledge ORDER BY id DESC LIMIT ?""", (limit,))
    return [dict(r) for r in rows]


def get(kid):
    ensure_tables()
    r = fetch_one("SELECT * FROM knowledge WHERE id=?", (int(kid),))
    return dict(r) if r else None


def delete(kid):
    ensure_tables()
    execute("DELETE FROM knowledge WHERE id=?", (int(kid),))
    audit.log("knowledge_deleted", actor="learn", payload={"kid": int(kid)})
    return {"ok": True}


def stats():
    ensure_tables()
    r = fetch_one("""SELECT COUNT(*) AS n,
                     COALESCE(AVG(confidence),0) AS avg_conf
                     FROM knowledge""")
    return dict(r) if r else {"n": 0, "avg_conf": 0}


def learn_question(question, topic=None, providers=None):
    """Ask all providers, score, save best answer."""
    ensure_tables()
    providers = providers or _providers()
    if not providers:
        return {"ok": False, "error": "no providers available"}

    replies = ask_many(question, providers=providers, temperature=0.4)
    if not replies:
        return {"ok": False, "error": "no replies"}

    ranked = score_answers(question, replies, judge_providers=providers)
    if not ranked:
        return {"ok": False, "error": "scoring failed"}

    top_provider, top_score, top_text = ranked[0]
    sources = ",".join(f"{p}:{s}" for p, s, _ in ranked)
    confidence = top_score / max(1, len(providers) - 1)

    cur = execute(
        """INSERT INTO knowledge
           (topic, question, answer, sources, confidence)
           VALUES (?, ?, ?, ?, ?)""",
        (topic or question.split()[:3] and " ".join(question.split()[:3]),
         question, top_text, sources, confidence))
    kid = cur.lastrowid if hasattr(cur, "lastrowid") else None

    audit.log("knowledge_learned", actor="learn",
              payload={"kid": kid, "topic": topic,
                       "winner": top_provider,
                       "score": top_score})
    return {
        "ok": True,
        "id": kid,
        "winner": top_provider,
        "score": top_score,
        "confidence": round(confidence, 2),
        "answer": top_text,
        "ranking": [{"provider": p, "score": s} for p, s, _ in ranked],
    }


def recall(question, limit=3):
    """Search knowledge base for a matching question."""
    ensure_tables()
    rows = fetch_all(
        """SELECT * FROM knowledge
           WHERE question LIKE ?
           ORDER BY confidence DESC, use_count DESC LIMIT ?""",
        (f"%{question[:60]}%", limit))
    out = [dict(r) for r in rows]
    # bump use count
    for r in out:
        execute("UPDATE knowledge SET use_count = use_count + 1 WHERE id=?",
                (r["id"],))
    return out


def all_knowledge(limit=50):
    ensure_tables()
    rows = fetch_all(
        """SELECT id, topic, question, substr(answer,1,80) AS snippet,
                  confidence, use_count, learned_at
           FROM knowledge ORDER BY id DESC LIMIT ?""", (limit,))
    return [dict(r) for r in rows]


def get(kid):
    ensure_tables()
    r = fetch_one("SELECT * FROM knowledge WHERE id=?", (int(kid),))
    return dict(r) if r else None


def delete(kid):
    ensure_tables()
    execute("DELETE FROM knowledge WHERE id=?", (int(kid),))
    audit.log("knowledge_deleted", actor="learn", payload={"kid": int(kid)})
    return {"ok": True}


def stats():
    ensure_tables()
    r = fetch_one("""SELECT COUNT(*) AS n,
                     COALESCE(AVG(confidence),0) AS avg_conf
                     FROM knowledge""")
    return dict(r) if r else {"n": 0, "avg_conf": 0}
