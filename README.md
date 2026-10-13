# AWS CLF-C02 Study Lab

로컬 문제 풀이, 오답 복습, Obsidian 개념 노트를 묶은 개인 학습 저장소입니다.

## 시작

```sh
cd /path/to/aws-clf-c02-practice-lab
python3 app.py
```

브라우저에서 <http://127.0.0.1:8765>를 엽니다. 서버는 `127.0.0.1`에만 바인딩하며 Python 표준 라이브러리만 사용합니다. API 키 없이 문제 풀이, 채점, 복습, 노트 저장이 가능합니다.

AI 해설을 쓰려면 저장소의 `.env` 파일에 `OPENAI_API_KEY=...`를 적고 서버를 재시작합니다. 앱이 시작할 때 이 파일을 읽습니다. 이미 셸에서 지정한 환경 변수는 `.env`보다 우선합니다.

```sh
export OPENAI_API_KEY='your-key'
python3 app.py
```

기본 모델은 `gpt-6-luna`이며 `AWS_CCP_MODEL`로 바꿀 수 있습니다. 해설 요청 시에만 API를 호출하고 결과는 로컬 SQLite에 캐시합니다. 문제, 보기, 문제은행 정답, 학습자 선택, 해당 개념 노트의 **개인 오답 이전 부분**을 전송합니다. PDF 원문과 개인 오답은 전송하지 않습니다. API 사용료는 ChatGPT 구독과 별도입니다.

오답 또는 오래 걸린 정답에서 **AI 비교 해설 요청**을 누르면 선택지 비교, 헷갈린 개념, 다음 복습 질문을 포함한 노트가 로컬 `vault/Review/00-오답-지도.md`에 연결됩니다. 노트는 문제를 푼 시도별로 만들며, 카테고리 폴더와 학습서 장별 목차 양쪽에서 찾을 수 있습니다. 같은 시도의 해설을 다시 열어도 직접 수정한 노트는 덮어쓰지 않습니다. `vault/Review/`는 개인 학습 기록이므로 Git에서 제외됩니다. AI 설명은 공식 문서를 실시간으로 조회한 결과가 아니므로 노트의 공식 문서 링크에서 확인하세요.

## 학습 흐름

1. 새 문제, 복습 예정, 무작위 문제 중 하나를 선택합니다.
2. 답을 고르면 화면에 보인 풀이 시간이 자동 기록됩니다. 정답을 확인한 뒤 바로 **다음 문제**를 누르거나 `N` 키를 사용합니다.
3. 오답과 오래 걸린 정답은 다음날 다시 나옵니다. 빠르게 맞힌 정답은 2·4·8일 간격으로 복습합니다.
4. 개인 풀이 시간이 8건 이상이면 상위 25% 경계(최소 30초)를 느린 풀이 기준으로 씁니다. 그전에는 임시로 90초를 적용합니다. 같은 문제를 3회 이상 풀고 오답률이 40% 이상이며 평균 시간이 느린 기준 이상이면 **헷갈리는 문제**에 표시합니다.
5. 오답은 AI 비교 해설을 요청하고 Obsidian의 장·카테고리별 노트에서 정답과 내 선택을 대조합니다.
6. 개념 노트에서 구별법, 자주 틀리는 지점, 책의 관련 장, AWS 공식 문서를 확인합니다.
7. 틀린 이유를 내 문장으로 기록합니다.

브라우저 탭을 숨기거나 다른 학습 메뉴로 이동한 시간은 풀이 시간에서 제외합니다. 기존 풀이 기록은 유지되지만 시간이 없으므로 시간 분포 계산에는 쓰지 않습니다.

Obsidian 볼트는 [vault](vault)에 있습니다. 새 PC에서는 이 **실제 프로젝트 폴더의 `vault`**를 Obsidian 볼트로 엽니다. 웹의 **Obsidian에서 열기** 링크는 현재 PC의 실제 파일 경로를 사용합니다. `AWS_CCP_VAULT`로 다른 볼트를 지정할 수 있으며 앱은 기존 노트를 덮어쓰지 않습니다. 21개 개념 노트와 [학습서 안내](vault/References/학습서-안내.md)가 들어 있습니다.

## 다른 PC로 이전

Git 저장소에는 문제은행과 기본 개념 노트만 있습니다. **풀이 기록·복습 일정·AI 해설 캐시**는 `data/study.sqlite3`, **개인 오답과 수정한 개념 노트·PDF·Obsidian 설정**은 `vault/`에 있습니다. 이 둘을 빠뜨리지 않도록 독립 실행 가능한 ZIP 백업을 만듭니다. 실행 중인 서버를 끄지 않아도 SQLite의 일관된 스냅샷을 저장합니다.

```sh
python3 portable.py export
python3 portable.py verify ../aws-clf-c02-practice-backup-YYYYMMDD-HHMMSS.zip
```

백업 ZIP은 프로젝트 상위 폴더에 만들어지며, 소스 코드·문제은행·학습 DB·볼트 전체와 파일별 SHA-256 검증 기록을 포함합니다. `portable.py export /path/to/external-drive/study-backup.zip`처럼 저장 위치를 지정할 수 있습니다. 개인 학습 내용과 PDF가 들어 있으므로 ZIP은 본인이 관리하는 저장소에만 보관하세요. `.env`와 API 키, Git 이력은 포함하지 않습니다. 새 PC에서 키를 다시 발급하거나 기존 키를 안전한 방법으로 전달해야 합니다.

새 PC에서는 ZIP을 원하는 폴더에 풀어 `aws-clf-c02-practice-lab` 폴더로 이동합니다. Python 3.10 이상을 설치한 뒤 아래처럼 확인하고 실행합니다.

```sh
cd /path/to/aws-clf-c02-practice-lab
python3 portable.py verify /path/to/study-backup.zip
cp .env.example .env
# .env에 실제 OPENAI_API_KEY 입력. 이전 PC의 절대 경로 설정은 복사하지 않습니다.
python3 app.py
```

브라우저에서 <http://127.0.0.1:8765>를 열어 풀이 건수와 복습 목록을 확인하고, `vault`를 Obsidian에서 새 볼트로 엽니다. Git 작업을 이어가려면 새 폴더에서 이 공개 저장소를 다시 클론한 후 ZIP의 `data/study.sqlite3`와 `vault/`를 클론 폴더에 복사하세요. 클론 전에 서버를 실행하면 새 빈 DB가 만들어지므로, 이전 파일을 넣은 뒤 서버를 시작하는 것이 간단합니다. 이전 PC의 Obsidian 별칭 심볼릭 링크는 옮길 필요가 없습니다.

## 책과 저작권

개인적으로 보유한 학습서 PDF는 포함되지 않습니다. [Tom Taulli, *AWS Certified Cloud Practitioner (CLF-C02) Study Guide* (O'Reilly, 2026)](https://www.oreilly.com/)를 보유했다면 `vault/References/Taulli-2026-CLF-C02.pdf`에 직접 복사해 관련 장·쪽수 링크를 사용할 수 있습니다. 개념 노트는 별도로 작성한 한국어 요약이며 책의 본문이나 문제는 저장소에 복제하지 않습니다. 변동 가능한 AWS 서비스·요금·지원 정보는 공식 문서를 우선합니다.

## 문제은행과 검증

[kananinirav/AWS-Certified-Cloud-Practitioner-Notes](https://github.com/kananinirav/AWS-Certified-Cloud-Practitioner-Notes)의 Markdown 시험 23개에서 1,142문항을 가져왔습니다. 원본 MIT 라이선스는 [data/UPSTREAM_LICENSE](data/UPSTREAM_LICENSE)에 포함되어 있습니다. 12번 시험은 42문항이고, 13번 시험의 반복된 Markdown 번호는 가져오기 과정에서 순차 번호로 보정했습니다. 재수입: `python3 import_questions.py /path/to/upstream/repo`.

오래된 용어가 명확한 문항은 재검토 표시를 하지만 전체 정확도 감사를 뜻하지는 않습니다. [AWS 공식 CLF-C02 가이드](https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02.html)가 시험 범위의 기준입니다. AI 해설도 연결된 페이지를 직접 조회하지 않으므로 중요한 판단은 공식 문서에서 확인하세요.

```sh
python3 -m unittest discover -s tests
```
