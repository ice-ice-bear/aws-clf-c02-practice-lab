---
tags: [aws-ccp, clf-c02]
domain: '보안 및 규정 준수'
---

# CloudTrail·CloudWatch·Config

## 한 줄 구별법

CloudTrail은 API 활동, CloudWatch는 지표·로그·경보, Config는 리소스 구성 변화를 다룬다.

## 이해와 비교

- CloudTrail은 계정의 API 활동 기록을 조사할 때 먼저 본다. 누가 언제 어떤 API 작업을 요청했는지가 핵심이다.
- CloudWatch는 메트릭, 로그, 경보를 이용해 성능과 운영 상태를 관찰한다. CPU 사용률 경보나 로그 패턴 감지는 이 범주다.
- AWS Config는 리소스 설정의 변경 이력과 규칙 준수 상태를 추적한다. '설정이 어떻게 바뀌었나'는 Config, '누가 API를 호출했나'는 CloudTrail이다.

## 자주 틀리는 지점

CloudTrail 자체를 모든 애플리케이션 성능 메트릭의 저장소로 보지 않는다.

## 스스로 확인

보안 그룹 규칙 변경 이력과 이를 변경한 API 주체를 각각 어디서 확인하는가?

## 근거와 더 읽기

- [[Taulli-2026-CLF-C02.pdf#page=71|Taulli, 2026 학습서, PDF 71쪽부터 (관련 장: 5, 7)]]
- [AWS 공식 문서](https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain2.html)

책의 설명은 학습 보조 자료입니다. 변동 가능한 서비스·요금·지원 플랜은 위 공식 문서에서 다시 확인하세요.

## 내 오답
