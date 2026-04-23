# Tech Debt Tracker

> Updated: 2026-04-07

---

## Critical (즉시 수정)

| ID | 위치 | 문제 | 상태 |
|---|---|---|---|
| TD-1 | `util.py` (구조 분리 전) | `eval()` 사용 — 코드 인젝션 위험 | ✅ Done |
| TD-2 | `consts.py:40` | Telegram Bot Token 하드코딩 | ✅ Done |

## High

| ID | 위치 | 문제 | 상태 |
|---|---|---|---|
| TD-3 | `api/checkRSI.py:17-18` | 15m RSI 초기화 변수 오류 | ✅ Done |
| TD-4 | `api/checkRSI.py:31-34` | 4h RSI 초기화 변수 오류 | ✅ Done |
| TD-5 | `position_reporting.py` (구 `util.py`) | ETH/XRP Binance 데이터 스왑 | ✅ Done |
| TD-6 | `command_handlers.py` (구 `commandMain.py`) | `allowed_chat_id` 하드코딩 | ✅ Done |

## Medium

| ID | 위치 | 문제 | 상태 |
|---|---|---|---|
| TD-7 | `storage_utils.py` | `put_close_mode()` 경로 타이포 | ✅ Done |
| TD-8 | `api/bithumb.py` | upbit.py에서 복사된 `check_order`/`spot_order` 데드코드 (103줄) | ✅ Done (2026-04-07) |
| TD-9 | `api/checkRSI.py` | `print()` 디버그 출력 4건 | ✅ Done |
| TD-10 | `api/checkRSI.py`, `position_reporting.py` | `datetime.utcfromtimestamp()` deprecated | ✅ Done |
| TD-11 | `api/checkRSI.py:124` | `get_duplicate_ticker()` — `checkOrderbook.get_common_orderbook_ticker()`와 중복 | ✅ Done (2026-04-07) |
| TD-19 | `main.py:109` | `socket_connect == 3` → `socket_check == 3` 비교 버그 | ✅ Done |
| TD-20 | `position_reporting.py:5` | `from api import hana` — shared 레이어 → api 의존 (ARCHITECTURE.md §3 위반) | 🟡 Proposed |
| TD-21 | `api/bithumb.py`, `collectMain.py:6` | `bithumb` 을 EXCHANGE_LIST에 포함하지만 실제 orderbook 가공에서는 무시 | 🟡 Proposed |

## Low

| ID | 위치 | 문제 | 상태 |
|---|---|---|---|
| TD-12 | `util.py` | 617줄 → 28줄로 분리 완료 (`storage_utils`, `telegram_utils`, `position_reporting`, `logging_utils`) | ✅ Done |
| TD-13 | `commandMain.py` | 438줄 → 139줄로 분리 완료 (`command_handlers`, `graph_command_service`) | ✅ Done |
| TD-14 | `api/binance.py` | 424줄 → 286줄 (추가 분리 선택적) | 🟡 Proposed |
| TD-15 | `comparePriceOpenOrder.py` | 333줄 → 254줄 (필터/실행 분리는 선택적) | 🟡 Proposed |
| TD-16 | `crawl/upbitListing.py` | 미완성 + 관련 없는 TrailingStop 클래스 포함 | 🟡 Proposed |
| TD-17 | `api/hana.py` | `pd.read_html()` 의존 — 하나은행 레이아웃 변경 시 깨짐 | 🟡 Proposed |
| TD-18 | 전체 | 파일 기반 상태 관리 (.DAT) — Python repr 포맷의 취약성, JSON 통일 검토 | 🟡 Proposed |

---

## 자동 검증 인프라 (2026-04-07 추가)

| 항목 | 위치 | 역할 |
|---|---|---|
| `bin/check-structure.sh` | 파일 크기 300+ / `eval()` / `print()` / 시크릿 리터럴 검출 | 하네스 #3 |
| `bin/check-deps.py` | ARCHITECTURE.md §3 import 방향 강제 (AST 기반) | 하네스 #3 |
| `tests/` (pytest × 14) | 김프 공식, VWAP, 필터 스킵 조건 회귀 가드 | 하네스 #7 |
| `.github/workflows/ci.yml` | 3단계 CI 파이프라인 (structure → deps → pytest) | 하네스 #7 |

---

## P1 실행 우선순위 (2026-04-07 갱신)

1. **TD-20 해결**: `position_reporting.py`의 `api/hana.py` 의존 제거 (환율 주입 방식으로 역전)
2. **TD-8~18 정리성 잔여 작업**: TD-16, TD-17, TD-18 중 우선순위 판단
3. **전략 확장**: 2x 레버리지 → Upbit 랜딩 → 동적 파라미터 (`docs/exec-plans/active/leverage-and-lending.md`)

---

## 해결 완료

| ID | 위치 | 문제 | 해결일 |
|---|---|---|---|
| TD-1 | `util.py` | `eval()` 제거 | 2026-04-06 |
| TD-2 | `consts.py` | Telegram 토큰 환경변수 기준 정리 | 2026-04-06 |
| TD-3 | `api/checkRSI.py` | 15m RSI 초기화 오류 수정 | 2026-04-06 |
| TD-4 | `api/checkRSI.py` | 4h RSI 초기화 오류 수정 | 2026-04-06 |
| TD-5 | `position_reporting.py` | ETH/XRP Binance 데이터 스왑 수정 | 2026-04-06 |
| TD-6 | `command_handlers.py` | allowed chat id 환경변수 기준 정리 | 2026-04-06 |
| TD-7 | `storage_utils.py` | close mode 저장 경로 수정 | 2026-04-06 |
| TD-9 | `api/checkRSI.py` | 디버그 print 제거 | 2026-04-06 |
| TD-10 | `api/checkRSI.py`, `position_reporting.py` | deprecated timestamp 처리 수정 | 2026-04-06 |
| TD-12 | `util.py` | 617줄 → 28줄 분리 (shared 레이어 파일 4개 추출) | 2026-04-06 |
| TD-13 | `commandMain.py` | 438줄 → 139줄 분리 | 2026-04-06 |
| TD-19 | `main.py` | socket check 비교 버그 수정 | 2026-04-06 |
| TD-8 | `api/bithumb.py` | `check_order`/`spot_order` 데드코드 103줄 삭제 + 중복 if 블록 정리 (162줄 → 45줄) | 2026-04-07 |
| TD-11 | `api/checkRSI.py` | `get_duplicate_ticker()` → `get_common_orderbook_ticker` alias 통합 | 2026-04-07 |
