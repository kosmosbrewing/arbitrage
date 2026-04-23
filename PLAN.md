# PLAN.md

> Status: current mission charter
> Updated: 2026-04-06
> Purpose: 이 저장소의 장기 목표, 운영 원칙, 문서 계층을 고정한다.
> Use with: [`docs/exec-plans/active/leverage-and-lending.md`](./docs/exec-plans/active/leverage-and-lending.md) for current active execution work.

## Role

이 문서는 "지금 당장 무엇을 할 것인가"를 세부적으로 지시하지 않는다.
대신 아래 3가지만 고정한다.

1. 이 봇이 무엇을 하려는가
2. 어떤 원칙으로 운영 판단을 내리는가
3. 하위 plan 문서를 어떻게 읽어야 하는가

즉:

- 현재 active execution work는 [`docs/exec-plans/active/leverage-and-lending.md`](./docs/exec-plans/active/leverage-and-lending.md)
- 완료된 plan은 `docs/exec-plans/completed/`
- 이 문서는 그 둘의 상위 헌장이다

## Mission

> 가격 방향에 베팅하지 않는다. 구조적 김프 차이를 체계적으로 수익화한다.

최종 목표는 단순 수익 극대화가 아니라,
**설명 가능한 진입, 측정 가능한 엣지, 반복 가능한 수익 구조**를 갖춘 자동화 경로를 만드는 것이다.

## Operating Principles

### P1. 감으로 진입하지 않는다

- 7단계 필터 체인을 통과한 진입만 유효하다.
- 필터를 우회한 진입은 성공 사례로 세지 않는다.

### P2. 방향성에 노출되지 않는다

- 현물 롱 + 선물 숏 = 방향성 중립이 기본 포지션이다.
- 레버리지 비대칭(1x:2x)은 자본 효율을 위한 것이지 방향성 베팅이 아니다.

### P3. 측정 없이 파라미터를 바꾸지 않는다

- 진입/청산 파라미터 변경 전 백테스트 또는 시뮬레이션 데이터를 수집한다.
- 변경 이유와 이전 값을 반드시 기록한다.

### P4. 슬리피지와 수수료를 먼저 확인한다

- VWAP 기반 예상 체결가 확인 없이 진입하지 않는다.
- 체결 후 실제 슬리피지를 측정하고 기록한다.

### P5. 안정성이 수익성보다 우선한다

- WebSocket 끊김, 프로세스 크래시는 수익 기회 상실보다 위험하다.
- 연결 상태 확인 후에만 주문을 실행한다.

## Plan Hierarchy

### Layer 1. 상위 헌장
- [`PLAN.md`](./PLAN.md)
- 변하지 않는 mission, 원칙, 판정 구조

### Layer 2. 현재 active execution plan
- [`docs/exec-plans/active/leverage-and-lending.md`](./docs/exec-plans/active/leverage-and-lending.md)
- 현재 검증 순서와 실행 우선순위를 정한다

### Layer 3. completed archive
- `docs/exec-plans/completed/`
- 완료된 plan을 모은 archive다

## Mission Horizons

### Horizon 1. 라이브 거래 안정화 (완료)
- 시뮬레이션 → 라이브 전환 완료
- 3-프로세스 독립 실행 안정화
- WebSocket 재연결, 주문 검증 로직 구현

### Horizon 2. 자본 효율화 (진행 예정)
- 2x 레버리지로 필요 자본 감소 (2억 → 1.5억)
- 마진 관리 로직 추가
- 펀딩비 수익 정량화

### Horizon 3. 추가 알파 소스
- Upbit 랜딩 서비스로 유휴 현물 수익화
- 다중 환율 소스 크로스 체크
- 진입/청산 파라미터 동적 조정

### Horizon 4. 운영 자동화
- Docker 컨테이너화
- 헬스체크 + 자동 재시작
- 구조화된 로깅 (JSON)

## Decision Rules

### Do
- 현재 active 판단은 항상 최신 active execution plan으로 읽는다.
- 파라미터 조정보다 먼저 슬리피지·수수료·수익률 데이터를 수집한다.
- 시뮬레이션 모드에서 먼저 검증한 후 라이브에 반영한다.

### Do Not
- 백테스트 결과만으로 라이브 파라미터를 변경하지 않는다.
- 표본 없이 김프 임계값, 그리드, RSI 조건을 감으로 완화하지 않는다.
- 방향성 베팅 요소를 전략에 추가하지 않는다.
