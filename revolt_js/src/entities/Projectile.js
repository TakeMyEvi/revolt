import Phaser from 'phaser';

export class Mermi {
  constructor(scene, x, y, hizX, hizY, renk, hasar, oyuncuMermisi) {
    this.scene = scene;
    this.x = x; this.y = y;
    this.hizX = hizX; this.hizY = hizY;
    this.renk = renk; this.hasar = hasar;
    this.oyuncuMermisi = oyuncuMermisi;
    this.omur = oyuncuMermisi ? 80 : 100000;
    this.homing = false;
    this.hedefDusman = null;
    this.dead = false;

    this.gfx = scene.add.graphics();
    this.gfx.setDepth(9);
  }

  guncelle() {
    if (this.homing && this.hedefDusman && this.hedefDusman.can > 0) {
      const tx = this.hedefDusman.x + this.hedefDusman.w / 2;
      const ty = this.hedefDusman.y + this.hedefDusman.h / 2;
      const dx = tx - this.x, dy = ty - this.y;
      const len = Math.hypot(dx, dy) || 1;
      const hiz = Math.hypot(this.hizX, this.hizY) || 5;
      this.hizX += (dx / len * hiz - this.hizX) * 0.15;
      this.hizY += (dy / len * hiz - this.hizY) * 0.15;
    }
    this.x += this.hizX;
    this.y += this.hizY;
    this.omur--;
    if (this.omur <= 0 || this.x < -20 || this.x > 920 || this.y < -20 || this.y > 570) {
      this.dead = true;
    }
  }

  rect() {
    return new Phaser.Geom.Rectangle(this.x - 3, this.y - 3, 6, 6);
  }

  draw() {
    const g = this.gfx;
    g.clear();
    g.fillStyle(this.renk, 1);
    g.fillRect(this.x - 3, this.y - 3, 6, 6);
  }

  destroy() {
    this.gfx.destroy();
  }
}
