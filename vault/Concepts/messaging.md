---
tags: [aws-ccp, clf-c02]
domain: '클라우드 기술 및 서비스'
---

# SQS·SNS·EventBridge

## 한 줄 구별법

SQS는 메시지 대기열, SNS는 발행·구독 알림, EventBridge는 이벤트 라우팅이다.

## 이해와 비교

- SQS는 소비자가 나중에 처리할 메시지를 큐에 보관해 시스템을 느슨하게 결합한다. 처리율을 맞추거나 일시 장애를 흡수할 때 유용하다.
- SNS는 하나의 발행을 여러 구독자에게 전달하는 발행·구독 방식이다. EventBridge는 이벤트 패턴 규칙으로 대상을 선택해 라우팅한다.
- Step Functions는 여러 단계의 작업 흐름을 조정한다. SQS의 메시지 저장, SNS의 팬아웃, EventBridge의 이벤트 규칙을 질문 문구로 구별한다.

## 자주 틀리는 지점

SNS가 SQS처럼 소비자가 꺼내 갈 때까지 메시지를 보관하는 큐라고 생각하지 않는다.

## 스스로 확인

주문 이벤트를 여러 구독 시스템에 즉시 알릴 때와 작업을 나중에 처리할 때의 선택지는?

## 근거와 더 읽기

- [[Taulli-2026-CLF-C02.pdf#page=254|Taulli, 2026 학습서, PDF 254쪽부터 (관련 장: 14)]]
- [AWS 공식 문서](https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html)

책의 설명은 학습 보조 자료입니다. 변동 가능한 서비스·요금·지원 플랜은 위 공식 문서에서 다시 확인하세요.

## 내 오답
