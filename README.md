# SoftDeck

Windows용 커스텀 버튼 덱 — 키보드 넘패드 또는 마우스로 조작하는 나만의 컨트롤 패널

## 개요

SoftDeck는 화면에 격자형 버튼 패널을 띄워놓고 다양한 동작을 원클릭으로 실행하는 앱입니다.

- 프로그램 실행, 단축키 전송, 텍스트 입력, 매크로, 미디어/볼륨/마이크 제어, 시스템 모니터링, URL·폴더 열기, 셸 명령 실행
- 버튼을 무한 중첩 폴더로 정리
- 활성 앱에 따라 자동 폴더 전환
- 10종 테마, 투명도 조절, 항상 위에 표시
- 포커스를 빼앗지 않는 오버레이 UI

### 두 가지 입력 모드

| 모드 | 설명 |
|------|------|
| **Shortcut Mode** (기본) | 넘패드 키로 버튼 조작. Num Lock OFF = 창 표시, ON = 창 숨김 |
| **Widget Mode** | 항상 표시되는 마우스 전용 위젯. 넘패드 없는 환경에 적합 |

Settings에서 재시작 없이 즉시 전환 가능합니다.

## 설치 및 실행

### SoftDeck.bat (권장)

**`SoftDeck.bat` 더블클릭** — 끝.

Python, 패키지 설치가 필요 없습니다. 첫 실행 시 Python 3.13.2 임베디드 배포판과 의존성이 `python/` 폴더에 자동 설치되며, 이후에는 바로 실행됩니다.

### 소스에서 실행

```bash
pip install -r requirements.txt
python main.py
```

## 넘패드 매핑 (Shortcut Mode)

물리적 넘패드 배치 그대로 버튼에 대응됩니다.

```
┌───────┬───────┬───────┐
│ Num 7 │ Num 8 │ Num 9 │  ← 1행
├───────┼───────┼───────┤
│ Num 4 │ Num 5 │ Num 6 │  ← 2행
├───────┼───────┼───────┤
│ Num 1 │ Num 2 │ Num 3 │  ← 3행
├───────┴───────┼───────┤
│    Num 0      │ Num . │  ← 4행
└───────────────┴───────┘
```

- **Num 0** (2칸 너비) — 상위 폴더 이동
- **Num .** — 이전 폴더로 되돌아가기
- **Num Lock OFF** → 버튼 조작 + 창 표시
- **Num Lock ON** → 숫자 입력 + 창 숨김

## 기능

### 12가지 액션 타입

| 타입 | 설명 |
|------|------|
| **Launch App** | 프로그램 실행 (Find App으로 실행 중 프로세스/시작 메뉴에서 선택) |
| **Hotkey** | 단축키 전송 (`ctrl+c`, `win+l` 등) |
| **Text Input** | 텍스트 자동 입력 (클립보드 모드 지원) |
| **Open URL** | 기본 브라우저로 웹사이트 열기 |
| **Open Folder** | 탐색기에서 폴더 열기 (`%USERPROFILE%`, `~` 지원) |
| **Run Command** | 셸 명령 실행 |
| **Macro** | 여러 동작 순차 실행 (8종 단계 + 녹화) |
| **Media Control** | 미디어/볼륨/마이크 제어 (10종 커맨드) |
| **System Monitor** | CPU/RAM 실시간 표시 |
| **Navigate Folder** | 특정 폴더로 이동 |
| **Navigate Parent** | 상위 폴더로 이동 |
| **Navigate Back** | 방문 기록에서 이전 폴더로 되돌아가기 |

### 미디어 컨트롤 (10종)

Play/Pause, Next, Previous, Stop, Volume Up/Down, Mute, Mic Mute, Now Playing (현재 곡 표시), Audio Device Switch (출력 장치 전환)

토글 버튼(Play/Pause, Mute, Mic Mute)은 상태에 따라 아이콘과 라벨이 자동 전환됩니다.

### 매크로

8가지 단계 타입: Hotkey, Text Input, Delay, Key Down/Up, Mouse Down/Up, Mouse Scroll

**녹화 기능:** Record 버튼으로 키보드·마우스 입력을 자동 기록 (F9 = 중지, Esc = 취소)

### 폴더 시스템

- 무한 중첩 가능한 폴더 트리
- 드래그 앤 드롭으로 폴더 이동/순서 변경
- 폴더별 Export/Import (아이콘 포함, JSON)
- 활성 앱에 따른 자동 폴더 전환 + 자동 포커스
- 방문 기록 기반 뒤로가기 (최대 50개)

### 버튼 편집

- 우클릭 → Edit/Clear/Copy/Paste
- 드래그로 버튼 위치 교환
- 아이콘 (PNG/SVG/ICO), 라벨 색상, 폰트 크기 커스터마이징
- 긴 텍스트 자동 마키 스크롤

## 설정

| 항목 | 설명 | 기본값 |
|------|------|--------|
| Button Size | 버튼 크기 | 100px |
| Button Spacing | 버튼 간격 | 8px |
| Default Font | 기본 라벨 폰트 | 시스템 기본 |
| Default Font Size | 기본 라벨 크기 | 10px |
| Input Mode | Shortcut / Widget | Shortcut |
| Auto-switch | 활성 앱 기반 폴더 전환 | ON |
| Always on top | 항상 위에 표시 | ON |
| Theme | 테마 (10종) | Dark |
| Opacity | 창 투명도 | 100% |

**테마:** Dark, Light, Solarized Light, Midnight, Emerald, Violet, Nord, Dracula, Amber, Cyber

## 게임 호환성

| 모드 | 넘패드 조작 | 창 표시 |
|------|------------|---------|
| 보더리스 (창모드) | O | O |
| 전체화면 (Exclusive) | O | X |

버튼 클릭 시 게임 포커스가 빠지지 않습니다.

## 기술 스택

- **UI:** PyQt6
- **키보드 훅:** C DLL (`numpad_hook.dll`) + `rundll32.exe` (별도 프로세스)
- **Windows API:** ctypes (kernel32, user32), pywin32, pycaw, WinRT (SMTC)
- **입력:** keyboard, pynput
- **플러그인:** 자동 검색 기반 플러그인 시스템

## 요구 사항

- Windows 10/11
- Python 3.10+ (SoftDeck.bat 사용 시 자동 설치)

## 문서

- [USAGE.md](USAGE.md) — 상세 사용법 (한국어)
- [docs/SoftDeck가이드.pdf](docs/SoftDeck가이드.pdf) — PDF 가이드 (한국어)

## 라이선스

Private
