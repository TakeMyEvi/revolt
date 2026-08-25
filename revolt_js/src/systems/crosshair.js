import { GameState } from '../data/state.js';

// Direct port of the Python original's `nisangah_ciz(ekran, fare_x, fare_y)`.
export const NISANGAH_RENKLERI = [
  { ad: 'CYAN', renk: 0x00fff7 }, { ad: 'KIRMIZI', renk: 0xe94560 }, { ad: 'YESIL', renk: 0x00ff64 },
  { ad: 'SARI', renk: 0xffee00 }, { ad: 'BEYAZ', renk: 0xffffff }, { ad: 'MOR', renk: 0xaa00ff }, { ad: 'TURUNCU', renk: 0xf5a623 }
];
export const NISANGAH_SEKILLERI = ['arti', 'daire', 'nokta', 'kare'];

// Pure shape-drawing, reused by the in-game Crosshair below AND by Settings'
// live cursor preview (which has no player/aim point, just a fixed spot).
export function drawNisangah(g, x, y, renkIdx, sekilIdx) {
  const renk = NISANGAH_RENKLERI[renkIdx || 0].renk;
  const sekil = NISANGAH_SEKILLERI[sekilIdx || 0];
  if (sekil === 'daire') {
    g.lineStyle(2, renk, 1); g.strokeCircle(x, y, 10);
    g.fillStyle(renk, 1); g.fillCircle(x, y, 2);
  } else if (sekil === 'nokta') {
    g.fillStyle(renk, 1); g.fillCircle(x, y, 3);
  } else if (sekil === 'kare') {
    g.lineStyle(2, renk, 1); g.strokeRect(x - 9, y - 9, 18, 18);
    g.fillStyle(renk, 1); g.fillRect(x - 1, y - 1, 2, 2);
  } else { // 'arti'
    g.fillStyle(renk, 1);
    g.fillRect(x - 12, y - 1, 8, 2);
    g.fillRect(x + 4, y - 1, 8, 2);
    g.fillRect(x - 1, y - 12, 2, 8);
    g.fillRect(x - 1, y + 4, 2, 8);
    g.lineStyle(1, renk, 1); g.strokeRect(x - 4, y - 4, 8, 8);
  }
}

// Draws the aiming reticle at (x, y) every frame during gameplay — this runs
// regardless of GameState.imlecGizli (the crosshair is always the aim marker);
// imlecGizli only decides whether the OS pointer is ALSO shown on top of it.
export class Crosshair {
  constructor(scene) {
    this.scene = scene;
    this.gfx = scene.add.graphics().setDepth(45);
    this._applyOsCursor();
  }

  _applyOsCursor() {
    const canvas = this.scene.sys.game.canvas;
    if (canvas) canvas.style.cursor = GameState.imlecGizli ? 'none' : '';
  }

  draw(x, y) {
    this._applyOsCursor();
    this.gfx.clear();
    drawNisangah(this.gfx, x, y, GameState.nisangahRenkIdx, GameState.nisangahSekilIdx);
  }

  destroy() {
    this.gfx.destroy();
    const canvas = this.scene.sys.game.canvas;
    if (canvas) canvas.style.cursor = '';
  }
}
