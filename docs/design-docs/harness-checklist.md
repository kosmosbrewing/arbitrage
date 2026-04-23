# Harness Engineering Checklist

> Created: 2026-04-06
> Updated: 2026-04-07 (P1 인프라 반영)
> Source: shakilabs harness.md (OpenAI "Harness engineering" 원칙 기반)
> Purpose: 하네스 엔지니어링 10대 원칙 적용 현황 추적

---

## 핵심 원칙

> "에이전트 품질의 천장은 레포 환경(구조, 문서, 린터, 피드백 루프)이 결정한다. 프롬프트가 아니다."

---

## 최근 문서 감사

- 2026-04-06 기준 문서 감사 36개 이슈 정정 반영
- 주요 정정 범주: 필터 스킵 로직 방향, RSI 35/65 임계값, 시뮬레이션/라이브 김프 공식 분리, 잔고 2단계 체크, TD-19 추가, `print()`/deprecated/ETH-XRP 스왑 메모 보강, 깨진 링크 제거

---

## 적용 현황

### 1. Repository = Single Source of Truth
> 모든 아키텍처 결정, 규칙, 기술 부채는 `docs/` 마크다운에 있어야 한다.

| 항목 | 상태 | 비고 |
|---|---|---|
| ARCHITECTURE.md (모듈 구조) | ✅ | 16개 모듈 맵, 의존성 규칙, 데이터 흐름 |
| docs/design-docs/ (설계 문서) | ✅ | core-beliefs, kimchi-premium-model, entry-filter-chain |
| docs/exec-plans/ (실행 계획) | ✅ | active + completed + tech-debt-tracker |
| ADR (Architecture Decision Records) | 🟡 | docs/decisions/ 구조 미생성, 향후 주요 결정 시 추가 |

### 2. AGENTS.md as Table of Contents (100줄 이내)
> 백과사전이 아닌 네비게이션 포인터. Progressive disclosure.

| 항목 | 상태 | 비고 |
|---|---|---|
| AGENTS.md 존재 | ✅ | ~60줄 |
| 100줄 이내 | ✅ | |
| 문서 맵 테이블 | ✅ | 운영/구조/참조 3-tier |
| 에이전트 작업 규칙 | ✅ | 10개 규칙 |

### 3. Mechanical Boundary Enforcement
> 린터, CI, 파일 크기 제한으로 구조를 기계적으로 강제한다.

| 항목 | 상태 | 비고 |
|---|---|---|
| Import 방향 린터 | ✅ 적용 | `bin/check-deps.py` (AST 기반, ARCHITECTURE.md §3 강제) |
| 파일 크기 CI 체크 | ✅ 적용 | `bin/check-structure.sh` (POSIX-only, rg 의존 제거) |
| 네이밍 컨벤션 강제 | 🟡 부분 | 레거시 camelCase 일부 공존 (checkRSI, checkOrderbook 등) |
| CI/CD 파이프라인 | ✅ 적용 | `.github/workflows/ci.yml` (structure → deps → pytest 3단계) |
| 시크릿 리터럴 검출 | ✅ 적용 | `check-structure.sh` 내 TOKEN/API_KEY/SECRET_KEY 리터럴 정규식 검사 |

### 4. App Legibility for Agents
> 에이전트가 실행 중인 앱 상태를 검사할 수 있어야 한다.

| 항목 | 상태 | 비고 |
|---|---|---|
| 단일 명령 기동 | 🟡 | `bin/boot_all.sh` 존재, 하지만 conda 의존 |
| Health check | 🔴 미적용 | HTTP 엔드포인트 없음 |
| 구조화된 로깅 (JSON) | 🔴 미적용 | 현재 문자열 로깅 (pipe-separated) |
| 텔레그램 상태 조회 | ✅ | `/current` 명령으로 포지션 확인 가능 |

### 5. Boring Technology Wins
> LLM 학습 데이터가 풍부한 기술을 우선한다.

| 항목 | 상태 | 비고 |
|---|---|---|
| Python 3.x | ✅ | 풍부한 학습 데이터 |
| asyncio | ✅ | 표준 라이브러리 |
| pandas/numpy | ✅ | |
| requests | ✅ | |
| 표준 구조 | 🟡 | 커스텀 파일 구조이나 명확 |

### 6. Entropy Management (Garbage Collection)
> 중복 제거, 표준화, 정기 정리.

| 항목 | 상태 | 비고 |
|---|---|---|
| 공유 유틸 > 중복 헬퍼 | ✅ | TD-11 해결: `get_duplicate_ticker` → `get_common_orderbook_ticker` alias 통합 |
| "Parse, don't validate" | 🟡 | `eval()` 제거 완료. `.DAT` → JSON 이관은 TD-18로 잔여 |
| 200줄 타겟 | 🟡 | 300줄 초과 파일 0개 (util 28, commandMain 139, binance 286, comparePriceOpenOrder 254) |
| print() 제거 | ✅ | 코어 경로 0건 (check-structure.sh가 회귀 차단) |
| 데드코드 제거 | ✅ | TD-8 해결: bithumb.py 162줄 → 45줄 (dead code 103줄 삭제) |

### 7. Throughput-First Merge Philosophy
> 작은 PR, CI pass = mergeable.

| 항목 | 상태 | 비고 |
|---|---|---|
| CI 파이프라인 | ✅ 적용 | `.github/workflows/ci.yml` (structure → deps → pytest) |
| 테스트 | ✅ 적용 | `tests/` pytest 14개 (김프 공식, VWAP, 필터 스킵 조건) |
| PR 워크플로 | 🟡 부분 | 1인 개발이지만 CI gating 가능, 현재는 로컬 pre-commit 수동 |

### 8. Agent Feedback Loop
> 에이전트 실수 → 프롬프트 수정 ❌ → 레포 개선 ✅

| 항목 | 상태 | 비고 |
|---|---|---|
| AGENTS.md 피드백 루프 섹션 | ✅ | 추가 완료 |
| llm-wiki.md 주의사항 | ✅ | 9개 항목 기재 |
| 코드 필터 로직 설명 | ✅ | "스킵 조건" 패턴 명시 (이전 오해 반영) |

### 9. Security — Non-Negotiable
> 입력 검증, 시크릿 관리, 기본 방어.

| 항목 | 상태 | 비고 |
|---|---|---|
| `eval()` 제거 | ✅ | P0 반영 완료, `check-structure.sh`로 회귀 차단 |
| 시크릿 환경변수화 | ✅ | Telegram 토큰/Chat ID 환경변수 기준 정리 |
| `.env.example` | ✅ | repo 루트 추가 완료 |
| 보안 문서 | ✅ | docs/SECURITY.md |
| 시크릿 하드코딩 CI 차단 | ✅ | `check-structure.sh`가 TOKEN/API_KEY 리터럴 자동 검출 |

### 10. Immediate Execution Checklist
> P0(1-2일) → P1(1개월) → P2(분기)

| Phase | 내용 | 상태 |
|---|---|---|
| **P0** | AGENTS.md, ARCHITECTURE.md, docs/ 구조 | ✅ 완료 |
| **P1a** | 구조 검증 스크립트 (파일 크기, eval, print, secret) | ✅ 완료 |
| **P1b** | Import 방향 린터 (`bin/check-deps.py`) | ✅ 완료 |
| **P1c** | CI 파이프라인 (GitHub Actions) | ✅ 완료 |
| **P1d** | 크리티컬 패스 pytest (김프, VWAP, 필터 스킵) | ✅ 완료 |
| **P1e** | 300줄 초과 파일 분리 + 기술 부채 해결 | ✅ 완료 (TD-8, TD-11 포함) |
| **P2** | Docker화, 구조화 로깅, 헬스체크 | 🔴 미시작 |

### 현재 P2 우선순위
1. TD-20 해결: `position_reporting.py`의 `api/hana.py` 의존 제거 (환율 주입 역전)
2. 구조화 로깅 (JSON: timestamp/level/ticker/action)
3. Docker화 + 헬스체크 엔드포인트
4. 전략 확장 Phase 2 착수: 2x 레버리지 시뮬레이션 검증

---

## 종합 점수

| 원칙 | 적용도 (2026-04-06) | 적용도 (2026-04-07) |
|---|---|---|
| 1. Repo = SSOT | ✅ 적용 | ✅ 적용 |
| 2. AGENTS.md | ✅ 적용 | ✅ 적용 |
| 3. Mechanical Enforcement | 🔴 미적용 | ✅ 적용 |
| 4. App Legibility | 🟡 부분 | 🟡 부분 |
| 5. Boring Technology | ✅ 적용 | ✅ 적용 |
| 6. Entropy Management | 🔴 미적용 | ✅ 적용 |
| 7. Merge Philosophy | 🔴 미적용 | ✅ 적용 |
| 8. Feedback Loop | ✅ 적용 | ✅ 적용 |
| 9. Security | 🔴 미적용 | ✅ 적용 |
| 10. Execution Checklist | 🟡 P0 완료 | ✅ P1 전체 완료 |

**2026-04-06: 10개 중 4개 적용, 2개 부분, 4개 미적용**
**2026-04-07: 10개 중 9개 적용, 1개 부분 (App Legibility 남음 — 헬스체크/JSON 로깅)**

**다음 단계 (P2):** 구조화 로깅(JSON), 헬스체크, Docker화 — `docs/exec-plans/active/leverage-and-lending.md`의 전략 확장과 병행
