import { GENISLIK, YUKSEKLIK, ZEMIN_Y } from '../data/constants.js';
import { GameState } from '../data/state.js';

// Direct port of the Python original's `fon_ciz(ekran, kaydirma, bolum)` —
// two-layer parallax skyline (or, in ruins, jagged broken buildings) over a
// starfield, tinted per act, plus the deep-space planet / its ruins-theme
// shattered remains (same body, same GEZEGEN_X/Y/R — see game (1).py:3307).
const THEMES = {
  metropol: {
    bg: 0x05050f, star: 0xb4b4b4,
    bina0: 0x060614, bina1Dolgu: 0x0a0a1e, bina1Kenar: 0x001e28,
    zeminC: 0x0a0a1e, zeminCizgi: 0x00fff7, space: false, harabe: false
  },
  derinUzay: {
    bg: 0x080414, star: 0xc8b4e6,
    bina0: 0x0e061e, bina1Dolgu: 0x160a2d, bina1Kenar: 0x46145a,
    zeminC: 0x120823, zeminCizgi: 0xaa00ff, space: true, harabe: false
  },
  harabe: {
    bg: 0x140404, star: 0xdca08c,
    bina0: 0x1c0806, bina1Dolgu: 0x2d0e0a, bina1Kenar: 0x64190a,
    zeminC: 0x230a08, zeminCizgi: 0xe94560, space: false, harabe: true
  }
};

const GEZEGEN_X = 720, GEZEGEN_Y = 95, GEZEGEN_R = 70;

export function currentTheme() {
  return themeForBolum(GameState.enYuksekBolum);
}

// Story mode keys the backdrop to the stage actually being played, not the
// player's overall progress — so the world visibly changes across acts.
export function themeForBolum(bolum) {
  if (bolum <= 10) return THEMES.metropol;
  if (bolum <= 20) return THEMES.derinUzay;
  return THEMES.harabe;
}

function mod(n, m) { return ((n % m) + m) % m; }

function generateBuildings() {
  const list = [];
  for (let i = 0; i < 40; i++) {
    list.push({ x: i * 60 - 100, w: 30 + Math.random() * 40, h: 60 + Math.random() * 220, layer: Math.random() < 0.5 ? 0 : 1 });
  }
  return list;
}

function generateStars() {
  const list = [];
  for (let i = 0; i < 80; i++) {
    list.push({ x: Math.random() * GENISLIK, y: Math.random() * (YUKSEKLIK - 140), r: 1 + Math.floor(Math.random() * 2) });
  }
  return list;
}

function generateGezegenParcalari() {
  const parts = [];
  for (let i = 0; i < 7; i++) {
    const a0 = (2 * Math.PI / 7) * i + (Math.random() * 0.3 - 0.15);
    const a1 = a0 + (2 * Math.PI / 7) * (0.55 + Math.random() * 0.25);
    const icR = GEZEGEN_R * (0.15 + Math.random() * 0.2);
    const disR = GEZEGEN_R * (0.85 + Math.random() * 0.2);
    const surukleme = 12 + Math.random() * 24;
    const ortaAci = (a0 + a1) / 2;
    const pts = [];
    for (const t of [0, 0.5, 1]) { const aa = a0 + (a1 - a0) * t; pts.push({ x: Math.cos(aa) * disR, y: Math.sin(aa) * disR }); }
    for (const t of [1, 0.5, 0]) { const aa = a0 + (a1 - a0) * t; pts.push({ x: Math.cos(aa) * icR, y: Math.sin(aa) * icR }); }
    parts.push({ pts, dx: Math.cos(ortaAci) * surukleme, dy: Math.sin(ortaAci) * surukleme });
  }
  return parts;
}

function binaCiz(g, dolgu, kenar, bx, top, w, h, harabe) {
  if (!harabe) {
    g.fillStyle(dolgu, 1);
    g.fillRect(bx, top, w, h);
    if (kenar !== null) { g.lineStyle(1, kenar, 1); g.strokeRect(bx, top, w, h); }
    return;
  }
  const taban = YUKSEKLIK - 80;
  const kink1 = top + (w % 5) * 3 + 4;
  const kink2 = top + (h % 4) * 4 + 8;
  const pts = [
    { x: bx, y: taban }, { x: bx, y: kink1 }, { x: bx + w * 0.4, y: top },
    { x: bx + w * 0.7, y: kink2 }, { x: bx + w, y: top + (w % 3) * 5 }, { x: bx + w, y: taban }
  ];
  g.fillStyle(dolgu, 1);
  g.fillPoints(pts, true);
  if (kenar !== null) { g.lineStyle(1, kenar, 1); g.strokePoints(pts, true); }
  g.fillStyle(dolgu, 1);
  g.fillRect(bx - 4, taban - 6, w * 0.35, 6);
  g.fillRect(bx + w * 0.5, taban - 10, w * 0.4, 10);
}

// Draws a live, per-frame-redrawn parallax backdrop at depth -10.
// `kaydirmaFn`, when given, returns the scroll offset each frame (the
// original ties this to the player's own x position in gameplay scenes —
// `fon_ciz(ekran, oyuncu.x, ...)` — so the world visibly shifts as you move).
// Without it, the offset auto-increments each frame (menus/select screens).
export function drawThemedBackground(scene, theme = null, kaydirmaFn = null) {
  const t = theme || currentTheme();
  const buildings = generateBuildings();
  const stars = generateStars();
  const parcalari = t.harabe ? generateGezegenParcalari() : null;
  const gfx = scene.add.graphics().setDepth(-10);
  let autoKaydirma = 0;

  const draw = () => {
    const kaydirma = kaydirmaFn ? kaydirmaFn() : (autoKaydirma += 0.3);
    gfx.clear();
    gfx.fillStyle(t.bg, 1);
    gfx.fillRect(0, 0, GENISLIK, YUKSEKLIK);
    gfx.fillStyle(t.star, 1);
    for (const s of stars) gfx.fillRect(s.x, s.y, s.r, s.r);

    if (t.space) {
      gfx.fillStyle(0x281445, 1);
      gfx.fillCircle(GEZEGEN_X, GEZEGEN_Y, GEZEGEN_R);
      gfx.lineStyle(2, 0x462364, 1);
      gfx.strokeCircle(GEZEGEN_X, GEZEGEN_Y, GEZEGEN_R);
    } else if (t.harabe) {
      for (const p of parcalari) {
        const pts = p.pts.map(pt => ({ x: GEZEGEN_X + p.dx + pt.x, y: GEZEGEN_Y + p.dy + pt.y }));
        gfx.fillStyle(0x3c0e0a, 1);
        gfx.fillPoints(pts, true);
        gfx.lineStyle(2, 0x962314, 1);
        gfx.strokePoints(pts, true);
      }
    }

    for (const b of buildings) {
      if (b.layer !== 0) continue;
      const bx = mod(b.x - kaydirma * 0.2, GENISLIK + 200) - 100;
      binaCiz(gfx, t.bina0, null, bx, YUKSEKLIK - 80 - b.h, b.w, b.h, t.harabe);
    }
    for (const b of buildings) {
      if (b.layer !== 1) continue;
      const bx = mod(b.x - kaydirma * 0.5, GENISLIK + 200) - 100;
      binaCiz(gfx, t.bina1Dolgu, t.bina1Kenar, bx, YUKSEKLIK - 80 - b.h, b.w, b.h, t.harabe);
    }

    gfx.fillStyle(t.zeminC, 1);
    gfx.fillRect(0, ZEMIN_Y, GENISLIK, 80);
    gfx.fillStyle(t.zeminCizgi, 1);
    for (let x = 0; x < GENISLIK; x += 6) gfx.fillRect(x, ZEMIN_Y, 4, 2);
  };

  scene.events.on('update', draw);
  draw();
  return t;
}
