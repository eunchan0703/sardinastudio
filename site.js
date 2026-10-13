/* Sardina Studio — 작은 덧붙임들. 전부 «없어도 되는 것» 이다:
   JS 가 꺼져도 스크린샷은 손가락으로 밀리고, 메일 단추는 기본 틀로 열리고, 목차 링크는 그대로 간다.
   ① 머리띠 투명/단색 ② 스크린샷 앞뒤 단추
   ③ 고객지원 메일 쓰기(+주소 복사, 질문 바로 펼치기) ④ 방침 목차에 지금 읽는 절 표시 */
(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ① 머리띠 — 첫 화면 위에서는 투명, 조금이라도 내려가면 흰 단색 띠
  var header = document.querySelector('[data-header]');
  if (header && document.body.classList.contains('has-hero')) {
    var onScroll = function () { header.classList.toggle('is-solid', window.scrollY > 24); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // ② 스크린샷 앞뒤 단추 — 끝에 닿으면 그쪽 단추를 끈다. 넘칠 것이 없으면 둘 다 숨긴다
  document.querySelectorAll('.shot-nav').forEach(function (nav) {
    var track = document.getElementById(nav.querySelector('[aria-controls]').getAttribute('aria-controls'));
    if (!track) return;
    var prev = nav.querySelector('[data-dir="-1"]'), next = nav.querySelector('[data-dir="1"]');
    var update = function () {
      var max = track.scrollWidth - track.clientWidth;
      nav.hidden = max <= 2;
      prev.disabled = track.scrollLeft <= 2;
      next.disabled = track.scrollLeft >= max - 2;
    };
    nav.addEventListener('click', function (e) {
      var b = e.target.closest('[data-dir]');
      if (!b) return;
      var item = track.querySelector('li');
      var step = item ? item.getBoundingClientRect().width + 16 : track.clientWidth * 0.8;
      track.scrollBy({ left: Number(b.getAttribute('data-dir')) * step, behavior: reduce ? 'auto' : 'smooth' });
    });
    track.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    // 그림이 늦게 오면 폭이 그때 정해진다
    track.querySelectorAll('img').forEach(function (img) { img.addEventListener('load', update); });
    update();
  });

  // ③ 고객지원 — 게임·문의 종류를 고르면 메일 제목과 본문 틀을 채운다.
  //    틀은 _gen.py 의 표 하나에서 JSON 으로 온다(두 벌로 적지 않는다).
  var cfgEl = document.getElementById('composer-data');
  var composer = document.querySelector('[data-composer]');
  var cfg = {};
  if (cfgEl && composer) {
    try { cfg = JSON.parse(cfgEl.textContent); } catch (err) {
      // 틀을 못 읽으면 기본 메일 단추(서버가 찍어 둔 href)가 그대로 남는다
      console.warn('메일 틀을 못 읽음 — 기본 단추를 쓴다', err);
    }
    var game = composer.querySelector('[name="game"]');
    var topic = composer.querySelector('[name="topic"]');
    var link = composer.querySelector('[data-mailto]');
    var out = composer.querySelector('[data-subject]');
    // support.html?game=워드리아&topic=bug 처럼 미리 고른 채로 열 수 있다(없는 값은 무시)
    var params = new URLSearchParams(location.search);
    var pick = function (sel, v) {
      if (v && [].some.call(sel.options, function (o) { return o.value === v; })) sel.value = v;
    };
    pick(game, params.get('game'));
    pick(topic, params.get('topic'));
    // 손가락 화면(폰 · 태블릿)은 mailto 그대로 — 안드로이드는 Gmail 앱이 열린다. 웹 Gmail 로 보내면 폰에서는 앱 대신 좁은 웹 화면이 뜬다
    var gmail = !(window.matchMedia && window.matchMedia('(hover: none) and (pointer: coarse)').matches);
    if (gmail) { link.target = '_blank'; link.rel = 'noopener'; }
    var build = function () {
      var t = cfg.topics && cfg.topics[topic.value];
      if (!t) return;
      var g = game.value;
      var subject = (g ? '[' + g + '] ' : '[Sardina Studio] ') + t.label;
      var body = t.body.replace('{game}', g).replace(/\n/g, '\r\n');
      if (gmail) {
        // PC — Gmail 쓰기 화면을 새 탭으로(사장님 2026-10-13 «메일 쓰기 하면 구글 메일로»).
        //   PC 에는 메일 앱이 없는 경우가 많아 mailto 가 아무 일도 안 했다
        link.href = 'https://mail.google.com/mail/?view=cm&fs=1&to=' + encodeURIComponent(cfg.mail) +
                    '&su=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      } else {
        link.href = 'mailto:' + cfg.mail + '?subject=' + encodeURIComponent(subject) +
                    '&body=' + encodeURIComponent(body);
      }
      out.textContent = subject;
    };
    game.addEventListener('change', build);
    topic.addEventListener('change', build);
    build();
  }

  // 메일 주소 복사 — 메일 앱이 없는 PC 에서 mailto 가 아무 일도 안 하는 경우를 메운다
  document.querySelectorAll('[data-copy]').forEach(function (b) {
    var status = b.parentNode.querySelector('.copy-status');
    var say = function (msg) { if (status) status.textContent = msg; };
    b.addEventListener('click', function () {
      var text = b.getAttribute('data-copy');
      var ok = cfg.copied || 'Copied', fail = cfg.copy_fail || 'Copy failed';
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function () { say(ok); }, function () { say(fail); });
      } else {
        say(fail);
      }
    });
  });

  // 자주 묻는 질문 — support.html#refund 처럼 질문을 바로 가리키면 그 질문을 펼친다
  // (닫힌 채로 두면 링크를 따라온 사람이 «답이 없다» 로 본다)
  var openFromHash = function () {
    var id = decodeURIComponent(location.hash.slice(1));
    var el = id && document.getElementById(id);
    if (el && el.tagName === 'DETAILS') el.open = true;
  };
  window.addEventListener('hashchange', openFromHash);
  openFromHash();

  // ④ 방침 목차 — 지금 읽는 절의 목차 줄에 aria-current 를 단다(넓은 화면에서 왼쪽에 붙어 있다)
  var toc = document.querySelector('nav.toc');
  if (toc && 'IntersectionObserver' in window) {
    var links = {};
    toc.querySelectorAll('a[href^="#"]').forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
    var current = null;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var a = links[en.target.id];
        if (!a || a === current) return;
        if (current) current.removeAttribute('aria-current');
        a.setAttribute('aria-current', 'true');
        current = a;
      });
    }, { rootMargin: '-20% 0px -70% 0px' });
    Object.keys(links).forEach(function (id) { var s = document.getElementById(id); if (s) io.observe(s); });
  }
})();
