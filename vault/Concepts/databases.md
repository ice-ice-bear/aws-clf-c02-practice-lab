---
tags: [aws-ccp, clf-c02]
domain: '클라우드 기술 및 서비스'
---

# RDS·DynamoDB·데이터베이스

## 한 줄 구별법

RDS·Aurora는 관계형, DynamoDB는 NoSQL, ElastiCache는 인메모리 캐시다.

## 이해와 비교

- RDS는 관리형 관계형 데이터베이스이고 Aurora는 AWS의 관계형 엔진이다. 표와 SQL, 트랜잭션 요구가 있으면 관계형을 먼저 떠올린다.
- DynamoDB는 서버리스 NoSQL 키 값·문서 DB다. Redshift는 대규모 분석용 데이터 웨어하우스, ElastiCache는 빠른 조회를 돕는 인메모리 캐시다.
- Multi-AZ는 고가용성, 읽기 복제본은 읽기 트래픽 확장에 초점이 있다. DB를 EC2에 직접 설치하면 OS·DB 운영 책임이 커진다.

## 자주 틀리는 지점

캐시를 영구 저장소의 유일한 원본으로 취급하지 않는다. Multi-AZ와 읽기 복제본의 목적도 구별한다.

## 스스로 확인

관계형 주문 데이터와 초저지연 키 값 조회의 후보는 각각 무엇인가?

## 근거와 더 읽기

- [[Taulli-2026-CLF-C02.pdf#page=213|Taulli, 2026 학습서, PDF 213쪽부터 (관련 장: 11)]]
- [AWS 공식 문서](https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html)

책의 설명은 학습 보조 자료입니다. 변동 가능한 서비스·요금·지원 플랜은 위 공식 문서에서 다시 확인하세요.

## 내 오답
