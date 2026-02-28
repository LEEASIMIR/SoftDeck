"""Generate SoftDeck가이드.pdf — comprehensive user guide."""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Font setup (Windows Korean font) ---
pdfmetrics.registerFont(TTFont("Malgun", "C:/Windows/Fonts/malgun.ttf"))
pdfmetrics.registerFont(TTFont("MalgunBold", "C:/Windows/Fonts/malgunbd.ttf"))
pdfmetrics.registerFontFamily("Malgun", normal="Malgun", bold="MalgunBold")

# --- Colors ---
BLACK = HexColor("#000000")
DARK = HexColor("#1a1a1a")
GRAY = HexColor("#666666")
LIGHT_GRAY = HexColor("#f5f5f5")
ACCENT = HexColor("#e94560")
ACCENT_LIGHT = HexColor("#ffeef1")
WHITE = HexColor("#ffffff")
TH_BG = HexColor("#222222")
ALT_BG = HexColor("#f9f9f9")
BORDER = HexColor("#cccccc")
CODE_BG = HexColor("#f0f0f0")
TIP_BG = HexColor("#f0f7ff")
TIP_BORDER = HexColor("#4a9eff")
WARN_BG = HexColor("#fff8e6")
WARN_BORDER = HexColor("#e6a817")

# --- Styles ---
s_title = ParagraphStyle(
    "DocTitle", fontName="MalgunBold", fontSize=24, leading=30,
    textColor=BLACK, alignment=TA_CENTER, spaceAfter=4,
)
s_subtitle = ParagraphStyle(
    "DocSubtitle", fontName="Malgun", fontSize=12, leading=16,
    textColor=GRAY, alignment=TA_CENTER, spaceAfter=6,
)
s_version = ParagraphStyle(
    "Version", fontName="Malgun", fontSize=9, leading=12,
    textColor=GRAY, alignment=TA_CENTER, spaceAfter=20,
)
s_h1 = ParagraphStyle(
    "H1", fontName="MalgunBold", fontSize=16, leading=22,
    textColor=BLACK, spaceBefore=24, spaceAfter=10,
)
s_h2 = ParagraphStyle(
    "H2", fontName="MalgunBold", fontSize=13, leading=18,
    textColor=DARK, spaceBefore=16, spaceAfter=8,
)
s_h3 = ParagraphStyle(
    "H3", fontName="MalgunBold", fontSize=11, leading=15,
    textColor=DARK, spaceBefore=10, spaceAfter=6,
)
s_body = ParagraphStyle(
    "Body", fontName="Malgun", fontSize=10, leading=16,
    textColor=DARK, spaceAfter=6,
)
s_bullet = ParagraphStyle(
    "Bullet", fontName="Malgun", fontSize=10, leading=16,
    textColor=DARK, leftIndent=16, spaceAfter=3,
    bulletIndent=4, bulletFontSize=10,
)
s_bullet2 = ParagraphStyle(
    "Bullet2", fontName="Malgun", fontSize=10, leading=16,
    textColor=DARK, leftIndent=32, spaceAfter=3,
    bulletIndent=20, bulletFontSize=10,
)
s_note = ParagraphStyle(
    "Note", fontName="Malgun", fontSize=9, leading=14,
    textColor=GRAY, leftIndent=12, spaceAfter=8,
)
s_tip = ParagraphStyle(
    "Tip", fontName="Malgun", fontSize=9.5, leading=14,
    textColor=HexColor("#1a5276"), leftIndent=12, rightIndent=8,
    spaceBefore=2, spaceAfter=2,
)
s_warn = ParagraphStyle(
    "Warn", fontName="Malgun", fontSize=9.5, leading=14,
    textColor=HexColor("#7d6608"), leftIndent=12, rightIndent=8,
    spaceBefore=2, spaceAfter=2,
)
s_th = ParagraphStyle(
    "TH", fontName="MalgunBold", fontSize=9, leading=13,
    textColor=WHITE, alignment=TA_CENTER,
)
s_td = ParagraphStyle(
    "TD", fontName="Malgun", fontSize=9, leading=13,
    textColor=DARK, alignment=TA_CENTER,
)
s_td_l = ParagraphStyle(
    "TDL", fontName="Malgun", fontSize=9, leading=13,
    textColor=DARK,
)
s_td_bold = ParagraphStyle(
    "TDBold", fontName="MalgunBold", fontSize=9, leading=13,
    textColor=DARK,
)
# Grid cell style for numpad layout
s_grid_cell = ParagraphStyle(
    "GridCell", fontName="MalgunBold", fontSize=9, leading=13,
    textColor=DARK, alignment=TA_CENTER,
)
s_grid_label = ParagraphStyle(
    "GridLabel", fontName="Malgun", fontSize=8, leading=11,
    textColor=GRAY, alignment=TA_CENTER,
)


def hr():
    return HRFlowable(
        width="100%", thickness=0.5, color=BORDER,
        spaceAfter=12, spaceBefore=8,
    )


def sp(h=8):
    return Spacer(1, h)


def tbl(headers, rows, col_widths=None):
    """Create a styled table."""
    data = [[Paragraph(h, s_th) for h in headers]]
    for row in rows:
        cells = []
        for i, c in enumerate(row):
            style = s_td if i == 0 else s_td_l
            cells.append(Paragraph(str(c), style))
        data.append(cells)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), TH_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "MalgunBold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), ALT_BG))
    t.setStyle(TableStyle(cmds))
    return t


def grid_4x3(rows_data, footer_wide=None, footer_right=None):
    """Create a 4x3 numpad-style grid table.

    rows_data: list of 3 rows, each row is [col0, col1, col2] as (label, sublabel) tuples.
    footer_wide: (label, sublabel) for the wide Num 0 cell spanning 2 columns.
    footer_right: (label, sublabel) for the Num . cell.
    """
    data = []
    for row in rows_data:
        cells = []
        for label, sub in row:
            text = f'<b>{label}</b><br/><font size="7" color="#888888">{sub}</font>'
            cells.append(Paragraph(text, s_grid_cell))
        data.append(cells)

    # 4th row
    if footer_wide or footer_right:
        wide_label, wide_sub = footer_wide or ("", "")
        right_label, right_sub = footer_right or ("", "")
        wide_text = f'<b>{wide_label}</b><br/><font size="7" color="#888888">{wide_sub}</font>'
        right_text = f'<b>{right_label}</b><br/><font size="7" color="#888888">{right_sub}</font>'
        data.append([
            Paragraph(wide_text, s_grid_cell),
            "",  # merged
            Paragraph(right_text, s_grid_cell),
        ])

    cw = 53 * mm
    t = Table(data, colWidths=[cw, cw, cw])
    cmds = [
        ("GRID", (0, 0), (-1, -1), 1, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
    ]
    if footer_wide:
        last = len(data) - 1
        cmds.append(("SPAN", (0, last), (1, last)))
    t.setStyle(TableStyle(cmds))
    return t


def tip_box(text):
    """Tip box with blue left border."""
    inner = Paragraph(text, s_tip)
    t = Table([[inner]], colWidths=[155 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TIP_BG),
        ("LINEBEFORESTARTS", (0, 0), (0, -1)),
        ("LINEBEFORE", (0, 0), (0, -1), 3, TIP_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def warn_box(text):
    """Warning box with amber left border."""
    inner = Paragraph(text, s_warn)
    t = Table([[inner]], colWidths=[155 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WARN_BG),
        ("LINEBEFORE", (0, 0), (0, -1), 3, WARN_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )
    story = []

    # =========================================================================
    # TITLE PAGE
    # =========================================================================
    story.append(Spacer(1, 40))
    story.append(Paragraph("SoftDeck", s_title))
    story.append(Paragraph(
        "사용자 가이드", ParagraphStyle(
            "Accent", fontName="Malgun", fontSize=14, leading=18,
            textColor=ACCENT, alignment=TA_CENTER, spaceAfter=8,
        ),
    ))
    story.append(Paragraph(
        "키보드 넘패드 또는 마우스로 조작하는 나만의 버튼 덱",
        s_subtitle,
    ))
    story.append(Paragraph("v0.1.1", s_version))
    story.append(hr())

    # =========================================================================
    # 1. SoftDeck란?
    # =========================================================================
    story.append(Paragraph("1. SoftDeck란?", s_h1))
    story.append(Paragraph(
        "SoftDeck는 Windows용 커스텀 버튼 덱 앱입니다. "
        "Stream Deck처럼 화면에 버튼 패널을 띄워놓고, "
        "프로그램 실행 / 단축키 / 볼륨 조절 / 텍스트 입력 / 매크로 등을 "
        "버튼 하나로 실행할 수 있습니다.",
        s_body,
    ))
    story.append(Paragraph(
        "버튼은 폴더로 정리할 수 있으며, 폴더 안에 폴더를 만들 수 있어서 "
        "원하는 만큼 버튼을 늘릴 수 있습니다.",
        s_body,
    ))
    story.append(sp())

    story.append(Paragraph("두 가지 모드", s_h2))
    story.append(tbl(
        ["모드", "설명", "적합한 사용자"],
        [
            [
                "Widget Mode (기본)",
                "항상 화면에 표시. 마우스로 클릭하여 사용",
                "처음 사용자, 넘패드 없는 환경",
            ],
            [
                "Shortcut Mode",
                "넘패드 키로 버튼 조작. Num Lock으로 창 표시/숨김 전환",
                "넘패드 키보드 사용자",
            ],
        ],
        col_widths=[35 * mm, 70 * mm, 55 * mm],
    ))
    story.append(sp())
    story.append(tip_box(
        "<b>모드는 언제든 전환 가능합니다.</b> "
        "설정(Settings)에서 Input Mode를 바꾸면 재시작 없이 즉시 적용됩니다."
    ))

    # =========================================================================
    # 2. 설치 및 실행
    # =========================================================================
    story.append(Paragraph("2. 설치 및 실행", s_h1))
    story.append(Paragraph("<b>SoftDeck.bat</b>를 더블클릭하면 됩니다.", s_body))
    story.append(Paragraph(
        "Python이나 패키지를 직접 설치할 필요가 없습니다. "
        "첫 실행 시 필요한 모든 것이 자동으로 다운로드됩니다.",
        s_body,
    ))
    story.append(sp())
    story.append(tbl(
        ["실행 횟수", "동작"],
        [
            ["첫 실행", "Python 임베디드 배포판 + 의존성 자동 다운로드·설치 → 앱 실행"],
            ["이후 실행", "바로 실행"],
        ],
        col_widths=[40 * mm, 120 * mm],
    ))

    # =========================================================================
    # 3. 넘패드로 조작하기 (Shortcut Mode)
    # =========================================================================
    story.append(Paragraph("3. 넘패드로 조작하기 (Shortcut Mode)", s_h1))
    story.append(Paragraph(
        "<b>Num Lock을 끄세요.</b> 그러면 넘패드가 버튼 리모컨이 됩니다. "
        "Num Lock을 다시 켜면 넘패드는 원래대로 숫자 입력용으로 돌아가고, "
        "창도 자동으로 숨겨집니다.",
        s_body,
    ))
    story.append(sp())

    story.append(Paragraph("넘패드 키 → 버튼 위치 매핑", s_h2))
    story.append(Paragraph(
        "물리적 넘패드 배치 그대로 화면 버튼에 대응됩니다. "
        "4행 구조로, Num 0은 넓은 버튼(2칸), Num .은 우측 1칸입니다.",
        s_body,
    ))
    story.append(tbl(
        ["넘패드 키", "버튼 위치", "기본 역할"],
        [
            ["Num 7 / 8 / 9", "1행 (왼 → 오)", "자유 배치"],
            ["Num 4 / 5 / 6", "2행", "자유 배치"],
            ["Num 1 / 2 / 3", "3행", "자유 배치"],
            ["Num 0 (넓은 키)", "4행 왼쪽 (2칸)", "상위 폴더 이동"],
            ["Num .", "4행 오른쪽", "이전 폴더로 되돌아가기"],
        ],
        col_widths=[40 * mm, 45 * mm, 75 * mm],
    ))
    story.append(sp())

    story.append(Paragraph("Num Lock에 따른 동작", s_h2))
    story.append(tbl(
        ["Num Lock", "넘패드 키", "창 상태"],
        [
            ["OFF", "버튼 덱 조작", "창 표시"],
            ["ON", "일반 숫자 입력", "창 숨김"],
        ],
        col_widths=[40 * mm, 60 * mm, 60 * mm],
    ))
    story.append(sp())
    story.append(warn_box(
        "Widget Mode에서는 넘패드 키 캡처가 비활성화됩니다. "
        "넘패드 키는 항상 일반 숫자 입력으로 동작하며, 버튼은 마우스로 클릭하세요."
    ))

    # =========================================================================
    # 4. 기본으로 들어있는 버튼
    # =========================================================================
    story.append(Paragraph("4. 기본으로 들어있는 버튼", s_h1))
    story.append(Paragraph(
        "앱을 처음 실행하면 기본 버튼 구성이 세팅되어 있어 바로 사용할 수 있습니다. "
        "추가로 미디어, 폴더, 가상 데스크톱 예제 폴더도 자동으로 추가됩니다.",
        s_body,
    ))
    story.append(sp())

    story.append(Paragraph("Root (메인 화면)", s_h2))
    story.append(grid_4x3(
        [
            [("VOL -", "Num 7"), ("MUTE", "Num 8"), ("VOL +", "Num 9")],
            [("PREV", "Num 4"), ("PLAY", "Num 5"), ("NEXT", "Num 6")],
            [("CPU", "Num 1"), ("RAM", "Num 2"), ("Apps →", "Num 3")],
        ],
        footer_wide=("← Back", "Num 0"),
        footer_right=("", "Num ."),
    ))
    story.append(sp())

    story.append(Paragraph("Apps 폴더 (Num 3으로 진입)", s_h2))
    story.append(grid_4x3(
        [
            [("계산기", "Num 7"), ("메모장", "Num 8"), ("탐색기", "Num 9")],
            [("작업관리자", "Num 4"), ("화면캡처", "Num 5"), ("CMD", "Num 6")],
            [("Shortcuts →", "Num 1"), ("YouTube", "Num 2"), ("Google", "Num 3")],
        ],
        footer_wide=("← Back", "Num 0"),
        footer_right=("", "Num ."),
    ))
    story.append(sp())

    story.append(Paragraph("Shortcuts 폴더 (Apps에서 Num 1로 진입)", s_h2))
    story.append(grid_4x3(
        [
            [("복사", "Num 7"), ("붙여넣기", "Num 8"), ("되돌리기", "Num 9")],
            [("잘라내기", "Num 4"), ("전체선택", "Num 5"), ("다시실행", "Num 6")],
            [("저장", "Num 1"), ("스크린샷", "Num 2"), ("PC 잠금", "Num 3")],
        ],
        footer_wide=("← Back", "Num 0"),
        footer_right=("", "Num ."),
    ))
    story.append(sp())
    story.append(tip_box(
        "<b>4행 버튼은 자동 배치됩니다.</b> "
        "Num 0 위치(← Back)는 비루트 폴더에서 비어있으면 상위 폴더 이동 버튼이 자동 배치됩니다. "
        "Num . 위치는 모든 폴더에서 비어있으면 이전 폴더로 돌아가기 버튼이 자동 배치됩니다."
    ))

    story.append(sp())
    story.append(Paragraph("예제 폴더 (첫 실행 시 자동 추가)", s_h2))
    story.append(tbl(
        ["폴더 이름", "내용"],
        [
            ["Media", "미디어 컨트롤 — 재생/정지, 볼륨, 음소거, 마이크, Now Playing, 장치 전환"],
            ["폴더", "자주 쓰는 폴더 바로 열기 — 사진, 문서, 다운로드, 바탕화면"],
            ["가상 데스크톱", "Windows 가상 데스크톱 단축키 — 전환, 생성, 닫기, 작업 보기"],
        ],
        col_widths=[35 * mm, 125 * mm],
    ))
    story.append(Paragraph(
        "버전 업그레이드 시 새로운 예제 폴더가 자동 추가됩니다. "
        "같은 이름의 폴더가 이미 있으면 중복 추가되지 않습니다.",
        s_note,
    ))

    # =========================================================================
    # 5. 내 버튼 만들기
    # =========================================================================
    story.append(Paragraph("5. 내 버튼 만들기", s_h1))
    story.append(Paragraph(
        "버튼을 <b>마우스 우클릭</b> → <b>Edit Button</b>을 누르면 편집 창이 열립니다.",
        s_body,
    ))
    story.append(sp())

    story.append(Paragraph("버튼 우클릭 메뉴", s_h2))
    story.append(tbl(
        ["메뉴", "설명"],
        [
            ["Edit Button", "버튼의 액션, 아이콘, 라벨 등을 편집"],
            ["Clear Button", "버튼을 빈 상태로 초기화"],
            ["Copy Button", "버튼 설정을 클립보드에 복사"],
            ["Paste Button", "복사한 설정을 이 버튼에 붙여넣기"],
        ],
        col_widths=[40 * mm, 120 * mm],
    ))
    story.append(sp())

    story.append(Paragraph("버튼 드래그 앤 드롭", s_h2))
    story.append(Paragraph(
        "버튼을 <b>좌클릭한 채로 드래그</b>하면 다른 버튼과 위치를 교환할 수 있습니다. "
        "빈 자리에 드롭하면 이동, 다른 버튼 위에 드롭하면 서로 위치 교환됩니다.",
        s_body,
    ))
    story.append(sp())

    story.append(Paragraph("액션 타입 — 무엇을 할 수 있나요?", s_h2))
    story.append(tbl(
        ["하고 싶은 것", "액션 타입", "예시"],
        [
            ["프로그램 실행", "Launch App", "notepad.exe, chrome.exe"],
            ["단축키 보내기", "Hotkey", "ctrl+c, alt+f4, win+l"],
            ["텍스트 자동 입력", "Text Input", "자주 쓰는 문장, 이메일 주소"],
            ["웹사이트 열기", "Open URL", "https://youtube.com"],
            ["폴더 열기 (탐색기)", "Open Folder", "%USERPROFILE%\\Documents"],
            ["셸 명령 실행", "Run Command", "ipconfig, shutdown /s /t 0"],
            ["여러 동작 연속 실행", "Macro", "녹화 또는 수동 편집"],
            ["음악/볼륨/마이크", "Media Control", "재생, 음소거, 장치 전환 등"],
            ["CPU/RAM 확인", "System Monitor", "(실시간 자동 업데이트)"],
            ["다른 폴더로 이동", "Navigate Folder", "폴더 목록에서 선택"],
            ["상위 폴더로", "Navigate Parent", "현재 폴더의 부모로 이동"],
            ["이전 폴더로", "Navigate Back", "방문 기록에서 뒤로 이동"],
        ],
        col_widths=[40 * mm, 38 * mm, 82 * mm],
    ))
    story.append(sp())

    story.append(Paragraph("앱 찾기 기능 (Find App)", s_h3))
    story.append(Paragraph(
        "Launch App 편집 시 <b>Find App...</b> 버튼을 누르면 현재 실행 중인 프로세스와 "
        "시작 메뉴 바로가기 목록에서 앱을 선택할 수 있습니다. "
        "선택하면 경로, 작업 디렉터리, 아이콘이 자동으로 채워집니다.",
        s_body,
    ))
    story.append(sp())

    story.append(Paragraph("버튼 꾸미기", s_h2))
    story.append(tbl(
        ["항목", "설명"],
        [
            ["Label", "버튼에 표시할 이름 (비우면 액션 기본 텍스트가 표시됨)"],
            ["Icon", "아이콘 이미지 (png, jpg, svg, ico). 아이콘 위에 글씨가 겹쳐 표시됩니다"],
            ["Label Color", "글씨 색상 — 색상 버튼 클릭 또는 #ff0000 같은 색상코드 입력"],
            ["Font Size", "글씨 크기 — 0으로 두면 설정의 기본값 사용 (기본 10px)"],
        ],
        col_widths=[35 * mm, 125 * mm],
    ))
    story.append(sp())
    story.append(tip_box(
        "<b>텍스트가 길면 자동 스크롤!</b> "
        "버튼 폭을 초과하는 긴 텍스트는 자동으로 좌우 마키 스크롤됩니다. "
        "Now Playing(현재 재생 곡), 오디오 장치 이름 등에 유용합니다."
    ))

    # =========================================================================
    # 6. 미디어 컨트롤
    # =========================================================================
    story.append(Paragraph("6. 미디어 컨트롤 상세", s_h1))
    story.append(Paragraph(
        "Media Control 액션은 10가지 커맨드를 제공합니다.",
        s_body,
    ))
    story.append(tbl(
        ["커맨드", "기능", "추가 설명"],
        [
            ["Play / Pause", "재생 / 일시정지 토글", "상태에 따라 아이콘 자동 전환"],
            ["Next Track", "다음 곡", ""],
            ["Previous Track", "이전 곡", ""],
            ["Stop", "정지", ""],
            ["Volume Up", "볼륨 업", ""],
            ["Volume Down", "볼륨 다운", ""],
            ["Mute / Unmute", "음소거 토글", "상태에 따라 아이콘 자동 전환"],
            ["Mic Mute", "마이크 음소거 토글", "상태에 따라 아이콘 자동 전환"],
            ["Now Playing", "현재 재생 곡 표시", "클릭 시 재생/일시정지"],
            ["Audio Device Switch", "오디오 출력 장치 순환 전환", "현재 장치 이름 표시"],
        ],
        col_widths=[40 * mm, 45 * mm, 75 * mm],
    ))
    story.append(sp())

    story.append(Paragraph("상태별 아이콘 · 라벨 커스터마이징", s_h2))
    story.append(Paragraph(
        "Play/Pause, Mute, Mic Mute 버튼은 현재 상태에 따라 아이콘과 라벨이 자동 전환됩니다. "
        "버튼 편집에서 각 상태별로 아이콘과 라벨을 개별 설정할 수 있습니다.",
        s_body,
    ))
    story.append(tbl(
        ["커맨드", "상태 1 (아이콘/라벨)", "상태 2 (아이콘/라벨)"],
        [
            ["Play / Pause", "재생 중: Pause 아이콘/라벨", "정지 중: Play 아이콘/라벨"],
            ["Mute", "음소거됨: Mute 아이콘/라벨", "음소거 해제: Unmute 아이콘/라벨"],
            ["Mic Mute", "마이크 꺼짐: Mic Off 아이콘/라벨", "마이크 켜짐: Mic On 아이콘/라벨"],
        ],
        col_widths=[35 * mm, 62 * mm, 63 * mm],
    ))

    # =========================================================================
    # 7. 매크로
    # =========================================================================
    story.append(Paragraph("7. 매크로", s_h1))
    story.append(Paragraph(
        "여러 동작을 순서대로 실행합니다. 수동으로 단계를 편집하거나, "
        "실제 입력을 녹화하여 자동 생성할 수 있습니다.",
        s_body,
    ))
    story.append(sp())

    story.append(Paragraph("8가지 단계 타입", s_h2))
    story.append(tbl(
        ["단계", "설명", "예시"],
        [
            ["Hotkey", "키 조합 전송", "ctrl+c, alt+tab"],
            ["Text Input", "텍스트 입력 (클립보드 모드 지원)", "Hello World"],
            ["Delay", "대기 시간 (밀리초)", "500ms"],
            ["Key Down", "키 누르기 (유지)", "shift 누른 채로..."],
            ["Key Up", "키 떼기", "...shift 떼기"],
            ["Mouse Down", "마우스 버튼 누르기 (좌표 지정)", "좌클릭 (100, 200)"],
            ["Mouse Up", "마우스 버튼 떼기 (좌표 지정)", "좌클릭 해제"],
            ["Mouse Scroll", "마우스 스크롤 (좌표 + 방향)", "아래로 3칸"],
        ],
        col_widths=[35 * mm, 60 * mm, 65 * mm],
    ))
    story.append(sp())
    story.append(Paragraph("▲▼ 버튼으로 단계 순서를 변경할 수 있습니다.", s_note))
    story.append(sp())

    story.append(Paragraph("매크로 녹화", s_h2))
    story.append(Paragraph(
        "버튼 편집 → Macro 선택 → <b>Record</b> 버튼을 누르면 "
        "키보드와 마우스 입력이 자동으로 기록됩니다.",
        s_body,
    ))
    story.append(tbl(
        ["키", "동작"],
        [
            ["F9", "녹화 중지 — 기록된 단계가 매크로에 추가됨"],
            ["Escape", "녹화 취소 — 기록 폐기"],
        ],
        col_widths=[40 * mm, 120 * mm],
    ))
    story.append(sp())
    story.append(tip_box(
        "녹화 중에는 플로팅 창이 표시되어 이벤트 수와 경과 시간을 확인할 수 있습니다. "
        "동작 사이의 지연 시간도 자동으로 기록됩니다."
    ))

    # =========================================================================
    # 8. 폴더 관리
    # =========================================================================
    story.append(Paragraph("8. 폴더 관리", s_h1))
    story.append(Paragraph(
        "버튼을 폴더별로 정리할 수 있습니다. "
        "폴더는 무한 중첩이 가능하여 원하는 만큼 버튼을 구성할 수 있습니다.",
        s_body,
    ))
    story.append(sp())

    story.append(Paragraph("폴더 트리 (좌측 패널)", s_h2))
    story.append(Paragraph(
        "왼쪽 패널에 폴더 트리가 표시됩니다. "
        "타이틀 바의 ☰ 버튼으로 숨기기/보이기를 전환할 수 있습니다.",
        s_body,
    ))
    story.append(sp())

    story.append(Paragraph("폴더 우클릭 메뉴", s_h3))
    story.append(tbl(
        ["메뉴", "설명"],
        [
            ["New Sub-Folder", "선택한 폴더 아래에 하위 폴더 생성"],
            ["Rename", "폴더 이름 변경"],
            ["Edit (Mapped Apps)", "자동 전환용 앱 매핑 편집"],
            ["Export Folder", "폴더를 JSON 파일로 내보내기 (아이콘 포함)"],
            ["Import Folder", "JSON 파일에서 하위 폴더로 가져오기"],
            ["Move Up / Move Down", "같은 레벨에서 폴더 순서 변경"],
            ["Delete", "폴더 삭제"],
        ],
        col_widths=[45 * mm, 115 * mm],
    ))
    story.append(sp())

    story.append(Paragraph("폴더 드래그 앤 드롭", s_h3))
    story.append(Paragraph(
        "폴더 트리에서 폴더를 드래그하여 다른 폴더 아래로 이동하거나 순서를 변경할 수 있습니다.",
        s_body,
    ))
    story.append(sp())

    story.append(Paragraph("폴더 내보내기 / 가져오기", s_h2))
    story.append(Paragraph(
        "개별 폴더를 JSON 파일로 저장하고 불러올 수 있습니다. "
        "다른 PC로 버튼 구성을 옮기거나, 다른 사람과 공유할 때 유용합니다.",
        s_body,
    ))
    story.append(Paragraph("  \u2022  내보내기: 폴더 + 하위 폴더 + 버튼 + 아이콘이 모두 포함됩니다", s_bullet))
    story.append(Paragraph("  \u2022  가져오기: 아이콘이 자동 복원되고, ID가 재생성되어 충돌이 방지됩니다", s_bullet))
    story.append(sp())

    story.append(Paragraph("Navigate Parent vs Navigate Back", s_h2))
    story.append(tbl(
        ["기능", "동작", "기본 키"],
        [
            ["Navigate Parent", "폴더 트리에서 현재 폴더의 부모로 이동", "Num 0"],
            ["Navigate Back", "방문 기록에서 이전 폴더로 되돌아가기 (최대 50개)", "Num ."],
        ],
        col_widths=[40 * mm, 80 * mm, 40 * mm],
    ))
    story.append(sp())
    story.append(Paragraph(
        "Navigate Back은 어떤 폴더에서 왔는지 기억합니다. "
        "예를 들어, 자동 전환으로 이동한 경우에도 이전 폴더로 돌아갈 수 있습니다.",
        s_note,
    ))

    story.append(Paragraph("자동 폴더 전환", s_h2))
    story.append(Paragraph(
        "폴더에 앱을 매핑하면, 해당 앱이 활성화될 때 자동으로 폴더가 전환됩니다.",
        s_body,
    ))
    story.append(Paragraph("  1. 폴더 트리에서 폴더 우클릭 → <b>Edit (Mapped Apps)</b>", s_bullet))
    story.append(Paragraph("  2. 프로그램 이름 추가 (예: chrome.exe)", s_bullet))
    story.append(Paragraph(
        '     <b>Find App...</b> 버튼으로 실행 중인 프로세스에서 바로 선택 가능',
        s_bullet2,
    ))
    story.append(Paragraph("  3. Settings에서 <b>Auto-switch</b> 활성화 (기본 ON)", s_bullet))
    story.append(sp())
    story.append(tip_box(
        "<b>자동 포커스:</b> 매핑된 앱이 있는 폴더에서 핫키/텍스트 입력/매크로를 실행하면, "
        "해당 앱이 자동으로 포커스된 후 실행됩니다. "
        "키 입력이 올바른 앱에 전달되도록 보장합니다."
    ))

    # =========================================================================
    # 9. 창 다루기
    # =========================================================================
    story.append(Paragraph("9. 창 다루기", s_h1))

    story.append(tbl(
        ["조작", "방법"],
        [
            ["창 이동", "상단 타이틀 바를 드래그"],
            ["크기 조절", "창 가장자리를 드래그 (8방향)"],
            ["숨기기/보이기", "Num Lock 토글 (Shortcut Mode)"],
            ["투명도 조절", "상단 바 슬라이더 (20%~100%)"],
            ["트레이로 보내기", "▼ 버튼 또는 창 닫기 버튼 (종료 아님!)"],
            ["창 다시 표시", "트레이 아이콘 더블클릭"],
            ["위치 초기화", "트레이 우클릭 → Reset Position"],
            ["완전 종료", "트레이 우클릭 → Quit"],
        ],
        col_widths=[40 * mm, 120 * mm],
    ))
    story.append(sp())

    story.append(Paragraph("타이틀 바 구성", s_h2))
    story.append(tbl(
        ["위치", "요소", "설명"],
        [
            ["왼쪽", "☰ 버튼", "폴더 트리 패널 표시/숨기기"],
            ["중앙", "폴더 이름", "현재 폴더 이름 표시"],
            ["오른쪽", "투명도 슬라이더", "창 투명도 실시간 조절"],
            ["오른쪽", "▼ 버튼", "트레이로 최소화"],
            ["전체", "우클릭", "Settings / Export Config / Import Config"],
        ],
        col_widths=[25 * mm, 40 * mm, 95 * mm],
    ))
    story.append(sp())

    story.append(Paragraph("시스템 트레이", s_h2))
    story.append(Paragraph("트레이 아이콘 우클릭 메뉴:", s_body))
    story.append(tbl(
        ["메뉴", "설명"],
        [
            ["Show", "창 표시"],
            ["Settings", "설정 창 열기"],
            ["Reset Position", "창 위치를 주 모니터 중앙 상단으로 초기화"],
            ["Quit", "앱 완전 종료"],
        ],
        col_widths=[40 * mm, 120 * mm],
    ))
    story.append(sp())
    story.append(warn_box(
        "창의 X 버튼(닫기)은 <b>종료가 아닙니다.</b> "
        "트레이로 최소화되며, 앱은 백그라운드에서 계속 실행됩니다. "
        "완전히 종료하려면 트레이 우클릭 → Quit을 사용하세요."
    ))

    # =========================================================================
    # 10. 설정
    # =========================================================================
    story.append(Paragraph("10. 설정 (Settings)", s_h1))
    story.append(Paragraph(
        "타이틀 바 우클릭 → <b>Settings</b> 또는 트레이 아이콘 → <b>Settings</b>",
        s_body,
    ))
    story.append(sp())

    story.append(Paragraph("Grid Layout (격자 설정)", s_h2))
    story.append(tbl(
        ["설정", "설명", "기본값"],
        [
            ["Button Size", "버튼 한 변의 크기", "100px"],
            ["Button Spacing", "버튼 사이 간격", "8px"],
            ["Default Font", "버튼 라벨 기본 폰트", "시스템 기본"],
            ["Default Font Size", "버튼 라벨 기본 크기", "10px"],
        ],
        col_widths=[40 * mm, 80 * mm, 40 * mm],
    ))
    story.append(sp())

    story.append(Paragraph("Behavior (동작 설정)", s_h2))
    story.append(tbl(
        ["설정", "설명", "기본값"],
        [
            ["Input Mode", "Widget Mode (마우스 전용) / Shortcut Mode (넘패드)", "Widget"],
            ["Auto-switch", "활성 앱에 따라 폴더 자동 전환", "ON"],
            ["Always on top", "다른 창 위에 항상 표시", "ON"],
        ],
        col_widths=[40 * mm, 80 * mm, 40 * mm],
    ))
    story.append(sp())

    story.append(Paragraph("Appearance (외관 설정)", s_h2))
    story.append(tbl(
        ["설정", "설명", "기본값"],
        [
            ["Theme", "테마 선택 (10종)", "Dark"],
            ["Opacity", "창 투명도 (20%~100%)", "100%"],
        ],
        col_widths=[40 * mm, 80 * mm, 40 * mm],
    ))
    story.append(sp())

    story.append(Paragraph("사용 가능한 테마 (10종)", s_h3))
    themes = [
        ["Dark", "어두운 기본 테마"],
        ["Light", "밝은 테마"],
        ["Solarized Light", "Solarized 계열 밝은 테마"],
        ["Midnight", "깊은 남색 테마"],
        ["Emerald", "에메랄드 녹색 테마"],
        ["Violet", "보라색 테마"],
        ["Nord", "Nord 색상 체계"],
        ["Dracula", "Dracula 색상 체계"],
        ["Amber", "호박색 워밍 테마"],
        ["Cyber", "사이버펑크 스타일"],
    ]
    story.append(tbl(
        ["테마", "설명"],
        themes,
        col_widths=[45 * mm, 115 * mm],
    ))

    # =========================================================================
    # 11. 설정 백업/복원
    # =========================================================================
    story.append(Paragraph("11. 설정 백업 / 복원", s_h1))

    story.append(Paragraph("전체 설정", s_h2))
    story.append(Paragraph(
        "타이틀 바 우클릭에서 전체 설정을 JSON 파일로 내보내거나 불러올 수 있습니다.",
        s_body,
    ))
    story.append(Paragraph("  \u2022  <b>Export Config</b> — 모든 폴더, 버튼, 설정, 아이콘을 JSON으로 저장", s_bullet))
    story.append(Paragraph("  \u2022  <b>Import Config</b> — JSON에서 불러와 기존 설정을 덮어쓰기", s_bullet))
    story.append(sp())

    story.append(Paragraph("개별 폴더", s_h2))
    story.append(Paragraph(
        "폴더 트리 우클릭에서 개별 폴더를 내보내거나 가져올 수 있습니다.",
        s_body,
    ))
    story.append(Paragraph("  \u2022  <b>Export Folder</b> — 해당 폴더 + 하위 폴더 + 아이콘을 JSON으로 저장", s_bullet))
    story.append(Paragraph("  \u2022  <b>Import Folder</b> — JSON에서 하위 폴더로 가져오기", s_bullet))
    story.append(sp())
    story.append(Paragraph(
        "설정 파일 위치: %APPDATA%\\SoftDeck\\config.json",
        s_note,
    ))

    # =========================================================================
    # 12. 게임할 때
    # =========================================================================
    story.append(Paragraph("12. 게임할 때", s_h1))
    story.append(tbl(
        ["게임 화면 모드", "넘패드 조작", "창 보임"],
        [
            ["보더리스 (창모드)", "O", "O"],
            ["전체화면 (Exclusive)", "O", "X"],
        ],
        col_widths=[55 * mm, 50 * mm, 55 * mm],
    ))
    story.append(sp())
    story.append(Paragraph(
        "대부분의 게임은 보더리스 모드를 사용하므로 정상 동작합니다.",
        s_body,
    ))
    story.append(tip_box(
        "<b>포커스 보호:</b> SoftDeck 버튼을 클릭해도 게임 포커스가 빠지지 않습니다. "
        "게임 중에 앱을 실행하면 실행된 앱에 자동으로 포커스가 전달됩니다."
    ))

    # =========================================================================
    # 13. 자주 묻는 질문
    # =========================================================================
    story.append(Paragraph("13. 자주 묻는 질문", s_h1))

    faq = [
        (
            "넘패드로도 조작할 수 있나요?",
            "네, Settings에서 Input Mode를 Shortcut Mode로 변경하세요. "
            "넘패드 키가 버튼에 매핑되어 키보드만으로 조작할 수 있습니다.",
        ),
        (
            "버튼이 12개로 부족합니다.",
            "폴더를 만들어서 용도별로 나누세요. 폴더 안에 폴더를 무한히 만들 수 있습니다. "
            "Navigate Folder 액션으로 폴더 간 이동 버튼을 만들 수 있습니다.",
        ),
        (
            "설정을 다른 PC로 옮기고 싶어요.",
            "타이틀 바 우클릭 → Export Config로 JSON 파일로 저장한 후, "
            "다른 PC에서 Import Config로 불러오세요. 아이콘도 함께 포함됩니다.",
        ),
        (
            "창이 안 보여요.",
            "Shortcut Mode에서는 Num Lock이 ON이면 창이 숨겨집니다. "
            "Num Lock을 끄거나, 트레이 아이콘을 더블클릭하세요.",
        ),
        (
            "특정 앱에서 단축키가 안 먹어요.",
            "폴더에 해당 앱을 매핑(Edit → Mapped Apps)하면, "
            "핫키/텍스트/매크로 실행 시 해당 앱이 자동으로 포커스됩니다.",
        ),
        (
            "매크로로 마우스 조작도 기록할 수 있나요?",
            "네, Record 버튼을 눌러 녹화하면 키보드와 마우스 입력이 모두 기록됩니다. "
            "마우스 클릭 좌표, 스크롤, 키 입력, 대기 시간이 자동으로 저장됩니다.",
        ),
    ]
    for q, a in faq:
        story.append(KeepTogether([
            Paragraph(f"<b>Q. {q}</b>", s_body),
            Paragraph(f"A. {a}", ParagraphStyle(
                "FAQ_A", fontName="Malgun", fontSize=10, leading=16,
                textColor=GRAY, leftIndent=16, spaceAfter=10,
            )),
        ]))

    # =========================================================================
    # 빠른 참조
    # =========================================================================
    story.append(hr())
    story.append(Paragraph("빠른 참조", s_h1))

    story.append(Paragraph("넘패드 키 (Shortcut Mode, Num Lock OFF)", s_h2))
    story.append(tbl(
        ["키", "동작"],
        [
            ["Num 7 / 8 / 9", "1행 버튼 실행"],
            ["Num 4 / 5 / 6", "2행 버튼 실행"],
            ["Num 1 / 2 / 3", "3행 버튼 실행"],
            ["Num 0", "상위 폴더로 이동 (Navigate Parent)"],
            ["Num .", "이전 폴더로 돌아가기 (Navigate Back)"],
            ["Num Lock 토글", "버튼 모드 ↔ 숫자 모드 전환 + 창 표시/숨김"],
        ],
        col_widths=[45 * mm, 115 * mm],
    ))
    story.append(sp())

    story.append(Paragraph("마우스 조작", s_h2))
    story.append(tbl(
        ["조작", "동작"],
        [
            ["버튼 좌클릭", "버튼 실행"],
            ["버튼 우클릭", "편집 / 초기화 / 복사 / 붙여넣기"],
            ["버튼 드래그", "다른 버튼과 위치 교환"],
            ["타이틀 바 드래그", "창 이동"],
            ["타이틀 바 우클릭", "설정 / 내보내기 / 가져오기"],
            ["창 가장자리 드래그", "크기 조절"],
            ["폴더 트리 클릭", "폴더 이동"],
            ["폴더 트리 우클릭", "폴더 생성/편집/삭제/내보내기/가져오기"],
            ["폴더 트리 드래그", "폴더 이동/순서 변경"],
            ["트레이 더블클릭", "창 다시 표시"],
            ["트레이 우클릭", "표시 / 설정 / 위치 초기화 / 종료"],
        ],
        col_widths=[45 * mm, 115 * mm],
    ))

    # Build
    doc.build(story)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    out = str(Path(__file__).resolve().parent / "SoftDeck가이드.pdf")
    build_pdf(out)
