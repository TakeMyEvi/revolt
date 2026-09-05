import Phaser from 'phaser';
import { GENISLIK, YUKSEKLIK } from '../data/constants.js';
import { GameState } from '../data/state.js';
import { t } from '../data/translations.js';

// Touch-first control scheme, matching the Python original's twin-stick
// design (see SPEC_mobile_ui.md §A): a movement joystick, a fire joystick
// that aims+fires continuously in its drag direction, and E/Q/Special buttons.
export class MobileControls {
  constructor(scene) {
    this.scene = scene;
    this.active = !!GameState.mobilKontrolAcik;
    if (!this.active) return;

    this.joyCenter = { x: 90, y: YUKSEKLIK - 90 };
    this.fireCenter = { x: GENISLIK - 90, y: YUKSEKLIK - 90 };
    this.radius = 55;

    this.joyPointerId = null; this.joyDx = 0; this.joyDy = 0;
    this.firePointerId = null; this.fireDx = 0; this.fireDy = 0; this.fireHeld = false;

    this.specialBtn = { x: this.fireCenter.x - 129, y: this.fireCenter.y + 3, r: 26 };
    this.eBtn = { x: this.fireCenter.x - 129, y: this.fireCenter.y - 83, r: 24 };
    this.qBtn = { x: this.fireCenter.x - 193, y: this.fireCenter.y - 45, r: 24 };
    this.eJustPressed = false; this.qJustPressed = false; this.specialJustPressed = false;
    this._eDownIds = new Set(); this._qDownIds = new Set(); this._specialDownIds = new Set();

    this.gfx = scene.add.graphics().setDepth(50).setScrollFactor(0);

    scene.input.on('pointerdown', (p) => this._down(p));
    scene.input.on('pointermove', (p) => this._move(p));
    scene.input.on('pointerup', (p) => this._up(p));
    scene.input.on('pointerupoutside', (p) => this._up(p));
  }

  _dist(x1, y1, x2, y2) { return Math.hypot(x1 - x2, y1 - y2); }

  _down(p) {
    if (!this.active) return;
    if (this._dist(p.x, p.y, this.joyCenter.x, this.joyCenter.y) <= this.radius * 1.7 && this.joyPointerId === null) {
      this.joyPointerId = p.id; this._updateJoy(p);
    } else if (this._dist(p.x, p.y, this.specialBtn.x, this.specialBtn.y) <= this.specialBtn.r * 1.4) {
      this._specialDownIds.add(p.id); this.specialJustPressed = true;
    } else if (this._dist(p.x, p.y, this.eBtn.x, this.eBtn.y) <= this.eBtn.r * 1.4) {
      this._eDownIds.add(p.id); this.eJustPressed = true;
    } else if (this._dist(p.x, p.y, this.qBtn.x, this.qBtn.y) <= this.qBtn.r * 1.4) {
      this._qDownIds.add(p.id); this.qJustPressed = true;
    } else if (this._dist(p.x, p.y, this.fireCenter.x, this.fireCenter.y) <= this.radius * 1.7 && this.firePointerId === null) {
      this.firePointerId = p.id; this.fireHeld = true; this._updateFire(p);
    }
  }

  _move(p) {
    if (!this.active) return;
    if (p.id === this.joyPointerId) this._updateJoy(p);
    if (p.id === this.firePointerId) this._updateFire(p);
  }

  _up(p) {
    if (!this.active) return;
    if (p.id === this.joyPointerId) { this.joyPointerId = null; this.joyDx = 0; this.joyDy = 0; }
    if (p.id === this.firePointerId) { this.firePointerId = null; this.fireDx = 0; this.fireDy = 0; this.fireHeld = false; }
    this._eDownIds.delete(p.id);
    this._qDownIds.delete(p.id);
    this._specialDownIds.delete(p.id);
  }

  _updateJoy(p) {
    const dx = p.x - this.joyCenter.x, dy = p.y - this.joyCenter.y;
    const dist = Math.hypot(dx, dy) || 1;
    const oran = Math.min(1, dist / this.radius);
    this.joyDx = (dx / dist) * oran; this.joyDy = (dy / dist) * oran;
  }

  _updateFire(p) {
    const dx = p.x - this.fireCenter.x, dy = p.y - this.fireCenter.y;
    const dist = Math.hypot(dx, dy) || 1;
    const oran = Math.min(1, dist / this.radius);
    this.fireDx = (dx / dist) * oran; this.fireDy = (dy / dist) * oran;
  }

  // Digital movement flags (matches the source's asymmetric dead zones).
  keys() {
    if (!this.active) return null;
    return {
      left: this.joyDx < -0.35,
      right: this.joyDx > 0.35,
      up: this.joyDy < -0.40,
      down: this.joyDy > 0.55
    };
  }

  // Aim point projected 400px from the player in the fire-stick's drag
  // direction — the original's twin-stick aiming formula.
  aimPoint(playerCx, playerCy) {
    if (!this.fireHeld) return null;
    return { x: playerCx + this.fireDx * 400, y: playerCy + this.fireDy * 400 };
  }

  consumeE() { const v = this.eJustPressed; this.eJustPressed = false; return v; }
  consumeQ() { const v = this.qJustPressed; this.qJustPressed = false; return v; }
  consumeSpecial() { const v = this.specialJustPressed; this.specialJustPressed = false; return v; }

  draw() {
    if (!this.active) return;
    const g = this.gfx;
    g.clear();

    const drawStick = (center, dx, dy, knobColor) => {
      g.lineStyle(3, 0xffffff, 0.27);
      g.strokeCircle(center.x, center.y, this.radius + 8);
      g.fillStyle(knobColor, 0.85);
      g.fillCircle(center.x + dx * this.radius, center.y + dy * this.radius, 24);
      g.lineStyle(2, Phaser.Display.Color.IntegerToColor(knobColor).darken(40).color, 1);
      g.strokeCircle(center.x + dx * this.radius, center.y + dy * this.radius, 24);
    };
    drawStick(this.joyCenter, this.joyDx, this.joyDy, 0x00fff7);
    drawStick(this.fireCenter, this.fireDx, this.fireDy, 0xffee00);

    const drawBtn = (btn, label, color) => {
      g.fillStyle(0x141422, 0.55);
      g.fillEllipse(btn.x, btn.y, btn.r * 2, btn.r * 2);
      g.lineStyle(2, color, 0.9);
      g.strokeEllipse(btn.x, btn.y, btn.r * 2, btn.r * 2);
    };
    drawBtn(this.specialBtn, t('mobileSag'), 0xf5a623);
    drawBtn(this.eBtn, 'E', 0x78dcff);
    drawBtn(this.qBtn, 'Q', 0xff78dc);

    if (!this._labels) {
      this._labels = [
        this.scene.add.text(this.specialBtn.x, this.specialBtn.y, t('mobileSag'), { fontFamily: 'monospace', fontSize: '11px', color: '#f5a623' }).setOrigin(0.5).setDepth(51).setScrollFactor(0),
        this.scene.add.text(this.eBtn.x, this.eBtn.y, 'E', { fontFamily: 'monospace', fontSize: '15px', color: '#78dcff' }).setOrigin(0.5).setDepth(51).setScrollFactor(0),
        this.scene.add.text(this.qBtn.x, this.qBtn.y, 'Q', { fontFamily: 'monospace', fontSize: '15px', color: '#ff78dc' }).setOrigin(0.5).setDepth(51).setScrollFactor(0)
      ];
    }
  }

  destroy() {
    if (!this.active) return;
    this.gfx.destroy();
    if (this._labels) this._labels.forEach(l => l.destroy());
  }
}
