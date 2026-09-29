/* Frame clock and shared pieces for "The Fairer Test" scenes.
   A scene is a pure function of time: render(t) sets every element for time t,
   so any frame can be rendered alone and a render is repeatable. Motion values
   follow studio/design-system/README.md ("Motion"). */
(function () {
  'use strict';
  const FT = {};

  function bezier(x1, y1, x2, y2) {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
    const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const sx = (t) => ((ax * t + bx) * t + cx) * t;
    const sy = (t) => ((ay * t + by) * t + cy) * t;
    return (x) => {
      if (x <= 0) return 0;
      if (x >= 1) return 1;
      let lo = 0, hi = 1, t = x;
      for (let i = 0; i < 40; i++) {
        if (sx(t) < x) lo = t; else hi = t;
        t = (lo + hi) / 2;
      }
      return sy(t);
    };
  }

  FT.settle = bezier(0.2, 0.8, 0.2, 1);           // the system's one easing curve
  FT.linear = (x) => Math.min(Math.max(x, 0), 1);
  // Progress of an animation that starts at `start` and lasts `dur` seconds, 0..1.
  FT.p = (t, start, dur, ease = FT.settle) => (dur <= 0 ? (t >= start ? 1 : 0) : ease((t - start) / dur));
  FT.lerp = (a, b, p) => a + (b - a) * p;

  // Numbers use a real minus sign; units live in separate labels.
  FT.fmt = (v, digits = 1, sign = false) => {
    let s = Math.abs(v).toFixed(digits);
    if (v < 0 && Number(s) !== 0) s = '−' + s;
    else if (sign && v > 0) s = '+' + s;
    return s;
  };

  FT.value = (key) => {
    const v = window.SCENE_DATA && window.SCENE_DATA.values[key];
    if (v === undefined) throw new Error('Scene value missing from data.js: ' + key);
    return v;
  };
  FT.series = (key) => {
    const v = window.SCENE_DATA && window.SCENE_DATA.series[key];
    if (v === undefined) throw new Error('Scene series missing from data.js: ' + key);
    return v;
  };

  FT.el = (parent, cls, style, html) => {
    const e = document.createElement('div');
    if (cls) e.className = cls;
    Object.assign(e.style, style || {});
    if (html != null) e.innerHTML = html;
    parent.appendChild(e);
    return e;
  };

  // Fade in and rise; used for kickers (rise 12px) and chart labels.
  FT.rise = (e, t, start, rise = 12, dur = 0.5) => {
    const p = FT.p(t, start, dur);
    e.style.opacity = p;
    e.style.transform = 'translateY(' + (1 - p) * rise + 'px)';
  };
  // Hard cut on (captions, the "BUT" tag).
  FT.cut = (e, t, start) => { e.style.visibility = t >= start ? 'visible' : 'hidden'; };

  FT.kicker = (frame, text, s) =>
    FT.el(frame, 'kicker', { left: s.x + 'px', top: s.y + 'px', fontSize: s.size + 'px', color: s.color || 'var(--player-a-text)' }, text);

  // Claim lines are given explicitly and mask-wipe up 80 ms apart.
  FT.claim = (frame, lines, s) => {
    const box = FT.el(frame, 'claim', { left: s.x + 'px', top: s.y + 'px', fontSize: s.size + 'px',
      lineHeight: String(s.lh || 0.88), color: s.color || 'inherit' });
    const inner = lines.map((html) => {
      const line = FT.el(box, 'line', { paddingBottom: '0.04em' });
      const span = document.createElement('span');
      span.innerHTML = html;
      line.appendChild(span);
      return span;
    });
    box.at = (t, start) => inner.forEach((span, i) => {
      const p = FT.p(t, start + i * 0.08, 0.5);
      span.style.transform = 'translateY(' + (1 - p) * 110 + '%)';
    });
    return box;
  };

  // Source / scope strip: static, on screen whenever the data is.
  FT.source = (frame, rows, s) => {
    const html = rows.map(([k, v]) => '<b>' + k + '</b>&nbsp;&nbsp;' + v).join('<br>');
    return FT.el(frame, 'source', { left: s.x + 'px', width: s.width + 'px', top: s.y + 'px', fontSize: s.size + 'px',
      paddingTop: '14px' }, html);
  };

  FT.grain = (frame) => FT.el(frame, 'grain');

  const SAFE = { landscape: { top: 96, bottom: 96, left: 96, right: 96 },
                 vertical: { top: 220, bottom: 420, left: 72, right: 160 } };

  // Register a scene: formats it supports, background, duration, build and render.
  FT.scene = (def) => {
    const params = new URLSearchParams(location.search);
    const name = params.get('format') || Object.keys(def.formats)[0];
    const format = def.formats[name];
    if (!format) throw new Error('Scene does not support format ' + name);
    const size = name === 'vertical' ? { w: 1080, h: 1920 } : { w: 1920, h: 1080 };
    const frame = document.createElement('div');
    frame.className = 'frame ' + (def.background || 'paper');
    Object.assign(frame.style, { width: size.w + 'px', height: size.h + 'px' });
    document.body.appendChild(frame);
    const ctx = { format: name, w: size.w, h: size.h, safe: SAFE[name] };
    const render = format(frame, ctx);
    FT.grain(frame);
    if (params.get('safe') === '1') {
      const s = SAFE[name];
      FT.el(frame, 'safe', { left: s.left + 'px', top: s.top + 'px', right: s.right + 'px', bottom: s.bottom + 'px' });
    }
    window.__ft = { ready: true, duration: def.duration, width: size.w, height: size.h, format: name,
                    seek: (t) => { render(t); return true; } };
    render(Number(params.get('t') || def.duration));
  };

  window.FT = FT;
})();
