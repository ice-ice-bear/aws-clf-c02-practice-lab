"""Import the MIT-licensed practice exams into a stable JSON seed file."""

import json
import re
import sys
from pathlib import Path


QUESTION = re.compile(r"(?m)^(\d+)\.\s+(.+?)(?=^\d+\.\s+|\Z)", re.S)
OPTION = re.compile(r"(?m)^\s*-\s+([A-F])\.\s+(.+)$")
ANSWER = re.compile(r"(?im)^[ \t]*Correct answer:[ \t]*([A-F][A-F, \t]*)$")


def parse_exam(path: Path, exam: int):
    body = path.read_text(encoding="utf-8").split("---", 2)[-1]
    result = []
    for ordinal, match in enumerate(QUESTION.finditer(body), 1):
        _, block = match.groups()
        options = {letter: text.strip() for letter, text in OPTION.findall(block)}
        answer = ANSWER.search(block)
        stem = block.split("\n", 1)[0].strip()
        if not options or not answer:
            raise ValueError(f"Cannot parse exam {exam} question {ordinal}")
        correct = sorted(re.findall(r"[A-F]", answer.group(1).upper()))
        if not set(correct).issubset(options):
            raise ValueError(f"Invalid answer in exam {exam} question {ordinal}")
        result.append({
            "id": f"E{exam:02d}-Q{ordinal:02d}",
            "exam": exam,
            "number": ordinal,
            "stem": stem,
            "options": options,
            "correct": correct,
            "source_url": f"https://github.com/kananinirav/AWS-Certified-Cloud-Practitioner-Notes/blob/master/practice-exam/practice-exam-{exam}.md",
        })
    return result


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/aws-ccp-source")
    questions = []
    for exam in range(1, 24):
        questions += parse_exam(root / "practice-exam" / f"practice-exam-{exam}.md", exam)
    output = Path(__file__).parent / "data" / "questions.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(questions)} questions from 23 exams to {output}")


if __name__ == "__main__":
    main()
