import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import app
import portable


class PortableBackupTest(unittest.TestCase):
    def test_live_database_and_personal_vault_survive_export(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            for name in (*portable.SOURCE_FILES, *portable.DATA_FILES, "portable.py"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("sample", encoding="utf-8")
            (root / ".env").write_text("OPENAI_API_KEY=secret-do-not-export\n", encoding="utf-8")
            vault = root / "vault"
            note = vault / "Review" / "오답.md"
            note.parent.mkdir(parents=True)
            note.write_text("내 오답 메모", encoding="utf-8")
            pdf = vault / "References" / "book.pdf"
            pdf.parent.mkdir()
            pdf.write_bytes(b"%PDF-1.4 sample")
            db_path = root / "data" / "study.sqlite3"
            with sqlite3.connect(db_path) as db:
                for table in ("questions", "attempts", "progress", "explanations"):
                    db.execute(f"CREATE TABLE {table} (value TEXT)")
                db.execute("INSERT INTO attempts VALUES ('solved')")
            output = Path(temp) / "backup.zip"
            with patch.object(portable, "ROOT", root), patch.object(app, "DB_PATH", db_path), patch.object(app, "VAULT", vault):
                manifest = portable.export(output)
                checked = portable.verify(output)
            self.assertEqual(manifest["counts"]["attempts"], 1)
            self.assertEqual(checked["counts"], manifest["counts"])
            with zipfile.ZipFile(output) as archive:
                self.assertNotIn(portable.PREFIX + ".env", archive.namelist())
                self.assertEqual(archive.read(portable.PREFIX + "vault/Review/오답.md").decode(), "내 오답 메모")
                self.assertEqual(archive.read(portable.PREFIX + "vault/References/book.pdf"), b"%PDF-1.4 sample")
                restored = Path(temp) / "restored"
                archive.extractall(restored)
            restored_db = restored / "aws-clf-c02-practice-lab" / "data" / "study.sqlite3"
            with sqlite3.connect(restored_db) as db:
                self.assertEqual(db.execute("SELECT value FROM attempts").fetchone()[0], "solved")

    def test_verify_rejects_changed_file(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "bad.zip"
            manifest = {"format": 1, "files": {
                "portable.py": {"bytes": 4, "sha256": portable.digest(b"good")},
                "data/study.sqlite3": {"bytes": 0, "sha256": portable.digest(b"")},
            }}
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(portable.PREFIX + "portable.py", b"evil")
                archive.writestr(portable.PREFIX + "data/study.sqlite3", b"")
                archive.writestr(portable.PREFIX + "backup-manifest.json", json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "손상된 파일"):
                portable.verify(archive_path)
