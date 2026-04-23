# CONVENTIONS.md — 코딩 및 문서 규칙

> Updated: 2026-04-06

---

## 코드 규칙

### 네이밍
- **변수명/함수명/에러 메시지**: 영어 (snake_case)
- **주석/설명**: 한국어
- **파일명**: snake_case (`comparePriceOpenOrder.py` 같은 camelCase는 레거시, 신규 파일은 snake_case)
- **상수**: UPPER_SNAKE_CASE (`BALANCE`, `OPEN_TS_GRID`)

### 파일 크기
- 파일당 200줄 이내 지향
- 300줄 초과 시 분리 우선 검토
- 현재 초과 파일: `util.py`(617), `commandMain.py`(438), `binance.py`(424)

### 의존성
- 환경변수·상수는 반드시 `consts.py`에서 정의
- 외부 API 호출은 반드시 `api/` 모듈 경유
- `from consts import *` 사용 허용 (상수 전용 파일이므로)

### 비동기
- 모든 I/O 바운드 작업은 `async/await` 사용
- 동시 실행이 필요한 주문은 `asyncio.gather()` 사용
- 무한 루프 태스크는 `while True` + `await asyncio.sleep()` 패턴

### 에러 처리
- 각 async 태스크는 자체 try-except로 격리
- 에러 시 `logging.info(traceback.format_exc())` 패턴
- 에러로 인한 프로세스 종료 방지 (무한 루프 유지)

### 로깅
- 주문 로그: `order.log` (TimedRotatingFileHandler, 30일 보관)
- 프리미엄 데이터: `premium.log`
- `logging.info()` 사용 (print 금지 — 단, RSI 디버그용 print는 레거시)

---

## 문서 규칙

### 파일 구조
```
arbitrage/
├── AGENTS.md          # 진입점 (100줄 이내)
├── ARCHITECTURE.md    # 모듈 구조, 의존성
├── PROJECT.md         # 목표, 페르소나, 사명
├── PLAN.md            # mission charter
├── STRATEGY.md        # 전략 quick reference
├── MEASUREMENT.md     # 측정 프레임워크
├── README.md          # 저장소 개요
└── docs/
    ├── CONVENTIONS.md    # 이 파일
    ├── SECURITY.md       # 보안 정책
    ├── design-docs/      # 설계 문서
    ├── exec-plans/       # 실행 계획
    │   ├── active/       # 현재 진행 중
    │   └── completed/    # 완료 아카이브
    └── references/       # LLM/참조 자료
```

### 문서 메타데이터
- 상단에 `> Updated: YYYY-MM-DD` 표기
- 상태 마커: `✅ Confirmed`, `🟡 Proposed`, `🔴 Blocked`
- 완료된 plan은 `docs/exec-plans/completed/`로 이관

### 진입 순서 (Progressive Disclosure)
```
AGENTS.md (진입점)
  → ARCHITECTURE.md (구조 이해)
  → PROJECT.md (사명 이해)
  → STRATEGY.md (현재 전략)
  → docs/ (상세 참조)
```

---

## Git 규칙

### 커밋 메시지
- 한국어 또는 영어 일관 사용
- 파라미터 변경 시: `[param] OPEN_TS_GRID: 0.15 → 0.20 (reason: ...)`
- 전략 변경 시: `[strategy] RSI 4h 조건 추가 (reason: ...)`
- 버그 수정 시: `[fix] checkRSI.py 변수 할당 오류 수정`

### 브랜치
- `main`: 라이브 운영 코드
- `dev`: 개발/시뮬레이션 코드
- 기능 브랜치: `feature/2x-leverage`, `fix/rsi-variable`
