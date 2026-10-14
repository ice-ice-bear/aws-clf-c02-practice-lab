"""Completed-set feedback from the answers attached to that set."""

import json

from concepts import BY_ID, as_dict


REVIEW_FOCUS = {
    "shared-responsibility": "EC2와 RDS·Lambda에서 AWS와 고객의 패치·데이터·접근 권한 책임을 각각 써 보세요.",
    "iam": "사용자·역할·정책을 구별하고 임시 자격 증명, 최소 권한, 명시적 Deny의 적용 사례를 설명하세요.",
    "security-services": "GuardDuty·Inspector·Macie·WAF·Shield·KMS를 탐지 대상과 보호 대상으로 나눠 비교하세요.",
    "cloudtrail-cloudwatch-config": "API 활동, 지표·로그·경보, 구성 변경이라는 요구를 CloudTrail·CloudWatch·Config에 연결하세요.",
    "region-az-edge": "리전·AZ·엣지의 역할을 그려 보고 데이터 위치, 장애 격리, 지연 시간 요구에 맞춰 선택하세요.",
    "resilience-scaling": "Multi-AZ·Auto Scaling·로드 밸런싱·백업이 각각 해결하는 문제와 RTO·RPO를 구별하세요.",
    "compute": "EC2·Lambda·ECS·EKS·Fargate를 실행 방식과 고객이 관리할 서버 범위로 비교하세요.",
    "ec2-purchasing": "중단 가능 여부, 사용량의 예측 가능성, 약정 조건으로 On-Demand·Spot·RI·Savings Plans를 선택하세요.",
    "s3-storage": "접근 빈도, 복원 대기, AZ 보호, 최소 보관 과금 기간으로 S3 클래스 선택표를 다시 작성하세요.",
    "ebs-efs": "블록·공유 파일·객체의 차이부터 EBS·EFS·FSx의 연결 범위와 사용 사례를 비교하세요.",
    "databases": "관계형·키-값·캐시 요구를 구별하고 RDS Multi-AZ와 읽기 복제본의 목적을 대조하세요.",
    "networking": "VPC의 네트워크 격리, Route 53의 DNS, CloudFront의 콘텐츠 전달을 요청 흐름에 배치하세요.",
    "messaging": "SQS 큐, SNS 팬아웃, EventBridge 이벤트 라우팅을 생산자·소비자 연결 방식으로 그려 보세요.",
    "billing": "비용 분석, 예산 알림·조치, 사전 견적에 Cost Explorer·Budgets·Pricing Calculator를 연결하세요.",
    "support": "지원 플랜의 기술 지원·응답 목표와 TAM의 역할을 비교하고 현재 제공 조건을 공식 자료로 확인하세요.",
    "migration": "서버·데이터베이스·파일·오프라인 전송에 맞는 도구를 골라 스키마 변환과 데이터 전송을 구별하세요.",
    "governance-compliance": "Organizations·SCP·Control Tower의 통제와 Artifact·Audit Manager의 감사 역할을 대조하세요.",
    "ai-analytics": "이미지·텍스트·음성 AI와 수집·ETL·질의·시각화 요구를 나눠 서비스 선택 근거를 써 보세요.",
    "well-architected": "6개 원칙에 대표 요구를 하나씩 연결하고 안정성·성능 효율성·운영 우수성의 차이를 설명하세요.",
    "cloud-benefits": "고정 투자와 변동 비용, 규모의 경제, 탄력성, 민첩성을 실제 도입 사례로 설명하세요.",
    "general-services": "문제의 목적을 한 문장으로 바꾸고 전문 인력 지원·제품 구매·승인된 제품 배포를 구별하세요.",
}


def build_session_report(items, domain_weights, slow_threshold):
    concepts = {}
    domains = {}
    fields = ("total", "answered", "correct", "wrong", "skipped", "timed_answers",
              "total_seconds", "slow_correct", "flagged_correct", "review_count")
    overall = dict.fromkeys(fields, 0)
    for domain, weight in domain_weights.items():
        domains[domain] = {**dict.fromkeys(fields, 0), "domain": domain, "weight": weight}
    review_questions = []
    for item in items:
        concept_id = item["concept_id"]
        concept = as_dict(BY_ID[concept_id])
        group = concepts.setdefault(concept_id, {**dict.fromkeys(fields, 0), **concept,
                                   "focus": REVIEW_FOCUS[concept_id], "question_ids": []})
        answered = item["attempt_id"] is not None
        correct = answered and item["correct"] == 1
        seconds = item["duration_seconds"] if answered else None
        slow = seconds is not None and seconds >= slow_threshold
        flagged = correct and item["confidence"] != "sure"
        review = not correct or slow or flagged
        for target in (overall, group, domains[concept["domain"]]):
            target["total"] += 1
            target["answered"] += int(answered)
            target["correct"] += int(correct)
            target["wrong"] += int(answered and not correct)
            target["skipped"] += int(not answered)
            target["timed_answers"] += int(seconds is not None)
            target["total_seconds"] += seconds or 0
            target["slow_correct"] += int(correct and slow)
            target["flagged_correct"] += int(flagged)
            target["review_count"] += int(review)
        if review:
            group["question_ids"].append(item["question_id"])
            review_questions.append({"id": item["question_id"], "exam": item["exam"],
                "number": item["number"], "stem": item["stem"], "concept_id": concept_id,
                "status": "correct" if correct else "wrong" if answered else "skipped",
                "selected": json.loads(item["selected"]) if answered else [],
                "correct_answers": json.loads(item["correct_answers"]),
                "duration_seconds": seconds, "slow": slow, "flagged": bool(flagged),
                "needs_review": bool(item["needs_review"])})
    for target in (overall, *concepts.values(), *domains.values()):
        target["score_percent"] = round(100 * target["correct"] / target["total"], 1) if target["total"] else None
        target["wrong_percent"] = round(100 * target["wrong"] / target["answered"], 1) if target["answered"] else None
        target["average_seconds"] = round(target["total_seconds"] / target["timed_answers"], 1) if target["timed_answers"] else None
        target["total_seconds"] = round(target["total_seconds"], 1)
    priorities = sorted(concepts.values(), key=lambda c: (
        c["wrong"] + c["skipped"], c["wrong_percent"] or 0, c["review_count"]), reverse=True)
    return {**overall, "slow_threshold_seconds": slow_threshold,
            "domains": list(domains.values()), "concepts": priorities,
            "review_questions": review_questions}
