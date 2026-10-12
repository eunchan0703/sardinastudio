# 홈페이지를 찍어 내는 도구.
#
# 게임이 다섯이고 언어가 둘이라 손으로 쓰면 스무 장이 넘는다 — 머리말·메뉴·바닥글이
# 장마다 흩어지면 게임을 하나 늘릴 때마다 그만큼 고쳐야 하고, 반드시 어긋난다.
# 그래서 «게임 표» 한 곳만 고치고 이 파일을 돌린다.
#
#   python3 _gen.py && python3 _check.py
#
# 찍는 것 (전부 한/영 짝, 이름은 옛 주소 그대로 — 플레이 콘솔이 이 주소들을 물고 있다):
#   index · <게임>.html · support · delete-account · privacy(본문은 손글, 껍데기만)
#   + 404.html · sitemap.xml
#
# 스크린샷은 우리가 담지 않고 Play 스토어 CDN 을 그대로 가리킨다 — 저장소도
# 페이지 트래픽도 늘지 않는다. 주소는 스토어 페이지의 «스크린샷 이미지» img
# 에서 뽑았다(shots 값).
#
# 2026-10 2차 시안 — «너무 어수선하다» 를 받고 덜어냈다. 한 장에 큰 문장 하나·그림 하나·
# 단추 하나, 색은 잉크와 강조색 하나. 꼬리표·숫자 상자·장식 그림은 넣지 않는다.
# 근거와 참고 사이트는 REDESIGN_NOTES.md.

import datetime, hashlib, html, io, json, os, re
from urllib.parse import quote

OUT = os.path.dirname(os.path.abspath(__file__))

# 절대 주소 — og:image · hreflang · canonical · sitemap 은 상대 주소를 못 쓴다.
# 도메인을 붙이면 이 두 줄만 바꾼다.
SITE = "https://eunchan0703.github.io/sardinastudio/"
BASE = "/sardinastudio/"
MAIL = "sardina.chans@gmail.com"
# 찍는 날의 해. 손으로 적어 두면 해가 바뀌어도 아무도 안 고친다.
YEAR = datetime.date.today().year


def _hash(name):
    # 정적 파일 주소에 내용 해시를 붙인다. 브라우저·CDN 이 옛 파일을 물고 있어
    # «고쳤는데 화면이 그대로» 가 반복됐다 — 내용이 바뀌면 주소가 바뀌므로
    # 강제 새로고침 없이도 새 것을 받는다.
    return hashlib.md5(io.open(os.path.join(OUT, name), "rb").read()).hexdigest()[:8]


CSS_V = _hash("style.css")
JS_V = _hash("site.js")

# 웹폰트 — Pretendard(OFL) 를 jsDelivr 에서 받는다. 버전을 못박고(1.3.9, 2023-11 배포)
# SRI 로 내용까지 묶는다. «dynamic-subset» 이라 화면에 쓰인 글자 묶음만 받는다.
# ⚠ 2026-08 에는 «외부 폰트 없음(트래픽 최소)» 이 사장님 지시였다(커밋 3571de3).
#   다시 여쭙는 중 — False 로 두면 시스템 폰트(애플 산돌고딕·맑은 고딕)로 돌아가고,
#   다른 곳은 하나도 안 바뀐다. 첫 방문에 약 350~380KB 를 더 받는다(2026-10-13 실측).
WEBFONT = True
FONT_CSS = ("https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/"
            "pretendardvariable-dynamic-subset.css")
FONT_SRI = "sha384-uR1wgObmx89ZQ4VVXHdzjbDJZ1PvBK01K+E3GebmaBKdZ87qRJvBWPoPbzWeEd5T"

# ── 스튜디오 표 — 회사 정보는 여기만 ───────────────────────────────────────
# 비어 있으면 화면에 아예 안 나온다. «준비 중» 같은 빈 자리를 공개 화면에 띄우지 않는다.
# 위치(도시·주소)는 사장님 지시로 사이트 어디에도 안 적는다(2026-10-13).
STUDIO = dict(
    # TODO(사장님): 히어로 문구·소개 문구는 초안이다. 사실이 아닌 것은 안 적었다
    #   (장르는 게임 표가 근거).
    ko=dict(
        hero="손끝으로 즐기는<br><span>작은 즐거움</span>",
        lede="Sardina Studio 가 만든 모바일 게임을 만나 보세요.",
        about=("Sardina Studio 는 모바일 게임을 만드는 스튜디오입니다. 고양이를 위한 게임부터 "
               "워드 퍼즐, 레트로 감성의 아케이드까지 — 짧게 켜도 즐거운 게임을 만듭니다."),
    ),
    en=dict(
        hero="Little joys,<br><span>right at your fingertips</span>",
        lede="Mobile games made by Sardina Studio.",
        about=("Sardina Studio is a mobile game studio. From games made for cats to word "
               "puzzles and retro arcade — games that are fun even in a short break."),
    ),
    # TODO(사장님): SNS 가 생기면 (이름, 주소) 로 넣는다. 예: ("YouTube", "https://…")
    sns=[],
    # TODO(사장님): 사업자 정보. (한국어 이름, 영어 이름, 값) — 값이 None 인 줄은 안 나온다.
    #   «주소» 칸은 위치를 안 적기로 해서 뺐다. 법적으로 적어야 하면 그때 줄을 더한다.
    biz=[
        ("상호", "Company", None),
        ("대표자", "CEO", None),
        ("사업자등록번호", "Business registration no.", None),
        ("통신판매업 신고번호", "Mail-order business no.", None),
    ],
)

# ── 게임 표 — 여기만 고친다 ─────────────────────────────────────────────
# 한 줄 = 홈 타일 · 게임 쪽 · 다른 게임 줄 · 고객지원 선택칸 · 사이트맵.
# shot_wide — 스크린샷이 가로(540×306)면 True, 세로(540×960)면 False.
#   두 비율은 CDN 에서 실제로 받아 잰 값이다(2026-10-13). width/height 를 맞춰 둬야
#   그림이 늦게 와도 자리가 안 흔들린다.
# facts — 게임 쪽 «정보» 목록의 «특징» 줄에만 글자로 쓴다(꼬리표로 그리지 않는다).
GAMES = [
    dict(
        slug="catbat", accent="#e98783", icon="game_cat.png", shot_wide=True,
        store="https://play.google.com/store/apps/details?id=com.BigSmileMen.Cat",
        platforms=("Android",),
        ko=dict(
            name="냥방망이",
            tagline="집사야, 나도 게임하고 싶다.",
            blurb="사랑스러운 우리 냥이에게도 취미 하나. 화면 위를 도망 다니는 "
                  "장난감을 앞발로 탁 잡는 사이 즐거움과 활력이 따라오고, 덤으로 "
                  "반사 신경까지 단련됩니다. 최고의 집사가 되어 주세요.",
            facts=["캐주얼", "고양이 전용", "전체이용가"],
        ),
        en=dict(
            name="Cat Bat",
            tagline="Hey human — I want to play too.",
            blurb="Give your cat a hobby of their own. A toy darts across the screen, "
                  "a paw comes down: fun, energy, and sharper reflexes in the bargain. "
                  "Be the best human they could ask for.",
            facts=["Casual", "Made for cats", "Everyone"],
        ),
        shots=[
            "https://play-lh.googleusercontent.com/Gx7TE359GExQnS5H4u6v67pArgjYBpCVvtt1KVg1vdBCOazkcX5oZOtWyQk9Ov5Os2sjxfMpw1mk06BpaSid",
            "https://play-lh.googleusercontent.com/kPeURQOfDJtQLodKMdKCePQgV0ItGO9smmbJOLFPQABhHOcR7f2Fcd77ElbDK8elRBBu9-Yvhi_AwuiS-i3I4W0",
            "https://play-lh.googleusercontent.com/LxNz7uhWk_BQt7jjoayAc55Dx3XyoGSOacIXJmx74gbGhSdoRF0Z_G1IiEIVwGabq5nJQfJ9Z85ttos-YfDO",
            "https://play-lh.googleusercontent.com/pzOF79B9WyZNZVJYZNCp9KLge5VU-qtehb1jD1yj7QSXyYKnkqkwK1IgWUJf-g9-rgjNawmcKA28hMisEoeY",
        ],
    ),
    dict(
        slug="catbat2", accent="#f07a2b", icon="game_cat2.png", shot_wide=True,
        store="https://play.google.com/store/apps/details?id=com.silverchan.catbat2",
        platforms=("Android",),
        ko=dict(
            name="냥방망이 2",
            tagline="집사야, 나도 게임하고 싶다 — 이번엔 3D 로.",
            blurb="우리 냥이의 취미가 입체가 됐습니다. 속이 통째로 3D 라 장난감이 "
                  "다가왔다 멀어지고 옆으로 빠져나갑니다. 앞발이 거리까지 재야 하니 "
                  "더 오래, 더 신나게 놉니다. 최고의 집사가 되어 주세요.",
            facts=["3D", "캐주얼", "고양이 전용"],
        ),
        en=dict(
            name="Cat Bat 2",
            tagline="Hey human — I want to play too. In 3D this time.",
            blurb="Your cat's hobby just gained depth. The whole thing is 3D inside, so "
                  "the toy drifts closer, backs away and slips past the side. A paw now "
                  "has to judge distance too — longer play, more excitement. "
                  "Be the best human they could ask for.",
            facts=["3D", "Casual", "Made for cats"],
        ),
        shots=[
            "https://play-lh.googleusercontent.com/YJLPNsr2TK0SSgSqXtcidsJc2QRHDlheD7D6I9b_HuJuFGlvsZ1cVUoe375aPE39rntO1zmAh-11KWoqkho_7w",
            "https://play-lh.googleusercontent.com/l4pgDHpSVbv0TdZluCAFDNQ6NdJZLEOPSJf211ztCGrVB7ZuSlANyqD8SSXCRjsdjse8VMa6msn1XdPLaPpN",
            "https://play-lh.googleusercontent.com/aq9WO7LbSHxqNTgenOa78LagqA-Avgis7z80Z0-Ve-C-1A-3oCQMxX3cUGZfY_hQZQelvhOF8QbkuEddZDUB",
            "https://play-lh.googleusercontent.com/XbpNNYp-PKuCJwkItvbIGqOSn0496bc6AbB_E6Tg3wkIcWXiPkiI2KYP5LbcV3SNlEriEPggTnK4emTsANCC",
        ],
    ),
    dict(
        slug="wordria", accent="#7c4dbe", icon="game_wordria.png", shot_wide=False,
        store="https://play.google.com/store/apps/details?id=com.sardinastudio.wordria",
        platforms=("Android",),
        ko=dict(
            name="워드리아",
            tagline="쓸어서 단어를 만들고, 판을 채웁니다.",
            blurb="쉽고 재미있게 당신의 두뇌를 영리하게 만드세요. "
                  "알파벳을 스와이프하여 단어를 조합하면 빈칸이 채워집니다. "
                  "수많은 스테이지와 특별 스테이지, 다양한 보너스까지 전부 무료 — "
                  "인터넷이 없는 곳에서도 그대로 이어집니다.",
            facts=["워드 퍼즐", "오프라인 플레이", "무료"],
        ),
        en=dict(
            name="WORDRIA",
            tagline="Swipe the letters, fill the board.",
            blurb="Swipe across the scattered letters to spell a word and the empty "
                  "squares fill in, one row at a time. An easy, enjoyable way to keep "
                  "your mind sharp — plenty of stages, special stages and bonuses, all "
                  "free, and it keeps going with no internet at all.",
            facts=["Word puzzle", "Plays offline", "Free"],
        ),
        shots=[
            "https://play-lh.googleusercontent.com/mVXFewaU-mYI1fruET46EgMn72q2zeER8GxNQ_0Q3gkrzN7kayuvZE88z2u7kZzC4HR4I1JaOAnadDwwRSR73w",
            "https://play-lh.googleusercontent.com/jdiMQ_Gh4_e3KwuIqtneXYUyAgI2nQTv7EkCP5juzaBEW9l7NgQP160JJKw1koQum2Uybo5WFiYJ5jRwhU7W",
            "https://play-lh.googleusercontent.com/9ufoeybIGzxAVZaw1r5c_bxQDFjcBfjBg_94rP8mni-XPLZYNKAkROcBD0zlPdcegQtRW1lrZxRNUFiQbfjnfU0",
        ],
    ),
    dict(
        slug="boombrick", accent="#3ac6e8", icon="game_boombrick.png", shot_wide=False,
        store="https://play.google.com/store/apps/details?id=com.BigSmileMen.BlockDestroy",
        platforms=("Android",),
        ko=dict(
            name="붐브릭",
            tagline="우주로 날아간 토끼 «개토» 와 함께 벽돌을 부숩니다.",
            blurb="개토와 함께 우주에 있는 벽돌을 부셔주세요! "
                  "레트로 감성의 그래픽과 시원한 타격감을 느껴보세요. "
                  "높은 점수를 획득해 1등에 도전하세요! "
                  "출퇴근길·등하굣길 심심할 때 시간을 순삭하세요.",
            facts=["아케이드", "벽돌깨기", "레트로 도트"],
        ),
        en=dict(
            name="BoomBrick",
            tagline="Smashing space bricks with Gaeto the rabbit.",
            blurb="Bounce the ball up and take the floating bricks out one by one. "
                  "Retro pixel art, a satisfying pop on every hit, and a high score to "
                  "chase all the way to first place. One run fits neatly into a commute.",
            facts=["Arcade", "Brick breaker", "Retro pixel art"],
        ),
        shots=[
            "https://play-lh.googleusercontent.com/RGjkScrcPV2Z9KipwLjpCfAD9fwIAOT6jiK1hFSpcxI-znz0Dti4Z2Q7WuPE2dPVtH2lvGO-60Q7GHofqc_v4A",
            "https://play-lh.googleusercontent.com/O314RmP7G3M9USJNAY56LJlBHfhnbs-XDdE2KV8CWkl1jjW1lo181ugw61pXixVNhsIo1sxWqScNKcKUQf5u4cE",
            "https://play-lh.googleusercontent.com/XtbfI8MMRWAjYN0wFoMK13IW4fJ7X25SobHDu3g4ELU8PmCuoymbVhllPFHXThkvk_8lBXcUnxa3OYxZHEb40w",
        ],
    ),
    dict(
        slug="spacesmasher", accent="#6d5cf0", icon="game_spacesmasher.png", shot_wide=False,
        store="https://play.google.com/store/apps/details?id=com.sardinastudio.spacesmasher",
        platforms=("Android",),
        ko=dict(
            name="우주뿌셔",
            tagline="좌우로 두드려 행성을 부수는 캐주얼 아케이드.",
            blurb="좌우를 번갈아 두드려 쏟아지는 낙석을 피하고 행성을 부숩니다. "
                  "1:1 대전으로 다른 사람과 같은 판을 동시에 달릴 수도 있습니다.",
            facts=["캐주얼 아케이드", "1:1 대전"],
        ),
        en=dict(
            name="Space Smasher",
            tagline="Tap left and right to smash planets.",
            blurb="Alternate taps to dodge the falling rocks and break the planets. "
                  "A 1v1 mode lets you run the very same board against someone else.",
            facts=["Casual arcade", "1v1 versus"],
        ),
        shots=[],
    ),
]

# ── 문구 표 ─────────────────────────────────────────────────────────────
# topics — 메일 틀. 게임 쪽 «버그 신고» 링크와 고객지원의 메일 쓰기가 같은 틀을 쓴다
#   (JS 에도 이 표를 JSON 으로 넘긴다 — 두 벌로 적으면 어긋난다). {game} 에 게임 이름.
#   계정 삭제 틀은 delete-account 장이 묻는 것(게임 이름 · 로그인 구글 계정)과 같은 것을
#   묻는다 — 둘이 다르면 사용자가 어느 쪽을 따라야 할지 모른다.
STR = dict(
    ko=dict(
        lang="ko", skip="본문 바로가기", nav_label="주 메뉴", lang_label="언어 선택",
        home="홈", games="게임", support="고객지원", about="스튜디오 소개",
        privacy="개인정보처리방침", delete="계정 삭제", faq="자주 묻는 질문",
        foot_nav="바닥글 메뉴", contact="문의",
        cta="게임 보기", store="Google Play에서 다운로드",
        shots="스크린샷", prev="이전 스크린샷", next="다음 스크린샷",
        shot_alt="{name} 스크린샷 {i}/{n}", about_game="게임 소개", info="정보",
        i_dev="개발", i_platform="플랫폼", i_features="특징", i_download="다운로드",
        i_privacy="개인정보",
        help="도움이 필요하세요?", h_bug="버그 신고", h_other="문의 메일",
        more_games="다른 게임",
        s_title="고객지원", s_h1="무엇을 도와드릴까요?",
        s_lede="먼저 자주 묻는 질문을 확인해 주세요. 해결되지 않으면 메일로 알려 주세요.",
        c_h="메일 문의",
        c_p="게임과 문의 종류를 고르면 제목과 적을 내용이 채워진 메일이 열립니다.",
        c_game="게임", c_none="고르지 않음", c_topic="문의 종류", c_btn="메일 쓰기",
        c_subject="제목", c_copy="주소 복사", c_copied="주소를 복사했습니다.",
        c_copy_fail="복사하지 못했습니다. 주소를 직접 선택해 주세요.",
        c_note="메일 앱이 열리지 않으면 위 주소로 직접 보내 주세요.",
        nf_title="페이지를 찾을 수 없습니다", nf_p="주소가 바뀌었거나 없는 페이지입니다.",
        topics=dict(
            bug=("버그 신고",
                 "게임: {game}\n기기 모델: \nAndroid 버전: \n앱 버전: \n"
                 "언제, 무엇을 하다가 생겼나요: \n\n(스크린샷이나 화면 녹화가 있으면 첨부해 주세요)"),
            payment=("결제·환불 문의",
                     "게임: {game}\nGoogle Play 주문 번호: \n구매한 날짜와 시각: \n상품: \n내용: "),
            restore=("데이터 복구 문의",
                     "게임: {game}\n기기 모델: \n구글 계정 연결 여부: \n상황: "),
            delete=("계정 삭제 요청",
                    "게임: {game}\n로그인에 쓰신 구글 계정 주소: \n\n"
                    "(본인 확인을 위해 로그인에 쓰신 구글 계정으로 보내 주세요)"),
            other=("기타 문의", "게임: {game}\n내용: "),
        ),
    ),
    en=dict(
        lang="en", skip="Skip to content", nav_label="Main menu", lang_label="Language",
        home="Home", games="Games", support="Support", about="About us",
        privacy="Privacy Policy", delete="Delete account", faq="FAQ",
        foot_nav="Footer menu", contact="Contact",
        cta="See our games", store="Get it on Google Play",
        shots="Screenshots", prev="Previous screenshot", next="Next screenshot",
        shot_alt="{name} screenshot {i} of {n}", about_game="About the game", info="Info",
        i_dev="Developer", i_platform="Platform", i_features="Features",
        i_download="Download", i_privacy="Privacy",
        help="Need a hand?", h_bug="Report a bug", h_other="Email us",
        more_games="More games",
        s_title="Support", s_h1="How can we help?",
        s_lede="Please check the FAQ first. If it does not answer your question, email us.",
        c_h="Email us",
        c_p="Pick the game and the topic, and your mail app opens with the subject and "
            "the details we need already filled in.",
        c_game="Game", c_none="Not selected", c_topic="Topic", c_btn="Write email",
        c_subject="Subject", c_copy="Copy address", c_copied="Address copied.",
        c_copy_fail="Could not copy. Please select the address manually.",
        c_note="If no mail app opens, send your message to the address above.",
        nf_title="Page not found", nf_p="The address may have changed, or the page does not exist.",
        topics=dict(
            bug=("Bug report",
                 "Game: {game}\nDevice model: \nAndroid version: \nApp version: \n"
                 "What happened, and when: \n\n(Screenshots or a screen recording help a lot.)"),
            payment=("Payment or refund",
                     "Game: {game}\nGoogle Play order number: \nDate and time of purchase: \n"
                     "Item: \nDetails: "),
            restore=("Data recovery",
                     "Game: {game}\nDevice model: \nGoogle account linked (yes/no): \n"
                     "What happened: "),
            delete=("Account deletion request",
                    "Game: {game}\nGoogle account you signed in with: \n\n"
                    "(To verify it is you, please send this from that same Google account.)"),
            other=("Other question", "Game: {game}\nMessage: "),
        ),
    ),
)

# Google Play 고객센터 «Google Play에서 환불 요청하기» — 환불 안내의 1차 근거
# (2026-10-13 확인: 구매 후 48시간이 지난 항목은 개발자에게 문의하라고 안내한다).
# 우리 정책이 아니라 구글 정책이라 우리 말로 옮겨 적지 않고 링크로 넘긴다.
REFUND_URL = dict(ko="https://support.google.com/googleplay/answer/15574897?hl=ko",
                  en="https://support.google.com/googleplay/answer/15574897?hl=en")


# ── 도움 함수 ───────────────────────────────────────────────────────────
def esc(s):
    return html.escape(s, quote=True)


def page_name(slug, lang):
    return f"{slug}.html" if lang == "ko" else f"{slug}-en.html"


def other(lang):
    return "en" if lang == "ko" else "ko"


def home_href(lang):
    # 한국어 홈은 «./» — 옛 장들이 쓰던 주소 그대로
    return "./" if lang == "ko" else "index-en.html"


def index_href(lang):
    return "index.html" if lang == "ko" else "index-en.html"


def abs_url(path):
    return SITE if path in ("index.html", "./") else SITE + path


def mailto(subject, body=""):
    # RFC 6068 — 줄바꿈은 %0D%0A. & 는 HTML 속성 안이라 &amp; 로 쓴다.
    q = "subject=" + quote(subject, safe="")
    if body:
        q += "&amp;body=" + quote(body.replace("\n", "\r\n"), safe="")
    return f"mailto:{MAIL}?{q}"


def topic_mail(lang, topic, game_name=""):
    label, body = STR[lang]["topics"][topic]
    prefix = f"[{game_name}] " if game_name else "[Sardina Studio] "
    return mailto(prefix + label, body.format(game=game_name))


def icon(name, size=20, cls="i"):
    return (f'<svg class="{cls}" width="{size}" height="{size}" aria-hidden="true" '
            f'focusable="false"><use href="#i-{name}"/></svg>')


# 아이콘은 꼭 필요한 넷만 — 화살표 둘(스크린샷 앞뒤), 바깥 링크, 복사. 장식 그림은 안 쓴다.
SPRITE = """<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <defs>
    <symbol id="i-left" viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
    <symbol id="i-right" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
    <symbol id="i-ext" viewBox="0 0 24 24"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
    <symbol id="i-copy" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="8.5" y="8.5" width="11.5" height="11.5" rx="2"/><path d="M15.5 8.5V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v9.5a1 1 0 0 0 1 1h3.5"/></g></symbol>
  </defs>
</svg>"""


# ── 껍데기 ───────────────────────────────────────────────────────────────
def head(lang, title, desc, path, alt_path, noindex=False):
    """path / alt_path — 이 장과 짝 장의 파일 이름. hreflang 로 서로를 가리킨다."""
    ko_path, en_path = (path, alt_path) if lang == "ko" else (alt_path, path)
    lines = ['<meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
             f"<title>{esc(title)}</title>",
             f'<meta name="description" content="{esc(desc)}">']
    if noindex:
        lines.append('<meta name="robots" content="noindex">')
    lines += ['<meta name="theme-color" content="#ffffff">',
              '<meta name="color-scheme" content="light">']
    if not noindex:
        lines.append(f'<link rel="canonical" href="{abs_url(path)}">')
    if alt_path:
        lines += [f'<link rel="alternate" hreflang="ko" href="{abs_url(ko_path)}">',
                  f'<link rel="alternate" hreflang="en" href="{abs_url(en_path)}">',
                  f'<link rel="alternate" hreflang="x-default" href="{abs_url(ko_path)}">']
    locale, alt_locale = ("ko_KR", "en_US") if lang == "ko" else ("en_US", "ko_KR")
    # og:image 하나를 모든 장이 같이 쓴다 — 카카오톡·메신저 미리보기용.
    lines += ['<meta property="og:type" content="website">',
              '<meta property="og:site_name" content="Sardina Studio">',
              f'<meta property="og:title" content="{esc(title)}">',
              f'<meta property="og:description" content="{esc(desc)}">',
              f'<meta property="og:url" content="{abs_url(path)}">',
              f'<meta property="og:image" content="{SITE}assets/og.jpg">',
              '<meta property="og:image:width" content="1200">',
              '<meta property="og:image:height" content="630">',
              '<meta property="og:image:alt" content="Sardina Studio">',
              f'<meta property="og:locale" content="{locale}">',
              f'<meta property="og:locale:alternate" content="{alt_locale}">',
              '<meta name="twitter:card" content="summary_large_image">',
              '<link rel="icon" href="assets/favicon-32.png" sizes="32x32" type="image/png">',
              '<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">']
    if WEBFONT:
        lines += ['<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>',
                  f'<link rel="stylesheet" href="{FONT_CSS}" integrity="{FONT_SRI}" crossorigin>']
    # «js» 표시를 그리기 전에 단다 — 안 그러면 JS 없을 때용 화면이 한 번 번쩍인다.
    lines += [f'<link rel="stylesheet" href="style.css?v={CSS_V}">',
              "<script>document.documentElement.className='js'</script>",
              f'<script src="site.js?v={JS_V}" defer></script>']
    return "<head>\n" + "\n".join(lines) + "\n</head>"


def lang_switch(lang, self_href, alt_href):
    # 지금 장의 짝으로 바로 간다 — 홈으로 튕기면 방침을 읽던 사람이 길을 잃는다
    # (참고한 국내 사이트 한 곳이 홈으로 튕겼다. REDESIGN_NOTES.md).
    ko_href, en_href = (self_href, alt_href) if lang == "ko" else (alt_href, self_href)
    cur_ko = ' aria-current="true"' if lang == "ko" else ""
    cur_en = ' aria-current="true"' if lang == "en" else ""
    return (f'<div class="lang" role="group" aria-label="{STR[lang]["lang_label"]}">'
            f'<a href="{ko_href}" hreflang="ko" lang="ko"{cur_ko}>KO</a>'
            f'<a href="{en_href}" hreflang="en" lang="en"{cur_en}>EN</a></div>')


def header(lang, here, self_href, alt_href):
    # 메뉴는 둘뿐이다(게임 · 고객지원). 폭이 좁아도 한 줄에 들어가므로 햄버거 단추가 없다
    # — 단추 하나를 눌러야 메뉴가 보이는 것보다 늘 보이는 쪽이 덜 헷갈린다.
    s = STR[lang]
    g_cur = ' class="is-here"' if here in [g["slug"] for g in GAMES] else ""
    sup_cur = ' aria-current="page"' if here == "support" else ""
    return f"""<header class="site-header">
  <div class="bar">
    <a class="brand" href="{home_href(lang)}">
      <img src="assets/logo_ink.png" alt="" width="44" height="36">
      <span class="brand-name">Sardina Studio</span>
    </a>
    <nav class="nav" aria-label="{s['nav_label']}">
      <a href="{index_href(lang)}#games"{g_cur}>{s['games']}</a>
      <a href="{page_name('support', lang)}"{sup_cur}>{s['support']}</a>
    </nav>
    {lang_switch(lang, self_href, alt_href)}
  </div>
</header>"""


def footer(lang, self_href, alt_href):
    s = STR[lang]
    sns = "".join(f'<a href="{esc(u)}" rel="noopener">{esc(n)}</a>' for n, u in STUDIO["sns"])
    biz = [(ko if lang == "ko" else en, v) for ko, en, v in STUDIO["biz"] if v]
    biz_html = ""
    if biz:
        biz_html = ('\n    <p class="ft-biz">' + " · ".join(
            f"{esc(k)} {esc(v)}" for k, v in biz) + "</p>")
    # 계정 삭제는 바닥글에 둔다 — 구글이 «눈에 띄고 찾기 쉬울 것» 을 요구한다
    # (`delete_page` 머리말). 모든 장에 깔리는 자리가 여기다.
    # 개인정보처리방침은 굵게 — 국내 사이트 관행이고, 찾는 사람이 바로 본다.
    return f"""<footer class="site-footer">
  <div class="ft">
    <div class="ft-row">
      <nav class="ft-links" aria-label="{s['foot_nav']}">
        <a href="{page_name('support', lang)}">{s['support']}</a>
        <a class="ft-strong" href="{page_name('privacy', lang)}">{s['privacy']}</a>
        <a href="{page_name('delete-account', lang)}">{s['delete']}</a>
        <a href="mailto:{MAIL}">{MAIL}</a>{sns}
      </nav>
      {lang_switch(lang, self_href, alt_href)}
    </div>
    <p class="ft-copy">© {YEAR} Sardina Studio</p>{biz_html}
  </div>
</footer>"""


def shell(lang, *, title, desc, path, alt, body, here=None, body_class="", noindex=False):
    s = STR[lang]
    if alt is None:
        # 짝이 없는 장(404)은 언어 단추가 각 언어의 홈으로 간다
        self_href, alt_href = home_href(lang), home_href(other(lang))
    else:
        self_href = home_href(lang) if path.startswith("index") else path
        alt_href = home_href(other(lang)) if alt.startswith("index") else alt
    if 'id="main"' not in body:
        # 손글 본문(<main class="page">)은 건드리지 않으므로 건너뛰기 표적을 앞에 둔다
        body = '<div id="main" tabindex="-1"></div>\n' + body
    return f"""<!DOCTYPE html>
<html lang="{s['lang']}" class="no-js">
{head(lang, title, desc, path, alt, noindex=noindex)}
<body class="{body_class}">
<a class="skip" href="#main">{s['skip']}</a>
{SPRITE}

{header(lang, here, self_href, alt_href)}

{body}

{footer(lang, self_href, alt_href)}
</body>
</html>
"""


# ── 홈 ───────────────────────────────────────────────────────────────────
# 큰 문장 하나 · 단추 하나 · 그림 한 줄(아이콘) → 같은 모양의 게임 타일 → 짧은 소개.
def index_page(lang):
    s = STR[lang]
    st = STUDIO[lang]
    # 히어로의 아이콘 줄은 그림이다(아래 타일이 같은 링크를 갖는다) — 읽기 프로그램에는 숨긴다
    icons = "\n".join(
        f'      <li><img src="assets/{g["icon"]}" alt="" width="160" height="160"></li>'
        for g in GAMES)
    tiles = "\n".join(
        f"""      <li><a class="tile" href="{page_name(g['slug'], lang)}">
        <img class="tile-icon" src="assets/{g['icon']}" alt="" width="160" height="160" loading="lazy">
        <span class="tile-text"><span class="tile-name">{esc(g[lang]['name'])}</span>
        <span class="tile-line">{esc(g[lang]['tagline'])}</span></span></a></li>"""
        for g in GAMES)
    body = f"""<main id="main">

<section class="hero">
  <div class="container hero-inner">
    <h1>{st['hero']}</h1>
    <p class="lede">{esc(st['lede'])}</p>
    <a class="btn btn-primary btn-lg" href="#games">{s['cta']}</a>
    <ul class="icon-row" aria-hidden="true">
{icons}
    </ul>
  </div>
</section>

<section class="section" id="games" aria-labelledby="games-h">
  <div class="container">
    <h2 class="sec-title" id="games-h">{s['games']}</h2>
    <ul class="tiles">
{tiles}
    </ul>
  </div>
</section>

<section class="section about" id="about" aria-labelledby="about-h">
  <div class="container narrow">
    <h2 class="sec-title" id="about-h">{s['about']}</h2>
    <p class="about-p">{esc(st['about'])}</p>
    <p class="about-mail" id="contact">{s['contact']} <a href="mailto:{MAIL}">{MAIL}</a></p>
  </div>
</section>

</main>"""
    names = " · ".join(g[lang]["name"] for g in GAMES)
    desc = (f"Sardina Studio — {names}. 모바일 게임 스튜디오." if lang == "ko"
            else f"Sardina Studio — {names}. A mobile game studio.")
    return shell(lang, title="Sardina Studio", desc=desc,
                 path=index_href(lang), alt=index_href(other(lang)), body=body,
                 here="home", body_class="p-home")


# ── 게임 한 쪽 ───────────────────────────────────────────────────────────
# 히어로(아이콘 · 이름 · 한 줄 · 단추 하나) → 스크린샷 띠 → 소개 → 정보 → 도움 링크 → 다른 게임.
def srcset(u, cand):
    return ", ".join(f"{u}=w{c}-rj {c}w" for c in cand)


def shot_img(g, u, i, n, lang, eager=False):
    # 스크린샷은 스토어 CDN 에서 곧바로 받는다 (우리 트래픽 0).
    #  · -rj = JPEG. 안 붙이면 PNG 를 주는데 같은 장이 620KB vs 114KB 다
    #    (-rw 는 무손실 WebP 라 오히려 162KB. 이 CDN 에서는 JPEG 가 답이다)
    #  · srcset 으로 화면 크기·배율에 맞는 장만 받는다
    #  · sizes 는 style.css 의 .shot-track img 크기와 짝이다 — 한쪽만 바꾸면 흐려지거나 커진다
    wide = g["shot_wide"]
    w, h = (540, 306) if wide else (540, 960)
    cand = (400, 540, 800, 1080) if wide else (270, 400, 540, 720)
    sizes = "(max-width: 640px) 84vw, 560px" if wide else "(max-width: 640px) 203px, 248px"
    alt = STR[lang]["shot_alt"].format(name=g[lang]["name"], i=i, n=n)
    # 첫 장은 첫 화면 안에 든다 — 지연 로드하지 않는다
    load = "" if eager else 'loading="lazy" '
    return (f'<img src="{u}=w{cand[1]}-rj" srcset="{srcset(u, cand)}" sizes="{sizes}" '
            f'alt="{esc(alt)}" width="{w}" height="{h}" {load}decoding="async">')


def game_page(g, lang):
    s = STR[lang]
    t = g[lang]
    shots = g["shots"]
    n = len(shots)

    store = ""
    if g["store"]:
        # 구글 공식 배지 그림을 흉내 내지 않는다(배지는 고쳐 쓰지 말라는 지침) — 글자 단추.
        store = (f'<a class="btn btn-primary" href="{g["store"]}" rel="noopener">{s["store"]}'
                 f'<span class="sr-only"> — {esc(t["name"])}</span></a>')

    strip = ""
    if shots:
        imgs = "\n".join(f"      <li>{shot_img(g, u, i + 1, n, lang, eager=(i == 0))}</li>"
                         for i, u in enumerate(shots))
        track = "shot-track wide" if g["shot_wide"] else "shot-track"
        strip = f"""
<section class="shots" aria-labelledby="shots-h">
  <div class="container shots-head">
    <h2 class="sub-title" id="shots-h">{s['shots']}</h2>
    <div class="shot-nav">
      <button type="button" class="nav-btn" data-dir="-1" aria-label="{s['prev']}" aria-controls="shots-track">{icon('left', 18)}</button>
      <button type="button" class="nav-btn" data-dir="1" aria-label="{s['next']}" aria-controls="shots-track">{icon('right', 18)}</button>
    </div>
  </div>
  <ul class="{track}" id="shots-track" tabindex="0" aria-label="{s['shots']}">
{imgs}
  </ul>
</section>
"""

    plats = " · ".join(g["platforms"])
    rows = [(s["i_dev"], "Sardina Studio"), (s["i_platform"], esc(plats)),
            (s["i_features"], esc(" · ".join(t["facts"])))]
    if g["store"]:
        rows.append((s["i_download"],
                     f'<a href="{g["store"]}" rel="noopener">Google Play{icon("ext", 14)}</a>'))
    rows.append((s["i_privacy"], f'<a href="{page_name("privacy", lang)}">{s["privacy"]}</a>'))
    info = "\n".join(f"      <div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows)
    others = "\n".join(
        f"""      <li><a href="{page_name(o['slug'], lang)}"><img src="assets/{o['icon']}" alt="" width="160" height="160" loading="lazy"><span>{esc(o[lang]['name'])}</span></a></li>"""
        for o in GAMES if o is not g)

    body = f"""<main id="main">

<section class="g-hero">
  <div class="container g-head">
    <img class="g-icon" src="assets/{g['icon']}" alt="" width="160" height="160">
    <div class="g-text">
      <h1>{esc(t['name'])}</h1>
      <p class="g-line">{esc(t['tagline'])}</p>
      {store}
    </div>
  </div>
</section>
{strip}
<section class="section-sm">
  <div class="container narrow">
    <h2 class="sub-title">{s['about_game']}</h2>
    <p class="g-blurb">{esc(t['blurb'])}</p>

    <h2 class="sub-title">{s['info']}</h2>
    <dl class="info">
{info}
    </dl>

    <p class="help-row" id="help"><span>{s['help']}</span>
      <a href="{topic_mail(lang, 'bug', t['name'])}">{s['h_bug']}</a>
      <a href="{topic_mail(lang, 'other', t['name'])}">{s['h_other']}</a>
      <a href="{page_name('support', lang)}#faq">{s['faq']}</a>
      <a href="{page_name('delete-account', lang)}">{s['delete']}</a></p>
  </div>
</section>

<section class="section-sm more" aria-labelledby="more-h">
  <div class="container narrow">
    <h2 class="sub-title" id="more-h">{s['more_games']}</h2>
    <ul class="mini-row">
{others}
    </ul>
  </div>
</section>

</main>"""
    return shell(lang, title=t["name"] + " · Sardina Studio", desc=t["tagline"],
                 path=page_name(g["slug"], lang), alt=page_name(g["slug"], other(lang)),
                 body=body, here=g["slug"], body_class="p-game")


# ── 고객지원 ─────────────────────────────────────────────────────────────
def faq(lang):
    """자주 묻는 질문 — (묶음 id, 제목, [(질문 id, 질문, 답 HTML)]).

    답은 이미 공개한 문서(개인정보처리방침·계정 삭제)와 구글 공식 안내에서만 가져왔다.
    우리가 지킬지 모르는 약속(답장 기한·환불 보장·복구 보장)은 안 적는다
    (2026-08-30 «영업일 3일» 을 뺀 것과 같은 이유)."""
    dele, priv = page_name("delete-account", lang), page_name("privacy", lang)
    bug_mail, pay_mail, rest_mail = (topic_mail(lang, k) for k in ("bug", "payment", "restore"))
    if lang == "ko":
        return [
            ("bug", "버그·오류", [
                ("bug-report", "게임이 멈추거나 이상하게 동작해요.",
                 f"""<p>아래 내용을 함께 보내 주시면 원인을 찾는 데 큰 도움이 됩니다.</p>
<ul><li>게임 이름</li><li>기기 모델명과 Android 버전</li><li>앱 버전</li>
<li>언제, 무엇을 하다가 생겼는지</li><li>스크린샷이나 화면 녹화(있으면)</li></ul>
<p><a href="{bug_mail}">버그 신고 메일 쓰기</a></p>"""),
                ("app-version", "앱 버전은 어디서 보나요?",
                 "<p>Android <b>설정 › 애플리케이션</b>에서 게임을 고르면 화면 아래쪽에 버전이 "
                 "나옵니다. 기기마다 메뉴 이름은 조금 다를 수 있습니다.</p>"),
            ]),
            ("payment", "결제·환불", [
                ("missing-item", "결제했는데 아이템이 들어오지 않았어요.",
                 f"""<p>Google Play 영수증 메일에 있는 <b>주문 번호</b>와 게임 이름, 구매한 날짜와
시각을 적어 메일로 보내 주세요.</p>
<p><a href="{pay_mail}">결제 문의 메일 쓰기</a></p>"""),
                ("refund", "환불받고 싶어요.",
                 f"""<p>결제는 Google Play 가 처리하며, 스튜디오는 카드 정보를 받지 않습니다.
환불은 Google Play 고객센터의 <a href="{REFUND_URL['ko']}" rel="noopener">«Google Play에서 환불 요청하기»</a>
안내에 따라 요청하실 수 있습니다.</p>
<p>Google 은 구매한 지 48시간이 지난 항목은 개발자에게 문의하라고 안내합니다. 이때는
주문 번호를 적어 메일로 보내 주세요.</p>"""),
            ]),
            ("restore", "데이터 복구", [
                ("lost-progress", "기기를 바꾸거나 앱을 지웠더니 기록이 사라졌어요.",
                 f"""<p>서버 백업은 <b>구글 계정을 연결한 경우에만</b> 이루어집니다. 연결하지 않았다면
기록은 기기에만 저장되어, 앱을 지우면 함께 사라집니다
(<a href="{priv}#s3">개인정보처리방침 3항</a>).</p>
<p>구글 계정을 연결해 두셨는데 기록이 보이지 않으면 게임 이름과 상황을 적어 메일로 알려 주세요.</p>
<p><a href="{rest_mail}">복구 문의 메일 쓰기</a></p>"""),
            ]),
            ("account", "계정 삭제·개인정보", [
                ("delete", "계정과 데이터를 지우고 싶어요.",
                 f"""<p>요청하는 법과 지워지는 것·남는 것을 <a href="{dele}">계정 삭제</a> 안내에
정리해 두었습니다.</p>"""),
                ("ads", "맞춤 광고를 받고 싶지 않아요.",
                 f"""<p>Android <b>설정 › 개인정보 보호 › 광고</b>에서 광고 ID 를 삭제하거나 재설정할 수
있습니다. 자세한 내용은 <a href="{priv}#s7">개인정보처리방침 7항</a>을 보세요.</p>"""),
                ("data", "게임이 어떤 정보를 다루나요?",
                 f"""<p>스튜디오의 모든 게임에 적용되는 <a href="{priv}">개인정보처리방침</a>에 적었습니다.
게임별로 처리하는 항목은 각 게임의 Google Play 스토어 페이지 «데이터 보안» 항목에서
확인하실 수 있습니다.</p>"""),
            ]),
        ]
    return [
        ("bug", "Bugs & errors", [
            ("bug-report", "The game freezes or behaves oddly.",
             f"""<p>Sending these along helps us find the cause much faster:</p>
<ul><li>Game name</li><li>Device model and Android version</li><li>App version</li>
<li>When it happened and what you were doing</li><li>A screenshot or screen recording, if you have one</li></ul>
<p><a href="{bug_mail}">Email a bug report</a></p>"""),
            ("app-version", "Where do I find the app version?",
             "<p>In Android <b>Settings › Apps</b>, pick the game — the version is shown near the "
             "bottom. Menu names can differ slightly between devices.</p>"),
        ]),
        ("payment", "Payments & refunds", [
            ("missing-item", "I paid but did not receive my item.",
             f"""<p>Email us the <b>order number</b> from your Google Play receipt, the game name, and the
date and time of purchase.</p>
<p><a href="{pay_mail}">Email about a payment</a></p>"""),
            ("refund", "I would like a refund.",
             f"""<p>Payments are processed by Google Play; the studio never receives card details.
You can request a refund by following Google Play Help's
<a href="{REFUND_URL['en']}" rel="noopener">“Request a refund on Google Play”</a> guide.</p>
<p>Google asks you to contact the developer for items bought more than 48 hours ago. In that
case, email us with your order number.</p>"""),
        ]),
        ("restore", "Data recovery", [
            ("lost-progress", "I changed phones or reinstalled, and my progress is gone.",
             f"""<p>Cloud backup only happens <b>if you linked a Google account</b>. Without it, progress
is kept on the device only and is removed when the app is uninstalled
(<a href="{priv}#s3">Privacy Policy, section 3</a>).</p>
<p>If you did link a Google account and still cannot see your progress, email us with the game
name and what happened.</p>
<p><a href="{rest_mail}">Email about recovery</a></p>"""),
        ]),
        ("account", "Account & privacy", [
            ("delete", "I want to delete my account and data.",
             f"""<p>How to ask, and what is deleted or kept, is set out on the
<a href="{dele}">Delete your account</a> page.</p>"""),
            ("ads", "I do not want personalised ads.",
             f"""<p>On Android, go to <b>Settings › Privacy › Ads</b> to delete or reset your advertising
ID. See <a href="{priv}#s7">Privacy Policy, section 7</a> for details.</p>"""),
            ("data", "What information do the games handle?",
             f"""<p>It is set out in the <a href="{priv}">Privacy Policy</a>, which covers every game by
the studio. What each game handles is listed in the Data safety section of its Google Play
listing.</p>"""),
        ]),
    ]


def support_page(lang):
    s = STR[lang]
    groups = faq(lang)
    jump = "\n".join(f'      <a href="#{gid}">{esc(title)}</a>' for gid, title, _ in groups)
    faq_html = []
    for gid, title, items in groups:
        qs = "\n".join(
            f"""      <details class="faq" id="{qid}">
        <summary>{esc(q)}</summary>
        <div class="faq-body">{a}</div>
      </details>""" for qid, q, a in items)
        faq_html.append(f"""    <div class="faq-group" id="{gid}">
      <h3>{esc(title)}</h3>
{qs}
    </div>""")
    game_opts = "\n".join(
        f'          <option value="{esc(g[lang]["name"])}">{esc(g[lang]["name"])}</option>'
        for g in GAMES)
    topic_opts = "\n".join(
        f'          <option value="{k}">{esc(v[0])}</option>' for k, v in s["topics"].items())
    # 메일 틀은 파이썬 표 하나에서 나온다 — JS 에 따로 적으면 두 벌이 되어 어긋난다
    cfg = json.dumps(dict(
        mail=MAIL,
        topics={k: dict(label=v[0], body=v[1]) for k, v in s["topics"].items()},
        copied=s["c_copied"], copy_fail=s["c_copy_fail"],
    ), ensure_ascii=False).replace("</", "<\\/")
    generic = topic_mail(lang, "bug")

    body = f"""<main id="main">

<section class="page-head">
  <div class="container">
    <h1>{s['s_h1']}</h1>
    <p class="lede">{s['s_lede']}</p>
    <nav class="jump" aria-label="{s['faq']}">
{jump}
      <a href="#contact">{s['c_h']}</a>
    </nav>
  </div>
</section>

<section class="section-sm">
  <div class="container support-grid">
    <div class="faq-col" id="faq">
      <h2 class="sub-title">{s['faq']}</h2>
{chr(10).join(faq_html)}
    </div>

    <aside class="contact-box" id="contact" aria-labelledby="contact-h">
      <h2 class="sub-title" id="contact-h">{s['c_h']}</h2>
      <p class="cc-addr"><a href="mailto:{MAIL}">{MAIL}</a></p>
      <p class="cc-copy-row"><button type="button" class="btn btn-quiet btn-sm" data-copy="{MAIL}">{icon('copy', 16)}{s['c_copy']}</button>
        <span class="copy-status" role="status" aria-live="polite"></span></p>
      <div class="composer" data-composer>
        <p>{s['c_p']}</p>
        <label>{s['c_game']}
          <select name="game">
            <option value="">{s['c_none']}</option>
{game_opts}
          </select>
        </label>
        <label>{s['c_topic']}
          <select name="topic">
{topic_opts}
          </select>
        </label>
        <p class="composer-subject">{s['c_subject']}: <output data-subject></output></p>
        <a class="btn btn-primary btn-block" data-mailto href="{generic}">{s['c_btn']}</a>
      </div>
      <p class="cc-nojs"><a class="btn btn-primary btn-block" href="{generic}">{s['c_btn']}</a></p>
      <p class="cc-note">{s['c_note']}</p>
      <script type="application/json" id="composer-data">{cfg}</script>
    </aside>
  </div>
</section>

</main>"""
    desc = ("Sardina Studio 고객지원 — 자주 묻는 질문, 버그 신고, 결제·환불, 데이터 복구, 계정 삭제."
            if lang == "ko" else
            "Sardina Studio Support — FAQ, bug reports, payments and refunds, data recovery, account deletion.")
    return shell(lang, title=s["s_title"] + " · Sardina Studio", desc=desc,
                 path=page_name("support", lang), alt=page_name("support", other(lang)),
                 body=body, here="support", body_class="p-support")


# ── 계정 삭제 ────────────────────────────────────────────────────────────
def delete_page(lang):
    """
    계정 삭제 안내. **구글 플레이가 요구하는 웹 리소스다.**

    계정을 만들 수 있는 앱은 «앱 안 경로» 와 «웹 링크» 를 **둘 다** 내야 하고,
    웹 쪽은 «눈에 띄고 찾기 쉬워야» 한다. 개인정보처리방침 안에 한 줄로 묻어
    두면 그 조건을 못 채운다 — 그래서 장을 따로 뺐다.
    (support.google.com/googleplay/android-developer/answer/13327111)

    자동 삭제 시스템은 안 만든다. 구글이 «메일로 요청받는 것» 을 명시적으로
    허용한다 — *"a customer service email or a form they can submit a request
    through"*.

    ★ 2026-10 개편 때 <main> 안의 글은 한 글자도 안 바꿨다 — 법적 문구라 사장님 확인
      없이는 고치지 않는다. 바꾼 것은 껍데기(머리말·바닥글·스타일)뿐이다.
    """
    if lang == "ko":
        title = "계정 삭제"
        body = f"""<main class="page">
 <div class="read">

  <div class="hero doc">
    <p class="eyebrow">Sardina Studio</p>
    <h1>계정 삭제</h1>
    <p class="lede">Sardina Studio 게임의 계정과 저장된 데이터를
      <strong>삭제해 드립니다.</strong> 아래 주소로 메일 주시면 됩니다.</p>
  </div>

  <section id="how">
    <h2><span class="num">01</span> 요청하는 법</h2>

    <div class="callout">
      <p><strong><a href="mailto:{MAIL}?subject=계정%20삭제%20요청">{MAIL}</a></strong>
      으로 메일을 보내 주세요. 아래 둘을 적어 주시면 빠릅니다.</p>
    </div>

    <ul>
      <li><b>게임 이름</b> — 예: 우주뿌셔</li>
      <li><b>로그인에 쓰신 구글 계정 주소</b> — 그 계정으로 저장된 것을 찾습니다.</li>
    </ul>

    <p>본인 확인을 위해 <b>요청하신 메일 주소가 로그인에 쓰신 구글 계정과
    같아야 합니다.</b> 다르면 확인을 위해 한 번 더 여쭐 수 있습니다.</p>
  </section>

  <section id="what">
    <h2><span class="num">02</span> 무엇이 지워지나</h2>

    <table>
      <thead><tr><th>지워지는 것</th><th>남는 것</th></tr></thead>
      <tbody>
        <tr>
          <td>계정 식별자, 서버에 백업된 게임 기록(점수·재화·진행), 닉네임,
              순위표 기록, 우편함</td>
          <td>결제 영수증 — <b>법으로 5년간 보관해야 합니다</b>
              (전자상거래법). 게임 진행과는 이어지지 않습니다</td>
        </tr>
      </tbody>
    </table>

    <p><b>기기에 저장된 것은 앱을 지우면 함께 사라집니다.</b>
    서버 쪽만 이 요청으로 지워집니다.</p>
  </section>

  <section id="when">
    <h2><span class="num">03</span> 처리</h2>
    <p>요청을 확인한 뒤 처리하고 결과를 회신드립니다.
    한 번 지운 것은 <b>되돌릴 수 없습니다.</b></p>
  </section>

  <p class="back"><a href="{page_name('privacy', lang)}">← 개인정보처리방침</a></p>

 </div>
</main>"""
        desc = "Sardina Studio 게임의 계정 및 데이터 삭제를 요청하는 방법."
    else:
        title = "Delete your account"
        body = f"""<main class="page">
 <div class="read">

  <div class="hero doc">
    <p class="eyebrow">Sardina Studio</p>
    <h1>Delete your account</h1>
    <p class="lede">We will <strong>delete your account and saved data</strong>
      for any Sardina Studio game. Just send us an email.</p>
  </div>

  <section id="how">
    <h2><span class="num">01</span> How to request</h2>

    <div class="callout">
      <p>Email <strong><a href="mailto:{MAIL}?subject=Account%20deletion%20request">{MAIL}</a></strong>.
      Including the two items below helps us act faster.</p>
    </div>

    <ul>
      <li><b>Game name</b> — for example, Space Smasher</li>
      <li><b>The Google account you signed in with</b> — we use it to find your saved data.</li>
    </ul>

    <p>To verify it is really you, <b>please write from the same Google account
    you signed in with.</b> If it differs we may ask one follow-up question.</p>
  </section>

  <section id="what">
    <h2><span class="num">02</span> What gets deleted</h2>

    <table>
      <thead><tr><th>Deleted</th><th>Kept</th></tr></thead>
      <tbody>
        <tr>
          <td>Account identifier, game data backed up on our servers
              (scores, currency, progress), nickname, leaderboard entries, mailbox</td>
          <td>Purchase receipts — <b>Korean law requires us to keep these for
              5 years</b>. They are not linked back to your game progress</td>
        </tr>
      </tbody>
    </table>

    <p><b>Anything stored on your device is removed when you uninstall the app.</b>
    This request covers the server side.</p>
  </section>

  <section id="when">
    <h2><span class="num">03</span> After you send it</h2>
    <p>We process the request once we have confirmed it, and reply when it is done.
    Deletion <b>cannot be undone.</b></p>
  </section>

  <p class="back"><a href="{page_name('privacy', lang)}">← Privacy Policy</a></p>

 </div>
</main>"""
        desc = "How to request deletion of your Sardina Studio game account and data."

    return shell(lang, title=title + " · Sardina Studio", desc=desc,
                 path=page_name("delete-account", lang),
                 alt=page_name("delete-account", other(lang)),
                 body=body, here="delete", body_class="p-doc")


# ── 개인정보처리방침 — 손으로 쓴 본문, 껍데기만 갈아 끼운다 ───────────────
def privacy_page(lang):
    # 본문(<main>…</main>)·제목·설명은 파일에 적힌 그대로 옮긴다. 법적 문구라
    # 이 도구가 한 글자도 만들거나 고치지 않는다. 고칠 때는 html 파일의 <main> 안을 고친다.
    name = page_name("privacy", lang)
    src = io.open(os.path.join(OUT, name), encoding="utf-8").read()
    main = re.search(r"<main\b.*?</main>", src, flags=re.S).group(0)
    title = html.unescape(re.search(r"<title>(.*?)</title>", src, flags=re.S).group(1))
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)">', src).group(1))
    return shell(lang, title=title, desc=desc, path=name, alt=page_name("privacy", other(lang)),
                 body=main, here="privacy", body_class="p-doc p-privacy")


# ── 404 ──────────────────────────────────────────────────────────────────
def not_found_page():
    # 깃허브 페이지는 없는 주소에 이 장을 준다. 어느 깊이의 주소에서 뜰지 모르므로
    # 안쪽 주소를 전부 사이트 뿌리(/sardinastudio/…) 기준으로 바꿔 찍는다 — 안 그러면
    # style.css 가 상대 경로로 깨진다. <base> 는 안 쓴다: <base> 를 달면 아이콘의
    # <use href="#i-…"> 까지 다른 문서를 가리키게 되어 아이콘이 통째로 사라진다.
    k, e = STR["ko"], STR["en"]
    body = f"""<main id="main" class="nf">
  <div class="container narrow">
    <p class="nf-code">404</p>
    <h1>{k['nf_title']}</h1>
    <p>{k['nf_p']}</p>
    <p lang="en" class="nf-en">{e['nf_title']}. {e['nf_p']}</p>
    <p class="nf-links"><a class="btn btn-primary" href="./">{k['home']}</a>
      <a class="btn btn-quiet" href="index-en.html" lang="en">Home (English)</a></p>
  </div>
</main>"""
    page = shell("ko", title=k["nf_title"] + " · Sardina Studio", desc=k["nf_p"],
                 path="404.html", alt=None, body=body, body_class="p-404", noindex=True)
    page = re.sub(r'(href|src)="(?!https?:|mailto:|#|/)', lambda m: f'{m.group(1)}="{BASE}', page)
    return page.replace(f'"{BASE}./"', f'"{BASE}"')


# ── 사이트맵 ─────────────────────────────────────────────────────────────
def sitemap(pairs):
    # robots.txt 는 안 만든다 — 프로젝트 사이트라 /sardinastudio/robots.txt 는
    # 검색엔진이 안 읽는다(호스트 뿌리의 것만 읽는다). 사이트맵은 서치 콘솔에 직접 낸다.
    rows = []
    for ko, en in pairs:
        for p in (ko, en):
            rows.append(f"""  <url><loc>{abs_url(p)}</loc>
    <xhtml:link rel="alternate" hreflang="ko" href="{abs_url(ko)}"/>
    <xhtml:link rel="alternate" hreflang="en" href="{abs_url(en)}"/>
  </url>""")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(rows) + "\n</urlset>\n")


def write(name, text):
    with io.open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("  ", name)


if __name__ == "__main__":
    print("찍는다:")
    pairs = [("index.html", "index-en.html")]
    write("index.html", index_page("ko"))
    write("index-en.html", index_page("en"))
    for g in GAMES:
        write(page_name(g["slug"], "ko"), game_page(g, "ko"))
        write(page_name(g["slug"], "en"), game_page(g, "en"))
        pairs.append((page_name(g["slug"], "ko"), page_name(g["slug"], "en")))
    write("support.html", support_page("ko"))
    write("support-en.html", support_page("en"))
    write("delete-account.html", delete_page("ko"))
    write("delete-account-en.html", delete_page("en"))
    # 개인정보처리방침은 두 장을 먼저 다 읽고 나서 쓴다
    priv = {lang: privacy_page(lang) for lang in ("ko", "en")}
    write("privacy.html", priv["ko"])
    write("privacy-en.html", priv["en"])
    write("404.html", not_found_page())
    pairs += [("support.html", "support-en.html"),
              ("delete-account.html", "delete-account-en.html"),
              ("privacy.html", "privacy-en.html")]
    write("sitemap.xml", sitemap(pairs))
