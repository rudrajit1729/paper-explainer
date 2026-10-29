/* The cast for "What Should I Do?": rigged Humaaans-style people, the Agent, and crowd figures.
   People are drawn in Humaaans' 380-unit frame (head at (82,0), body at (22,82), legs at (0,187));
   pose() places them on the stage. Needs humaaans.js loaded first. */
(function(){
  const NS = 'http://www.w3.org/2000/svg', H = window.HUMAAANS;
  function el(tag, attrs, parent){
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  const shade = (hex, f) => '#' + [1, 3, 5].map(i => Math.min(255, Math.round(parseInt(hex.slice(i, i + 2), 16) * f)).toString(16).padStart(2, '0')).join('');
  const paint = (markup, c) => markup.replace(/\{\{(\w+)\}\}/g, (_, k) => c[k]);
  const deg = r => r * 180 / Math.PI;
  const lim = (v, a, b) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, p) => a + (b - a) * p;
  const backOut = x => { x = lim(x, 0, 1); return 1 + 2.2 * Math.pow(x - 1, 3) + 1.2 * Math.pow(x - 1, 2); };   // overshoot, then settle
  // Blend two poses; keys missing from B keep A's value.
  function mix(A, B, k){
    const o = {};
    for (const key in A){
      const a = A[key], b = B[key];
      if (b === undefined) o[key] = a;
      else if (Array.isArray(a)) o[key] = a.map((v, i) => lerp(v, b[i], k));
      else if (typeof a === 'number') o[key] = lerp(a, b, k);
      else o[key] = k < .5 ? a : b;
    }
    for (const key in B) if (!(key in o)) o[key] = B[key];
    return o;
  }

  const LOOKS = {
    aisha:    { head: 'Wavy',       skin: '#6b4430', hair: '#191847', top: '#fbbc04', pants: '#2f3676', pantsDark: '#191847', shoes: '#e4e4e4', shoesDark: '#191847' },
    reviewer: { head: 'ShortBeard', skin: '#c69c72', hair: '#2b1d17', top: '#4285f4', pants: '#3c4043', pantsDark: '#202124', shoes: '#e4e4e4', shoesDark: '#202124' },
    allIn:    { head: 'Short',      skin: '#e8b996', hair: '#8d4a2b', top: '#ea4335', pants: '#1f2a44', pantsDark: '#141b2e', shoes: '#e4e4e4', shoesDark: '#141b2e' },
    unsure:   { head: 'Top',        skin: '#8b5e3c', hair: '#191847', top: '#34a853', pants: '#2f3676', pantsDark: '#191847', shoes: '#e4e4e4', shoesDark: '#191847' },
  };

  const RIG = { pelvis: [140, 214], neck: [150, 96], shN: [170, 130], shF: [157, 122], L1: 58, L2: 56 };
  const TORSO = 'M134,84 L166,84 C171,108 178,128 184,150 C190,172 197,194 193,211 C189,226 160,231 122,229 C105,228 94,227 89,225 C83,205 84,185 92,166 C98,151 101,141 101,128 C103,108 116,92 134,84 Z';
  const TORSO_BACK = 'M92,166 C98,151 101,141 101,128 C103,108 116,92 134,84 L140,84 C122,100 114,124 114,150 C114,180 108,206 106,228 C99,227 93,226 89,225 C83,205 84,185 92,166 Z';
  // Typing hand, palm down, seen from the side: wrist at (0,0), curled fingertips at (40,12).
  const TYPE_HAND = 'M0,-7 C12,-9.5 24,-8 32,-3.5 C37.5,-.5 41,4.5 41.4,9.6 C41.6,12.6 38.8,13.8 37,11.6 C35.4,9.4 33,8 29.4,7.8 C20,8 10,8.4 0,7.6 Z';
  const TYPE_THUMB = 'M10,6 C15,7.4 18,9.4 17.2,11 C15.8,12.2 12.2,11 9,8.8 Z';
  const TIP = [40, 12];
  // More hands in the same style, drawn with the wrist at (0,0) and the hand pointing along +x.
  const HANDS = {
    point:  ['M0,-6.5 C6,-8.5 14,-8.6 19,-6.4 L40.5,-3.6 C44,-3.2 44,1.6 40.5,2 L21,3 C20.6,6.6 18,9.6 13.6,10 C8,10.4 3,9.4 0,7.2 Z',
             'M9,-6.8 C10.4,-12 15.4,-14.6 19.4,-12.4 C21,-11.4 19.6,-8.4 16.6,-6.6 Z'],
    // An open hand with the fingers joined in one rounded mitten and a short, low thumb. No single digit ever
    // sticks out, so no angle can read as a rude gesture. Used for palm-up, open-hand and any upward hand.
    palm:   ['M0,-7 C8,-9.2 18,-10.4 27,-9.6 C34.4,-9 38.6,-5.4 38.6,0 C38.6,5.4 34.4,9 27,9.6 C18,10.4 8,9.2 0,7 Z',
             'M7,6.4 C11,10.6 15.6,12.4 18.6,11 C19.8,10.2 18.4,8 14.6,6.8 Z'],
  };
  const HAIR = { Long: { first: true, pivot: '160 60' }, Wavy: { pivot: '178 58' }, Top: { pivot: '170 40' } };

  // Two-bone IK: the elbow bends down and back.
  function ik(S, W, L1, L2){
    const dx = W[0] - S[0], dy = W[1] - S[1], d = Math.hypot(dx, dy);
    // A reach past full length stretches the arm a little (rubber-hose style) instead of locking it straight.
    const st = lim(d / (L1 + L2 - .5), 1, 1.07); L1 *= st; L2 *= st;
    const dc = lim(d, 8, L1 + L2 - .5), a = Math.atan2(dy, dx);
    const A = Math.acos(lim((L1 * L1 + dc * dc - L2 * L2) / (2 * L1 * dc), -1, 1));
    return { E: [S[0] + L1 * Math.cos(a + A), S[1] + L1 * Math.sin(a + A)], W: [S[0] + dc * Math.cos(a), S[1] + dc * Math.sin(a)] };
  }
  // Sleeve: a tapered shape along a smooth curve through shoulder, elbow and wrist, with a soft balloon before the cuff.
  const width = t => t < .5 ? lerp(36, 28, t / .5) : t < .84 ? lerp(28, 31, (t - .5) / .34) : lerp(31, 23, (t - .84) / .16);
  function sleeve(S, E, W){
    const C = [2 * E[0] - (S[0] + W[0]) / 2, 2 * E[1] - (S[1] + W[1]) / 2], L = [], R = [], N = 36;
    for (let i = 0; i <= N; i++){
      const t = i / N, u = 1 - t;
      const P = [u * u * S[0] + 2 * u * t * C[0] + t * t * W[0], u * u * S[1] + 2 * u * t * C[1] + t * t * W[1]];
      const T = [2 * u * (C[0] - S[0]) + 2 * t * (W[0] - C[0]), 2 * u * (C[1] - S[1]) + 2 * t * (W[1] - C[1])];
      const n = Math.hypot(T[0], T[1]) || 1, w = width(t) / 2;
      L.push([P[0] - T[1] / n * w, P[1] + T[0] / n * w]); R.push([P[0] + T[1] / n * w, P[1] - T[0] / n * w]);
    }
    const f = p => p[0].toFixed(1) + ',' + p[1].toFixed(1);
    return { d: 'M' + L.map(f).join(' L') + ' L' + R.reverse().map(f).join(' L') + ' Z', dir: Math.atan2(W[1] - C[1], W[0] - C[0]) };
  }
  // A rig point in world space, moved into the leaning upper body's frame.
  function toUpper(P, lean, lift){
    const a = -lean * Math.PI / 180, x = P[0] - RIG.pelvis[0], y = P[1] - (lift || 0) - RIG.pelvis[1];
    return [RIG.pelvis[0] + x * Math.cos(a) - y * Math.sin(a), RIG.pelvis[1] + x * Math.sin(a) + y * Math.cos(a)];
  }
  // Wrist position and hand angle for a typing fingertip at F, with the hand pitched a degrees.
  function typingWrist(F, a){
    const r = a * Math.PI / 180;
    return [F[0] - (TIP[0] * Math.cos(r) - TIP[1] * Math.sin(r)), F[1] - (TIP[0] * Math.sin(r) + TIP[1] * Math.cos(r))];
  }

  // A person. legs: 'legsStand' or 'legsSit'. front: optional group for the near arm, to draw it over props.
  function person(parent, c, legs, front){
    const root = el('g', {}, parent);
    el('g', {}, root).innerHTML = `<g transform="translate(0 187)">${paint(H[legs], c)}</g>`;
    const upper = el('g', {}, root);
    const farHand = el('path', { d: H.hand, fill: shade(c.skin, .86) }, upper);
    const farType = el('g', {}, upper);
    el('path', { d: TYPE_THUMB, fill: shade(c.skin, .78) }, farType); el('path', { d: TYPE_HAND, fill: shade(c.skin, .86) }, farType);
    const farMore = handSet(upper, shade(c.skin, .86));
    const farSleeve = el('path', { fill: shade(c.top, .78) }, upper);
    const head = el('g', {}, upper);
    const headInner = el('g', { transform: 'translate(82 0)' }, head);
    headInner.innerHTML = paint(H['head' + c.head], c);
    const hs = HAIR[c.head], hair = hs ? (hs.first ? headInner.firstElementChild : headInner.lastElementChild) : null;
    const torsoEl = el('path', { d: TORSO, fill: c.top }, upper);
    el('path', { d: TORSO_BACK, fill: shade(c.top, .9) }, upper);
    el('path', { d: 'M132,84 L168,84 L169,92 C156,96 144,96 131,92 Z', fill: shade(c.top, .82) }, upper);
    const fore = front ? el('g', {}, front) : el('g', {}, upper);
    const nearHand = el('path', { d: H.hand, fill: c.skin }, fore);
    const nearType = el('g', {}, fore);
    el('path', { d: TYPE_THUMB, fill: shade(c.skin, .93) }, nearType); el('path', { d: TYPE_HAND, fill: c.skin }, nearType);
    const nearMore = handSet(fore, c.skin);
    const nearSleeve = el('path', { fill: c.top }, fore);
    const shoulderDot = el('circle', { cx: RIG.shN[0] - 2, cy: RIG.shN[1] + 2, r: 18, fill: c.top }, fore);   // fills the gap where the sleeve leaves the shoulder
    function handSet(parent, col){
      const out = {};
      for (const k in HANDS){ const g = el('g', { opacity: 0 }, parent); el('path', { d: HANDS[k][1], fill: shade(col, .9) }, g); el('path', { d: HANDS[k][0], fill: col }, g); out[k] = g; }
      return out;
    }
    const solved = {};
    function arm(sl, hand, typeG, more, S, Wt, handTurn, typeAngle, typeK, shape, key){
      const { E, W } = ik(S, Wt, RIG.L1, RIG.L2), s = sleeve(S, E, W), typing = typeK > .5;
      if (key) solved[key] = { W, dir: deg(s.dir) };
      sl.setAttribute('d', s.d);
      let kind = typing ? 'type' : (shape && more[shape] ? shape : 'relax');
      // Guard: the source hand has a long separate thumb and finger, so any upward angle swaps to the mitten.
      const relaxAngle = ((deg(s.dir) + 24 + (handTurn || 0)) % 360 + 540) % 360 - 180;
      if (kind === 'relax' && relaxAngle < -15 && relaxAngle > -165) kind = 'palm';
      // The pointing hand is for pointing at screens, roughly level; never upward.
      const handAngle = ((deg(s.dir) + (handTurn || 0)) % 360 + 540) % 360 - 180;
      if (kind === 'point' && (handAngle < -35 && handAngle > -145)) kind = 'palm';
      hand.setAttribute('opacity', kind === 'relax' ? 1 : 0); typeG.setAttribute('opacity', kind === 'type' ? 1 : 0);
      for (const k in more){
        more[k].setAttribute('opacity', kind === k ? 1 : 0);
        if (kind === k) more[k].setAttribute('transform', `translate(${W[0]} ${W[1]}) rotate(${deg(s.dir) + (handTurn || 0)})`);
      }
      // Open hand: anchor (213,64) points up and right at about -24 degrees in the source drawing.
      hand.setAttribute('transform', `translate(${W[0]} ${W[1]}) rotate(${deg(s.dir) + 24 + (handTurn || 0)}) translate(-213 -64)`);
      typeG.setAttribute('transform', `translate(${W[0]} ${W[1]}) rotate(${typeAngle || 0})`);
    }
    return {
      root, upper, fore, solved,
      pose(p){
        const base = `translate(${p.x} ${p.y}) scale(${p.s})`, body = `translate(0 ${p.lift || 0}) rotate(${p.lean || 0} ${RIG.pelvis[0]} ${RIG.pelvis[1]})`;
        root.setAttribute('transform', base); upper.setAttribute('transform', body);
        if (front) fore.setAttribute('transform', base + ' ' + body);
        head.setAttribute('transform', `rotate(${p.head || 0} ${RIG.neck[0]} ${RIG.neck[1]})`);
        // headFront: the head draws over the near arm (hands behind the head); otherwise the torso covers the neck.
        const wantFront = !!p.headFront && !front;
        if (wantFront !== (head.nextSibling === null)) wantFront ? upper.appendChild(head) : upper.insertBefore(head, torsoEl);
        if (hair) hair.setAttribute('transform', `rotate(${p.hair || 0} ${hs.pivot})`);
        const up = p.shrug || 0;                      // shoulders rise with a shrug
        arm(farSleeve, farHand, farType, farMore, [RIG.shF[0], RIG.shF[1] - up], p.wF, p.hF, p.aF, p.typeK || 0, p.handF);
        arm(nearSleeve, nearHand, nearType, nearMore, [RIG.shN[0], RIG.shN[1] - up], p.wN, p.hN, p.aN, p.typeK || 0, p.handN, 'near');
        shoulderDot.setAttribute('cy', RIG.shN[1] + 2 - up);
      },
    };
  }

  // Standing poses, in the rig frame. Each takes time t for idle life.
  const STAND = {
    rest: t => { const s = Math.sin(t * 1.5); return { lean: s * .8, lift: Math.sin(t * 2) * .8, head: s * 1.5, hair: -s * 1.5, wN: [178 + s * 3, 234], hN: -12, wF: [152 - s * 3, 230], hF: -8 }; },
    wave: t => { const w = Math.sin(t * 7.5); return { head: -5, hair: 2 * w, wN: [222 + w * 7, 40], hN: w * 22 }; },
    present: t => { const b = Math.max(0, Math.sin(t * 5.2)) * 6; return { lean: 3, head: 2 + b * .3, wN: [266, 148 - b], hN: -18, wF: [240, 152 - b * .6], hF: -12 }; },
    think: t => ({ lean: -2, head: -8 + Math.sin(t * 1.4) * 1.5, wN: [200, 97], hN: -4 + Math.sin(t * 2) * 5 }),
    delegate: t => { const f = Math.max(0, Math.sin(t * 2.2)) ** 3; return { lean: -8, lift: Math.sin(t * 1.4) * .8, head: -5, hair: f * 2, wN: [262 + f * 6, 166 - f * 10], hN: 8 - f * 30, wF: [176, 214], hF: -40 }; },   // leans back, flicks a lazy "you do it"
    // Anxious, body only: hunched in close to the screen, shoulders up, a small nervous rock. Combine it with typing
    // or scrolling hands; the hands never leave the desk (raised hands near the head read badly in profile).
    anxious: t => { const r = Math.sin(t * 2.6); return { lean: 10 + r * 1.2, lift: 2, shrug: 7, head: 13 + r * 1.5 + Math.sin(t * 7.5) * .5, hair: -r }; },
    overwhelmed: t => { const s = Math.sin(t * 3.2); return { lean: -3 + s, head: 6 + s * 2, hair: s * 2, wN: [176, 50 + s * 2], hN: -60, wF: [146, 46 - s * 2], hF: -70 }; },
  };

  // The Agent: a friendly blue pebble with eyes and a little antenna. It lives on screens and pops out of them.
  function agent(parent, col = { body: '#4285f4', hi: '#8ab4f8', stem: '#2f6fdc' }){
    const root = el('g', {}, parent), shadow = el('ellipse', { rx: 24, ry: 5, fill: '#191847', opacity: .12 }, parent);
    const body = el('g', {}, root);
    const stem = el('path', { stroke: col.stem, 'stroke-width': 3.5, fill: 'none', 'stroke-linecap': 'round' }, body);
    const bulb = el('circle', { r: 5.5, fill: '#fbbc04' }, body);
    el('path', { d: 'M0,-28 C20,-28 31,-17 31,1 C31,19 19,28 0,28 C-19,28 -31,19 -31,1 C-31,-17 -20,-28 0,-28 Z', fill: col.body }, body);
    el('ellipse', { cx: -12, cy: -15, rx: 9, ry: 5, fill: col.hi, transform: 'rotate(-32 -12 -15)' }, body);
    const eyes = el('g', {}, body), pupils = [];
    [-9.5, 9.5].forEach(x => { el('ellipse', { cx: x, cy: -1, rx: 6, ry: 8, fill: '#fff' }, eyes); pupils.push(el('circle', { cx: x, cy: 0, r: 3.4, fill: '#191847' }, eyes)); });
    return {
      root,
      // p: x, y, s (scale), sq (squash, + is flatter), tilt (deg), look [dx, dy] in -1..1, blink 0..1, ground (shadow y), lag (antenna)
      pose(p){
        const s = p.s ?? 1, sq = p.sq || 0;
        root.setAttribute('transform', `translate(${p.x} ${p.y}) rotate(${p.tilt || 0}) scale(${s * (1 + sq)} ${s * (1 - sq)})`);
        const lag = p.lag || 0;
        stem.setAttribute('d', `M0,-27 Q${lag * 4},-36 ${lag * 7},-42`); bulb.setAttribute('cx', lag * 7); bulb.setAttribute('cy', -44);
        const lx = (p.look || [0, 0])[0] * 2.6, ly = (p.look || [0, 0])[1] * 3;
        pupils.forEach((c, i) => { c.setAttribute('cx', (i ? 9.5 : -9.5) + lx); c.setAttribute('cy', ly); });
        eyes.setAttribute('transform', `translate(0 -1) scale(1 ${1 - (p.blink || 0) * .9}) translate(0 1)`);
        if (p.ground !== undefined){
          shadow.setAttribute('cx', p.x); shadow.setAttribute('cy', p.ground);
          const lift = lim((p.ground - p.y) / 160, 0, 1);
          shadow.setAttribute('rx', 24 * s * (1 - lift * .4)); shadow.setAttribute('opacity', p.show === 0 ? 0 : .12 * (1 - lift * .6) * s);
        } else shadow.setAttribute('opacity', 0);
        root.setAttribute('opacity', p.show ?? 1);
      },
    };
  }
  // Springs: a pose follows its target like a damped spring, integrated from t0 to t at 120 steps a second,
  // so every frame is reproducible. Wrists get a looser spring than the body, so hands lead with follow-through.
  // While typing, the hands stay exactly on the keys (the spring just tracks the target).
  const SPRING = { wN: [2.6, .52], wF: [2.3, .5], hN: [3, .6], hF: [3, .6], head: [2.2, .55], hair: [1.6, .3], lean: [1.6, .7], lift: [2.2, .6], shrug: [2.8, .5] };
  function springPose(target, t0, t){
    const dt = 1 / 120, steps = Math.max(0, Math.min(6000, Math.round((t - t0) / dt)));
    let p = target(t0), x = {}, v = {};
    for (const k in SPRING) if (p[k] !== undefined){ x[k] = Array.isArray(p[k]) ? p[k].slice() : p[k]; v[k] = Array.isArray(p[k]) ? p[k].map(() => 0) : 0; }
    for (let i = 1; i <= steps; i++){
      const T = target(t0 + i * dt), typing = T.typeK > .5;
      for (const k in x){
        if (T[k] === undefined) continue;
        const [f, z] = SPRING[k], K = (2 * Math.PI * f) ** 2, C = 2 * z * Math.sqrt(K);
        const exact = typing && (k === 'wN' || k === 'wF');
        if (Array.isArray(x[k])) x[k].forEach((xv, j) => { if (exact){ x[k][j] = T[k][j]; v[k][j] = 0; return; } v[k][j] += (K * (T[k][j] - xv) - C * v[k][j]) * dt; x[k][j] += v[k][j] * dt; });
        else { v[k] += (K * (T[k] - x[k]) - C * v[k]) * dt; x[k] += v[k] * dt; }
      }
    }
    return { ...target(t), ...x };
  }

  // Blink pattern: quick blinks at fixed times, so renders match.
  const blinkAt = t => { const p = (t + .3) % 3.1; return p < .12 ? Math.sin(p / .12 * Math.PI) : 0; };

  // A crowd figure: tiny, simplified, same shape language.
  function crowd(parent, top, skin, hair){
    const g = el('g', {}, parent);
    el('path', { d: 'M-12,26 C-12,12 -7,7 0,7 C7,7 12,12 12,26 Z', fill: top }, g);
    el('circle', { cx: 0, cy: 0, r: 6.5, fill: skin }, g);
    el('path', { d: 'M-6.8,-.5 C-6.8,-6 -3,-8 .5,-8 C4.5,-8 7,-5.5 6.8,-1.5 C4,-4.5 -2,-5 -6.8,-.5 Z', fill: hair }, g);
    return g;
  }

  window.Cast = { el, shade, lerp, lim, backOut, mix, deg, LOOKS, RIG, STAND, person, agent, crowd, blinkAt, toUpper, typingWrist, springPose };
})();
