# 찍어 낸 장을 검사한다 — _gen.py 를 돌린 뒤에 돌린다.
#
#   python3 _check.py            # 안쪽 링크만
#   python3 _check.py --online   # 바깥 링크(스토어·구글 안내)도 실제로 열어 본다
#
# 무엇을 보나:
#   ① 안쪽 링크·그림이 실제 파일을 가리키나, #앵커가 그 장에 있나
#   ② 옛 주소(main 브랜치에 있던 .html)가 하나도 안 빠졌나 — 플레이 콘솔이 물고 있다
#   ③ 언어 단추가 «같은 장의 짝» 으로 가나 (홈으로 튕기지 않나)
#   ④ 한 장 안에 같은 id 가 둘 있지 않나
#   ⑤ hreflang·canonical 절대 주소가 실제 파일로 이어지나
# 하나라도 걸리면 끝 코드 1 로 끝난다.

import io, os, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://eunchan0703.github.io/sardinastudio/"
BASE = "/sardinastudio/"
problems = []


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.base, self.lang_links = [], [], None, []
        self._in_lang = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "base":
            self.base = a.get("href")
        if tag == "div" and "lang" in (a.get("class") or "").split():
            self._in_lang += 1
        if tag == "link" and a.get("rel") == "preconnect":
            return  # 연결 예열일 뿐 여는 주소가 아니다
        for k in ("href", "src"):
            if k in a and a[k] is not None:
                self.links.append((tag, k, a[k], a))
        if "srcset" in a:
            for part in a["srcset"].split(","):
                self.links.append((tag, "srcset", part.strip().split(" ")[0], a))
        if tag == "a" and self._in_lang and "hreflang" in a:
            self.lang_links.append((a["hreflang"], a["href"]))

    def handle_endtag(self, tag):
        if tag == "div" and self._in_lang:
            self._in_lang -= 1


def parse(name):
    p = Page()
    p.feed(io.open(os.path.join(ROOT, name), encoding="utf-8").read())
    return p


pages = sorted(f for f in os.listdir(ROOT) if f.endswith(".html"))
parsed = {f: parse(f) for f in pages}
external = set()


def resolve(src_page, url, base):
    """안쪽 주소 → (파일 이름, 앵커). 바깥 주소면 None."""
    parts = urlsplit(url)
    if parts.scheme in ("mailto", "tel", "data", "javascript"):
        return None
    if parts.scheme in ("http", "https"):
        if url.startswith(SITE):
            path = url[len(SITE):]
        else:
            external.add(url)
            return None
    else:
        path = parts.path
        if base and not path.startswith("/"):
            path = base + path
        if path.startswith(BASE):
            path = path[len(BASE):]
        elif path.startswith("/"):
            problems.append(f"{src_page}: 뿌리 기준 주소 {url} — 프로젝트 사이트에서는 깨진다")
            return None
    path = unquote(path)
    if path in ("", ".", "./"):   # 사이트 뿌리 = 한국어 홈
        path = "index.html"
    return path, parts.fragment


for name, p in parsed.items():
    # ④ 같은 id
    seen = set()
    for i in p.ids:
        if i in seen:
            problems.append(f"{name}: id «{i}» 가 둘 이상")
        seen.add(i)
    # ① 링크
    for tag, attr, url, a in p.links:
        if url.startswith("#"):
            target, frag = name, url[1:]
            if p.base:  # <base> 가 있으면 #x 도 사이트 뿌리 기준이 된다
                target = "index.html"
        else:
            r = resolve(name, url, p.base)
            if r is None:
                continue
            target, frag = r
        if not os.path.exists(os.path.join(ROOT, target)):
            problems.append(f"{name}: {attr}={url} → 없는 파일 {target}")
            continue
        if frag and target.endswith(".html"):
            if frag not in parsed[target].ids:
                problems.append(f"{name}: {url} → {target} 에 #{frag} 이 없다")

# ② 옛 주소
try:
    old = subprocess.run(["git", "-C", ROOT, "ls-tree", "--name-only", "main"],
                         capture_output=True, text=True, check=True).stdout.split()
    for f in old:
        if f.endswith(".html") and f not in pages:
            problems.append(f"옛 주소가 사라졌다: {f}")
    old_html = [f for f in old if f.endswith(".html")]
except Exception as e:
    old_html = []
    print("⚠ main 브랜치를 못 읽어 옛 주소 대조를 건너뛴다 —", e)

# ③ 언어 단추 — X.html ↔ X-en.html, 홈은 ./ ↔ index-en.html
def pair(name):
    if name == "404.html":
        return None
    return name[:-8] + ".html" if name.endswith("-en.html") else name[:-5] + "-en.html"

norm = lambda h: "index.html" if h in ("./", "") else h
for name, p in parsed.items():
    if not p.lang_links:
        problems.append(f"{name}: 언어 단추가 없다")
        continue
    other = pair(name)
    if other is None:
        continue
    ko, en = (name, other) if not name.endswith("-en.html") else (other, name)
    for lang, href in p.lang_links:
        want = ko if lang == "ko" else en
        if norm(href) != want:
            problems.append(f"{name}: 언어 단추 {lang} → {href} (기대: {want})")
    if not os.path.exists(os.path.join(ROOT, other)):
        problems.append(f"{name}: 짝 장 {other} 이 없다")

# ⑤ 바깥 링크(선택)
if "--online" in sys.argv:
    for url in sorted(external):
        if not url.startswith("https://"):
            continue
        # curl 로 연다 — 파이썬에 인증서 묶음이 없는 맥이 있어 urllib 이 SSL 에서 넘어진다
        r = subprocess.run(["curl", "-s", "-L", "-o", "/dev/null", "-w", "%{http_code}",
                            "-A", "Mozilla/5.0 link-check", "--max-time", "20", url],
                           capture_output=True, text=True)
        code = int(r.stdout) if r.stdout.isdigit() else r.stdout or "curl 실패"
        mark = "ok " if code == 200 else "!! "
        print(f"  {mark}{code} {url[:100]}")
        if code != 200:
            problems.append(f"바깥 링크 {url} → {code}")

n_links = sum(len(p.links) for p in parsed.values())
print(f"장 {len(pages)}개 · 링크/그림 {n_links}개 · 바깥 주소 {len(external)}개 · 옛 주소 {len(old_html)}개 대조")
if problems:
    print(f"문제 {len(problems)}건:")
    for x in problems:
        print("  ✗", x)
    sys.exit(1)
print("문제 없음")
