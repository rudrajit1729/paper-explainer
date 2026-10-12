/* Explainer engine.
 *
 * The page is a 1600x900 "stage" of <section class="scene" data-scene="start,end"> elements.
 * Everything is authored on ANIMATION time (seconds). A time map (window.EXPLAINER_KEYS, made by
 * `explainer timing`) stretches animation time into VIDEO time so each scene lasts as long as its
 * narration or its reading needs. Elements animate with data attributes:
 *
 *   data-fx="rise|fade|bar|count|ring"  data-in="12.3"  [data-dur="0.6"]  [data-out="14.6"]  [data-val="45.0"]
 *
 * Project scripts add custom motion with Explainer.onRender((at, vt) => {...}), where `at` is
 * animation time and `vt` is video time. The renderer drives the page through window.__seek(vt).
 */
(function(){
  const $ = id => document.getElementById(id);
  const clamp = p => p < 0 ? 0 : p > 1 ? 1 : p;
  const easeOut = p => { p = clamp(p); return 1 - Math.pow(1 - p, 3); };
  const easeIO = p => { p = clamp(p); return p < .5 ? 4*p*p*p : 1 - Math.pow(-2*p + 2, 3) / 2; };
  const seg = (t, a, d) => easeOut((t - a) / d);                 // 0 → 1 starting at a over d seconds
  const lerp = (a, b, p) => a + (b - a) * p;
  const win = (t, a, b, f) => seg(t, a, f) * (1 - seg(t, b, f));  // on between a and b, fading over f

  /* time map: [[video, anim], ...] */
  const KEYS = window.EXPLAINER_KEYS || [[0, 0], [40, 40]];
  const D = KEYS[KEYS.length - 1][0];
  function Araw(v){
    if(v <= 0) return KEYS[0][1];
    for(let i = 1; i < KEYS.length; i++){
      const [v1, a1] = KEYS[i], [v0, a0] = KEYS[i-1];
      if(v <= v1) return v1 === v0 ? a1 : a0 + (a1 - a0) * (v - v0) / (v1 - v0);
    }
    return KEYS[KEYS.length - 1][1];
  }
  // a short moving average eases every change of pace, so holds and transitions flow
  function A(v){ let s = 0; for(let k = -4; k <= 4; k++) s += Araw(Math.min(D, Math.max(0, v + k*0.09))); return s / 9; }
  function V(a){
    for(let i = 1; i < KEYS.length; i++){
      const [v1, a1] = KEYS[i], [v0, a0] = KEYS[i-1];
      if(a <= a1 && a1 > a0) return v0 + (v1 - v0) * (Math.max(a, a0) - a0) / (a1 - a0);
    }
    return D;
  }

  const hooks = [];
  window.Explainer = { KEYS, D, A, V, $, clamp, easeOut, easeIO, seg, lerp, win, onRender: fn => hooks.push(fn) };

  function boot(){
    const stage = $('stage'), screen = $('screen');
    const scenes = [...stage.querySelectorAll('[data-scene]')].map(el => {
      const [a, b] = el.dataset.scene.split(',').map(Number); return { el, a, b };
    });
    const items = [...stage.querySelectorAll('[data-fx]')];

    /* controls: play, scrub, time, full screen, and one chip per scene that has data-chip */
    const bar = document.createElement('div'); bar.className = 'controls';
    bar.innerHTML = '<button class="btn" type="button">Pause</button>' +
      '<input class="scrub" type="range" min="0" step="0.01" value="0" aria-label="Position in the video">' +
      '<span class="time">0:00</span><button class="btn ghost" type="button">Full screen</button>';
    const [btn, scrub, time, fs] = bar.children;
    const chipRow = document.createElement('div'); chipRow.className = 'chips';
    const chips = scenes.filter(s => s.el.dataset.chip).map(s => {
      const c = document.createElement('button'); c.type = 'button'; c.className = 'chip';
      const color = s.el.dataset.chipColor;
      c.innerHTML = (color ? `<i class="${color}"></i>` : '') + s.el.dataset.chip;
      c.dataset.t = Math.max(0, V(s.a + .2) - .3).toFixed(2);
      chipRow.appendChild(c); return c;
    });
    screen.after(bar); if(chips.length) bar.after(chipRow);

    function render(at, vt){
      scenes.forEach(s => {
        const pin = seg(at, s.a, .45), pout = seg(at, s.b - .45, .45), o = pin * (1 - pout);
        s.el.style.opacity = o; s.el.style.visibility = o < .01 ? 'hidden' : 'visible';
        s.el.style.transform = `scale(${(1 - .012*(1 - pin) + .012*pout).toFixed(4)})`;
      });
      items.forEach(el => {
        const a = +el.dataset.in, d = +(el.dataset.dur || .6);
        const p = seg(at, a, d);
        const q = el.dataset.out ? 1 - seg(at, +el.dataset.out, .4) : 1;
        switch(el.dataset.fx){
          case 'rise':  el.style.opacity = p*q; el.style.transform = `translateY(${(1-p)*26 - (1-q)*12}px)`; break;
          case 'fade':  el.style.opacity = p*q; break;
          case 'bar':   el.style.transform = `scaleX(${p})`; break;
          case 'count': el.textContent = (p * +el.dataset.val).toFixed(+(el.dataset.decimals ?? 1)) + (el.dataset.unit ?? '%'); break;
          case 'ring':  el.setAttribute('stroke-dasharray', `${(p * +el.dataset.val).toFixed(2)} 100`); break;
        }
      });
      hooks.forEach(fn => fn(at, vt));
    }

    const reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    let t = 0, playing = !reduce, last = null;
    const fmt = s => `${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2, '0')}`;
    scrub.max = D;
    function sync(){
      render(A(t), t);
      scrub.value = t;
      time.textContent = `${fmt(t)} / ${fmt(D)}`;
      btn.textContent = playing ? 'Pause' : (t >= D ? 'Replay' : 'Play');
      let cur = -1; chips.forEach((c, i) => { if(t >= +c.dataset.t - .25) cur = i; });
      chips.forEach((c, i) => c.setAttribute('aria-current', i === cur ? 'true' : 'false'));
    }
    function frame(ts){
      if(playing){
        if(last != null) t += Math.min(.1, (ts - last) / 1000);
        if(t >= D){ t = D; playing = false; }
        last = ts; sync();
      } else last = null;
      requestAnimationFrame(frame);
    }
    function toggle(){ if(t >= D) t = 0; playing = !playing; last = null; sync(); }
    btn.addEventListener('click', toggle);
    scrub.addEventListener('input', () => { t = +scrub.value; sync(); });
    chips.forEach(c => c.addEventListener('click', () => { t = +c.dataset.t; last = null; sync(); }));
    screen.addEventListener('click', toggle);
    screen.addEventListener('keydown', e => { if(e.code === 'Space'){ e.preventDefault(); toggle(); } });
    fs.addEventListener('click', () => {
      try{
        if(document.fullscreenElement) document.exitFullscreen().catch(() => {});
        else if(screen.requestFullscreen) screen.requestFullscreen().catch(() => {});
      }catch(e){}
    });

    function fit(){
      const w = screen.clientWidth, h = screen.clientHeight, s = Math.min(w/1600, h/900);
      stage.style.transform = `translate(${(w - 1600*s)/2}px, ${(h - 900*s)/2}px) scale(${s})`;
    }
    if(window.ResizeObserver) new ResizeObserver(fit).observe(screen); else window.addEventListener('resize', fit);

    // hooks for the video renderer
    window.__seek = s => { playing = false; t = s; sync(); };
    window.__D = D;
    fit(); sync();
    requestAnimationFrame(frame);
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => setTimeout(boot, 0));
  else setTimeout(boot, 0);
})();
