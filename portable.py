"""Create and check a self-contained, key-free study archive."""

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import app


ROOT = Path(__file__).resolve().parent
PREFIX = "aws-clf-c02-practice-lab/"
SOURCE_FILES = ("README.md", ".gitignore", ".env.example")
SOURCE_DIRS = ("static", "tests")
DATA_FILES = ("data/questions.json", "data/UPSTREAM_LICENSE")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_paths():
    for path in sorted(ROOT.glob("*.py")):
        yield path.relative_to(ROOT).as_posix(), path
    for name in (*SOURCE_FILES, *DATA_FILES):
        path = ROOT / name
        if not path.is_file():
            raise FileNotFoundError(path)
        yield name, path
    for name in SOURCE_DIRS:
        for path in sorted((ROOT / name).rglob("*")):
            if path.is_file() and not path.is_symlink() and not path.name.startswith(".DS_Store") and "__pycache__" not in path.parts and path.suffix != ".pyc":
                yield path.relative_to(ROOT).as_posix(), path
    if not app.VAULT.is_dir():
        raise FileNotFoundError(app.VAULT)
    for path in sorted(app.VAULT.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"볼트 안 심볼릭 링크는 직접 복사해야 합니다: {path}")
        if path.is_file() and path.name != ".DS_Store":
            yield "vault/" + path.relative_to(app.VAULT).as_posix(), path


def database_snapshot(path):
    if not app.DB_PATH.is_file():
        raise FileNotFoundError(f"학습 DB가 없습니다: {app.DB_PATH}")
    with sqlite3.connect(f"file:{app.DB_PATH}?mode=ro", uri=True) as source:
        with sqlite3.connect(path) as target:
            source.backup(target)
    with sqlite3.connect(path) as db:
        result = db.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise ValueError(f"SQLite 백업 무결성 오류: {result}")
        counts = {name: db.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                  for name in ("questions", "attempts", "progress", "explanations")}
    return counts


def export(destination):
    destination = Path(destination).expanduser().resolve()
    if destination.is_relative_to(ROOT) or destination.exists():
        raise ValueError("백업 파일은 프로젝트 바깥의 새 경로에 저장하세요.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        db_snapshot = Path(temp) / "study.sqlite3"
        counts = database_snapshot(db_snapshot)
        entries = list(source_paths()) + [("data/study.sqlite3", db_snapshot)]
        names = [name for name, _ in entries]
        if len(names) != len(set(names)):
            raise ValueError("백업 항목 경로가 중복됩니다.")
        manifest = {"format": 1, "created_at": datetime.now(timezone.utc).isoformat(),
                    "model": app.MODEL, "counts": counts, "files": {}}
        temporary_zip = Path(temp) / "backup.zip"
        with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for name, path in entries:
                data = path.read_bytes()
                archive.writestr(PREFIX + name, data)
                manifest["files"][name] = {"bytes": len(data), "sha256": digest(data)}
            archive.writestr(PREFIX + "backup-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        verify(temporary_zip)
        os.replace(temporary_zip, destination)
        destination.chmod(0o600)
    return manifest


def verify(archive_path):
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("백업 안에 중복 파일이 있습니다.")
        manifest_name = PREFIX + "backup-manifest.json"
        manifest = json.loads(archive.read(manifest_name))
        if manifest.get("format") != 1:
            raise ValueError("지원하지 않는 백업 형식입니다.")
        expected = {PREFIX + name for name in manifest["files"]} | {manifest_name}
        if set(names) != expected:
            raise ValueError("백업 파일 목록이 기록과 다릅니다.")
        for name, info in manifest["files"].items():
            safe = Path(name)
            if safe.is_absolute() or ".." in safe.parts or (name.startswith(".env") and name != ".env.example") or name.startswith(".git/"):
                raise ValueError(f"허용하지 않는 경로: {name}")
            data = archive.read(PREFIX + name)
            if len(data) != info["bytes"] or digest(data) != info["sha256"]:
                raise ValueError(f"손상된 파일: {name}")
        if "data/study.sqlite3" not in manifest["files"] or "portable.py" not in manifest["files"]:
            raise ValueError("필수 파일이 없습니다.")
        return manifest


def main():
    parser = argparse.ArgumentParser(description="학습 기록·Obsidian·PDF를 함께 이전하는 ZIP 백업")
    commands = parser.add_subparsers(dest="command", required=True)
    exporting = commands.add_parser("export", help="이 PC에서 백업 생성")
    exporting.add_argument("output", nargs="?", help="저장 경로 (기본: 프로젝트 상위 폴더)")
    checking = commands.add_parser("verify", help="백업 해시 검증")
    checking.add_argument("archive")
    args = parser.parse_args()
    if args.command == "export":
        output = args.output or str(ROOT.parent / f"aws-clf-c02-practice-backup-{datetime.now():%Y%m%d-%H%M%S}.zip")
        manifest = export(output)
        print(f"백업 완료: {Path(output).expanduser().resolve()}")
    else:
        manifest = verify(args.archive)
        print(f"검증 완료: {args.archive}")
    print(f"문항 {manifest['counts']['questions']}, 풀이 {manifest['counts']['attempts']}, "
          f"AI 해설 {manifest['counts']['explanations']}, 파일 {len(manifest['files'])}개")
    print("API 키는 포함하지 않았습니다. 새 PC에서 .env를 다시 설정하세요.")


if __name__ == "__main__":
    main()
