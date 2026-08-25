import Phaser from 'phaser';
import { GENISLIK, ZEMIN_Y, REAPER } from '../data/constants.js';

// Direct port of `class Iskelet` (REAPER's summoned skeleton ally).
export class Iskelet {
  constructor(scene, x, y, guclu = false, okcu = false) {
    this.scene = scene;
    this.x = x; this.y = y;
    this.w = 22; this.h = 34;
    this.hizY = 0;
    this.can = REAPER.ISKELET_CAN;
    this.maxCan = REAPER.ISKELET_CAN;
    this.hasar = REAPER.ISKELET_HASAR;
    this.hiz = REAPER.ISKELET_HIZ;
    this.guclu = guclu;
    this.okcu = okcu;
    this.gucSuresi = 0;
    this.atisBekleme = 0;
    this.ziplamaBekleme = 0;
    this.yerde = false;
    this.animZamani = 0; this.animFrame = 0;
    this.dead = false;
    this.gfx = scene.add.graphics().setDepth(8);
  }

  rect() { return new Phaser.Geom.Rectangle(this.x, this.y, this.w, this.h); }

  guclendir() {
    this.can = this.maxCan;
    this.gucSuresi = REAPER.GUC_SURESI;
  }

  guncelle(enemies, applyDamage) {
    this.hizY += 0.6;
    this.y += this.hizY;
    this.yerde = false;
    if (this.y >= ZEMIN_Y - this.h) { this.y = ZEMIN_Y - this.h; this.hizY = 0; this.yerde = true; }

    if (this.gucSuresi > 0) this.gucSuresi--;
    if (this.atisBekleme > 0) this.atisBekleme--;
    if (this.ziplamaBekleme > 0) this.ziplamaBekleme--;

    let hedef = null, enYakin = Infinity;
    const mx = this.x + this.w / 2;
    for (const d of enemies) {
      if (d.dead) continue;
      if (d.tip === 'hayalet' && d.hayaletMod) continue;
      const mesafe = Math.hypot((d.x + d.w / 2) - mx, (d.y + d.h / 2) - (this.y + this.h / 2));
      if (mesafe < enYakin) { enYakin = mesafe; hedef = d; }
    }

    if (hedef) {
      const hedefMx = hedef.x + hedef.w / 2;
      const mesafeX = Math.abs(hedefMx - mx);
      if (mesafeX > REAPER.ISKELET_MENZIL) {
        const yon = hedefMx > mx ? 1 : -1;
        const carpan = this.gucSuresi > 0 ? REAPER.GUC_CARPAN : 1;
        this.x += this.hiz * carpan * yon;
      } else if (this.atisBekleme <= 0) {
        if (hedef.can > 0) { applyDamage(hedef, this.hasar); this.atisBekleme = 40; }
      }
      if (this.yerde && this.ziplamaBekleme <= 0 && (hedef.y + hedef.h) < this.y - 20) {
        this.hizY = -14; this.yerde = false; this.ziplamaBekleme = 40;
      }
    }

    this.x = Phaser.Math.Clamp(this.x, 0, GENISLIK - this.w);
    this.animZamani++;
    if (this.animZamani >= 10) { this.animZamani = 0; this.animFrame = 1 - this.animFrame; }
  }

  draw() {
    const g = this.gfx;
    g.clear();
    let body = 0xe1dccd, eye = 0x2a2420;
    if (this.gucSuresi > 0) { body = 0x0a0a0c; eye = 0xff2819; }
    else if (this.okcu) { body = 0x2846a0; eye = 0xa0d2ff; }
    else if (this.guclu) { body = 0x1a0e11; eye = 0xff2d28; }

    g.fillStyle(body, 1);
    g.fillRect(this.x, this.y, this.w, this.h);
    g.fillStyle(eye, 1);
    g.fillRect(this.x + 5, this.y + 8, 3, 3);
    g.fillRect(this.x + this.w - 8, this.y + 8, 3, 3);

    if (this.guclu) {
      const t = this.scene.time.now;
      for (let k = 0; k < 3; k++) {
        const a = t / 220 + k * (2 * Math.PI / 3);
        const r = 11 + (k % 2) * 4;
        g.fillStyle(0xff2828, 0.8);
        g.fillCircle(this.x + this.w / 2 + Math.cos(a) * r, this.y + this.h / 2 + Math.sin(a) * r, 2);
      }
    }

    const hpRatio = this.can / this.maxCan;
    g.fillStyle(0x000000, 0.6);
    g.fillRect(this.x, this.y - 6, this.w, 3);
    g.fillStyle(hpRatio > 0.4 ? 0x00ff64 : 0xe94560, 1);
    g.fillRect(this.x, this.y - 6, this.w * Math.max(0, hpRatio), 3);
  }

  destroy() { this.gfx.destroy(); }
}
