# 게임 페이지를 찍어 내는 도구.
#
# 게임이 다섯이고 언어가 둘이라 손으로 쓰면 열 장이 된다 — 머리말·드롭다운·바닥글이
# 열 곳에 흩어지면 게임을 하나 늘릴 때마다 열 곳을 고쳐야 하고, 반드시 어긋난다.
# 그래서 «게임 표» 한 곳만 고치고 이 파일을 돌린다.
#
#   python _gen.py
#
# 스크린샷은 우리가 담지 않고 Play 스토어 CDN 을 그대로 가리킨다 — 저장소도
# 페이지 트래픽도 늘지 않는다. 주소는 스토어 페이지의 «스크린샷 이미지» img
# 에서 뽑았다(_shots 값).

import io, os, re

OUT = os.path.dirname(os.path.abspath(__file__))
MAIL = "lee.silver.chan@gmail.com"

# ── 게임 표 — 여기만 고친다 ─────────────────────────────────────────────
GAMES = [
    dict(
        slug="catbat", icon="game_cat.png", shot_wide=True,
        store="https://play.google.com/store/apps/details?id=com.BigSmileMen.Cat",
        ko=dict(
            name="냥방망이",
            tagline="집사야, 나도 게임하고 싶다.",
            blurb="사랑스러운 우리 냥이에게도 취미 하나. 화면 위를 도망 다니는 "
                  "장난감을 앞발로 탁 잡는 사이 즐거움과 활력이 따라오고, 덤으로 "
                  "반사 신경까지 단련됩니다. 최고의 집사가 되어 주세요.",
            facts=["캐주얼", "고양이 전용", "전체이용가", "Android"],
        ),
        en=dict(
            name="Cat Bat",
            tagline="Hey human — I want to play too.",
            blurb="Give your cat a hobby of their own. A toy darts across the screen, "
                  "a paw comes down: fun, energy, and sharper reflexes in the bargain. "
                  "Be the best human they could ask for.",
            facts=["Casual", "Made for cats", "Everyone", "Android"],
        ),
        shots=[
            "https://play-lh.googleusercontent.com/Gx7TE359GExQnS5H4u6v67pArgjYBpCVvtt1KVg1vdBCOazkcX5oZOtWyQk9Ov5Os2sjxfMpw1mk06BpaSid",
            "https://play-lh.googleusercontent.com/kPeURQOfDJtQLodKMdKCePQgV0ItGO9smmbJOLFPQABhHOcR7f2Fcd77ElbDK8elRBBu9-Yvhi_AwuiS-i3I4W0",
            "https://play-lh.googleusercontent.com/LxNz7uhWk_BQt7jjoayAc55Dx3XyoGSOacIXJmx74gbGhSdoRF0Z_G1IiEIVwGabq5nJQfJ9Z85ttos-YfDO",
            "https://play-lh.googleusercontent.com/pzOF79B9WyZNZVJYZNCp9KLge5VU-qtehb1jD1yj7QSXyYKnkqkwK1IgWUJf-g9-rgjNawmcKA28hMisEoeY",
        ],
    ),
    dict(
        slug="catbat2", icon="game_cat2.png", shot_wide=True,
        store="https://play.google.com/store/apps/details?id=com.silverchan.catbat2",
        ko=dict(
            name="냥방망이 2",
            tagline="집사야, 나도 게임하고 싶다 — 이번엔 3D 로.",
            blurb="우리 냥이의 취미가 입체가 됐습니다. 속이 통째로 3D 라 장난감이 "
                  "다가왔다 멀어지고 옆으로 빠져나갑니다. 앞발이 거리까지 재야 하니 "
                  "더 오래, 더 신나게 놉니다. 최고의 집사가 되어 주세요.",
            facts=["3D", "캐주얼", "고양이 전용", "Android"],
        ),
        en=dict(
            name="Cat Bat 2",
            tagline="Hey human — I want to play too. In 3D this time.",
            blurb="Your cat's hobby just gained depth. The whole thing is 3D inside, so "
                  "the toy drifts closer, backs away and slips past the side. A paw now "
                  "has to judge distance too — longer play, more excitement. "
                  "Be the best human they could ask for.",
            facts=["3D", "Casual", "Made for cats", "Android"],
        ),
        shots=[
            "https://play-lh.googleusercontent.com/YJLPNsr2TK0SSgSqXtcidsJc2QRHDlheD7D6I9b_HuJuFGlvsZ1cVUoe375aPE39rntO1zmAh-11KWoqkho_7w",
            "https://play-lh.googleusercontent.com/l4pgDHpSVbv0TdZluCAFDNQ6NdJZLEOPSJf211ztCGrVB7ZuSlANyqD8SSXCRjsdjse8VMa6msn1XdPLaPpN",
            "https://play-lh.googleusercontent.com/aq9WO7LbSHxqNTgenOa78LagqA-Avgis7z80Z0-Ve-C-1A-3oCQMxX3cUGZfY_hQZQelvhOF8QbkuEddZDUB",
            "https://play-lh.googleusercontent.com/XbpNNYp-PKuCJwkItvbIGqOSn0496bc6AbB_E6Tg3wkIcWXiPkiI2KYP5LbcV3SNlEriEPggTnK4emTsANCC",
        ],
    ),
    dict(
        slug="wordria", icon="game_wordria.png", shot_wide=False,
        store="https://play.google.com/store/apps/details?id=com.sardinastudio.wordria",
        ko=dict(
            name="워드리아",
            tagline="쓸어서 단어를 만들고, 판을 채웁니다.",
            blurb="쉽고 재미있게 당신의 두뇌를 영리하게 만드세요. "
                  "알파벳을 스와이프하여 단어를 조합하면 빈칸이 채워집니다. "
                  "수많은 스테이지와 특별 스테이지, 다양한 보너스까지 전부 무료 — "
                  "인터넷이 없는 곳에서도 그대로 이어집니다.",
            facts=["워드 퍼즐", "오프라인 플레이", "무료", "Android"],
        ),
        en=dict(
            name="WORDRIA",
            tagline="Swipe the letters, fill the board.",
            blurb="Swipe across the scattered letters to spell a word and the empty "
                  "squares fill in, one row at a time. An easy, enjoyable way to keep "
                  "your mind sharp — plenty of stages, special stages and bonuses, all "
                  "free, and it keeps going with no internet at all.",
            facts=["Word puzzle", "Plays offline", "Free", "Android"],
        ),
        shots=[
            "https://play-lh.googleusercontent.com/mVXFewaU-mYI1fruET46EgMn72q2zeER8GxNQ_0Q3gkrzN7kayuvZE88z2u7kZzC4HR4I1JaOAnadDwwRSR73w",
            "https://play-lh.googleusercontent.com/jdiMQ_Gh4_e3KwuIqtneXYUyAgI2nQTv7EkCP5juzaBEW9l7NgQP160JJKw1koQum2Uybo5WFiYJ5jRwhU7W",
            "https://play-lh.googleusercontent.com/9ufoeybIGzxAVZaw1r5c_bxQDFjcBfjBg_94rP8mni-XPLZYNKAkROcBD0zlPdcegQtRW1lrZxRNUFiQbfjnfU0",
        ],
    ),
    dict(
        slug="boombrick", icon="game_boombrick.png", shot_wide=False,
        store="https://play.google.com/store/apps/details?id=com.BigSmileMen.BlockDestroy",
        ko=dict(
            name="붐브릭",
            tagline="우주로 날아간 토끼 «개토» 와 함께 벽돌을 부숩니다.",
            blurb="개토와 함께 우주에 있는 벽돌을 부셔주세요! "
                  "레트로 감성의 그래픽과 시원한 타격감을 느껴보세요. "
                  "높은 점수를 획득해 1등에 도전하세요! "
                  "출퇴근길·등하굣길 심심할 때 시간을 순삭하세요.",
            facts=["아케이드", "벽돌깨기", "레트로 도트", "Android"],
        ),
        en=dict(
            name="BoomBrick",
            tagline="Smashing space bricks with Gaeto the rabbit.",
            blurb="Bounce the ball up and take the floating bricks out one by one. "
                  "Retro pixel art, a satisfying pop on every hit, and a high score to "
                  "chase all the way to first place. One run fits neatly into a commute.",
            facts=["Arcade", "Brick breaker", "Retro pixel art", "Android"],
        ),
        shots=[
            "https://play-lh.googleusercontent.com/RGjkScrcPV2Z9KipwLjpCfAD9fwIAOT6jiK1hFSpcxI-znz0Dti4Z2Q7WuPE2dPVtH2lvGO-60Q7GHofqc_v4A",
            "https://play-lh.googleusercontent.com/O314RmP7G3M9USJNAY56LJlBHfhnbs-XDdE2KV8CWkl1jjW1lo181ugw61pXixVNhsIo1sxWqScNKcKUQf5u4cE",
            "https://play-lh.googleusercontent.com/XtbfI8MMRWAjYN0wFoMK13IW4fJ7X25SobHDu3g4ELU8PmCuoymbVhllPFHXThkvk_8lBXcUnxa3OYxZHEb40w",
        ],
    ),
    dict(
        slug="spacesmasher", icon=None, shot_wide=False, store=None,
        ko=dict(
            name="우주뿌셔",
            tagline="좌우로 두드려 행성을 부수는 캐주얼 아케이드.",
            blurb="좌우를 번갈아 두드려 쏟아지는 낙석을 피하고 행성을 부숩니다. "
                  "1:1 대전으로 다른 사람과 같은 판을 동시에 달릴 수도 있습니다. "
                  "곧 출시합니다.",
            facts=["캐주얼 아케이드", "1:1 대전", "Android"],
        ),
        en=dict(
            name="Space Smasher",
            tagline="Tap left and right to smash planets.",
            blurb="Alternate taps to dodge the falling rocks and break the planets. "
                  "A 1v1 mode lets you run the very same board against someone else. "
                  "Coming soon.",
            facts=["Casual arcade", "1v1 versus", "Android"],
        ),
        shots=[],
    ),
]

STR = dict(
    ko=dict(
        home="./", home_label="홈", games="게임", contact="문의",
        privacy="개인정보처리방침", privacy_href="privacy.html",
        other_lang="EN", other_lang_href_suffix="-en.html", index="index.html",
        get="Google Play 에서 받기", soon="곧 출시",
        contact_note="버그·문의·개인정보 삭제 요청은 이 주소로 메일 주세요.",
        studio="사르디나 스튜디오", shots="스크린샷", back="← 게임 목록",
        title_suffix=" · 사르디나 스튜디오",
    ),
    en=dict(
        home="index-en.html", home_label="Home", games="Games", contact="Contact",
        privacy="Privacy Policy", privacy_href="privacy-en.html",
        other_lang="KO", other_lang_href_suffix=".html", index="index-en.html",
        get="Get it on Google Play", soon="Coming soon",
        contact_note="Bug reports, questions and data deletion requests — write to this address.",
        studio="Sardina Studio", shots="Screenshots", back="← All games",
        title_suffix=" · Sardina Studio",
    ),
)


def page_name(slug, lang):
    return f"{slug}.html" if lang == "ko" else f"{slug}-en.html"


def topbar(lang, here, other_href):
    s = STR[lang]
    items = "\n".join(
        f'            <a href="{page_name(g["slug"], lang)}">{g[lang]["name"]}</a>'
        for g in GAMES)
    return f"""<header class="topbar">
  <div class="topbar-inner">
    <a class="brand" href="{s['home']}">
      <img src="assets/logo.png" alt="">
      Sardina Studio
    </a>
    <nav class="navlinks">
      <div class="navmenu">
        <a href="{s['index']}#games">{s['games']}</a>
        <div class="dropdown">
          <div class="dropdown-inner">
{items}
          </div>
        </div>
      </div>
      <a href="{s['index']}#contact">{s['contact']}</a>
      <a class="lang" href="{other_href}">{s['other_lang']}</a>
    </nav>
  </div>
</header>"""


def footer(lang):
    s = STR[lang]
    other = "index-en.html" if lang == "ko" else "./"
    other_label = "English" if lang == "ko" else "한국어"
    return f"""<footer>
  <div class="footer-inner">
    <span>© 2026 Sardina Studio · Seoul, Korea</span>
    <div class="footer-links">
      <a href="{s['privacy_href']}">{s['privacy']}</a>
      <a href="{s['index']}#contact">{s['contact']}</a>
      <a href="{other}">{other_label}</a>
    </div>
  </div>
</footer>"""


def shell(lang, title, desc, body, here_other):
    s = STR[lang]
    return f"""<!DOCTYPE html>
<html lang="{'ko' if lang == 'ko' else 'en'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#fbfbfd">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="assets/logo_icon.png">
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="wrap">

{topbar(lang, None, here_other)}

{body}

{footer(lang)}

</div>
</body>
</html>
"""


def index_page(lang):
    s = STR[lang]
    cards = []
    for g in GAMES:
        t = g[lang]
        icon = (f'<img class="icon" src="assets/{g["icon"]}" alt="" width="128" height="128">'
                if g["icon"] else '<div class="icon blank"></div>')
        badge = "" if g["store"] else f'<span class="badge">{s["soon"]}</span>'
        cards.append(f"""      <a class="card" href="{page_name(g['slug'], lang)}">
        {icon}
        <div>
          <h2>{t['name']}{badge}</h2>
          <p>{t['tagline']}</p>
        </div>
      </a>""")
    body = f"""<main class="page">

  <div class="hero">
    <img class="logo" src="assets/logo.png" alt="{s['studio']}">
    <h1>Sardina Studio</h1>
  </div>

  <div class="section" id="games">
    <p class="section-label">{s['games']}</p>
    <div class="cards">
{chr(10).join(cards)}
    </div>
  </div>

  <div class="section" id="contact">
    <p class="section-label">{s['contact']}</p>
    <div class="contact">
      <p class="who">{s['studio']}</p>
      <p class="mail"><a href="mailto:{MAIL}">{MAIL}</a></p>
      <p class="note">{s['contact_note']}</p>
    </div>
  </div>

</main>"""
    other = "index-en.html" if lang == "ko" else "./"
    return shell(lang, s["studio"], s["studio"], body, other)


def game_page(g, lang):
    s = STR[lang]
    t = g[lang]
    facts = "\n".join(f"          <li>{f}</li>" for f in t["facts"])
    icon = (f'<img class="icon" src="assets/{g["icon"]}" alt="" width="128" height="128">'
            if g["icon"] else "")
    if g["store"]:
        btn = f'<a class="btn" href="{g["store"]}">{s["get"]}</a>'
    else:
        btn = f'<span class="btn disabled">{s["soon"]}</span>'

    shots = ""
    if g["shots"]:
        w, h = (480, 270) if g["shot_wide"] else (270, 480)
        imgs = "\n".join(
            # -rj = JPEG. 안 붙이면 CDN 이 PNG 를 준다 — 같은 장이 620KB vs 114KB
            f'        <img src="{u}=w{w * 2}-rj" alt="" width="{w}" height="{h}" loading="lazy">'
            for u in g["shots"])
        shots = f"""
  <div class="section">
    <p class="section-label">{s['shots']}</p>
    <div class="shots{' wide' if g['shot_wide'] else ''}">
{imgs}
    </div>
  </div>
"""

    body = f"""<main class="page">

  <div class="hero game-hero">
    {icon}
    <h1>{t['name']}</h1>
    <p class="lede">{t['tagline']}</p>
    <ul class="facts">
{facts}
    </ul>
    {btn}
  </div>

  <div class="section">
    <p class="blurb wide">{t['blurb']}</p>
  </div>
{shots}
  <p class="back"><a href="{s['index']}#games">{s['back']}</a></p>

</main>"""
    other = page_name(g["slug"], "en" if lang == "ko" else "ko")
    return shell(lang, t["name"] + s["title_suffix"], t["tagline"], body, other)


def write(name, text):
    with io.open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("  ", name)


print("찍는다:")
write("index.html", index_page("ko"))
write("index-en.html", index_page("en"))
for g in GAMES:
    write(page_name(g["slug"], "ko"), game_page(g, "ko"))
    write(page_name(g["slug"], "en"), game_page(g, "en"))

# 개인정보처리방침 두 장은 손으로 쓴 본문이라 머리말·바닥글만 갈아 끼운다
for lang, name in (("ko", "privacy.html"), ("en", "privacy-en.html")):
    p = os.path.join(OUT, name)
    src = io.open(p, encoding="utf-8").read()
    other = "privacy-en.html" if lang == "ko" else "privacy.html"
    src = re.sub(r"<header class=\"topbar\">.*?</header>",
                 lambda m: topbar(lang, None, other), src, flags=re.S)
    src = re.sub(r"<footer>.*?</footer>",
                 lambda m: footer(lang), src, flags=re.S)
    io.open(p, "w", encoding="utf-8", newline="\n").write(src)
    print("  ", name, "(머리말·바닥글만)")
