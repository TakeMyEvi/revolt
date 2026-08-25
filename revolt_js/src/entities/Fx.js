import Phaser from 'phaser';

// Direct port of `class Parca` (generic particle) and `class HasarYazisi`
// (floating combat text) plus the `patlama()` burst factory.
export class Parca {
  constructor(scene, x, y, renk) {
    this.scene = scene;
    this.x = x; this.y = y;
    this.hizX = Phaser.Math.FloatBetween(-4, 4);
    this.hizY = Phaser.Math.FloatBetween(-4, 4);
    this.renk = renk;
    this.omur = Phaser.Math.Between(15, 28);
    this.boyut = Phaser.Math.Between(2, 5);
    this.dead = false;
    this.gfx = scene.add.graphics().setDepth(15);
  }

  guncelle() {
    this.hizY += 0.2;
    this.x += this.hizX; this.y += this.hizY;
    this.omur--;
    if (this.omur <= 0) this.dead = true;
  }

  draw() {
    this.gfx.clear();
    this.gfx.fillStyle(this.renk, 1);
    this.gfx.fillRect(this.x, this.y, this.boyut, this.boyut);
  }

  destroy() { this.gfx.destroy(); }
}

export function patlama(scene, x, y, renk = 0xf5a623, sayi = 12) {
  const out = [];
  for (let i = 0; i < sayi; i++) out.push(new Parca(scene, x, y, renk));
  return out;
}

export class HasarYazisi {
  constructor(scene, x, y, deger, renk, art = false, yonX = 0, yonY = -1) {
    this.scene = scene;
    this.x = x; this.y = y;
    this.deger = deger; this.renk = renk; this.art = art;
    const len = Math.hypot(yonX, yonY) || 1;
    this.hizX = (yonX / len) * 1.6;
    this.hizY = (yonY / len) * 1.6 - 0.4;
    this.omurMax = 34; this.omur = 34;
    this.dead = false;
    this.text = scene.add.text(x, y, this.art ? `+${deger}` : `${deger}`, {
      fontFamily: 'monospace', fontSize: deger > 50 ? '16px' : '12px', color: Phaser.Display.Color.IntegerToColor(renk).rgba
    }).setOrigin(0.5).setDepth(25);
  }

  guncelle() {
    this.hizX *= 0.96; this.hizY *= 0.96;
    this.x += this.hizX; this.y += this.hizY;
    this.omur--;
    if (this.omur <= 0) this.dead = true;
  }

  draw() {
    this.text.setPosition(this.x, this.y);
    this.text.setAlpha(Math.max(0, this.omur / this.omurMax));
  }

  destroy() { this.text.destroy(); }
}
