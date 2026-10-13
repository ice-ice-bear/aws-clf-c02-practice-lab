---
tags: [aws-ccp, clf-c02]
domain: '클라우드 기술 및 서비스'
---

# AI·분석 서비스

## 한 줄 구별법

AI는 학습·추론 목적을, 분석은 수집·정제·질의·시각화 단계를 구별한다.

## 이해와 비교

- SageMaker는 ML 모델을 개발·학습·배포하는 플랫폼이다. Bedrock은 파운데이션 모델을 활용한 생성형 AI 애플리케이션 구축에 쓴다.
- Rekognition은 이미지·비디오 분석, Textract는 문서의 문자와 구조 추출, Comprehend는 텍스트의 의미 분석을 다룬다. Lex는 대화형 인터페이스를 만든다.
- Athena는 S3 데이터에 SQL로 질의하고, Glue는 데이터 통합·ETL, Kinesis는 스트리밍 데이터 처리에 쓰인다. 서비스 이름보다 입력 데이터와 원하는 결과를 먼저 본다.

## 자주 틀리는 지점

문서에서 글자를 읽는 일과 글의 의미를 분석하는 일을 같은 AI 서비스로 답하지 않는다.

## 스스로 확인

스캔 문서의 표 추출, S3 로그 SQL 질의, 생성형 AI 앱 구축의 후보는?

## 근거와 더 읽기

- [[Taulli-2026-CLF-C02.pdf#page=241|Taulli, 2026 학습서, PDF 241쪽부터 (관련 장: 13)]]
- [AWS 공식 문서](https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html)

책의 설명은 학습 보조 자료입니다. 변동 가능한 서비스·요금·지원 플랜은 위 공식 문서에서 다시 확인하세요.

## 내 오답
