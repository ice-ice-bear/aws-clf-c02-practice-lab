import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app
from study_supplements import SUPPLEMENTS


class StudySupplementsTest(unittest.TestCase):
    def test_all_concepts_have_valid_tables_and_local_page_references(self):
        self.assertEqual(set(SUPPLEMENTS), set(app.BY_ID))
        with tempfile.TemporaryDirectory() as temp, patch.object(app, "VAULT", Path(temp) / "vault"):
            app.init_vault()
            for concept in app.study_concepts():
                with self.subTest(concept=concept["id"]):
                    body = concept["body"]
                    first_heading = SUPPLEMENTS[concept["id"]].split("\n", 1)[0]
                    self.assertTrue(body.startswith(first_heading))
                    self.assertNotIn("PDF 기반 보강", body)
                    self.assertIn("확인 문제", body)
                    self.assertIn(first_heading, app.concept_context(concept["id"]))
                    references = body.split("## 근거와 더 읽기", 1)[1].split("## 내 오답", 1)[0]
                    self.assertNotIn("### 보강 자료", references)
                    self.assertNotIn("Taulli, 2026 학습서", references)
                    urls = re.findall(r"\]\((https://[^)]+)\)", references)
                    self.assertTrue(urls)
                    self.assertEqual(len(urls), len(set(urls)))
                    pages = re.findall(r"Taulli-2026-CLF-C02\.pdf#page=(\d+)", body)
                    self.assertTrue(pages)
                    self.assertTrue(all(1 <= int(page) <= 412 for page in pages))
                    rows = [line for line in body.splitlines() if line.startswith("|")]
                    self.assertGreaterEqual(len(rows), 4)
                    self.assertEqual(len({row.count("|") for row in rows}), 1)

    def test_reinitialization_keeps_edited_notes_and_excludes_personal_ai_context(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(app, "VAULT", Path(temp) / "vault"):
            app.init_vault()
            note = app.VAULT / "Concepts" / "s3-storage.md"
            original = note.read_text(encoding="utf-8")
            edited = original.replace("# S3와 스토리지 클래스\n", "# S3와 스토리지 클래스\n\n내가 추가한 설명\n", 1) + "\n내 개인 오답\n"
            note.write_text(edited, encoding="utf-8")
            app.init_vault()
            self.assertEqual(note.read_text(encoding="utf-8"), edited)
            self.assertIn("Glacier Instant Retrieval", app.concept_context("s3-storage"))
            self.assertNotIn("내 개인 오답", app.concept_context("s3-storage"))


if __name__ == "__main__":
    unittest.main()
