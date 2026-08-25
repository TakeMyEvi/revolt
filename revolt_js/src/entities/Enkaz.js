import Phaser from 'phaser';
import { ZEMIN_Y } from '../data/constants.js';

// Direct port of `class Enkaz` (falling debris hazard, story mode stages > 10).
export class Enkaz {
  // `olcek` is an optional extra size multiplier (ruins-only "even bigger"
  // meteors — not in the original, city/space stay at olcek=1 = unchanged).
  constructor(scene, x, buyuk, olcek = 1) {
    this.scene = scene;
    this.x = x;
    this.y = 0;
    this.buyuk = buyuk;
    this.boyut = (buyuk ? 34 : 20) * olcek;
    this.hasar = Math.round((buyuk ? 30 : 18) * olcek);
    this.hizY = buyuk ? 5.0 : 6.0;
    this.uyariKare = 40;
    this.dusuyor = false;
    this.hit = false; // consumed against the player already this fall
    this.gfx = scene.add.graphics().setDepth(6);
  }

  guncelle() {
    if (!this.dusuyor) {
      this.uyariKare--;
      if (this.uyariKare <= 0) { this.dusuyor = true; this.y = 0; }
    } else {
      this.y += this.hizY;
    }
  }

  bittiMi() { return this.dusuyor && this.y > ZEMIN_Y + 20; }

  rect() {
    const s = this.boyut;
    return new Phaser.Geom.Rectangle(this.x - s / 2, this.y - s * 0.8, s, s * 0.8);
  }

  draw() {
    const g = this.gfx;
    g.clear();
    if (!this.dusuyor) {
      if (Math.floor(this.uyariKare / 4) % 2 === 0) {
        const genislik = this.buyuk ? 6 : 4;
        g.fillStyle(0xe94560, 0.8);
        g.fillRect(this.x - genislik / 2, 0, genislik, ZEMIN_Y);
      }
    } else {
      const s = this.boyut;
      g.fillStyle(0x8c6a46, 1);
      g.fillRect(this.x - s / 2, this.y - s * 0.8, s, s * 0.8);
      g.lineStyle(1, 0x4a3420, 1);
      g.strokeRect(this.x - s / 2, this.y - s * 0.8, s, s * 0.8);
    }
  }

  destroy() { this.gfx.destroy(); }
}
