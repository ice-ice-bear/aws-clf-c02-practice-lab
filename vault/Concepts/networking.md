---
tags: [aws-ccp, clf-c02]
domain: '클라우드 기술 및 서비스'
---

# VPC·Route 53·CloudFront

## 한 줄 구별법

VPC는 가상 네트워크, Route 53은 DNS, CloudFront는 CDN이다.

## 이해와 비교

- VPC는 AWS에서 논리적으로 분리한 네트워크다. 서브넷은 VPC 주소 공간의 일부이며 하나의 AZ에 속한다.
- 보안 그룹은 인스턴스 등 리소스 수준의 상태 저장 규칙, 네트워크 ACL은 서브넷 수준의 상태 비저장 규칙이다. 인터넷 게이트웨이와 라우팅은 외부 통신 경로를 정한다.
- Route 53은 DNS와 라우팅 정책, CloudFront는 CDN, Direct Connect는 전용 연결, Site-to-Site VPN은 암호화된 네트워크 연결에 쓰인다.

## 자주 틀리는 지점

DNS 이름을 해석하는 Route 53과 콘텐츠를 캐시하는 CloudFront를 혼동하지 않는다.

## 스스로 확인

프라이빗 서브넷 인스턴스의 아웃바운드 인터넷 접근에는 어떤 경로가 필요한가?

## 근거와 더 읽기

- [[Taulli-2026-CLF-C02.pdf#page=227|Taulli, 2026 학습서, PDF 227쪽부터 (관련 장: 8, 12)]]
- [AWS 공식 문서](https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html)

책의 설명은 학습 보조 자료입니다. 변동 가능한 서비스·요금·지원 플랜은 위 공식 문서에서 다시 확인하세요.

## 내 오답
