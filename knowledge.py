"""Original Korean study notes, cross-referenced to a local book and AWS docs."""

from concepts import as_dict
from study_supplements import SUPPLEMENTS

BOOK = "Taulli-2026-CLF-C02.pdf"

CHAPTERS = {
    2: ("시작 및 기본 서비스", 26), 3: ("클라우드 기초", 39),
    4: ("비용·설계 프레임워크", 51), 5: ("규정 준수·거버넌스", 71),
    6: ("IAM", 88), 7: ("보안", 114), 8: ("글로벌 인프라", 152),
    9: ("컴퓨팅", 176), 10: ("스토리지", 194), 11: ("데이터베이스", 213),
    12: ("네트워킹", 227), 13: ("AI·분석", 241),
    14: ("개발·메시징 서비스", 254), 15: ("청구·예산", 271),
}

# PDF page numbers refer to the file page count (the cover is page 1).
# These notes are original summaries; the book itself is local and gitignored.
DETAILS = {
    'cloud-benefits': ('3, 4', 39),
    'shared-responsibility': ('5, 7', 71),
    'iam': ('6', 88),
    'security-services': ('5, 7', 114),
    'cloudtrail-cloudwatch-config': ('5, 7', 71),
    'region-az-edge': ('8', 152),
    'resilience-scaling': ('8, 9', 176),
    'compute': ('9', 176),
    'ec2-purchasing': ('9, 15', 271),
    's3-storage': ('10', 194),
    'ebs-efs': ('10', 194),
    'databases': ('11', 213),
    'networking': ('8, 12', 227),
    'messaging': ('14', 254),
    'billing': ('4, 15', 271),
    'support': ('2, 15', 271),
    'migration': ('4, 10', 194),
    'well-architected': ('4', 51),
    'governance-compliance': ('5', 71),
    'ai-analytics': ('13', 241),
    'general-services': ('2, 13, 14', 254),
}


def chapter_refs(concept_id):
    chapters, page = DETAILS[concept_id]
    numbers = [int(number.strip()) for number in chapters.split(",")]
    primary = max(numbers, key=lambda number: CHAPTERS[number][1] if CHAPTERS[number][1] <= page else -1)
    return numbers, primary, page


def render_note(item):
    concept = as_dict(item)
    content, references = SUPPLEMENTS[concept["id"]].split("## 근거와 더 읽기\n\n", 1)
    if "](https://" not in references:
        references += f"- [AWS 공식 문서]({concept['url']})\n"
    return (
        f"---\ntags: [aws-ccp, clf-c02]\ndomain: '{concept['domain']}'\n---\n\n"
        f"# {concept['title']}\n\n{content}"
        f"## 근거와 더 읽기\n\n"
        f"{references}\n"
        "책의 설명은 학습 보조 자료입니다. 변동 가능한 서비스·요금·지원 플랜은 위 공식 문서에서 다시 확인하세요.\n\n"
        "## 내 오답\n"
    )
