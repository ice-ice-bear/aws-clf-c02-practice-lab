"""Write AI assisted misconception notes into the local Obsidian vault."""

import json
from pathlib import Path

from concepts import BY_ID, CONCEPTS, as_dict
from knowledge import BOOK, CHAPTERS, chapter_refs

VERIFIED_QUESTION_NOTES = {
    "E11-Q34": (
        "Amazon Glacier는 S3 Glacier 스토리지 클래스와 구분되는 기존 볼트 기반 서비스입니다. "
        "AWS는 새 장기 보관 용도로 S3 Glacier 스토리지 클래스를 권장합니다. 문제은행의 명칭과 현재 서비스 선택을 구분하세요.",
        [("Amazon Glacier 서비스와 S3 Glacier 클래스 구분", "https://docs.aws.amazon.com/amazonglacier/latest/dev/introduction.html"),
         ("S3 스토리지 클래스", "https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html")],
    ),
    "E12-Q38": (
        "문제은행의 정답 중 AWS OpsWorks는 AWS 공식 종료 서비스 목록에 있습니다. "
        "온프레미스 인스턴스 배포는 현재 CodeDeploy 문서에서 확인할 수 있습니다. 이 문항의 과거 정답을 현행 서비스 선택으로 암기하지 마세요.",
        [("AWS 종료 서비스 목록", "https://docs.aws.amazon.com/general/latest/gr/full_shutdown_services.html"),
         ("CodeDeploy 온프레미스 인스턴스", "https://docs.aws.amazon.com/codedeploy/latest/userguide/instances-on-premises.html")],
    ),
    "E14-Q32": (
        "문제의 Personal Health Dashboard는 현재 AWS Health Dashboard의 계정별 이벤트 보기와 비교해 학습하세요. "
        "공개 서비스 상태와 내 계정에 영향을 주는 이벤트가 구별 단서입니다.",
        [("AWS Health 계정별 이벤트", "https://docs.aws.amazon.com/health/latest/ug/aws-health-account-views.html"),
         ("공개 이벤트와 계정별 이벤트", "https://docs.aws.amazon.com/health/latest/ug/about-public-events.html")],
    ),
    "E21-Q15": (
        "Storage Gateway는 온프레미스 애플리케이션이 AWS 클라우드 스토리지를 사용할 수 있게 연결합니다. "
        "Direct Connect는 전용 네트워크 연결을 제공하므로 문제의 스토리지 기능과 구별합니다.",
        [("Storage Gateway의 하이브리드 스토리지", "https://aws.amazon.com/storagegateway/"),
         ("Direct Connect의 전용 네트워크 연결", "https://docs.aws.amazon.com/directconnect/latest/UserGuide/Welcome.html")],
    ),
}


def wiki_link(path, vault, label):
    relative = path.relative_to(vault).with_suffix("").as_posix()
    return f"[[{relative}|{label}]]"


def create_index(path, title, intro):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# {title}\n\n{intro}\n\n", encoding="utf-8")


def append_once(path, link):
    current = path.read_text(encoding="utf-8")
    if link not in current:
        with path.open("a", encoding="utf-8") as out:
            out.write(f"- {link}\n")


def save_study_qa(vault, concept, selected_text, question, answer, model, created_at,
                  source_kind="concept", source_question=None):
    """Keep each saved follow-up beside its concept and index it for review."""
    if source_kind not in ("concept", "source", "ai"):
        raise ValueError("Invalid question source")
    folder = vault / "Questions" / concept["id"]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{created_at:%Y%m%d-%H%M%S-%f}.md"
    chapters, _, _ = chapter_refs(concept["id"])
    metadata = {
        "tags": ["aws-ccp", "clf-c02", "study-question"],
        "concept_id": concept["id"], "domain": concept["domain"],
        "chapters": chapters, "source": source_kind,
        "model": model, "created_at": created_at.isoformat(),
    }
    if source_question is not None:
        metadata["question_id"] = source_question["id"]
    frontmatter = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items())
    heading = f"{source_question['id']} · 해설 추가 질문" if source_question is not None else f"{concept['title']} · 개념 질문"
    problem = f"## 문제\n\n{source_question['stem']}\n\n" if source_question is not None else ""
    quote = selected_text.replace("\n", "\n> ")
    path.write_text(
        f"---\n{frontmatter}\n---\n\n# {heading}\n\n{problem}"
        f"## 선택한 내용\n\n> {quote}\n\n"
        f"## 내 질문\n\n{question}\n\n## AI 답변\n\n{answer}\n\n"
        f"## 다시 구별하기\n\n- 내 말로 한 줄: \n- 다음에 볼 단서: \n\n"
        f"## 연결\n\n- [[Concepts/{concept['id']}|{concept['title']}]]\n",
        encoding="utf-8",
    )
    index = vault / "Questions" / "00-질문-목록.md"
    create_index(index, "학습 질문 목록", "개념과 문제 해설을 읽으며 AI에게 물어보고 저장한 질문입니다.")
    label = question.replace("|", " ").replace("[", "").replace("]", "")[:50]
    append_once(index, wiki_link(path, vault, f"{concept['title']} · {label}"))
    return path


def chapter_index(vault, number):
    title = CHAPTERS[number][0]
    return vault / "Review" / "Chapters" / f"{number:02d}장 {title}.md"


def verified_block(question_id):
    verified = VERIFIED_QUESTION_NOTES.get(question_id)
    if not verified:
        return ""
    summary, sources = verified
    links = "\n".join(f"- [{label}]({url})" for label, url in sources)
    return f"## 공식 자료 대조\n\n{summary}\n\n{links}\n\n"


def verified_sources(question_id):
    verified = VERIFIED_QUESTION_NOTES.get(question_id)
    return [{"label": label, "url": url} for label, url in verified[1]] if verified else []


def init_review_map(vault):
    root = vault / "Review"
    map_path = root / "00-오답-지도.md"
    if not map_path.exists():
        domains = list(dict.fromkeys(as_dict(item)["domain"] for item in CONCEPTS))
        category_links = "\n".join(
            f"- {wiki_link(root / domain / '00-카테고리.md', vault, domain)}" for domain in domains)
        chapter_links = "\n".join(
            f"- {wiki_link(chapter_index(vault, number), vault, f'{number}장 {title}')}"
            for number, (title, _) in CHAPTERS.items())
        root.mkdir(parents=True, exist_ok=True)
        map_path.write_text(
            "# 오답 복습 지도\n\nAI 해설을 요청한 오답과 오래 걸린 정답을 모읍니다. "
            "해설은 학습 보조 자료이므로 AWS 공식 문서와 비교해 확인하세요.\n\n"
            f"## 카테고리\n\n{category_links}\n\n## 학습서 장\n\n{chapter_links}\n",
            encoding="utf-8",
        )
    for item in CONCEPTS:
        domain = as_dict(item)["domain"]
        create_index(root / domain / "00-카테고리.md", domain,
                     "이 카테고리에 저장된 문제별 오답 해설입니다.")
    for number, (title, _) in CHAPTERS.items():
        create_index(chapter_index(vault, number), f"{number}장 · {title}",
                     "해당 장과 연결된 문제별 오답 해설입니다. 장 연결은 학습서 목차를 기준으로 합니다.")
    return map_path


def save_ai_review(vault, question, attempt, body, model):
    """Create one editable note per attempt and link it from category/chapter maps."""
    concept = as_dict(BY_ID[question["concept_id"]])
    chapters, primary, page = chapter_refs(concept["id"])
    # The catch-all concept lists several chapters; only its page-matched chapter
    # is justified for a particular question.
    if concept["id"] == "general-services":
        chapters = [primary]
    category = concept["domain"]
    title = CHAPTERS[primary][0]
    folder = vault / "Review" / category / f"{primary:02d}장 {title}"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{question['id']}-시도-{attempt['id']:04d}.md"
    if not path.exists():
        options = json.loads(question["options"])
        selected = set(json.loads(attempt["selected"]))
        correct = set(json.loads(question["correct"]))
        choices = "\n".join(
            f"| {letter} | {'✓' if letter in selected else ''} | {'✓' if letter in correct else ''} | {text.replace('|', '｜')} |"
            for letter, text in options.items())
        chapter_links = "\n".join(
            f"- {wiki_link(chapter_index(vault, number), vault, f'{number}장 {CHAPTERS[number][0]}')}"
            for number in chapters)
        metadata = {
            "tags": ["aws-ccp", "clf-c02", "ai-review"],
            "category": category, "chapters": chapters,
            "concept_id": concept["id"], "question_id": question["id"],
            "attempt_id": attempt["id"], "model": model,
        }
        frontmatter = "\n".join(
            f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items())
        caution = "\n> 이 문제는 오래된 서비스 명칭 또는 정답 재검토가 필요할 수 있습니다.\n" if question["needs_review"] else ""
        content = (
            f"---\n{frontmatter}\n---\n\n"
            f"# {question['id']} · {concept['title']}\n\n"
            f"> 모델 {model}이 생성한 학습용 해설입니다. 공식 문서를 직접 읽고 검증한 답변은 아닙니다.{caution}\n"
            f"## 문제와 내 선택\n\n{question['stem']}\n\n"
            f"| 보기 | 내 선택 | 문제은행 정답 | 내용 |\n|---|:---:|:---:|---|\n{choices}\n\n"
            f"풀이 시각: {attempt['created_at']} · "
            f"결과: {'정답이지만 복습 필요' if attempt['correct'] else '오답'}\n\n"
            f"{verified_block(question['id'])}"
            f"## AI 비교 해설\n\n{body.strip()}\n\n"
            "## 내 말로 다시 정리\n\n- 헷갈린 두 개념: \n- 다음에 볼 단서: \n\n"
            f"## 연결된 개념과 근거\n\n"
            f"- {wiki_link(vault / 'Concepts' / (concept['id'] + '.md'), vault, concept['title'])}\n"
            f"{chapter_links}\n"
            f"- [[References/{BOOK}#page={page}|학습서 PDF {page}쪽부터]]\n"
            "\n".join(f"- [{source['label']}]({source['url']})" for source in verified_sources(question['id'])) + "\n"
        )
        try:
            with path.open("x", encoding="utf-8") as out:
                out.write(content)
        except FileExistsError:
            pass
    research = verified_block(question["id"])
    if research:
        existing = path.read_text(encoding="utf-8")
        if "## 공식 자료 대조\n" not in existing:
            path.write_text(existing.replace("## AI 비교 해설\n", research + "## AI 비교 해설\n", 1), encoding="utf-8")
    init_review_map(vault)
    link = wiki_link(path, vault, f"{question['id']} · {concept['title']}")
    category_index = vault / "Review" / category / "00-카테고리.md"
    append_once(category_index, f"{link} · {primary}장")
    for number in chapters:
        append_once(chapter_index(vault, number), link)
    return path
