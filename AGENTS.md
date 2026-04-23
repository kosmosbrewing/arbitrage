# AGENTS.md — Kimchi Premium Arbitrage Bot

## 프로젝트 개요
- 한 줄 설명: Upbit(현물) - Binance(선물) 간 김프(Korea Premium) 차익거래 자동화 봇
- 스택: Python 3.x, asyncio, websockets, pyupbit, Binance API, pandas, matplotlib
- 모드: `real` / `local` (`ENV` in `consts.py`)
- 아키텍처 기준: [`ARCHITECTURE.md`](./ARCHITECTURE.md)

## 현재 우선 문서

### 운영 기준
| 문서 | 설명 |
|---|---|
| [`docs/exec-plans/active/leverage-and-lending.md`](./docs/exec-plans/active/leverage-and-lending.md) | 현재 active execution plan |
| [`STRATEGY.md`](./STRATEGY.md) | 현재 전략 quick reference |

### 구조/정책 기준
| 문서 | 설명 |
|---|---|
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | 모듈 책임, 의존성 방향, 데이터 흐름 |
| [`PROJECT.md`](./PROJECT.md) | 목표, 비목표, 페르소나, 사명 |
| [`MEASUREMENT.md`](./MEASUREMENT.md) | Mission / Execution / Edge 측정 기준 |
| [`PLAN.md`](./PLAN.md) | mission charter와 plan hierarchy |

### 참조 문서
| 문서 | 설명 |
|---|---|
| [`README.md`](./README.md) | 저장소 개요 |
| [`docs/CONVENTIONS.md`](./docs/CONVENTIONS.md) | 코딩/문서 규칙 |
| [`docs/SECURITY.md`](./docs/SECURITY.md) | 보안 정책 |
| [`docs/design-docs/index.md`](./docs/design-docs/index.md) | 설계 문서 카탈로그 |
| [`docs/exec-plans/tech-debt-tracker.md`](./docs/exec-plans/tech-debt-tracker.md) | 기술 부채 목록 |
| [`docs/references/llm-wiki.md`](./docs/references/llm-wiki.md) | LLM 에이전트용 프로젝트 레퍼런스 |

## 에이전트 작업 규칙

1. 새 파일 생성 전 [`ARCHITECTURE.md`](./ARCHITECTURE.md)의 의존성 방향을 확인한다.
2. 외부 API 호출은 반드시 `api/` 모듈을 경유한다. 직접 `requests` 호출 금지.
3. 환경변수·상수는 반드시 `consts.py`에서 정의·참조한다.
4. 파일당 200줄 이내를 지향한다. 300줄 초과 시 분리를 우선 검토한다.
5. 변수명·함수명·에러 메시지는 영어, 주석은 한국어를 사용한다.
6. 전략 파라미터 변경 시 변경 이유와 이전 값을 커밋 메시지에 명시한다.
7. 주문 실행 로직(`compareprice/`) 변경 시 시뮬레이션 모드에서 먼저 검증한다.
8. `eval()`, `exec()` 사용 금지 — `ast.literal_eval()` 또는 `json.loads()` 사용.
9. API 키·토큰은 코드에 하드코딩하지 않는다. 환경변수만 사용.
10. `print()` 사용 금지 — `logging.info()` 사용. 기존 print는 레거시.

## 에이전트 피드백 루프

에이전트가 실수하거나 코드를 잘못 해석했을 때:
- ❌ 프롬프트만 수정하지 않는다
- ✅ 누락된 컨텍스트를 문서에 추가한다 (docs/, ARCHITECTURE.md, llm-wiki.md)
- ✅ 반복 실수가 발생하면 AGENTS.md 작업 규칙에 항목을 추가한다

## 문서 정리 원칙

- 현재 동작의 기준은 `PLAN.md`, `docs/exec-plans/active/`, `STRATEGY.md`를 우선한다.
- 완료된 plan은 `docs/exec-plans/completed/`로 이관한다.
- 중복 메모는 남기지 않는다. 새로운 운영 해석은 기준 문서에 흡수한다.
- 외부(슬랙, 노션 등)의 결정은 repo에 커밋되기 전까지 존재하지 않는 것으로 간주한다.
