import Phaser from 'phaser';
import { GENISLIK, ZEMIN_Y, PATLAMA_YARICAP, FITIL_SURESI, MIZRAKLI } from '../data/constants.js';

const TYPE_DEFS = {
  melee:    { w: 28, h: 48, hp: 22, spd: (b) => 2.4 + b * 0.14, para: 60, ground: true },
  ranged:   { w: 26, h: 44, hp: 15, spd: (b) => 1.0 + b * 0.07, para: 80, ground: true },
  drone:    { w: 34, h: 24, hp: 12, spd: (b) => 1.5 + b * 0.11, para: 100, ground: false, spawnOffset: 170 },
  sniper:   { w: 22, h: 30, hp: 10, spd: () => 0, para: 130, ground: false, spawnOffset: 220 },
  shield:   { w: 32, h: 50, hp: 40, spd: (b) => 0.8 + b * 0.06, para: 120, ground: true },
  tank:     { w: 52, h: 60, hp: 90, spd: (b) => 0.6 + b * 0.04, para: 200, ground: true },
  suicide:  { w: 26, h: 40, hp: 18, spd: (b) => 3.6 + b * 0.10, para: 90, ground: true },
  gorunmez: { w: 28, h: 28, hp: 14, spd: (b) => 1.3 + b * 0.08, para: 140, ground: false, spawnOffset: 150 },
  hayalet:  { w: 30, h: 34, hp: 20, spd: (b) => 1.1 + b * 0.07, para: 150, ground: false, spawnOffset: 130 },
  mizrakli: { w: 30, h: 46, hp: 9, spd: () => 0, para: 45, ground: true },
  // Elite dark-mirror of the RONIN hero — last 5 story stages only (see bolumAyar).
  // Not in the original; spear-throw + teleport, faster and tougher than mizrakli.
  golgeRonin: { w: 30, h: 48, hp: 60, spd: (b) => 1.3 + b * 0.05, para: 260, ground: true },
  boss:     { w: 60, h: 80, hp: 200, spd: (b) => 1.0 + b * 0.05, para: 500, ground: true },
  finalboss:{ w: 110, h: 160, hp: 1500, spd: () => 0, para: 3000, ground: true }
};

const COOLDOWN_BASE = { ranged: 70, drone: 65, sniper: 35, tank: 110, boss: 35, finalboss: 20, gorunmez: 55, hayalet: 65, mizrakli: 75, golgeRonin: 100 };

export class Dusman {
  constructor(scene, tip, x, bolum, side) {
    this.scene = scene;
    this.tip = tip;
    const def = TYPE_DEFS[tip];
    this.w = def.w; this.h = def.h;
    const hm = 1 + (bolum - 1) * 0.11;
    const sm = 1 + (bolum - 1) * 0.055;
    const mm = 1 + (bolum - 1) * 0.17;

    this._can = (tip === 'finalboss') ? 1500 : def.hp * hm;
    this.maxCan = this._can;
    this.bolum = bolum;
    this.para = (tip === 'finalboss') ? 3000 : def.para * mm;
    this.sinirsiz = false;

    if (tip === 'finalboss') {
      this.x = GENISLIK / 2 - 55;
      this.y = ZEMIN_Y - 160;
    } else {
      this.x = x;
      this.y = def.ground ? ZEMIN_Y - this.h : ZEMIN_Y - (def.spawnOffset || 100) - Math.random() * 60;
    }

    const yon = side !== undefined ? side : (this.x > GENISLIK / 2 ? -1 : 1);
    const baseSpeed = def.spd(bolum) * sm;
    this.hizX = baseSpeed * yon;
    this.hizY = 0;
    this.yerde = false;

    this.animFrame = 0; this.animZamani = 0;
    this.atisTimer = (COOLDOWN_BASE[tip] || 60) * 0.6 + Math.random() * 20;
    this.yavaslatildi = 0;
    this.zehirKare = 0; this.zehirTik = 0;
    this.donduKare = 0; this.cekimKare = 0;

    // suicide
    this.fitil = 0; this.patlayacak = false;

    // gorunmez / hayalet
    this.gizli = tip === 'gorunmez';
    this.fazTimer = tip === 'gorunmez' ? (90 + Math.random() * 60) : (150 + Math.random() * 70);
    this.hayaletMod = false;
    this.hayaletCooldown = 0;

    // mizrakli
    this.hedefHavada = false;
    this.mizrakAtildi = false;

    // finalboss
    if (tip === 'finalboss') {
      this.faz = 1;
      this.bossFaz = 'saldiri';
      this.bossFazTimer = 260;
      this.kalkanli = true;
      this.desenIdx = 0;
    }

    this.dead = false;
    this.gfx = scene.add.graphics();
    this.gfx.setDepth(8);
  }

  get can() { return this._can; }
  set can(v) {
    const delta = this._can - v;
    this._can = v;
    if (this.scene.onEnemyDamaged && delta > 0 && v > 0) this.scene.onEnemyDamaged(this, delta);
    if (this._can <= 0 && !this.dead) {
      this.dead = true;
      if (this.scene.onEnemyKilled) this.scene.onEnemyKilled(this);
    }
  }

  rect() { return new Phaser.Geom.Rectangle(this.x, this.y, this.w, this.h); }

  atisYapabilirMi() {
    if (this.tip === 'mizrakli') {
      return this.hedefHavada && this.x > GENISLIK * 0.2 && this.x < GENISLIK * 0.8 &&
        !this.mizrakAtildi && this.atisTimer <= 0;
    }
    if (['melee', 'shield', 'suicide'].includes(this.tip)) return false;
    if (this.gizli || this.hayaletMod) return false;
    return this.atisTimer <= 0;
  }

  atisSifirla() {
    const base = COOLDOWN_BASE[this.tip] ?? 60;
    this.atisTimer = base + Math.random() * 20;
  }

  guncelle(px, py, zaman, mermiListesi, MermiClass) {
    if (this.donduKare > 0) { this.donduKare--; return; }
    if (this.cekimKare > 0) {
      this.cekimKare--;
      this.x += (this.cekimHedefX - this.x) * 0.35;
      this.y += (this.cekimHedefY - this.y) * 0.35;
      this.animZamani++;
      if (this.atisTimer > 0) this.atisTimer--;
      return;
    }
    if (this.yavaslatildi > 0) this.yavaslatildi--;
    const yavasCarpan = this.yavaslatildi > 0 ? 0.4 : 1.0;

    if (this.zehirKare > 0) {
      this.zehirKare--; this.zehirTik--;
      if (this.zehirTik <= 0) { this.zehirTik = 30; if (this.can > 0) this.can -= 3; }
    }

    const cx = this.x + this.w / 2, cy = this.y + this.h / 2;
    const yonDusman = px > cx ? 1 : -1;

    switch (this.tip) {
      case 'suicide': {
        this.hizX = yonDusman * Math.abs(this.hizX || 1);
        this.x += this.hizX * yavasCarpan;
        this.hizY += 0.5; this.y += this.hizY;
        if (this.y >= ZEMIN_Y - this.h) { this.y = ZEMIN_Y - this.h; this.hizY = 0; this.yerde = true; }
        const mesafe = Math.hypot(px - cx, py - cy);
        if (mesafe < PATLAMA_YARICAP + 15) {
          this.fitil++;
          if (this.fitil >= FITIL_SURESI) this.patlayacak = true;
        } else this.fitil = 0;
        break;
      }
      case 'mizrakli': {
        this.x += this.hizX * yavasCarpan;
        this.hedefHavada = (ZEMIN_Y - py) > MIZRAKLI.HAVADA_ESIK;
        if (this.atisYapabilirMi()) {
          this.mizrakAtildi = true;
          const dx = px - cx, dy = py - cy, len = Math.hypot(dx, dy) || 1;
          const m = new MermiClass(this.scene, cx, cy, dx / len * 12, dy / len * 12, 0xc8c850, 14, false);
          m.mizrakMermisi = true;
          mermiListesi.push(m);
          this.atisSifirla();
        }
        break;
      }
      case 'golgeRonin': {
        if (this.isinlanmaKare > 0) {
          this.isinlanmaKare--;
          if (this.isinlanmaKare === 0) {
            this.x = Phaser.Math.Clamp(this.isinlanmaHedefX, 10, GENISLIK - this.w - 10);
            this.y = Phaser.Math.Clamp(this.isinlanmaHedefY, 44, ZEMIN_Y - this.h);
          }
        } else {
          this.hizX = yonDusman * Math.abs(this.hizX || 1);
          this.x += this.hizX * yavasCarpan;
          this.hizY += 0.4; this.y += this.hizY;
          if (this.y >= ZEMIN_Y - this.h) { this.y = ZEMIN_Y - this.h; this.hizY = 0; this.yerde = true; }
        }
        if (this.atisYapabilirMi()) {
          const dx = px - cx, dy = py - cy, len = Math.hypot(dx, dy) || 1;
          const ux = dx / len, uy = dy / len;
          const menzil = 260;
          this.isinlanmaHedefX = cx + ux * menzil - this.w / 2;
          this.isinlanmaHedefY = cy + uy * menzil - this.h / 2;
          this.isinlanmaKare = 20;
          const m = new MermiClass(this.scene, cx, cy, ux * 13, uy * 13, 0x1a1a22, 16, false);
          m.mizrakMermisi = true;
          mermiListesi.push(m);
          this.atisSifirla();
        }
        break;
      }
      case 'drone': case 'sniper': case 'gorunmez': {
        const carpan = (this.tip === 'gorunmez' && this.gizli) ? 2.0 : 1.0;
        this.hizX = yonDusman * Math.abs(this.hizX || 1);
        this.x += this.hizX * carpan * yavasCarpan;
        this.y += Math.sin(zaman / 400 + this.x * 0.01) * 1.2;
        this.y = Phaser.Math.Clamp(this.y, 44, ZEMIN_Y - this.h);
        if (this.tip === 'gorunmez') {
          this.fazTimer--;
          if (this.fazTimer <= 0) {
            this.gizli = !this.gizli;
            if (this.gizli) { this.fazTimer = 90 + Math.random() * 60; this.atisTimer = 9999; }
            else { this.fazTimer = 55; this.atisTimer = 12; }
          }
        }
        if (this.atisYapabilirMi()) this._fireBasic(px, py, cx, cy, mermiListesi, MermiClass);
        break;
      }
      case 'hayalet': {
        if (this.hayaletMod) {
          const kacisYon = px > cx ? -1 : 1;
          this.hizX = kacisYon * 2.4;
        } else {
          this.hizX = yonDusman * Math.abs(this.hizX || 1);
        }
        this.x += this.hizX * yavasCarpan;
        this.y += Math.sin(zaman / 400 + this.x * 0.01) * 1.2;
        this.y = Phaser.Math.Clamp(this.y, 44, ZEMIN_Y - this.h);
        if (!this.hayaletMod && this.hayaletCooldown <= 0 && this.can < this.maxCan * 0.4) {
          this.hayaletMod = true;
          this.can = Math.min(this.maxCan, this.can + this.can * 0.30);
          this.fazTimer = 80;
        } else {
          if (this.hayaletCooldown > 0) this.hayaletCooldown--;
          this.fazTimer--;
          if (this.fazTimer <= 0) {
            this.hayaletMod = !this.hayaletMod;
            if (this.hayaletMod) { this.can = Math.min(this.maxCan, this.can + this.can * 0.30); this.fazTimer = 80; }
            else { this.fazTimer = 150 + Math.random() * 70; this.atisTimer = 20; this.hayaletCooldown = 100; }
          }
        }
        if (this.atisYapabilirMi()) this._fireBasic(px, py, cx, cy, mermiListesi, MermiClass);
        break;
      }
      case 'tank': {
        this.hizX = yonDusman * Math.abs(this.hizX || 1);
        this.x += this.hizX * yavasCarpan;
        this.hizY += 0.6; this.y += this.hizY;
        if (this.y >= ZEMIN_Y - this.h) { this.y = ZEMIN_Y - this.h; this.hizY = 0; this.yerde = true; }
        if (this.atisYapabilirMi()) {
          const dx = px - cx, dy = py - cy, len = Math.hypot(dx, dy) || 1;
          mermiListesi.push(new MermiClass(this.scene, cx, this.y - 10,
            dx / len * 5, dy / len * 5 - 3, 0xff8800, 22, false));
          this.atisSifirla();
        }
        break;
      }
      case 'boss': {
        this.hizX = yonDusman * Math.abs(this.hizX || 1);
        this.x += this.hizX * yavasCarpan;
        this.hizY += 0.6; this.y += this.hizY;
        if (this.y >= ZEMIN_Y - this.h) { this.y = ZEMIN_Y - this.h; this.hizY = 0; this.yerde = true; }
        if (this.atisYapabilirMi()) {
          const aci = Math.atan2(py - cy, px - cx);
          for (let k = 0; k < 3; k++) {
            const a = aci + (k - 1) * 0.28;
            mermiListesi.push(new MermiClass(this.scene, cx, cy, Math.cos(a) * 5, Math.sin(a) * 5, 0xff4400, 18, false));
          }
          this.atisSifirla();
        }
        break;
      }
      case 'finalboss': {
        this.bossFazTimer--;
        if (this.bossFazTimer <= 0) {
          if (this.bossFaz === 'saldiri') {
            this.bossFaz = 'yorgun'; this.kalkanli = false; this.bossFazTimer = 150; this.atisTimer = 9999;
          } else {
            this.bossFaz = 'saldiri'; this.kalkanli = true; this.bossFazTimer = 260;
            this.desenIdx = (this.desenIdx + 1) % 3; this.atisTimer = 30;
          }
        }
        if (this.faz === 1 && this.can < this.maxCan * 0.5) this.faz = 2;
        if (this.faz === 2 && this.can < this.maxCan * 0.2) this.faz = 3;
        if (this.bossFaz === 'saldiri' && this.atisTimer <= 0) {
          this._finalbossAttack(px, py, cx, cy, mermiListesi, MermiClass);
          this.atisTimer = 60;
        }
        break;
      }
      default: { // melee, ranged, shield
        this.hizX = yonDusman * Math.abs(this.hizX || 1);
        this.x += this.hizX * yavasCarpan;
        this.hizY += 0.4; this.y += this.hizY;
        if (this.y >= ZEMIN_Y - this.h) { this.y = ZEMIN_Y - this.h; this.hizY = 0; this.yerde = true; }
        if (this.atisYapabilirMi()) this._fireBasic(px, py, cx, cy, mermiListesi, MermiClass);
        break;
      }
    }

    if (!this.sinirsiz) {
      if (this.x < 10) { this.x = 10; this.hizX = Math.abs(this.hizX); }
      if (this.x > GENISLIK - this.w - 10) { this.x = GENISLIK - this.w - 10; this.hizX = -Math.abs(this.hizX); }
    }

    this.animZamani++;
    if (this.animZamani >= 10) { this.animZamani = 0; this.animFrame = 1 - this.animFrame; }
    if (this.atisTimer > 0) this.atisTimer--;
  }

  _fireBasic(px, py, cx, cy, mermiListesi, MermiClass) {
    const dx = px - cx, dy = py - cy, len = Math.hypot(dx, dy) || 1;
    let speed = 3.5, color = 0xff3366, dmg = 8;
    if (this.tip === 'sniper') {
      for (let i = 0; i < 3; i++) {
        mermiListesi.push(new MermiClass(this.scene, cx, cy, dx / len * 14, dy / len * 14, 0xff0000, 18, false));
      }
      this.atisSifirla();
      return;
    }
    if (this.tip === 'gorunmez') { color = 0xb400ff; dmg = 12; }
    if (this.tip === 'hayalet') { speed = 3.2; color = 0xbeffff; dmg = 9; }
    mermiListesi.push(new MermiClass(this.scene, cx, cy, dx / len * speed, dy / len * speed, color, dmg, false));
    this.atisSifirla();
  }

  _finalbossAttack(px, py, cx, cy, mermiListesi, MermiClass) {
    const aci = Math.atan2(py - cy, px - cx);
    const sp = 4 + this.faz * 1.5;
    const hasar = 20 + this.faz * 5;
    const ex = cx, ey = this.y + this.h * 0.3;
    if (this.desenIdx === 0) {
      const n = this.faz === 1 ? 3 : (this.faz === 2 ? 5 : 8);
      const spread = this.faz === 1 ? 0.3 : 0.2;
      for (let k = 0; k < n; k++) {
        const a = aci + (k - (n - 1) / 2) * spread;
        mermiListesi.push(new MermiClass(this.scene, ex, ey, Math.cos(a) * sp, Math.sin(a) * sp, 0xff0066, hasar, false));
      }
    } else if (this.desenIdx === 1) {
      const n = this.faz >= 2 ? 5 : 4;
      for (let k = 0; k < n; k++) {
        const yofs = (k - (n - 1) / 2) * 22;
        mermiListesi.push(new MermiClass(this.scene, ex, ey + yofs, Math.cos(aci) * sp * 0.9, Math.sin(aci) * sp * 0.9, 0xff0066, hasar, false));
      }
    } else {
      const n = this.faz === 1 ? 2 : 3;
      for (let k = 0; k < n; k++) {
        const dx = px - ex, dy = py - ey, len = Math.hypot(dx, dy) || 1;
        mermiListesi.push(new MermiClass(this.scene, ex, ey, dx / len * (sp + 3), dy / len * (sp + 3), 0xff0066, hasar + 5, false));
      }
    }
  }

  // Faithful port of the Python original's `Dusman.ciz` — same rects/polygons/colors.
  draw(zaman = 0) {
    const g = this.gfx;
    g.clear();
    if (this.tip === 'gorunmez' && this.gizli) return; // fully invisible while cloaked

    const px = this.x, py = this.y, w = this.w, h = this.h;
    const hpOran = this.can / this.maxCan;

    if (this.tip === 'finalboss') {
      const barY = 550 - 40;
      g.fillStyle(0x1e1e1e, 1);
      g.fillRect(10, barY, GENISLIK - 20, 14);
      const renk = hpOran > 0.5 ? 0x00ff64 : (hpOran > 0.2 ? 0xf5a623 : 0xe94560);
      g.fillStyle(renk, 1);
      g.fillRect(10, barY, Math.max(0, (GENISLIK - 20) * hpOran), 14);
      g.lineStyle(2, 0xff0066, 1);
      g.strokeRect(10, barY, GENISLIK - 20, 14);
    } else {
      g.fillStyle(0x282828, 1);
      g.fillRect(px, py - 8, w, 4);
      const renk = hpOran > 0.5 ? 0x00ff64 : 0xe94560;
      g.fillStyle(renk, 1);
      g.fillRect(px, py - 8, Math.max(0, w * hpOran), 4);
    }

    switch (this.tip) {
      case 'melee': {
        g.fillStyle(0xcc2233, 1); g.fillRect(px + 2, py, w - 4, h);
        g.fillStyle(0xee3344, 1); g.fillRect(px + 3, py + 2, w - 6, 16);
        g.fillStyle(0xffee00, 1); g.fillRect(px + 6, py + 6, 4, 4); g.fillRect(px + w - 10, py + 6, 4, 4);
        const lf = this.animFrame === 0 ? 4 : 0;
        g.fillStyle(0x881122, 1);
        g.fillRect(px + 2, py + h - 14, 10, 14 + lf);
        g.fillRect(px + w - 12, py + h - 14, 10, 14 - lf);
        g.fillStyle(0xc8c8c8, 1); g.fillRect(px - 12, py + h / 3, 12, 4);
        break;
      }
      case 'ranged': {
        g.fillStyle(0x1a44cc, 1); g.fillRect(px + 2, py, w - 4, h);
        g.fillStyle(0x2255ee, 1); g.fillRect(px + 3, py + 2, w - 6, 16);
        g.fillStyle(0x00fff7, 1); g.fillRect(px + 5, py + 6, w - 10, 4);
        const lf = this.animFrame === 0 ? 4 : 0;
        g.fillStyle(0x0d2e88, 1);
        g.fillRect(px + 2, py + h - 14, 10, 14 + lf);
        g.fillRect(px + w - 12, py + h - 14, 10, 14 - lf);
        g.fillStyle(0x44aaff, 1); g.fillRect(px + w, py + h / 3, 10, 4);
        break;
      }
      case 'drone': {
        g.fillStyle(0x1a2299, 1);
        this._poly(g, [[px + w / 2, py], [px + w, py + h / 2], [px + w / 2, py + h], [px, py + h / 2]]);
        g.fillStyle(0x4466ff, 1);
        g.fillRect(px - 10, py + h / 2 - 2, 10, 4);
        g.fillRect(px + w, py + h / 2 - 2, 10, 4);
        g.fillStyle(0xff2244, 1); g.fillRect(px + w / 2 - 3, py + h / 2 - 3, 6, 6);
        break;
      }
      case 'sniper': {
        g.fillStyle(0x440000, 1);
        this._poly(g, [[px + w / 2, py], [px + w, py + h / 2], [px + w / 2, py + h], [px, py + h / 2]]);
        g.fillStyle(0xff0000, 1); g.fillRect(px + w / 2 - 3, py + h / 2 - 3, 6, 6);
        break;
      }
      case 'shield': {
        g.fillStyle(0x224488, 1); g.fillRect(px + 2, py, w - 4, h);
        g.fillStyle(0x3355aa, 1); g.fillRect(px + 3, py + 2, w - 6, 16);
        g.fillStyle(0x00fff7, 1); g.fillRect(px + 5, py + 6, w - 10, 4);
        const yon = this.hizX < 0 ? -1 : 1;
        const kx = yon < 0 ? px - 10 : px + w;
        g.fillStyle(0x00fff7, 1); g.fillRect(kx, py + 4, 8, h - 8);
        break;
      }
      case 'tank': {
        g.fillStyle(0x554400, 1); g.fillRect(px, py + 10, w, h - 10);
        g.fillStyle(0x887722, 1); g.fillRect(px + 6, py, w - 12, 24);
        g.fillStyle(0x323232, 1); g.fillRect(px, py + h - 10, w, 10);
        const yon = this.hizX > 0 ? 1 : -1;
        const topX = yon > 0 ? px + w / 2 : px + w / 2 - 22;
        g.fillStyle(0xaaaaaa, 1); g.fillRect(topX, py + 10, 22, 8);
        break;
      }
      case 'suicide': {
        const fitilAktif = this.fitil > 0;
        const yaniyor = fitilAktif && Math.floor(this.fitil / 3) % 2 === 0;
        g.fillStyle(yaniyor ? 0xffff00 : 0xcc4400, 1); g.fillRect(px + 2, py, w - 4, h);
        g.fillStyle(0xff8800, 1); g.fillRect(px + 3, py + 2, w - 6, 14);
        g.fillStyle(0xe94560, 1); g.fillRect(px + w / 2 - 3, py + h / 2 - 3, 6, 6);
        const lf = this.animFrame === 0 ? 4 : 0;
        g.fillStyle(0x882200, 1);
        g.fillRect(px + 2, py + h - 12, 10, 12 + lf);
        g.fillRect(px + w - 12, py + h - 12, 10, 12 - lf);
        if (fitilAktif) {
          const yaricap = PATLAMA_YARICAP * (this.fitil / FITIL_SURESI);
          g.lineStyle(1, 0xe94560, 1);
          g.strokeCircle(px + w / 2, py + h / 2, yaricap);
        }
        break;
      }
      case 'gorunmez': {
        const belirme = 1.0 - Math.min(1.0, this.fazTimer / 55);
        g.fillStyle(0x7800c8, 1);
        this._poly(g, [[px + w / 2, py], [px + w, py + h / 3], [px + w, py + h], [px, py + h], [px, py + h / 3]]);
        g.fillStyle(0xc878ff, 1); g.fillRect(px + w / 2 - 3, py + h / 2 - 3, 6, 6);
        if (belirme < 1.0) { g.lineStyle(1, 0xc878ff, 1); g.strokeRect(px - 4, py - 4, w + 8, h + 8); }
        break;
      }
      case 'hayalet': {
        const renk = 0xbeffff;
        if (this.hayaletMod) {
          g.fillStyle(renk, 110 / 255); g.fillRect(px, py, w, h);
          g.lineStyle(1, renk, 160 / 255); g.strokeRect(px, py, w, h);
        } else {
          g.fillStyle(0x3c8c8c, 1); g.fillRect(px + 2, py, w - 4, h);
          g.lineStyle(1, renk, 1); g.strokeRect(px + 4, py + 4, w - 8, h - 8);
          g.fillStyle(renk, 1); g.fillRect(px + w / 2 - 3, py + 6, 6, 6);
        }
        break;
      }
      case 'mizrakli': {
        const yon = this.hizX >= 0 ? 1 : -1;
        g.fillStyle(0x5a5f69, 1); g.fillRect(px + 2, py, w - 4, h);
        g.fillStyle(0x828791, 1); g.fillRect(px + 3, py + 2, w - 6, 14);
        const gozRenk = this.hedefHavada ? 0xff3c3c : 0xffbe3c;
        g.fillStyle(gozRenk, 1); g.fillRect(px + w / 2 - 3, py + 6, 6, 6);
        const lf = this.animFrame === 0 ? 5 : 0;
        g.fillStyle(0x3c4048, 1);
        g.fillRect(px + 2, py + h - 14, 9, 14 + lf);
        g.fillRect(px + w - 11, py + h - 14, 9, 14 - lf);
        if (!this.mizrakAtildi) {
          const ucX = px + (yon > 0 ? w + 26 : -26);
          const spearY = py + h / 2 - 6;
          g.lineStyle(3, 0xc8c8d2, 1);
          g.lineBetween(px + w / 2, spearY, ucX, spearY);
          g.fillStyle(0xe6e6eb, 1);
          this._poly(g, [[ucX, spearY - 5], [ucX + 9 * yon, spearY], [ucX, spearY + 5]]);
        }
        break;
      }
      case 'golgeRonin': {
        const yon = this.hizX >= 0 ? 1 : -1;
        const isinlaniyor = this.isinlanmaKare > 0;
        g.fillStyle(0x0a0a0f, 1); g.fillRect(px + 2, py, w - 4, h);
        g.fillStyle(0x18141c, 1); g.fillRect(px + 3, py + 2, w - 6, 16);
        g.fillStyle(0x6622aa, 1); g.fillRect(px + w / 2 - 3, py + 6, 6, 6);
        const lf = this.animFrame === 0 ? 4 : 0;
        g.fillStyle(0x000000, 1);
        g.fillRect(px + 2, py + h - 14, 10, 14 + lf);
        g.fillRect(px + w - 12, py + h - 14, 10, 14 - lf);
        if (isinlaniyor) {
          g.lineStyle(2, 0xaa78ff, 0.6);
          g.strokeRect(px - 4, py - 4, w + 8, h + 8);
        } else {
          const ucX = px + (yon > 0 ? w + 30 : -30);
          const spearY = py + h / 2 - 6;
          g.lineStyle(3, 0x1a1a22, 1);
          g.lineBetween(px + w / 2, spearY, ucX, spearY);
          g.fillStyle(0x2a2a35, 1);
          this._poly(g, [[ucX, spearY - 5], [ucX + 9 * yon, spearY], [ucX, spearY + 5]]);
        }
        break;
      }
      case 'boss': {
        g.fillStyle(0x660011, 1); g.fillRect(px, py, w, h);
        g.fillStyle(0x990022, 1); g.fillRect(px + 4, py + 4, w - 8, 22);
        g.fillStyle(0xff0000, 1); g.fillRect(px + 8, py + 10, 8, 8); g.fillRect(px + w - 16, py + 10, 8, 8);
        g.fillStyle(0xcc0000, 1); g.fillRect(px + 4, py + h - 18, 12, 18); g.fillRect(px + w - 16, py + h - 18, 12, 18);
        break;
      }
      case 'finalboss': {
        const faz = this.faz || 1;
        const kalkanli = this.kalkanli;
        const pc = faz === 1 ? 0xcc0044 : (faz === 2 ? 0xff0066 : 0xff0000);
        const flash = Math.floor(zaman / 200) % 2 === 0;

        const panelX = px - 40, panelY = py - 30, panelW = w + 80, panelH = h + 55;
        g.fillStyle(0x080810, 1); g.fillRect(panelX, panelY, panelW, panelH);
        g.lineStyle(2, 0x28283c, 1); g.strokeRect(panelX, panelY, panelW, panelH);
        g.lineStyle(1, 0x141422, 1);
        for (let gx = panelX + 16; gx < panelX + panelW; gx += 24) g.lineBetween(gx, panelY, gx, panelY + panelH);
        for (let gy = panelY + 16; gy < panelY + panelH; gy += 24) g.lineBetween(panelX, gy, panelX + panelW, gy);

        g.fillStyle(0x1a0011, 1); g.fillRect(px + 8, py, w - 16, h);
        g.fillStyle(0x440022, 1); g.fillRect(px + 14, py + 8, w - 28, 50);
        g.fillStyle(flash ? pc : 0x880033, 1); g.fillRect(px + w / 2 - 10, py + 30, 20, 20);
        g.fillStyle(0xff0000, 1); g.fillRect(px + w / 2 - 18, py + 14, 10, 10); g.fillRect(px + w / 2 + 8, py + 14, 10, 10);
        g.fillStyle(0x330011, 1); g.fillRect(px - 16, py + 18, 16, 10); g.fillRect(px + w, py + 18, 16, 10);
        g.fillStyle(0x880000, 1); g.fillRect(px - 22, py + 20, 8, 6); g.fillRect(px + w + 14, py + 20, 8, 6);
        g.fillStyle(0x220008, 1); g.fillRect(px + 10, py + h - 30, 22, 30); g.fillRect(px + w - 32, py + h - 30, 22, 30);

        if (kalkanli) {
          const nabiz = 6 + Math.floor(4 * Math.sin(zaman / 120));
          g.fillStyle(0x00fff7, 55 / 255);
          g.fillEllipse(px + w / 2, py + h / 2, w + 40, h + 40);
          g.lineStyle(3 + Math.floor(nabiz / 3), 0x00fff7, 160 / 255);
          g.strokeEllipse(px + w / 2, py + h / 2, w + 40, h + 40);
        }

        const durum = kalkanli ? 'KALKANLI' : 'ZAYIF - VUR!';
        const durumRenk = kalkanli ? '#00fff7' : '#00ff64';
        if (!this._labelText) {
          this._labelText = this.scene.add.text(0, 0, '', { fontFamily: 'monospace', fontSize: '11px', fontStyle: 'bold' }).setDepth(9);
        }
        this._labelText.setText(`OMEGA-9  FAZ ${faz}  [${durum}]`);
        this._labelText.setColor(durumRenk);
        this._labelText.setPosition(px + w / 2 - this._labelText.width / 2, py - 18);
        break;
      }
    }

    if (this.zehirKare > 0) { g.fillStyle(0x3cdc5a, 90 / 255); g.fillRect(px, py, w, h); }
    if (this.donduKare > 0) { g.fillStyle(0x96dcff, 130 / 255); g.fillRect(px, py, w, h); }
  }

  _poly(g, pts) {
    g.beginPath();
    g.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]);
    g.closePath();
    g.fillPath();
  }

  destroy() {
    this.gfx.destroy();
    if (this._labelText) this._labelText.destroy();
  }
}
