---
tags: [aws-ccp, clf-c02]
domain: '보안 및 규정 준수'
---

# 거버넌스·규정 준수

## 한 줄 구별법

Organizations와 SCP는 계정 단위 가드레일, Artifact는 규정 준수 보고서, Audit Manager는 감사 증거 수집을 다룬다.

## 이해와 비교

- AWS Organizations는 계정을 묶어 관리하고 통합 결제·정책 적용을 돕는다. 서비스 제어 정책(SCP)은 계정에 허용 가능한 권한의 상한을 정하지만 자체적으로 권한을 부여하지 않는다.
- AWS Artifact는 AWS 규정 준수 보고서와 계약 자료를 확인하는 곳이다. Audit Manager는 감사에 필요한 증거 수집과 평가를 돕는다.
- AWS Config는 설정 규칙 준수를 평가한다. 규정 준수는 인증서 보유만으로 끝나지 않으며 고객의 구성과 데이터 처리도 포함된다.

## 자주 틀리는 지점

SCP를 IAM 권한을 주는 정책으로 착각하지 않는다. AWS의 인증 보고서와 내 워크로드의 준수 상태도 구분한다.

## 스스로 확인

감사인이 AWS의 보고서를 요구할 때와 계정의 권한 상한을 정할 때 각각 무엇을 쓰는가?

## 근거와 더 읽기

- [[Taulli-2026-CLF-C02.pdf#page=71|Taulli, 2026 학습서, PDF 71쪽부터 (관련 장: 5)]]
- [AWS 공식 문서](https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain2.html)

책의 설명은 학습 보조 자료입니다. 변동 가능한 서비스·요금·지원 플랜은 위 공식 문서에서 다시 확인하세요.

## 내 오답
