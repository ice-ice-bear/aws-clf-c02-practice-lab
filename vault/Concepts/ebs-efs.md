---
tags: [aws-ccp, clf-c02]
domain: '클라우드 기술 및 서비스'
---

# EBS·EFS·FSx

## 한 줄 구별법

EBS는 EC2용 블록 볼륨, EFS는 공유 파일 시스템이다.

## 이해와 비교

- EBS는 EC2에 연결하는 블록 볼륨이다. 운영체제 디스크나 블록 장치가 필요한 DB에 어울리며 스냅샷으로 백업한다.
- EFS는 여러 Linux 인스턴스가 공유할 수 있는 관리형 파일 시스템이다. FSx 계열은 Windows 파일 시스템이나 특정 고성능 파일 시스템 요구에 맞춘다.
- S3는 객체, EBS는 블록, EFS·FSx는 파일이라는 접근 단위부터 식별한다. 인스턴스 스토어는 인스턴스 수명과 연결된 임시 저장소다.

## 자주 틀리는 지점

EBS 볼륨을 일반적인 다중 AZ 공유 파일 시스템으로 기억하지 않는다.

## 스스로 확인

여러 EC2가 같은 파일 경로를 읽어야 한다면 어떤 서비스를 먼저 검토하는가?

## 근거와 더 읽기

- [[Taulli-2026-CLF-C02.pdf#page=194|Taulli, 2026 학습서, PDF 194쪽부터 (관련 장: 10)]]
- [AWS 공식 문서](https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html)

책의 설명은 학습 보조 자료입니다. 변동 가능한 서비스·요금·지원 플랜은 위 공식 문서에서 다시 확인하세요.

## 내 오답
