import Phaser from 'phaser';
import { ZEMIN_Y, SOLUCAN } from '../data/constants.js';

// Direct port of `class Solucan` (burrowing worm hazard).
export class Solucan {
  // opts.golge: true for OMEGA-9's summoned "gölge solucan" reinforcements —
  // same burrow/lunge behavior, recolored dark/shadow, counts as a real kill
  // (score + ulti charge via onGolgeSolucanKilled) instead of the story-mode
  // environmental worm's onWormKilled/stage-clear bookkeeping.
  constructor(scene, centerX, opts = {}) {
    this.scene = scene;
    this.golge = !!opts.golge;
    this.tip = this.golge ? 'golgeSolucan' : 'solucan';
    this.centerX = centerX;
    this.w = 30;
    this.yukseklik = 0;
    this.faz = 'yukseliyor'; // yukseliyor -> tehlikeli -> iniyor -> bitti | can<=0 -> oldu -> bitti
    this.tehlikeKare = SOLUCAN.TEHLIKE_SURESI;
    this.hasar = SOLUCAN.HASAR;
    this._can = SOLUCAN.CAN;
    this.maxCan = SOLUCAN.CAN;
    this.para = this.golge ? 90 : 40;
    this.anim = 0;
    this.sinirsiz = true; // never counts toward the "kalanDusman" stage-clear tally
    this.gfx = scene.add.graphics().setDepth(6);
  }

  // Dusman-array compatibility shims (left-edge x/y + w/h box, dead flag) so
  // this can ride along in the same bullet/melee/cone hit-test code paths.
  get x() { return this.centerX - this.w / 2; }
  set x(v) { this.centerX = v + this.w / 2; }
  get y() { return ZEMIN_Y - this.yukseklik; }
  get h() { return this.yukseklik + 12; }
  get dead() { return this.bittiMi(); }
  set dead(_) { /* driven by faz/yukseklik, not externally settable */ }

  get can() { return this._can; }
  set can(v) {
    const onceki = this._can;
    if (v < onceki && this.scene.onEnemyDamaged) this.scene.onEnemyDamaged(this, onceki - v);
    if (onceki > 0 && v <= 0) {
      if (this.golge) { if (this.scene.onGolgeSolucanKilled) this.scene.onGolgeSolucanKilled(this); }
      else if (this.scene.onWormKilled) this.scene.onWormKilled(this);
    }
    this._can = v;
  }

  vurulabilirMi() { return ['yukseliyor', 'tehlikeli', 'iniyor'].includes(this.faz) && this.yukseklik > 10; }
  tehlikeliMi() { return ['yukseliyor', 'tehlikeli'].includes(this.faz) && this.yukseklik > 14; }
  bittiMi() { return this.faz === 'bitti'; }

  guncelle() {
    this.anim++;
    if (this.can <= 0 && !['oldu', 'bitti'].includes(this.faz)) this.faz = 'oldu';
    if (this.faz === 'yukseliyor') {
      this.yukseklik += 14;
      if (this.yukseklik >= SOLUCAN.YUKSEKLIK) { this.yukseklik = SOLUCAN.YUKSEKLIK; this.faz = 'tehlikeli'; }
    } else if (this.faz === 'tehlikeli') {
      this.tehlikeKare--;
      if (this.tehlikeKare <= 0) this.faz = 'iniyor';
    } else if (this.faz === 'iniyor') {
      this.yukseklik -= 14;
      if (this.yukseklik <= 0) { this.yukseklik = 0; this.faz = 'bitti'; }
    } else if (this.faz === 'oldu') {
      this.yukseklik -= 20;
      if (this.yukseklik <= 0) { this.yukseklik = 0; this.faz = 'bitti'; }
    }
  }

  rect() {
    return new Phaser.Geom.Rectangle(this.x, this.y, this.w, this.h);
  }

  draw() {
    const g = this.gfx;
    g.clear();
    const cx = this.centerX;
    const segment = 20;
    const adet = Math.max(1, Math.floor(this.yukseklik / segment) + 1);
    const gRenk1 = this.golge ? 0x1c1024 : 0x373c44;
    const gRenk2 = this.golge ? 0x33163f : 0x5f646e;
    const gOutline = this.golge ? 0x000000 : 0x14161a;
    const gSheen = this.golge ? 0x6a2ea8 : 0x8c919b;
    for (let i = 0; i < adet; i++) {
      const sy = ZEMIN_Y - i * segment;
      const koyu = i % 2 === 1;
      const genislik = this.w - (koyu ? 5 : 0);
      g.fillStyle(koyu ? gRenk1 : gRenk2, 1);
      g.fillRect(cx - genislik / 2, sy - segment, genislik, segment + 4);
      g.lineStyle(1, gOutline, 1);
      g.strokeRect(cx - genislik / 2, sy - segment, genislik, segment + 4);
      g.lineStyle(1, gSheen, 1);
      g.lineBetween(cx - genislik / 2 + 2, sy - 2, cx + genislik / 2 - 2, sy - 2);
      if (Math.floor(this.anim / 6 + i) % 4 === 0) {
        g.fillStyle(this.faz === 'tehlikeli' ? 0xff3c3c : (this.golge ? 0xaa44ff : 0x3cb4ff), 1);
        g.fillCircle(cx + (genislik / 2 - 5) * (i % 2 === 0 ? 1 : -1), sy - segment / 2, 2);
      }
    }

    if (this.yukseklik > 10) {
      const basY = ZEMIN_Y - this.yukseklik;
      const renkGoz = this.faz === 'tehlikeli' ? 0xff1e1e : (this.golge ? 0xaa22ff : 0xffa01e);
      g.fillStyle(this.golge ? 0x0c0810 : 0x282a30, 1);
      g.fillRect(cx - 13, basY - 14, 26, 18);
      g.lineStyle(1, gOutline, 1);
      g.strokeRect(cx - 13, basY - 14, 26, 18);
      g.fillStyle(renkGoz, 1);
      g.fillCircle(cx, basY - 6, 5);
      g.lineStyle(1, 0xffffff, 1);
      g.strokeCircle(cx, basY - 6, 5);
      g.fillStyle(this.golge ? 0x4a2e5f : 0xb4b9c3, 1);
      for (let k = 0; k < 3; k++) {
        const dx = -9 + k * 9;
        g.beginPath();
        g.moveTo(cx + dx, basY - 4);
        g.lineTo(cx + dx + 5, basY - 4);
        g.lineTo(cx + dx + 2.5, basY + 6);
        g.closePath();
        g.fillPath();
      }

      const canOran = Math.max(0, this.can / this.maxCan);
      const barW = 60, barH = 13, barY = basY - 32;
      g.fillStyle(0x191919, 1);
      g.fillRect(cx - barW / 2, barY, barW, barH);
      const renkCan = canOran > 0.5 ? 0x00ff64 : (canOran > 0.25 ? 0xf5a623 : 0xe94560);
      g.fillStyle(renkCan, 1);
      g.fillRect(cx - barW / 2, barY, barW * canOran, barH);
      g.lineStyle(1, 0xc8c8c8, 1);
      g.strokeRect(cx - barW / 2, barY, barW, barH);
    }
  }

  destroy() { this.gfx.destroy(); }
}
