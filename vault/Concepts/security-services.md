---
tags: [aws-ccp, clf-c02]
domain: '보안 및 규정 준수'
---

# 보안 서비스 구별

## 한 줄 구별법

위협 탐지·취약점 평가·웹 요청 보호·암호화 키 관리의 역할을 구별한다.

## 이해와 비교

- GuardDuty는 위협 신호를 탐지하고, Inspector는 워크로드의 취약점과 노출을 평가한다. Macie는 S3의 민감 데이터를 발견한다.
- WAF는 웹 요청을 규칙으로 필터링하고 Shield는 DDoS 방어를 다룬다. KMS는 암호화 키 관리, Secrets Manager는 비밀 값 저장과 교체에 쓰인다.
- Security Hub는 여러 보안 결과를 한곳에서 모아 우선순위를 파악하게 한다. 서비스 이름보다 문제의 동사(탐지·평가·차단·암호화)를 먼저 본다.

## 자주 틀리는 지점

WAF를 네트워크 전체의 범용 방화벽이나 취약점 스캐너로 기억하지 않는다.

## 스스로 확인

S3 버킷에서 개인정보를 찾는 서비스와 EC2 취약점을 평가하는 서비스는?

## 근거와 더 읽기

- [[Taulli-2026-CLF-C02.pdf#page=114|Taulli, 2026 학습서, PDF 114쪽부터 (관련 장: 5, 7)]]
- [AWS 공식 문서](https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain2.html)

책의 설명은 학습 보조 자료입니다. 변동 가능한 서비스·요금·지원 플랜은 위 공식 문서에서 다시 확인하세요.

## 내 오답
