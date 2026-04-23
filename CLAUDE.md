# CLAUDE.md — Kimchi Premium Arbitrage Bot

## 진입점
작업 시작 시 `AGENTS.md` → `ARCHITECTURE.md` → 관련 `docs/` 문서 순서로 참조하라.

## 프로젝트 요약
- Upbit(현물 매수) + Binance(선물 숏) 김프 차익거래 자동화 봇
- Python 3.x, asyncio 기반 3-프로세스 아키텍처
- 7단계 진입 필터 + 4-trigger 청산 + 양방향 Trailing Stop

## 핵심 규칙
1. 방향성 베팅 금지 — 현물 롱 + 선물 숏 = 방향성 중립만 허용
2. 주문 로직 변경 시 시뮬레이션 모드에서 먼저 검증
3. 파라미터 변경 시 이전 값과 변경 이유를 커밋 메시지에 명시
4. `eval()` 사용 금지 — `ast.literal_eval()` 또는 `json.loads()` 사용
5. API 키/토큰은 환경변수로만 관리

## 스택
Python 3.x, asyncio, websockets, pyupbit, Binance API, pandas, matplotlib, aiogram

## 문서 맵
- `AGENTS.md`: 에이전트 진입점, 문서 목록
- `ARCHITECTURE.md`: 모듈 구조, 의존성 방향
- `PROJECT.md`: 사명, 목표, 로드맵
- `PLAN.md`: mission charter, 운영 원칙
- `STRATEGY.md`: 전략 파라미터 quick reference
- `MEASUREMENT.md`: Mission/Execution/Edge 측정 프레임워크
- `docs/exec-plans/active/`: 현재 실행 계획
- `docs/exec-plans/tech-debt-tracker.md`: 기술 부채 추적
- `docs/design-docs/`: 설계 문서
- `docs/references/llm-wiki.md`: LLM 에이전트용 레퍼런스
