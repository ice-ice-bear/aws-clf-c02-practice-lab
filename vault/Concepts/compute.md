---
tags: [aws-ccp, clf-c02]
domain: '클라우드 기술 및 서비스'
---

# EC2·Lambda·컨테이너

## 한 줄 구별법

EC2는 가상 서버, Lambda는 이벤트 기반 코드 실행, 컨테이너 서비스는 컨테이너 실행을 관리한다.

## 이해와 비교

- EC2는 운영체제와 인스턴스 구성을 직접 제어하는 가상 서버다. Lambda는 이벤트에 반응해 코드를 실행하며 서버 운영 부담을 줄인다.
- ECS는 AWS의 컨테이너 오케스트레이션, EKS는 Kubernetes 기반 운영이다. Fargate는 ECS 또는 EKS에서 서버를 직접 관리하지 않고 컨테이너를 실행하는 방식이다.
- Elastic Beanstalk는 애플리케이션 배포 환경을 관리하고, Lightsail은 단순한 웹 워크로드를 쉽게 시작하는 선택지다. 운영 제어 수준과 실행 단위로 구별한다.

## 자주 틀리는 지점

서버리스도 서버 위에서 실행된다. 사용자가 서버를 직접 준비·관리하지 않는다는 뜻이다.

## 스스로 확인

이벤트로 짧은 코드를 실행할 때와 OS를 직접 관리해야 할 때의 선택지는?

## 근거와 더 읽기

- [[Taulli-2026-CLF-C02.pdf#page=176|Taulli, 2026 학습서, PDF 176쪽부터 (관련 장: 9)]]
- [AWS 공식 문서](https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html)

책의 설명은 학습 보조 자료입니다. 변동 가능한 서비스·요금·지원 플랜은 위 공식 문서에서 다시 확인하세요.

## 내 오답
