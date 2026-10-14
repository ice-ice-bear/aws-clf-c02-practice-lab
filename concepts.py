"""Small, source-linked concept map for CLF-C02 study."""

import re

EXAM_GUIDE = "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02.html"

# id, Korean title, exam domain, recognition pattern, distinction, official reference
CONCEPTS = [
    ("shared-responsibility", "공동 책임 모델", "보안 및 규정 준수", r"shared responsibility|shared controls|responsibilit(?:y|ies)|patch(?:ing)? the guest|physical security", "AWS는 클라우드의 기반 시설을, 고객은 선택한 서비스에 따른 데이터·설정을 책임진다.", "https://aws.amazon.com/compliance/shared-responsibility-model/"),
    ("iam", "IAM과 최소 권한", "보안 및 규정 준수", r"\bIAM\b|least privilege|MFA|root user|access key|identity center|permission", "인증은 누구인지 확인하고, 권한 부여는 무엇을 할 수 있는지 결정한다.", "https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html"),
    ("security-services", "보안 서비스 구별", "보안 및 규정 준수", r"GuardDuty|Inspector|Macie|Shield|\bWAF\b|Security Hub|Artifact|\bKMS\b|Secrets Manager|DDoS|encryption|\bsecurity\b", "위협 탐지·취약점 평가·웹 요청 보호·암호화 키 관리의 역할을 구별한다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain2.html"),
    ("cloudtrail-cloudwatch-config", "CloudTrail·CloudWatch·Config", "보안 및 규정 준수", r"CloudTrail|CloudWatch|AWS Config|API call|audit|\blogs?\b", "CloudTrail은 API 활동, CloudWatch는 지표·로그·경보, Config는 리소스 구성 변화를 다룬다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain2.html"),
    ("region-az-edge", "리전·가용 영역·엣지", "클라우드 기술 및 서비스", r"Availability Zone|\bRegion\b|Edge Location|latency|global infrastructure", "리전은 지리적 위치, 가용 영역은 리전 안의 분리된 시설, 엣지는 사용자 가까이 콘텐츠를 전달하는 지점이다.", "https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions-availability-zones.html"),
    ("resilience-scaling", "고가용성·확장·복원력", "클라우드 개념", r"scal(?:e|ing)|elastic|reliab|availability|fault.toler|recover|load balan|single point of failure", "수평 확장은 인스턴스 수를 늘리고, 탄력성은 수요에 맞춰 용량을 조절한다.", "https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html"),
    ("compute", "EC2·Lambda·컨테이너", "클라우드 기술 및 서비스", r"\bEC2\b|Lambda|Fargate|Elastic Beanstalk|Lightsail|ECS|EKS|container|compute", "EC2는 가상 서버, Lambda는 이벤트 기반 코드 실행, 컨테이너 서비스는 컨테이너 실행을 관리한다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html"),
    ("ec2-purchasing", "EC2 구매 옵션", "청구·요금·지원", r"On.Demand (?:Instance|pricing|capacity|EC2)|Reserved Instance|Spot Instance|Savings Plan|Dedicated Host|purchase option|pricing model", "짧고 중단 불가면 온디맨드, 중단 허용 작업은 스팟, 지속 사용 약정은 할인 옵션을 검토한다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain4.html"),
    ("s3-storage", "S3와 스토리지 클래스", "클라우드 기술 및 서비스", r"\bS3\b|Glacier|object storage|archive|storage class|durability", "S3는 객체 스토리지이며 접근 빈도와 복구 요구에 따라 클래스를 고른다.", "https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html"),
    ("ebs-efs", "EBS·EFS·FSx", "클라우드 기술 및 서비스", r"\bEBS\b|\bEFS\b|\bFSx\b|block storage|file storage|snapshot", "EBS는 EC2용 블록 볼륨, EFS는 공유 파일 시스템이다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html"),
    ("databases", "RDS·DynamoDB·데이터베이스", "클라우드 기술 및 서비스", r"\bRDS\b|Aurora|DynamoDB|Redshift|ElastiCache|database|NoSQL|relational", "RDS·Aurora는 관계형, DynamoDB는 NoSQL, ElastiCache는 인메모리 캐시다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html"),
    ("networking", "VPC·Route 53·CloudFront", "클라우드 기술 및 서비스", r"\bVPC\b|Route 53|CloudFront|Direct Connect|VPN|DNS|CDN|subnet|(?<!Partner )network", "VPC는 가상 네트워크, Route 53은 DNS, CloudFront는 CDN이다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html"),
    ("messaging", "SQS·SNS·EventBridge", "클라우드 기술 및 서비스", r"\bSQS\b|\bSNS\b|EventBridge|Step Functions|queue|decoupl|Simple Queue Service|Simple Notification Service", "SQS는 메시지 대기열, SNS는 발행·구독 알림, EventBridge는 이벤트 라우팅이다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html"),
    ("billing", "비용 관리·통합 결제", "청구·요금·지원", r"Budgets|Cost Explorer|Cost and Usage|\bbill(?:ing|s)?\b|consolidated|Pricing Calculator|cost allocation|spend", "Budgets는 임계값 알림, Cost Explorer는 비용 분석, Pricing Calculator는 사전 추정에 쓴다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain4.html"),
    ("support", "AWS Support와 지원 플랜", "청구·요금·지원", r"Support plan|Enterprise Support|Technical Account Manager|Trusted Advisor|Support Center|Concierge|Abuse team", "지원 플랜의 명칭과 제공 범위는 변경될 수 있어 현행 공식 가이드를 확인한다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain4.html"),
    ("migration", "마이그레이션·전송", "클라우드 개념", r"migrat|Snowball|Storage Gateway|DataSync|transfer data|DMS|Application Discovery", "온라인 전송, 물리 장치 전송, 데이터베이스 이전의 목적을 구별한다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain1.html"),
    ("governance-compliance", "거버넌스·규정 준수", "보안 및 규정 준수", r"Organizations|Control Tower|Audit Manager|Artifact|Service Control Policy|\bSCP\b|compliance|governance", "Organizations와 SCP는 계정 단위 가드레일, Artifact는 규정 준수 보고서, Audit Manager는 감사 증거 수집을 다룬다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain2.html"),
    ("ai-analytics", "AI·분석 서비스", "클라우드 기술 및 서비스", r"SageMaker|Bedrock|Rekognition|Textract|Comprehend|Transcribe|Translate|\bLex\b|\bKendra\b|Athena|\bGlue\b|Kinesis|QuickSight|\bAI\b|machine learning|analytics", "AI는 학습·추론 목적을, 분석은 수집·정제·질의·시각화 단계를 구별한다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html"),
    ("well-architected", "Well-Architected 6개 원칙", "클라우드 개념", r"Well.Architected|pillar|operational excellence|sustainability|cost optimization|performance efficiency", "운영 우수성·보안·안정성·성능 효율성·비용 최적화·지속 가능성의 관점을 구별한다.", "https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html"),
    ("cloud-benefits", "클라우드 가치와 경제성", "클라우드 개념", r"cloud benefit|economies of scale|capital expense|variable cost|agility|right.siz|pay.as.you.go", "고정 투자 대신 사용량에 따른 지출과 빠른 자원 확보의 이점을 이해한다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain1.html"),
    ("general-services", "AWS 서비스 선택", "클라우드 기술 및 서비스", r"(?!)", "요구 사항의 핵심 단어를 찾고 각 서비스가 해결하는 문제를 공식 시험 범위와 대조한다.", "https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/clf-02-in-scope-services.html"),
]

BY_ID = {item[0]: item for item in CONCEPTS}


def classify(stem: str, options: dict, correct=None) -> str:
    order = ["ec2-purchasing", "cloudtrail-cloudwatch-config", "shared-responsibility", "support", "billing", "region-az-edge", "ebs-efs", "s3-storage", "databases", "networking", "messaging", "migration", "governance-compliance", "ai-analytics", "well-architected", "iam", "security-services", "resilience-scaling", "compute", "cloud-benefits"]
    specific = [key for key in order if key not in ("compute", "cloud-benefits")]
    answer_text = " ".join(options.get(letter, "") for letter in (correct or []))
    for text, keys in ((stem, specific), (answer_text, specific), (stem, order), (answer_text, order)):
        for concept_id in keys:
            if text and re.search(BY_ID[concept_id][3], text, re.I):
                return concept_id
    return "general-services"


def as_dict(item):
    key, title, domain, _, summary, url = item
    return {"id": key, "title": title, "domain": domain, "summary": summary, "url": url}
