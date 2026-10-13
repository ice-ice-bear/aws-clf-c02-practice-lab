"""Local CLF-C02 question practice and Obsidian review service (stdlib only)."""

import argparse
import json
import math
import os
import random
import re
import sqlite3
import sys
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from concepts import BY_ID, CONCEPTS, as_dict, classify
from knowledge import render_note
from review_notes import init_review_map, save_ai_review

ROOT = Path(__file__).resolve().parent


def load_local_env(path):
    """Load local settings without executing shell code; exported values take priority."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or key not in {"OPENAI_API_KEY", "AWS_CCP_MODEL", "AWS_CCP_DB", "AWS_CCP_VAULT"}:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if value and not os.environ.get(key):
            os.environ[key] = value


load_local_env(ROOT / ".env")
DB_PATH = Path(os.environ.get("AWS_CCP_DB", ROOT / "data" / "study.sqlite3"))
VAULT = Path(os.environ.get("AWS_CCP_VAULT", ROOT / "vault")).expanduser()
MODEL = os.environ.get("AWS_CCP_MODEL", "gpt-6-luna")


def now():
    return datetime.now(timezone.utc)


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY, exam INTEGER NOT NULL, number INTEGER NOT NULL,
            stem TEXT NOT NULL, options TEXT NOT NULL, correct TEXT NOT NULL,
            concept_id TEXT NOT NULL, source_url TEXT NOT NULL, needs_review INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY, question_id TEXT NOT NULL REFERENCES questions(id),
            selected TEXT NOT NULL, correct INTEGER NOT NULL, confidence TEXT NOT NULL,
            created_at TEXT NOT NULL, duration_seconds REAL
        );
        CREATE TABLE IF NOT EXISTS progress (
            question_id TEXT PRIMARY KEY REFERENCES questions(id),
            streak INTEGER NOT NULL, due_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS explanations (
            cache_key TEXT PRIMARY KEY, body TEXT NOT NULL, model TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)
        # Existing local study histories predate automatic timing.
        if "duration_seconds" not in {row["name"] for row in db.execute("PRAGMA table_info(attempts)")}:
            db.execute("ALTER TABLE attempts ADD COLUMN duration_seconds REAL")
        seed = ROOT / "data" / "questions.json"
        if seed.exists():
            rows = json.loads(seed.read_text(encoding="utf-8"))
            for q in rows:
                concept_id = classify(q["stem"], q["options"], q["correct"])
                review = bool(re.search(r"master account|AWS Abuse team|Concierge|OpsWorks|Server Migration Service|Enterprise On.Ramp", q["stem"] + " ".join(q["options"].values()), re.I))
                db.execute("""INSERT INTO questions VALUES (?,?,?,?,?,?,?,?,?)
                              ON CONFLICT(id) DO UPDATE SET stem=excluded.stem,options=excluded.options,
                              correct=excluded.correct,concept_id=excluded.concept_id,
                              source_url=excluded.source_url,needs_review=excluded.needs_review""", (
                    q["id"], q["exam"], q["number"], q["stem"],
                    json.dumps(q["options"], ensure_ascii=False), json.dumps(q["correct"]),
                    concept_id, q["source_url"], int(review),
                ))


def init_vault():
    (VAULT / "Concepts").mkdir(parents=True, exist_ok=True)
    (VAULT / "Review").mkdir(exist_ok=True)
    (VAULT / ".obsidian").mkdir(exist_ok=True)
    start = VAULT / "00-시작.md"
    if not start.exists():
        start.write_text((ROOT / "templates" / "00-시작.md").read_text(encoding="utf-8"), encoding="utf-8")
    reference = VAULT / "References" / "학습서-안내.md"
    reference.parent.mkdir(exist_ok=True)
    if not reference.exists():
        reference.write_text((ROOT / "templates" / "References" / "학습서-안내.md").read_text(encoding="utf-8"), encoding="utf-8")
    for item in CONCEPTS:
        concept = as_dict(item)
        path = VAULT / "Concepts" / f"{concept['id']}.md"
        if path.exists():
            continue
        path.write_text(render_note(item), encoding="utf-8")
    settings = VAULT / ".obsidian" / "app.json"
    if not settings.exists():
        settings.write_text('{"alwaysUpdateLinks":true}\n', encoding="utf-8")
    init_review_map(VAULT)


def question_dict(row, reveal=False):
    q = {"id": row["id"], "exam": row["exam"], "number": row["number"],
         "stem": row["stem"], "options": json.loads(row["options"]),
         "multiple": len(json.loads(row["correct"])) > 1,
         "concept": as_dict(BY_ID[row["concept_id"]]),
         "source_url": row["source_url"], "needs_review": bool(row["needs_review"])}
    if reveal:
        q["correct"] = json.loads(row["correct"])
    return q


def next_question(mode="random", exam=None, exclude_id=None):
    with connect() as db:
        where = ["1=1"]
        args = []
        if exam:
            where.append("q.exam=?")
            args.append(int(exam))
        if mode == "due":
            where.append("p.due_at <= ?")
            args.append(now().isoformat())
        if mode == "new":
            where.append("p.question_id IS NULL")
        if exclude_id:
            where.append("q.id != ?")
            args.append(exclude_id)
        sql = f"""SELECT q.* FROM questions q LEFT JOIN progress p ON p.question_id=q.id
                  WHERE {' AND '.join(where)} ORDER BY RANDOM() LIMIT 1"""
        row = db.execute(sql, args).fetchone()
        return question_dict(row) if row else None


def question_by_id(question_id):
    with connect() as db:
        row = db.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone()
        return question_dict(row) if row else None


def timing_baseline(db):
    """Use the learner's own 75th percentile; bootstrap until eight timed answers."""
    times = sorted(row[0] for row in db.execute(
        "SELECT duration_seconds FROM attempts WHERE duration_seconds IS NOT NULL"))
    if len(times) < 8:
        return 90.0, len(times), True
    position = (len(times) - 1) * .75
    lower = math.floor(position)
    fraction = position - lower
    p75 = times[lower] + (times[min(lower + 1, len(times) - 1)] - times[lower]) * fraction
    return max(30.0, p75), len(times), False


def submit_answer(question_id, selected, duration_seconds=None):
    if not isinstance(selected, list):
        raise ValueError("selected must be a list")
    if duration_seconds is not None:
        if (isinstance(duration_seconds, bool) or not isinstance(duration_seconds, (int, float))
                or not math.isfinite(duration_seconds) or not 1 <= duration_seconds <= 1800):
            raise ValueError("Invalid answer time")
    with connect() as db:
        q = db.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone()
        if not q:
            raise ValueError("Unknown question")
        options = json.loads(q["options"])
        selected = sorted(set(selected))
        if not selected or not set(selected).issubset(options):
            raise ValueError("Invalid selection")
        correct = selected == sorted(json.loads(q["correct"]))
        threshold, _, provisional = timing_baseline(db)
        slow = duration_seconds is not None and duration_seconds >= threshold
        confidence = "unsure" if slow or not correct else "sure"
        history = db.execute("""SELECT COUNT(*) attempts, AVG(duration_seconds) avg_seconds,
                                      SUM(CASE WHEN correct=0 THEN 1 ELSE 0 END) wrong
                               FROM attempts WHERE question_id=? AND duration_seconds IS NOT NULL""",
                             (question_id,)).fetchone()
        timed_attempts = history["attempts"] + int(duration_seconds is not None)
        avg_seconds = ((history["avg_seconds"] or 0) * history["attempts"] + (duration_seconds or 0)) / timed_attempts if timed_attempts else None
        wrong_count = (history["wrong"] or 0) + int(duration_seconds is not None and not correct)
        confused = (timed_attempts >= 3 and wrong_count / timed_attempts >= .4
                    and avg_seconds >= threshold)
        old = db.execute("SELECT streak FROM progress WHERE question_id=?", (question_id,)).fetchone()
        streak = (old["streak"] + 1 if old else 1) if correct and confidence == "sure" and not confused else 0
        days = min(30, 2 ** streak) if streak else 1
        due = (now() + timedelta(days=days)).isoformat()
        inserted = db.execute("INSERT INTO attempts(question_id,selected,correct,confidence,created_at,duration_seconds) VALUES (?,?,?,?,?,?)",
                              (question_id, json.dumps(selected), int(correct), confidence, now().isoformat(), duration_seconds))
        db.execute("INSERT INTO progress VALUES (?,?,?) ON CONFLICT(question_id) DO UPDATE SET streak=excluded.streak,due_at=excluded.due_at",
                   (question_id, streak, due))
        out = question_dict(q, reveal=True)
        out.update({"is_correct": correct, "selected": selected, "due_at": due,
                    "attempt_id": inserted.lastrowid,
                    "duration_seconds": duration_seconds, "slow": slow, "confused": confused,
                    "time_threshold_seconds": round(threshold), "timing_provisional": provisional,
                    "question_stats": {"attempts": timed_attempts,
                                       "avg_seconds": round(avg_seconds) if avg_seconds is not None else None,
                                       "wrong_rate": round(wrong_count / timed_attempts, 2) if timed_attempts else None},
                    "offline_explanation": as_dict(BY_ID[q["concept_id"]])["summary"]})
        return out


def stats():
    with connect() as db:
        total = db.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        attempts = db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
        distinct = db.execute("SELECT COUNT(*) FROM progress").fetchone()[0]
        due = db.execute("SELECT COUNT(*) FROM progress WHERE due_at<=?", (now().isoformat(),)).fetchone()[0]
        rows = db.execute("""SELECT q.concept_id, COUNT(a.id) n, SUM(CASE WHEN a.correct=0 OR a.confidence!='sure' THEN 1 ELSE 0 END) weak
                             FROM questions q JOIN attempts a ON a.question_id=q.id
                             GROUP BY q.concept_id ORDER BY weak DESC, n DESC""").fetchall()
        weak = [{**as_dict(BY_ID[r["concept_id"]]), "attempts": r["n"], "weak": r["weak"]}
                for r in rows if r["weak"]]
        threshold, timed_count, provisional = timing_baseline(db)
        question_rows = db.execute("""SELECT q.id, q.exam, q.number, q.stem, q.concept_id,
                                          COUNT(*) attempts, AVG(a.duration_seconds) avg_seconds,
                                          SUM(CASE WHEN a.correct=0 THEN 1 ELSE 0 END) wrong
                                   FROM attempts a JOIN questions q ON q.id=a.question_id
                                   WHERE a.duration_seconds IS NOT NULL
                                   GROUP BY q.id HAVING COUNT(*) >= 3""").fetchall()
        confusing = [{"id": r["id"], "exam": r["exam"], "number": r["number"],
                      "stem": r["stem"], "concept": as_dict(BY_ID[r["concept_id"]]),
                      "attempts": r["attempts"], "wrong_rate": round(r["wrong"] / r["attempts"], 2),
                      "avg_seconds": round(r["avg_seconds"])} for r in question_rows
                     if r["wrong"] / r["attempts"] >= .4 and r["avg_seconds"] >= threshold]
        confusing.sort(key=lambda r: (r["wrong_rate"], r["avg_seconds"]), reverse=True)
        return {"total": total, "attempts": attempts, "studied": distinct, "due": due, "weak": weak,
                "confusing_questions": confusing[:12],
                "timing": {"samples": timed_count, "slow_threshold_seconds": round(threshold),
                           "provisional": provisional},
                "model": MODEL, "api_ready": bool(os.getenv("OPENAI_API_KEY")), "vault": str(VAULT)}


def extract_output(response):
    chunks = []
    for item in response.get("output", []):
        for part in item.get("content", []):
            if part.get("type") == "output_text":
                chunks.append(part.get("text", ""))
    return "\n".join(chunks).strip()


def concept_context(concept_id):
    """Pass the authored study note, excluding personal mistakes, to the model."""
    path = VAULT / "Concepts" / f"{concept_id}.md"
    if not path.exists():
        return as_dict(BY_ID[concept_id])["summary"]
    return path.read_text(encoding="utf-8").split("## 내 오답", 1)[0][:5000]


def explain(question_id, selected, attempt_id=None):
    if not isinstance(selected, list) or not all(isinstance(letter, str) for letter in selected):
        raise ValueError("Invalid selection")
    selected = sorted(set(selected))
    key = question_id + ":" + ",".join(selected) + ":" + MODEL + ":compare-v2"
    with connect() as db:
        q = db.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone()
        if not q:
            raise ValueError("Unknown question")
        if not selected or not set(selected).issubset(json.loads(q["options"])):
            raise ValueError("Invalid selection")
        if attempt_id is not None:
            if isinstance(attempt_id, bool) or not isinstance(attempt_id, int) or attempt_id < 1:
                raise ValueError("Invalid attempt")
            attempt = db.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
        else:
            attempt = db.execute("SELECT * FROM attempts WHERE question_id=? AND selected=? ORDER BY id DESC LIMIT 1",
                                 (question_id, json.dumps(selected))).fetchone()
        if not attempt or attempt["question_id"] != question_id or json.loads(attempt["selected"]) != selected:
            raise ValueError("먼저 해당 문제에 답을 제출하세요")
        cached = db.execute("SELECT body,model FROM explanations WHERE cache_key=?", (key,)).fetchone()
        concept = as_dict(BY_ID[q["concept_id"]])
    if cached:
        body, model = cached["body"], cached["model"]
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY가 없습니다. 먼저 공식 근거와 개념 노트를 확인하세요.")
        prompt = ("AWS CLF-C02 문제의 오답 해설을 한국어 Markdown으로 작성하세요. 문제은행 정답이 오래됐을 수 있으므로 "
                  "충돌하거나 불확실한 내용은 '공식 문서 확인 필요'라고 표시하세요. 제공한 URL을 직접 읽었다고 주장하지 마세요. "
                  "새 링크나 이미지를 만들지 마세요. PDF 원문은 제공되지 않았습니다.\n"
                  "반드시 다음 네 소제목을 사용하세요: '### 정답의 핵심', '### 내 선택과 정답 비교', "
                  "'### 헷갈린 개념 구별', '### 다음 복습 질문'. "
                  "내가 고른 보기와 문제은행 정답이 왜 다른지 구체적인 서비스 기능과 문제의 결정적 단서로 비교하세요. "
                  "복수 선택이면 빠뜨린 정답과 잘못 선택한 보기를 모두 다루세요. 500~800자 내외.\n\n"
                  f"문제: {q['stem']}\n보기: {q['options']}\n문제은행 정답: {q['correct']}\n학습자 선택: {selected}\n"
                  f"카테고리: {concept['domain']}\n개념: {concept['title']}\n"
                  f"작성된 개념 노트 (PDF 본문과 개인 오답 제외):\n{concept_context(concept['id'])}\n"
                  f"공식 근거 URL: {concept['url']}\n"
                  f"문항 재검토 표시: {bool(q['needs_review'])}")
        payload = {"model": MODEL, "input": prompt, "reasoning": {"effort": "low"}, "max_output_tokens": 1200}
        request = urllib.request.Request("https://api.openai.com/v1/responses", data=json.dumps(payload).encode(),
                                         headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"OpenAI API 오류: HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError("OpenAI API에 연결하지 못했습니다.") from exc
        body = extract_output(result)
        if not body:
            raise RuntimeError("모델 응답에 해설 텍스트가 없습니다.")
        model = MODEL
        with connect() as db:
            db.execute("INSERT OR REPLACE INTO explanations VALUES (?,?,?,?)", (key, body, model, now().isoformat()))
    note_path = None
    if not attempt["correct"] or attempt["confidence"] != "sure":
        note_path = save_ai_review(VAULT, q, attempt, body, model)
    return {"body": body, "model": model, "cached": bool(cached),
            "note_path": str(note_path) if note_path else None,
            "note_relative": note_path.relative_to(VAULT).as_posix() if note_path else None}


def save_note(question_id, reason):
    reason = " ".join(str(reason).split())[:500]
    if not reason:
        raise ValueError("오답 이유를 적어주세요")
    with connect() as db:
        q = db.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone()
        if not q:
            raise ValueError("Unknown question")
    init_vault()
    path = VAULT / "Concepts" / f"{q['concept_id']}.md"
    with path.open("a", encoding="utf-8") as out:
        out.write(f"\n- {now().date().isoformat()} · [{question_id}]({q['source_url']}): {reason}\n")
    return {"path": str(path)}


class Handler(BaseHTTPRequestHandler):
    def respond(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        args = parse_qs(parsed.query)
        if parsed.path == "/api/stats":
            return self.respond(stats())
        if parsed.path == "/api/next":
            mode = args.get("mode", ["random"])[0]
            exam = args.get("exam", [None])[0]
            question_id = args.get("id", [None])[0]
            if question_id:
                return self.respond({"question": question_by_id(question_id)})
            exclude_id = args.get("exclude", [None])[0]
            if mode not in ("random", "new", "due"):
                return self.respond({"error": "Invalid mode"}, 400)
            return self.respond({"question": next_question(mode, exam, exclude_id)})
        if parsed.path == "/api/concepts":
            return self.respond({"concepts": [as_dict(c) for c in CONCEPTS]})
        file = "index.html" if parsed.path == "/" else parsed.path.removeprefix("/")
        if file not in ("index.html", "app.js", "style.css", "favicon.svg"):
            self.send_error(404)
            return
        content = (ROOT / "static" / file).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", {"index.html": "text/html; charset=utf-8", "app.js": "application/javascript; charset=utf-8", "style.css": "text/css; charset=utf-8", "favicon.svg": "image/svg+xml"}[file])
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        origin = self.headers.get("Origin")
        if origin and not origin.startswith(("http://127.0.0.1:", "http://localhost:")):
            return self.respond({"error": "Local origin required"}, 403)
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 20000:
                raise ValueError("Request too large")
            data = json.loads(self.rfile.read(length))
            if self.path == "/api/answer":
                return self.respond(submit_answer(data["id"], data["selected"], data.get("duration_seconds")))
            if self.path == "/api/explain":
                return self.respond(explain(data["id"], data.get("selected", []), data.get("attempt_id")))
            if self.path == "/api/save-note":
                return self.respond(save_note(data["id"], data["reason"]))
            self.send_error(404)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            self.respond({"error": str(exc)}, 400)
        except RuntimeError as exc:
            self.respond({"error": str(exc)}, 503)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--init-only", action="store_true")
    args = parser.parse_args()
    init_db()
    init_vault()
    if args.init_only:
        print(f"Ready: {stats()['total']} questions; vault {VAULT}")
        return
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"AWS CCP Study: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
