# DayTrace

매일 Linear, GitHub, Slack, Claude Code에서의 활동을 자동 수집하고, Claude Agent SDK(haiku)로 업무 요약을 생성하여 Obsidian 마크다운으로 기록하는 도구.

## 동작 방식

```
Collectors (Linear, GitHub, Slack, Claude Code)
    ↓ 원시 데이터 수집
Claude Agent SDK (haiku)
    ↓ 업무 관련 활동만 필터링 + 서술형 요약 생성
Obsidian Vault
    ↓ YYYY-MM-DD.md 파일 저장 (YAML frontmatter 포함, Dataview 호환)
```

화~토 오전 7시에 macOS launchd로 자동 실행되어 전날 활동을 기록합니다.

## 출력 예시

```markdown
---
date: '2026-03-03'
tracker: true
linear_completed: 6
slack_messages: 10
claude_sessions: 32
---
# 2026-03-03 (화)

## Linear

### Completed

- **AI-2300: HWP/HWPX 파일 처리 스킬 구축**
  - HWP/HWPX 파일 파싱 및 텍스트 추출 기능 구현 완료
  - 파일 처리 메커니즘에 대한 전수 조사 진행

## Slack

### onprem-tepsco

- **Gemma3 12B 모델 검증**
  - Runpod 환경에서 체크섬 대조 검증 완료

## Claude Code

### mally (8 sessions)

- **개발 워크플로우 프로세스 구축**
  - 워크트리 생성 → 계획 수립 → Linear 티켓 생성 → 구현 파이프라인 설계
```

## 설치

```bash
git clone https://github.com/your-username/daytrace.git
cd daytrace
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 본인의 토큰과 경로를 입력합니다:

| 변수 | 설명 | 필수 |
|------|------|------|
| `LINEAR_API_KEY` | Linear → 프로필 아이콘 → Account → API → Personal API key | 선택 |
| `GITHUB_TOKEN` | GitHub → Settings → Developer settings → Personal access tokens | 선택 |
| `GITHUB_USERNAME` | GitHub 사용자명 | 선택 |
| `SLACK_USER_TOKEN` | Slack App의 User OAuth Token (`search:read` scope) | 선택 |
| `OBSIDIAN_VAULT_PATH` | Obsidian Vault 절대 경로 | **필수** |
| `OBSIDIAN_DAYTRACE_DIR` | Vault 내 저장 폴더명 (기본: `DayTrace`) | 선택 |
| `CLAUDE_DIR` | Claude 설정 디렉토리 (기본: `~/.claude`) | 선택 |

설정하지 않은 collector는 자동으로 스킵됩니다.

### Slack App 생성

1. https://api.slack.com/apps → Create New App
2. OAuth & Permissions → User Token Scopes에 `search:read` 추가
3. Install to Workspace → User OAuth Token (`xoxp-...`) 복사

### Claude Code 필터링

`collectors/claude.py`의 `PERSONAL_KEYWORDS`에 업무 외 프로젝트 이름을 추가하면 해당 프로젝트가 요약에서 제외됩니다.

### 요약 프롬프트 커스터마이징

`prompts/daily_summary.md`를 수정하면 요약 톤, 포맷, 필터링 기준을 변경할 수 있습니다.

## 사용법

```bash
source .venv/bin/activate

# 어제 활동 기록
python main.py

# 특정 날짜 기록
python main.py --date 2026-03-03

# 개별 collector 테스트
python -m collectors.linear 2026-03-04
python -m collectors.slack 2026-03-04
python -m collectors.claude 2026-03-04
```

## 자동 실행 (macOS)

```bash
chmod +x setup_launchd.sh
./setup_launchd.sh
```

화~토 오전 7시에 자동 실행됩니다.

### Mac 자동 깨우기

```bash
sudo pmset repeat wake MTWRF 07:00:00
```

`wake`는 dark wake로 모니터를 켜지 않고 시스템만 깨웁니다.

### 전체 흐름

| 시간 | 이벤트 |
|------|--------|
| 07:00 | pmset이 Mac을 dark wake |
| 07:00 | launchd가 `caffeinate -i python main.py` 실행 |
| ~07:01 | 수집 → 요약 → 저장 완료 |
| ~07:02 | caffeinate 해제 → 시스템 자동 잠듦 |

## Backfill

`.last_run.json`에 마지막 실행 날짜가 기록됩니다.
놓친 날짜가 있으면 다음 실행 시 자동으로 backfill합니다.

## 프로젝트 구조

```
daytrace/
├── main.py                 # 엔트리포인트 (backfill + 수집 + 요약 + 기록)
├── config.py               # .env 로딩 + 설정값
├── summarizer.py           # Claude Agent SDK 기반 요약 생성
├── writer.py               # Obsidian 마크다운 생성 & 저장
├── collectors/
│   ├── linear.py           # Linear GraphQL API (읽기 전용)
│   ├── github.py           # GitHub Events API (읽기 전용)
│   ├── slack.py            # Slack search.messages (읽기 전용, 공개 채널만)
│   └── claude.py           # ~/.claude JSONL 파싱 (업무 프로젝트만)
├── prompts/
│   └── daily_summary.md    # 요약 프롬프트 가이드
├── setup_launchd.sh        # launchd plist 생성 & 등록
├── .env.example            # 토큰 템플릿
├── .gitignore
└── requirements.txt
```
