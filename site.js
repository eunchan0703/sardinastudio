/* Sardina Studio — 작은 덧붙임들. 전부 «없어도 되는 것» 이다:
   JS 가 꺼져도 첫 슬라이드는 보이고, 스크린샷은 손가락으로 밀리고, 메일 단추는 기본 틀로 열리고,
   목차 링크는 그대로 간다.
   ① 머리띠 투명/단색 ② 첫 화면 게임 슬라이드 ③ 스크린샷 앞뒤 단추
   ④ 고객지원 메일 쓰기(+주소 복사, 질문 바로 펼치기) ⑤ 방침 목차에 지금 읽는 절 표시 */
(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ① 머리띠 — 첫 화면 그림 위에서는 투명, 조금이라도 내려가면 어두운 단색 띠
  var header = document.querySelector('[data-header]');
  if (header && document.body.classList.contains('has-hero')) {
    var onScroll = function () { header.classList.toggle('is-solid', window.scrollY > 24); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // ② 첫 화면 슬라이드 — 6초마다 넘긴다. 마우스를 올리거나 안에 포커스가 있으면 멈추고,
  //    «움직임 줄이기» 를 켠 사람에게는 처음부터 멈춰 둔다. 멈춤 단추는 늘 있다(WCAG 2.2.2).
  var slider = document.querySelector('[data-slider]');
  if (slider) {
    var slides = [].slice.call(slider.querySelectorAll('.slide'));
    var thumbs = [].slice.call(slider.querySelectorAll('.thumb'));
    var toggle = slider.querySelector('[data-toggle]');
    var interval = Number(slider.getAttribute('data-interval')) || 6000;
    slider.style.setProperty('--interval', interval + 'ms');
    var cur = 0, timer = null, userPaused = reduce, hover = false;

    // 2번째부터 슬라이드의 그림은 data- 에 있다 — 첫 그림을 받은 뒤 «다음 것 하나» 만 채운다.
    // 한꺼번에 채우면 안 볼 수도 있는 큰 그림 넷(약 1MB)을 첫 방문에 다 받는다.
    var hydrate = function (el) {
      if (!el) return;
      el.querySelectorAll('img[data-src]').forEach(function (img) {
        if (img.dataset.srcset) img.srcset = img.dataset.srcset;
        img.src = img.dataset.src;
        img.removeAttribute('data-src'); img.removeAttribute('data-srcset');
      });
    };
    var hydrateNext = function () { hydrate(slides[(cur + 1) % slides.length]); };
    if (document.readyState === 'complete') setTimeout(hydrateNext, 300);
    else window.addEventListener('load', function () { setTimeout(hydrateNext, 300); });

    var show = function (i, focusThumb) {
      i = (i + slides.length) % slides.length;
      hydrate(slides[i]);
      slides.forEach(function (s, k) {
        var on = k === i;
        s.classList.toggle('is-current', on);
        if (on) { s.removeAttribute('aria-hidden'); s.inert = false; }
        else { s.setAttribute('aria-hidden', 'true'); s.inert = true; }
      });
      thumbs.forEach(function (t, k) {
        if (k === i) t.setAttribute('aria-current', 'true'); else t.removeAttribute('aria-current');
      });
      cur = i;
      hydrateNext();
      if (focusThumb && thumbs[i]) thumbs[i].focus();
      restartBar();
    };
    // 진행 막대 애니메이션을 처음부터 다시 — 클래스를 떼었다 붙여야 다시 돈다
    var restartBar = function () {
      var bar = thumbs[cur] && thumbs[cur].querySelector('.bar i');
      if (!bar) return;
      bar.style.animation = 'none'; void bar.offsetWidth; bar.style.animation = '';
    };
    var playing = function () { return !userPaused && !hover; };
    var schedule = function () {
      clearTimeout(timer);
      slider.classList.toggle('is-playing', !userPaused);
      slider.classList.toggle('is-paused', !playing());
      if (playing()) timer = setTimeout(function () { show(cur + 1); schedule(); }, remaining());
    };
    // 멈췄다가 다시 갈 때 막대가 남은 만큼만 기다린다(막대와 넘김이 어긋나지 않게)
    var started = Date.now(), left = interval;
    var remaining = function () { started = Date.now(); return left; };
    var pauseClock = function () { left = Math.max(300, left - (Date.now() - started)); };
    var resetClock = function () { left = interval; started = Date.now(); };

    thumbs.forEach(function (t, k) {
      t.addEventListener('click', function () { resetClock(); show(k); schedule(); });
    });
    slider.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      if (e.target.closest('.thumbs') == null && e.target !== slider) return;
      e.preventDefault(); resetClock();
      show(cur + (e.key === 'ArrowRight' ? 1 : -1), true); schedule();
    });
    if (toggle) toggle.addEventListener('click', function () {
      userPaused = !userPaused;
      toggle.setAttribute('aria-label', toggle.getAttribute(userPaused ? 'data-play' : 'data-pause'));
      if (!userPaused) resetClock(); else pauseClock();
      restartBar(); schedule();
    });
    if (toggle && userPaused) toggle.setAttribute('aria-label', toggle.getAttribute('data-play'));
    var setHover = function (v) { if (hover === v) return; if (v) pauseClock(); hover = v; schedule(); };
    slider.addEventListener('mouseenter', function () { setHover(true); });
    slider.addEventListener('mouseleave', function () { setHover(false); });
    slider.addEventListener('focusin', function () { setHover(true); });
    slider.addEventListener('focusout', function (e) { if (!slider.contains(e.relatedTarget)) setHover(false); });
    document.addEventListener('visibilitychange', function () { setHover(document.hidden); });
    slides.forEach(function (s, k) { if (k !== 0) s.inert = true; });
    schedule();
  }

  // ③ 스크린샷 앞뒤 단추 — 끝에 닿으면 그쪽 단추를 끈다. 넘칠 것이 없으면 둘 다 숨긴다
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

  // ④ 고객지원 — 게임·문의 종류를 고르면 메일 제목과 본문 틀을 채운다.
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
    var build = function () {
      var t = cfg.topics && cfg.topics[topic.value];
      if (!t) return;
      var g = game.value;
      var subject = (g ? '[' + g + '] ' : '[Sardina Studio] ') + t.label;
      var body = t.body.replace('{game}', g).replace(/\n/g, '\r\n');
      link.href = 'mailto:' + cfg.mail + '?subject=' + encodeURIComponent(subject) +
                  '&body=' + encodeURIComponent(body);
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

  // ⑤ 방침 목차 — 지금 읽는 절의 목차 줄에 aria-current 를 단다(넓은 화면에서 왼쪽에 붙어 있다)
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
