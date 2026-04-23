# SECURITY.md — 보안 정책

> Updated: 2026-04-06

---

## API 키 관리

### 현재 상태 (🔴 개선 필요)

| 항목 | 현재 | 목표 |
|---|---|---|
| Upbit API 키 | 환경변수 (`os.environ`) | ✅ 유지 |
| Binance API 키 | 환경변수 (`os.environ`) | ✅ 유지 |
| Telegram Bot Token | 환경변수 (`TELEGRAM_BOT_TOKEN`) | ✅ 유지 |
| Telegram Chat ID | 환경변수 (`TELEGRAM_CHAT_ID`) | ✅ 유지 |

### 규칙
- API 키는 반드시 환경변수로 관리한다
- `consts.py`에 토큰/키를 직접 기입하지 않는다
- `.env.example` 파일로 필요한 환경변수 목록을 문서화한다
- Git에 키가 커밋되었다면 즉시 키를 재발급한다

### 필요한 환경변수
```bash
# .env.example
UPBIT_OPEN_API_ACCESS_KEY=
UPBIT_OPEN_API_SECRET_KEY=
BINANCE_OPEN_API_ACCESS_KEY=
BINANCE_OPEN_API_SECRET_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

---

## 코드 보안

### 현재 취약점 (🔴 수정 필요)

| ID | 위치 | 문제 | 심각도 |
|---|---|---|---|
| SEC-1 | `data/chat_id.DAT` | 과거 Chat ID 데이터 파일이 저장소에 남아 있음 | Medium |
| SEC-2 | `graph/`, `backtest/` | 유틸/보조 코드에 `print()` 기반 운영 흔적 다수 | Low |
| SEC-3 | 운영 환경 | `.env.example`는 추가됐지만 실제 배포 환경 변수 주입 검증 필요 | Low |

### eval() 대체
```python
# 현재 (위험)
exchange_data['upbit_top_ticker'] = eval(line)

# 수정 (안전)
import ast
exchange_data['upbit_top_ticker'] = ast.literal_eval(line)

# 또는 JSON 사용
import json
exchange_data['upbit_top_ticker'] = json.loads(line)
```

### 규칙
- `eval()`, `exec()` 사용 금지 — `ast.literal_eval()` 또는 `json.loads()` 사용
- 사용자 입력(텔레그램 명령)은 화이트리스트 방식으로 검증
- 파일 I/O 시 경로 검증 (Path Traversal 방지)

---

## 인증 보안

### Upbit API
- JWT (SHA512) 서명
- `uuid` 기반 nonce로 리플레이 공격 방지
- `access_key`, `secret_key`는 환경변수에서 로드

### Binance API
- HMAC-SHA256 서명
- `timestamp` + `recvWindow`로 리플레이 공격 방지
- `X-MBX-APIKEY` 헤더로 키 전달

### 규칙
- API 키 권한은 최소 필요 범위로 설정 (출금 권한 비활성화)
- IP 화이트리스트 설정 (거래소 API 대시보드)
- API 키 주기적 갱신 (90일 권장)

---

## 네트워크 보안

### WebSocket
- WSS (TLS) 연결만 사용
- ping/pong 기반 헬스체크 (`SOCKET_PING_INTERVAL=30`)
- 연결 끊김 시 자동 재연결 (지수 백오프 권장)

### REST API
- HTTPS만 사용
- Rate Limiting 준수 (Upbit: 초당 10회, Binance: 분당 1200)

---

## 운영 보안

### 서버
- SSH 키 기반 접속만 허용
- 불필요한 포트 차단
- 프로세스는 비루트 사용자로 실행

### 로그
- API 키, 토큰은 로그에 남기지 않는다
- 주문 로그에는 금액과 티커만 기록
- 로그 파일 접근 권한 제한 (600)
