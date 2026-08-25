import Phaser from 'phaser';
import { ZEMIN_Y } from '../data/constants.js';

class Pickup {
  constructor(scene, x, y, omur) {
    this.scene = scene;
    this.x = x; this.y = y;
    this.hizY = -3.5;
    this.hizX = Phaser.Math.FloatBetween(-1.5, 1.5);
    this.omur = omur;
    this.dead = false;
    this.gfx = scene.add.graphics();
    this.gfx.setDepth(7);
  }

  guncelle() {
    this.hizY += 0.4;
    this.y += this.hizY;
    this.x += this.hizX;
    if (this.y >= ZEMIN_Y - 8) { this.y = ZEMIN_Y - 8; this.hizY = 0; }
    this.omur--;
    if (this.omur <= 0) this.dead = true;
  }

  destroy() { this.gfx.destroy(); }
}

export class Xp extends Pickup {
  constructor(scene, x, y) {
    super(scene, x, y, 260);
    this.deger = 1;
  }

  rect() { return new Phaser.Geom.Rectangle(this.x - 10, this.y - 10, 20, 20); }

  draw() {
    const g = this.gfx;
    g.clear();
    g.fillStyle(0x00ff64, 1);
    g.fillRect(this.x - 5, this.y - 5, 10, 10);
  }
}

export class CanTopu extends Pickup {
  constructor(scene, x, y) {
    super(scene, x, y, 320);
  }

  rect() { return new Phaser.Geom.Rectangle(this.x - 11, this.y - 11, 22, 22); }

  draw() {
    const g = this.gfx;
    g.clear();
    g.fillStyle(0xff3c5a, 1);
    g.fillCircle(this.x, this.y, 9);
    g.fillStyle(0xffffff, 1);
    g.fillRect(this.x - 1, this.y - 4, 2, 8);
    g.fillRect(this.x - 4, this.y - 1, 8, 2);
  }
}
