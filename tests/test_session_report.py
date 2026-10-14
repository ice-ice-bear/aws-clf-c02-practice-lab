import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app
from session_report import REVIEW_FOCUS, build_session_report


def item(concept_id, correct, seconds=None, confidence="sure", selected=None):
    return {"concept_id": concept_id, "correct": correct,
            "attempt_id": None if correct is None else 1, "duration_seconds": seconds,
            "confidence": confidence, "question_id": f"{concept_id}-{correct}-{seconds}",
            "exam": 1, "number": 1, "stem": "question", "needs_review": 0,
            "selected": json.dumps(selected or ["B"]), "correct_answers": '["A", "C"]'}


class SessionReportTest(unittest.TestCase):
    def report(self, items):
        return build_session_report(items, app.DOMAIN_WEIGHTS, app.EXAM_PACE_SECONDS)

    def test_denominators_priority_missing_times_and_overlapping_flags(self):
        r = self.report([item("iam", 0, 10), item("iam", 1, None),
                         item("compute", 1, 100, "unsure"), item("compute", None),
                         item("billing", 1, 20)])
        self.assertEqual((r["total"], r["answered"], r["correct"], r["wrong"], r["skipped"]), (5, 4, 3, 1, 1))
        self.assertEqual((r["score_percent"], r["wrong_percent"]), (60, 25))
        self.assertEqual((r["timed_answers"], r["total_seconds"], r["average_seconds"]), (3, 130, 43.3))
        self.assertEqual((r["slow_correct"], r["flagged_correct"], r["review_count"]), (1, 1, 3))
        self.assertEqual([c["id"] for c in r["concepts"]], ["iam", "compute", "billing"])
        self.assertEqual(len(r["concepts"][1]["question_ids"]), 2)
        self.assertEqual(r["review_questions"][0]["correct_answers"], ["A", "C"])
        self.assertEqual(r["review_questions"][2]["selected"], [])
        absent = next(d for d in r["domains"] if d["domain"] == "클라우드 개념")
        self.assertIsNone(absent["score_percent"])
        self.assertIsNone(absent["wrong_percent"])
        self.assertEqual(set(REVIEW_FOCUS), set(app.BY_ID))

    def test_all_skipped_perfect_and_exact_time_boundary(self):
        skipped = self.report([item("iam", None), item("billing", None)])
        self.assertEqual(skipped["score_percent"], 0)
        self.assertIsNone(skipped["wrong_percent"])
        self.assertIsNone(skipped["average_seconds"])
        self.assertEqual(skipped["review_count"], 2)
        perfect = self.report([item("iam", 1, 82), item("billing", 1, None)])
        self.assertEqual(perfect["score_percent"], 100)
        self.assertEqual(perfect["review_questions"], [])
        slow = self.report([item("iam", 1, 83)])
        self.assertEqual(slow["slow_correct"], 1)
        self.assertEqual(slow["review_count"], 1)

    def test_completed_set_uses_attached_attempt_and_is_stable_after_retry(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(app, "DB_PATH", Path(temp) / "study.sqlite3"):
            app.init_db()
            session = app.create_session("exam", exam=12)
            self.assertIsNone(session["report"])
            with app.connect() as db:
                questions = db.execute("SELECT * FROM questions WHERE exam=12 ORDER BY number").fetchall()
                for position, q in enumerate(questions):
                    correct = position < 21
                    answers = json.loads(q["correct"])
                    if not correct:
                        answers = [next(letter for letter in json.loads(q["options"]) if [letter] != answers)]
                    attempt_id = db.execute("""INSERT INTO attempts(question_id, selected, correct, confidence, created_at, duration_seconds)
                        VALUES (?,?,?,?,?,?)""", (q["id"], json.dumps(answers), int(correct), "sure" if correct else "unsure",
                                                 app.now().isoformat(), 20 if position < 10 else None)).lastrowid
                    db.execute("UPDATE session_items SET attempt_id=? WHERE session_id=? AND position=?",
                               (attempt_id, session["id"], position))
                db.execute("UPDATE sessions SET cursor=42 WHERE id=?", (session["id"],))
            original = app.session_details(session["id"])
            self.assertTrue(original["complete"])
            self.assertEqual((original["report"]["score_percent"], original["report"]["wrong_percent"]), (50, 50))
            self.assertEqual(original["report"]["timed_answers"], 10)
            app.submit_answer(questions[-1]["id"], json.loads(questions[-1]["correct"]), 15)
            self.assertEqual(app.activate_session(session["id"]), original)
            with app.connect() as db:
                before = list(db.iterdump())
            self.assertEqual(app.session_details(session["id"]), original)
            with app.connect() as db:
                self.assertEqual(list(db.iterdump()), before)

    def test_65_questions_match_raw_score_and_error_rate(self):
        r = self.report([item("iam", int(i < 33), 30) for i in range(65)])
        self.assertEqual((r["score_percent"], r["wrong_percent"], r["wrong"]), (50.8, 49.2, 32))


if __name__ == "__main__":
    unittest.main()
