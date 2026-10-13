import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app


class StudyFlowTest(unittest.TestCase):
    def test_selected_concept_and_explanation_questions_save_to_obsidian(self):
        with tempfile.TemporaryDirectory() as temp:
            app.DB_PATH = Path(temp) / "study.sqlite3"
            app.VAULT = Path(temp) / "vault"
            app.init_db()
            app.init_vault()
            concepts = app.study_concepts()
            iam = next(item for item in concepts if item["id"] == "iam")
            self.assertIn("최소 권한", iam["body"])
            self.assertNotIn("내 오답", iam["body"])
            self.assertNotIn("tags:", iam["body"])
            with patch.object(app, "request_study_answer", return_value={"body": "### 핵심\n역할을 사용합니다.", "model": app.MODEL}) as request:
                app.ask_concept("iam", "역할은 임시 자격 증명", "액세스 키와 다른 점은?")
                self.assertIn("IAM과 최소 권한", request.call_args.args[0])
                app.ask_explanation("E21-Q15", "스토리지 연결", "Direct Connect와 차이는?", "기존 AI 해설")
                prompt = request.call_args.args[0]
                self.assertIn("E21-Q15", prompt)
                self.assertIn("기존 AI 해설", prompt)
                self.assertIn("Direct Connect와 차이는?", prompt)
            saved = app.save_study_question("explanation", "E21-Q15", "ai", "스토리지 연결",
                                            "Direct Connect와 차이는?", "### 핵심\nStorage Gateway를 씁니다.", app.MODEL)
            note = Path(saved["path"])
            self.assertIn("Questions/migration/", saved["relative"])
            self.assertIn("chapters: [4, 10]", note.read_text(encoding="utf-8"))
            self.assertIn("[[Concepts/migration", note.read_text(encoding="utf-8"))
            self.assertIn(note.stem, (app.VAULT / "Questions" / "00-질문-목록.md").read_text(encoding="utf-8"))
            self.assertIn("학습 질문 목록", (app.VAULT / "00-시작.md").read_text(encoding="utf-8"))
            with self.assertRaisesRegex(ValueError, "Invalid explanation source"):
                app.save_study_question("explanation", "E21-Q15", "other", "선택", "질문", "답", app.MODEL)

    def test_exam_and_balanced_sessions_resume_without_finishing_bank(self):
        with tempfile.TemporaryDirectory() as temp:
            app.DB_PATH = Path(temp) / "study.sqlite3"
            app.init_db()
            exam = app.create_session("exam", exam=12)
            self.assertEqual((exam["total"], exam["question"]["id"]), (42, "E12-Q01"))
            first = app.submit_answer("E12-Q01", ["A"], 40, exam["id"])
            self.assertEqual(app.stats()["studied"], 1)
            self.assertEqual(app.session_details(exam["id"])["question"]["id"], "E12-Q02")
            self.assertEqual(app.advance_session(exam["id"], "E12-Q02")["question"]["id"], "E12-Q03")
            balanced = app.create_session("balanced")
            with app.connect() as db:
                domains = db.execute("""SELECT q.concept_id FROM session_items si
                                        JOIN questions q ON q.id=si.question_id WHERE si.session_id=?""",
                                     (balanced["id"],)).fetchall()
            from collections import Counter
            counts = Counter(app.BY_ID[row["concept_id"]][2] for row in domains)
            self.assertEqual(counts, app.balanced_counts(65))
            self.assertEqual(len({row["concept_id"] for row in domains}) > 1, True)
            self.assertEqual(app.session_details()["id"], balanced["id"])
            self.assertEqual([item["id"] for item in app.recent_sessions()], [balanced["id"], exam["id"]])
            self.assertEqual(app.session_details(exam["id"])["question"]["id"], "E12-Q03")
            app.activate_session(exam["id"])
            self.assertEqual(app.session_details()["id"], exam["id"])
            with self.assertRaisesRegex(ValueError, "65문항"):
                app.create_session("balanced", count=20)
            self.assertEqual(first["attempt_id"], 1)

    def test_due_session_uses_only_due_questions(self):
        with tempfile.TemporaryDirectory() as temp:
            app.DB_PATH = Path(temp) / "study.sqlite3"
            app.init_db()
            with self.assertRaisesRegex(ValueError, "맞는 문제가 없습니다"):
                app.create_session("due")
            app.submit_answer("E01-Q01", ["A"], 35)
            with app.connect() as db:
                db.execute("UPDATE progress SET due_at=? WHERE question_id='E01-Q01'",
                           ((app.now() - app.timedelta(days=1)).isoformat(),))
            due = app.create_session("due")
            self.assertEqual((due["total"], due["question"]["id"]), (1, "E01-Q01"))
            app.submit_answer("E01-Q01", ["A"], 22, due["id"])
            finished = app.advance_session(due["id"], "E01-Q01")
            self.assertTrue(finished["complete"])
            self.assertEqual((finished["answered"], finished["skipped"]), (1, 0))

    def test_source_line_breaks_and_verified_question_links(self):
        with tempfile.TemporaryDirectory() as temp:
            app.DB_PATH = Path(temp) / "study.sqlite3"
            app.init_db()
            broken = app.question_by_id("E13-Q04")
            self.assertIn("\nWhich", broken["stem"])
            self.assertNotIn("<br", broken["stem"])
            self.assertEqual(app.display_text("one&lt;/br&gt;two"), "one\ntwo")
            with app.connect() as db:
                verified = db.execute("SELECT * FROM questions WHERE id='E21-Q15'").fetchone()
                unrelated = db.execute("SELECT * FROM questions WHERE id='E01-Q04'").fetchone()
            sources = app.question_dict(verified, reveal=True)["official_sources"]
            self.assertTrue(sources)
            self.assertTrue(all(source["url"].startswith(("https://docs.aws.amazon.com/", "https://aws.amazon.com/")) for source in sources))
            self.assertEqual(app.question_dict(unrelated, reveal=True)["official_sources"], [])

    def test_import_grading_and_vault_write(self):
        with tempfile.TemporaryDirectory() as temp:
            app.DB_PATH = Path(temp) / "study.sqlite3"
            app.VAULT = Path(temp) / "vault"
            app.init_db()
            app.init_vault()
            self.assertTrue((app.VAULT / "References" / "학습서-안내.md").is_file())
            self.assertEqual(app.stats()["total"], 1142)
            with app.connect() as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM questions WHERE exam=13").fetchone()[0], 50)
                row = db.execute("SELECT * FROM questions WHERE id='E01-Q04'").fetchone()
                self.assertEqual(json.loads(row["correct"]), ["B", "E"])
            result = app.submit_answer("E01-Q04", ["A", "B"], 65)
            self.assertFalse(result["is_correct"])
            self.assertEqual(result["correct"], ["B", "E"])
            self.assertEqual(result["duration_seconds"], 65)
            self.assertEqual(app.stats()["studied"], 1)
            saved = app.save_note("E01-Q04", "탄력성과 복원력을 혼동했다")
            self.assertIn("탄력성과 복원력을 혼동했다", Path(saved["path"]).read_text())
            context = app.concept_context("resilience-scaling")
            self.assertIn("## 자주 틀리는 지점", context)
            self.assertNotIn("탄력성과 복원력을 혼동했다", context)
            self.assertNotIn("## 근거와 더 읽기", context)

    def test_timing_distribution_and_confusing_question(self):
        with tempfile.TemporaryDirectory() as temp:
            app.DB_PATH = Path(temp) / "study.sqlite3"
            app.VAULT = Path(temp) / "vault"
            app.init_db()
            with app.connect() as db:
                questions = db.execute("SELECT id, correct FROM questions WHERE id != 'E01-Q04' LIMIT 8").fetchall()
            for question, seconds in zip(questions, [30, 40, 50, 60, 70, 80, 90, 100]):
                app.submit_answer(question["id"], json.loads(question["correct"]), seconds)
            self.assertEqual(app.stats()["timing"]["slow_threshold_seconds"], 83)
            app.submit_answer("E01-Q04", ["A", "B"], 130)
            app.submit_answer("E01-Q04", ["A", "B"], 140)
            result = app.submit_answer("E01-Q04", ["B", "E"], 150)
            self.assertTrue(result["is_correct"])
            self.assertTrue(result["slow"])
            self.assertEqual(result["question_stats"]["avg_seconds"], 140)
            with app.connect() as db:
                self.assertEqual(db.execute("SELECT streak FROM progress WHERE question_id='E01-Q04'").fetchone()[0], 0)
            self.assertGreater(app.stats()["timing"]["slow_threshold_seconds"], 83)
            self.assertIn("E01-Q04", [q["id"] for q in app.stats()["confusing_questions"]])
            followup = app.submit_answer("E01-Q04", ["B", "E"], 100)
            self.assertFalse(followup["slow"])
            self.assertTrue(followup["confused"])
            with app.connect() as db:
                self.assertEqual(db.execute("SELECT streak FROM progress WHERE question_id='E01-Q04'").fetchone()[0], 0)

    def test_fast_personal_distribution_does_not_mark_exam_pace_answer_slow(self):
        with tempfile.TemporaryDirectory() as temp:
            app.DB_PATH = Path(temp) / "study.sqlite3"
            app.init_db()
            with app.connect() as db:
                questions = db.execute("SELECT id, correct FROM questions WHERE id != 'E01-Q04' LIMIT 8").fetchall()
            for question, seconds in zip(questions, [12, 16, 19, 22, 25, 28, 31, 35]):
                app.submit_answer(question["id"], json.loads(question["correct"]), seconds)
            result = app.submit_answer("E01-Q04", ["B", "E"], 43)
            self.assertTrue(result["is_correct"])
            self.assertFalse(result["slow"])
            self.assertEqual(result["time_threshold_seconds"], 83)
            self.assertEqual(result["personal_average_seconds"], 26)
            self.assertEqual(app.stats()["timing"]["slow_threshold_seconds"], 83)
            with app.connect() as db:
                self.assertEqual(db.execute("SELECT streak FROM progress WHERE question_id='E01-Q04'").fetchone()[0], 1)

    def test_existing_database_gets_timing_column(self):
        with tempfile.TemporaryDirectory() as temp:
            app.DB_PATH = Path(temp) / "old.sqlite3"
            with app.connect() as db:
                db.execute("""CREATE TABLE attempts (id INTEGER PRIMARY KEY, question_id TEXT NOT NULL,
                           selected TEXT NOT NULL, correct INTEGER NOT NULL, confidence TEXT NOT NULL,
                           created_at TEXT NOT NULL)""")
            app.init_db()
            with app.connect() as db:
                columns = {row["name"] for row in db.execute("PRAGMA table_info(attempts)")}
            self.assertIn("duration_seconds", columns)

    def test_ai_comparison_is_saved_by_category_and_chapter_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            app.DB_PATH = Path(temp) / "study.sqlite3"
            app.VAULT = Path(temp) / "vault"
            app.init_db()
            app.init_vault()
            attempt = app.submit_answer("E11-Q34", ["D"], 95)
            self.assertFalse(attempt["is_correct"])
            key = f"E11-Q34:D:{app.MODEL}:compare-v2"
            with app.connect() as db:
                db.execute("INSERT INTO explanations VALUES (?,?,?,?)",
                           (key, "### 정답의 핵심\n\nGlacier와 다른 스토리지를 비교한다.", app.MODEL, app.now().isoformat()))
            explained = app.explain("E11-Q34", ["D"], attempt["attempt_id"])
            note = Path(explained["note_path"])
            self.assertIn("10장 스토리지", str(note))
            self.assertIn("클라우드 기술 및 서비스", str(note))
            body = note.read_text(encoding="utf-8")
            self.assertIn("Glacier와 다른 스토리지를 비교한다", body)
            self.assertIn("## 공식 자료 대조", body)
            self.assertIn("[[Concepts/s3-storage|S3와 스토리지 클래스]]", body)
            self.assertIn("내 선택", body)
            self.assertIn("E11-Q34", (app.VAULT / "Review" / "Chapters" / "10장 스토리지.md").read_text())
            self.assertIn("E11-Q34", (app.VAULT / "Review" / "클라우드 기술 및 서비스" / "00-카테고리.md").read_text())
            with note.open("a", encoding="utf-8") as out:
                out.write("\n내가 수정한 메모\n")
            app.explain("E11-Q34", ["D"], attempt["attempt_id"])
            self.assertIn("내가 수정한 메모", note.read_text(encoding="utf-8"))
            links = [line for line in (app.VAULT / "Review" / "Chapters" / "10장 스토리지.md").read_text().splitlines()
                     if line.startswith("- [[") and "E11-Q34" in line]
            self.assertEqual(len(links), 1)

            deployment = app.submit_answer("E12-Q38", ["A", "D"], 100)
            key = f"E12-Q38:A,D:{app.MODEL}:compare-v2"
            with app.connect() as db:
                db.execute("INSERT INTO explanations VALUES (?,?,?,?)",
                           (key, "### 정답의 핵심\n\nCodeDeploy와 OpsWorks를 비교한다.", app.MODEL, app.now().isoformat()))
            deployment_note = Path(app.explain("E12-Q38", ["A", "D"], deployment["attempt_id"])["note_path"])
            self.assertIn("14장 개발·메시징 서비스", str(deployment_note))
            self.assertIn("chapters: [14]", deployment_note.read_text())
            self.assertNotIn("E12-Q38", (app.VAULT / "Review" / "Chapters" / "13장 AI·분석.md").read_text())


if __name__ == "__main__":
    unittest.main()
