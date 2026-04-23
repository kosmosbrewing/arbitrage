# Active Execution Plan: 안정화 → 구조화 → 전략 확장

> Created: 2026-04-06
> Updated: 2026-04-06
> Status: 🟡 Active
> Priority: 실거래 안전성, 보안, 정합성 우선

---

## 배경

현재 코드베이스는 전략 문서화는 많이 정리됐지만, 실거래 관점에서는 아직 아래 선행 과제가 남아 있다.

1. 보안: Telegram 토큰/Chat ID 하드코딩, `eval()` 잔존
2. 정합성: RSI 초기화 오류, ETH/XRP 데이터 스왑, socket 비교 버그
3. 운영성: 구조 검증 스크립트, 대형 파일 분리, 관측성 부족

이 상태에서 2x 레버리지나 랜딩 같은 기능 확장을 먼저 하면 수익성보다 운영 리스크가 더 빨리 커진다.
따라서 active execution 우선순위는 아래처럼 재배치한다.

---

## P0: 보안 + 정합성 + 실행 안전성

### 목표
- 시크릿 하드코딩 제거
- 액티브 트레이딩 경로의 명백한 버그 수정
- 최소한의 구조 검증 자동화 추가

### 작업 항목
- [x] `consts.py`, `commandMain.py`, `util.py`, `graph/graphUtil.py`, `backtest/backTestConsts.py`
  - Telegram 토큰/Chat ID를 환경변수 기준으로 정리
- [x] `util.py`
  - `eval()` 제거
  - `put_close_mode()` 경로 타이포 수정
  - ETH/XRP Binance 데이터 스왑 수정
- [x] `api/checkRSI.py`
  - RSI 딕셔너리 초기화 오류 수정
  - 디버그 `print()` 제거
  - deprecated timestamp 처리 수정
- [x] `main.py`
  - `socket_check == 3` 비교 버그 수정
- [x] `backtest/backTestMain.py`
  - CLI 입력 처리에서 `eval()` 제거
- [x] `bin/check-structure.sh`
  - `eval()`, `print()`, 300줄 초과 파일 검출 스크립트 추가
- [x] `main.py`, `order_execution.py`, `compareprice/*`
  - `EXECUTION_MODE=paper|live` 기준으로 주문 실행 경로 분리

### 완료 기준
- 실거래 메인 경로에 `eval()`이 없다
- Telegram 시크릿이 코드에 남아 있지 않다
- 문서에 적힌 Critical/High 버그 중 P0 범위 항목이 해소된다
- 주문 실행 모드가 `paper`와 `live`로 명시적으로 구분된다

### 리스크
- 환경변수 미설정 상태에서는 Telegram 기능이 비활성 또는 기동 실패할 수 있음
  → `.env.example` 제공, 운영 환경 변수 선행 설정 필요
- 구조 검증 스크립트는 기존 그래프/백테스트 코드의 `print()` 때문에 아직 실패할 수 있음
  → 현재 상태 가시화가 목적, P1에서 정리

### 기대 효과
- 실거래 사고 가능성 즉시 감소
- 이후 구조화/기능 확장의 기반 확보

---

## P1: 구조화 + 관측성 + 유지보수성

### 목표
- 대형 파일 분리와 역할 경계 명확화
- 구조 검증을 CI/운영 루틴에 포함
- 헬스체크와 로그 가시성 개선

### 작업 항목
- [x] `util.py` 분리: telegram, file I/O, reporting
- [ ] `commandMain.py` 분리: 핸들러별 모듈화
- [ ] `api/binance.py` 분리: REST, order, websocket, admin 유틸
- [ ] `api/bithumb.py` 데드코드 제거
- [ ] `api/checkRSI.py` 중복 헬퍼 제거
- [ ] `bin/check-structure.sh`를 CI 또는 운영 체크 루틴에 연결
- [ ] JSON 구조화 로깅 설계
- [ ] 프로세스 헬스체크 방식 정의

### 리스크
- 분리 중 회귀 가능성
  → 파일 경계는 바꾸되 전략/주문 로직 의미는 보존
- 로그 포맷 변경이 기존 그래프/백테스트 파서를 깨뜨릴 수 있음
  → 파서와 로그 포맷 전환 계획을 같이 설계

### 기대 효과
- 코드 해석 비용 감소
- 변경 리스크 감소
- 에이전트/사람 모두가 수정하기 쉬운 구조 확보

---

## P2: 전략 확장

### 목표
- 2x 레버리지, 랜딩, 동적 파라미터 조정 같은 전략 확장 착수
- 수익성 확장은 P0/P1 선행 조건을 만족한 뒤 진행

### 작업 항목
- [ ] Binance 2x 레버리지 적용 + 마진 모니터링
- [ ] Upbit 랜딩 서비스 API/상품 조사
- [ ] 랜딩 진입/상환 연동 설계
- [ ] 과거 김프 데이터 수집 (premium.log 파싱)
- [ ] 변동성 구간별 최적 파라미터 백테스트
- [ ] `CLOSE_GIMP_GAP` 동적 조정 (변동성 높을 때 확대)
- [ ] `OPEN_TS_GRID` / `CLOSE_TS_GRID` 변동성 연동
- [ ] `close_mode` 자동 전환 로직

### 후보 파라미터 스윕
| 파라미터 | 현재 | 탐색 범위 |
|---|---|---|
| `CLOSE_GIMP_GAP` | 0.5% | 0.3% ~ 0.8% |
| `OPEN_TS_GRID` | 0.15% | 0.10% ~ 0.25% |
| `CLOSE_TS_GRID` | 0.15% | 0.10% ~ 0.25% |
| `OPEN_TS_COUNT` | 5 | 3 ~ 7 |
| `CLOSE_TS_COUNT` | 5 | 3 ~ 7 |
| `BTC_GAP` | 1.2% | 0.8% ~ 1.5% |

---

## P0/P1/P2 작업표

| Phase | 초점 | 핵심 산출물 | 상태 |
|---|---|---|---|
| P0 | 보안, 정합성, 실행 안전성 | env 기반 시크릿, 버그 수정, 구조 검증 스크립트 | 🟡 진행 중 |
| P1 | 구조화, 관측성, 유지보수성 | 파일 분리, CI/검증 루틴, 로그/헬스체크 개선 | 🟡 진행 중 |
| P2 | 전략 확장 | 2x 레버리지, 랜딩, 동적 파라미터 | ⚪ 대기 |

---

## 기술 부채 병행 처리

상세 목록: [`tech-debt-tracker.md`](../tech-debt-tracker.md)

- P0는 TD-1, TD-2, TD-3, TD-4, TD-5, TD-6, TD-7, TD-10, TD-19를 우선 닫는다
- P1는 TD-8, TD-9, TD-11, TD-12~TD-18을 구조화 작업과 함께 처리한다
