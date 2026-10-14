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

기본 모델은 `gpt-6-luna`이며 `AWS_CCP_MODEL`로 바꿀 수 있습니다. AI 비교 해설은 로컬 SQLite에 캐시합니다. 문제, 보기, 문제은행 정답, 학습자 선택, 해당 개념 노트의 본문 요약을 전송합니다. 개념이나 해설의 선택 문장에 질문할 때는 선택 문장과 사용자가 쓴 질문, 관련 문제·개념 문맥을 전송합니다. PDF 원문과 개인 오답은 전송하지 않습니다. API 사용료는 ChatGPT 구독과 별도입니다.

오답 또는 오래 걸린 정답에서 **AI 비교 해설 요청**을 누르면 선택지 비교, 헷갈린 개념, 다음 복습 질문을 포함한 노트가 로컬 `vault/Review/00-오답-지도.md`에 연결됩니다. 노트는 문제를 푼 시도별로 만들며, 카테고리 폴더와 학습서 장별 목차 양쪽에서 찾을 수 있습니다. 같은 시도의 해설을 다시 열어도 직접 수정한 노트는 덮어쓰지 않습니다. 개인 오답을 포함한 `vault/` 전체는 Git에서 제외됩니다. AI 설명은 공식 문서를 실시간으로 조회하지 않습니다. 화면에는 문항별로 확인한 AWS 문서만 연결하고, 확인되지 않은 문항에는 근거 링크를 표시하지 않습니다.

## 학습 흐름

1. **회차별 모의고사**(원본 순서), **시험 비중 랜덤**(공식 시험과 같은 65문항), **복습 예정**(오늘 예정된 문제 전체), **전체 문제** 중 하나로 세트를 시작합니다. 랜덤 세트는 아직 풀지 않은 문항을 먼저 고릅니다. 진행 위치는 학습 DB에 저장되어 새로고침하거나 앱을 재시작해도 이어서 풀 수 있습니다.
2. 답을 고르면 화면에 보인 풀이 시간이 자동 기록됩니다. 문제의 개념 이름 옆 **?** 버튼으로 연결된 개념 설명·비교표·PDF 근거를 확인할 수 있습니다. 팝업을 읽는 시간은 풀이 시간에서 제외되며, 닫으면 선택한 답과 문제 위치가 유지됩니다. 정답을 확인한 뒤 바로 **다음 문제**를 누르거나 `N` 키를 사용합니다.
3. 오답과 오래 걸린 정답은 다음날 다시 나옵니다. 빠르게 맞힌 정답은 2·4·8일 간격으로 복습합니다.
4. [AWS 공식 시험의 65문항·90분](https://aws.amazon.com/certification/certified-cloud-practitioner/)에서 계산한 약 83초/문항을 느린 풀이의 최저 기준으로 씁니다. 시간 기록이 8건 이상이면 내 전체 풀이 시간의 상위 25% 경계와 비교해 **더 긴 시간**을 기준으로 적용합니다. 같은 문제를 3회 이상 풀고 오답률이 40% 이상이며 그 문제의 평균 풀이 시간이 이 기준 이상이면 **헷갈리는 문제**에 표시합니다.
5. 오답은 AI 비교 해설을 요청하고 Obsidian의 장·카테고리별 노트에서 정답과 내 선택을 대조합니다.
6. 개념 노트에서 구별법, 자주 틀리는 지점, 책의 관련 장, AWS 공식 문서를 확인합니다.
7. 틀린 이유를 내 문장으로 기록합니다.

사이드바의 **개념 학습**에서는 Obsidian 볼트의 개념 노트를 웹에서 읽을 수 있습니다. 제목·본문 검색으로 개념을 찾고, 세부 목차로 상세 설명·선택 조건·비교표·확인 문제·출처·내 오답을 바로 확인하세요. 공식 문서와 로컬 학습서 PDF 쪽수 링크를 열 수 있으며, 개념 주소는 새로고침해도 유지됩니다. 학습 본문을 드래그한 뒤 **선택 문장 AI에게 질문**을 누르세요. 출처와 개인 오답 부분에는 AI 질문 버튼을 표시하지 않습니다. 정답 확인 후에는 문제은행 해설이나 AI 비교 해설을 드래그해 해당 문제의 문맥을 포함한 추가 질문을 할 수 있습니다. 답변을 확인하고 **질문과 답변을 Obsidian에 저장**을 눌러야 `vault/Questions/`에 저장됩니다. 질문 목록은 `vault/Questions/00-질문-목록.md`에서 볼 수 있습니다. 질문 답변은 API를 호출하므로 `OPENAI_API_KEY`가 필요합니다.

브라우저 탭을 숨기거나 다른 학습 메뉴로 이동한 시간은 풀이 시간에서 제외합니다. 기존 풀이 기록은 유지되지만 시간이 없으므로 시간 분포 계산에는 쓰지 않습니다.

세트를 끝까지 풀지 않아도 제출한 답은 즉시 오답·복습 통계에 반영됩니다. **시험 비중 랜덤**은 [AWS CLF-C02 시험 가이드](https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02.html)의 채점 영역 비중(클라우드 개념 24%, 보안 및 규정 준수 30%, 클라우드 기술 및 서비스 34%, 청구·요금·지원 12%)을 문항 수에 가깝게 배분합니다. 문제은행의 개념 자동 분류를 사용하므로 공식 시험의 실제 문항 구성과 정확히 같다는 뜻은 아닙니다. 12회차에는 42문항만 있습니다. **새 세트**의 최근 세트 목록에서 이전 세트도 다시 열 수 있습니다.

Obsidian 볼트 `vault/`는 앱을 처음 실행할 때 만들어집니다. 새 PC에서는 이 **실제 프로젝트 폴더의 `vault`**를 Obsidian 볼트로 엽니다. 웹의 **Obsidian에서 열기** 링크는 현재 PC의 실제 파일 경로를 사용합니다. `AWS_CCP_VAULT`로 다른 볼트를 지정할 수 있으며 앱은 기존 노트를 덮어쓰지 않습니다. 첫 실행 시 21개 개념 노트와 [학습서 안내 템플릿](templates/References/학습서-안내.md)이 생성됩니다.

21개 핵심개념에는 PDF의 관련 장을 바탕으로 작성한 한국어 설명, 서비스 선택 조건 비교표, 상황 예시와 확인 문제·해설이 포함됩니다. S3의 접근·복원·AZ 조건, 컴퓨팅의 관리 책임, DB의 장애 대비·읽기 확장 등을 구별하며 보강 자료의 PDF 쪽수 링크로 원문을 확인할 수 있습니다. 지원 플랜·Snowball 제공 조건 등 변동 항목은 2026-10-14의 AWS 공식 안내와 책의 이전 설명을 구분했습니다. 새 노트는 보강 내용을 포함해 생성되며, 기존 노트는 자동으로 덮어쓰지 않습니다.

## 세트 결과와 복습

완료한 세트에서는 전체 문항 기준 **연습 점수(100점 만점)**, 제출 답안의 오답률, 영역별 정답률, 개념별 복습 우선순위와 오답·건너뛴 문제 목록을 확인합니다. 개념 설명과 원래 문제로 바로 이동할 수 있습니다. 다시 푼 결과는 복습 기록에 추가되며 이전 세트 점수를 바꾸지 않습니다. 최근 세트의 **결과 보기**로 예전 결과를 다시 열 수 있습니다.

점수는 `정답 / 세트 전체 문항 × 100`이며 건너뛴 문항은 0점입니다. 오답률은 `오답 / 제출 문항 × 100`으로 건너뜀과 구분합니다. 영역·개념도 같은 기준을 사용하며, 출제되지 않은 영역의 정답률은 표시하지 않습니다. [실제 AWS 시험](https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02.html)은 환산 점수를 사용하므로 이 연습 점수로 합격 여부를 판정하지 않습니다.

복습은 오답·건너뜀 문항이 많은 개념부터, 같은 수이면 오답률과 복습 대상 정답 수 순으로 제안합니다. 리포트의 느린 정답은 65문항·90분 기준 약 83초 이상인 정답입니다. 시간 없는 과거 답안은 시간 평균에서 제외하며, 풀이 시간 합계는 기록된 답안의 활동 시간만 포함합니다. 영역·개념은 문제은행 자동 분류에 따른 학습 참고 정보입니다.

### 세션 API 결과 계약

기존 `GET /api/session`, 세트 생성·활성화·다음 문제 응답의 `session`에 `report`를 추가합니다. 진행 중에는 `null`, 완료 시에는 결과 객체입니다. 기존 필드는 유지하며 저장 스키마는 바꾸지 않습니다. 결과는 `session_items.attempt_id`에 연결된 답안만 집계합니다.

- 전체: `total`, `answered`, `correct`, `wrong`, `skipped`, `score_percent`(전체 기준), `wrong_percent`(제출 기준, 미제출이면 null), `timed_answers`, `total_seconds`, `average_seconds`, `slow_correct`, `flagged_correct`, `review_count`, `slow_threshold_seconds`.
- `domains`: 영역별 `domain`, `weight`와 위 집계 항목. 출제되지 않은 영역은 점수가 null입니다.
- `concepts`: 복습 우선순위로 정렬된 개념별 집계와 `id`, `title`, `domain`, `summary`, `focus`, `question_ids`. 정상 정답만 있는 개념도 포함합니다.
- `review_questions`: 오답·건너뜀·복습 대상 정답의 `id`, `exam`, `number`, `stem`, `concept_id`, `status`, `selected`, `correct_answers`, `duration_seconds`, `slow`, `flagged`, `needs_review`. 상태는 `wrong`, `skipped`, `correct`입니다. 느림과 복습 표시는 겹칠 수 있으므로 `review_count`는 문항을 한 번씩 셉니다.

## 다른 PC로 이전

GitHub 공개 저장소에는 코드·문제은행·초기 템플릿이 있습니다. **풀이 기록·세트 진행 위치·복습 일정·AI 해설 캐시**는 `data/study.sqlite3`, **개인 오답과 수정한 개념 노트·PDF·Obsidian 설정**은 `vault/`에 있습니다. 개인 자료만 별도 ZIP으로 묶으세요. 실행 중인 서버를 끄지 않아도 SQLite의 일관된 스냅샷을 저장합니다. 백업 이후의 풀이와 노트 수정은 그 ZIP에 포함되지 않습니다.

```sh
python3 portable.py export-private
python3 portable.py verify ../aws-clf-c02-practice-private-YYYYMMDD-HHMMSS.zip
```

개인 ZIP은 프로젝트 상위 폴더에 만들어지며 학습 DB·볼트 전체·프로젝트 루트의 별도 `.obsidian/` 작업 공간 설정과 파일별 SHA-256 검증 기록을 포함합니다. `python3 portable.py export-private /path/to/external-drive/study-private.zip`처럼 저장 위치를 지정할 수 있습니다. 개인 학습 내용과 PDF가 들어 있으므로 ZIP은 본인이 관리하는 저장소에만 보관하세요. `.env`와 API 키, 코드, Git 이력은 포함하지 않습니다. 새 PC에서 키를 다시 발급하거나 기존 키를 안전한 방법으로 전달해야 합니다.

새 PC에서는 Python 3.10 이상을 설치하고 공개 저장소를 복제한 뒤, **서버를 처음 실행하기 전에** 개인 ZIP을 검증하고 복제 폴더에 풉니다.

```sh
git clone https://github.com/ice-ice-bear/aws-clf-c02-practice-lab.git
cd aws-clf-c02-practice-lab
python3 portable.py verify /path/to/study-private.zip
unzip /path/to/study-private.zip -d .
cp .env.example .env
# .env에 실제 OPENAI_API_KEY 입력. 이전 PC의 절대 경로 설정은 복사하지 않습니다.
python3 app.py
```

브라우저에서 <http://127.0.0.1:8765>를 열어 풀이 건수와 복습 목록을 확인하고, `vault`를 Obsidian에서 새 볼트로 엽니다. 이전 PC의 Obsidian 별칭 심볼릭 링크는 옮길 필요가 없습니다. 공개 저장소 접속 없이 전체를 옮겨야 한다면 기존 `python3 portable.py export`로 코드까지 포함한 독립 ZIP을 만들 수 있습니다.

## 책과 저작권

개인적으로 보유한 학습서 PDF는 포함되지 않습니다. [Tom Taulli, *AWS Certified Cloud Practitioner (CLF-C02) Study Guide* (O'Reilly, 2026)](https://www.oreilly.com/)를 보유했다면 `vault/References/Taulli-2026-CLF-C02.pdf`에 직접 복사해 관련 장·쪽수 링크를 사용할 수 있습니다. 개념 노트는 별도로 작성한 한국어 요약이며 책의 본문이나 문제는 저장소에 복제하지 않습니다. 변동 가능한 AWS 서비스·요금·지원 정보는 공식 문서를 우선합니다.

## 문제은행과 검증

[kananinirav/AWS-Certified-Cloud-Practitioner-Notes](https://github.com/kananinirav/AWS-Certified-Cloud-Practitioner-Notes)의 Markdown 시험 23개에서 1,142문항을 가져왔습니다. 원본 MIT 라이선스는 [data/UPSTREAM_LICENSE](data/UPSTREAM_LICENSE)에 포함되어 있습니다. 12번 시험은 42문항이고, 13번 시험의 반복된 Markdown 번호는 가져오기 과정에서 순차 번호로 보정했습니다. 재수입: `python3 import_questions.py /path/to/upstream/repo`.

오래된 용어가 명확한 문항은 재검토 표시를 하지만 전체 정확도 감사를 뜻하지는 않습니다. [AWS 공식 CLF-C02 가이드](https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02.html)가 시험 범위의 기준입니다. AI 해설도 연결된 페이지를 직접 조회하지 않으므로 중요한 판단은 공식 문서에서 확인하세요.

```sh
python3 -m unittest discover -s tests
```
