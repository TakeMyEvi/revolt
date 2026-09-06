import Phaser from 'phaser';
import { GENISLIK, ZEMIN_Y, PATLAMA_YARICAP, FITIL_SURESI, MIZRAKLI } from '../data/constants.js';
import { Solucan } from './Solucan.js';
import { t } from '../data/translations.js';
import { patlama } from './Fx.js';

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

// How close a ranged attacker (gunner/drone/sniper/cloaked/ghost) lets the
// player get before it stops advancing and just shoots from where it is,
// instead of walking all the way into melee range like the melee types do.
const RANGED_DURMA_MESAFESI = 260;

export class Dusman {
  // opts.golge: true for OMEGA-9's summoned shadow reinforcements — any
  // regular type, reskinned dark/glowing-purple, scaled to a mild fixed
  // level instead of the boss's own (usually very high) stage number, and
  // routed through onGolgeDusmanKilled instead of onEnemyKilled so they
  // never affect the stage's kalanDusman/spawnSira clear tally.
  constructor(scene, tip, x, bolum, side, opts = {}) {
    this.scene = scene;
    this.tip = tip;
    this.golge = !!opts.golge;
    const def = TYPE_DEFS[tip];
    this.w = def.w; this.h = def.h;
    const efektifBolum = this.golge ? Math.min(bolum, 6) : bolum;
    const hm = 1 + (efektifBolum - 1) * 0.11;
    const sm = 1 + (efektifBolum - 1) * 0.055;
    const mm = 1 + (efektifBolum - 1) * 0.17;

    this._can = (tip === 'finalboss') ? 1500 : def.hp * hm * (this.golge ? 0.85 : 1);
    this.maxCan = this._can;
    this.bolum = bolum;
    this.para = (tip === 'finalboss') ? 3000 : def.para * mm * (this.golge ? 1.4 : 1);
    this.sinirsiz = false;

    if (tip === 'finalboss') {
      this.x = GENISLIK / 2 - 55;
      this.y = ZEMIN_Y - 160;
    } else {
      this.x = x;
      this.y = def.ground ? ZEMIN_Y - this.h : ZEMIN_Y - (def.spawnOffset || 100) - Math.random() * 60;
    }

    const yon = side !== undefined ? side : (this.x > GENISLIK / 2 ? -1 : 1);
    const baseSpeed = def.spd(efektifBolum) * sm;
    this.hizX = baseSpeed * yon;
    // The movement code below reads this to re-derive a signed speed toward
    // the player each frame. It used to fall back to `this.hizX || 1`, which
    // silently turned any intentionally-stationary type (sniper's spd is a
    // flat 0) into a speed-1 walker — snipers were supposed to plant and
    // shoot, not close in. Storing the true magnitude once avoids that trap.
    this.hizTaban = Math.abs(baseSpeed);
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
      this.dikenler = [];
      this.dikenTimer = 200;
      this.lazerler = [];
      this.lazerTimer = 320;
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
      if (this.golge) { if (this.scene.onGolgeDusmanKilled) this.scene.onGolgeDusmanKilled(this); }
      else if (this.scene.onEnemyKilled) this.scene.onEnemyKilled(this);
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

  // WRAITH's ultimate: while active, every bullet an enemy fires is hijacked
  // the instant it's created — flips to a player-owned homing soul that flies
  // back at whoever fired it. Matches game (1).py's `wraith_modu and
  // oyuncu.wraith_ulti_aktif` bullet-conversion, which the JS port had never
  // wired up (only the 10%-damage-taken side of the ulti existed). A small
  // soul-colored spark at the muzzle makes the deflection actually visible.
  _wraithSektir(m) {
    const p = this.scene?.player;
    if (p && p.heroId === 7 && p.wraithUltiAktif) {
      m.oyuncuMermisi = true;
      m.renk = 0x50a0ff;
      m.wraithMermisi = true;
      m.homing = true;
      m.hedefDusman = this;
      // Spawns inside the shooter's own hitbox, so give it a brief grace
      // period before it can land a hit — otherwise it "deflects" and hits
      // the same enemy on the very same frame, before any homing is visible.
      m.golgeGecikme = 8;
      if (this.scene.fx) this.scene.fx.push(...patlama(this.scene, m.x, m.y, 0x50a0ff, 6));
    }
    return m;
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
        this.hizX = yonDusman * this.hizTaban;
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
          mermiListesi.push(this._wraithSektir(m));
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
          this.hizX = yonDusman * this.hizTaban;
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
          // Throw first, then teleport — the old 20-frame gap (~0.33s) read as
          // instant since the spear reached its target the same moment the
          // Ronin vanished. Widened so the throw clearly registers as its own
          // beat before the teleport happens.
          this.isinlanmaKare = 45;
          const m = new MermiClass(this.scene, cx, cy, ux * 8, uy * 8, 0x1a1a22, 16, false);
          m.mizrakMermisi = true;
          mermiListesi.push(this._wraithSektir(m));
          this.atisSifirla();
        }
        break;
      }
      case 'drone': case 'sniper': case 'gorunmez': {
        const carpan = (this.tip === 'gorunmez' && this.gizli) ? 2.0 : 1.0;
        const dx = px - cx;
        // Stop closing in once within firing range — a hovering shooter,
        // not a rusher. (Fixes sniper specifically stops here too, since
        // its hizTaban is 0 either way.)
        this.hizX = Math.abs(dx) > RANGED_DURMA_MESAFESI ? yonDusman * this.hizTaban : 0;
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
          // Same "hold firing range instead of closing to melee" behavior as
          // the other ranged types — a ghost that shoots shouldn't need to
          // touch the player to do it.
          const dx = px - cx;
          this.hizX = Math.abs(dx) > RANGED_DURMA_MESAFESI ? yonDusman * this.hizTaban : 0;
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
        this.hizX = yonDusman * this.hizTaban;
        this.x += this.hizX * yavasCarpan;
        this.hizY += 0.6; this.y += this.hizY;
        if (this.y >= ZEMIN_Y - this.h) { this.y = ZEMIN_Y - this.h; this.hizY = 0; this.yerde = true; }
        if (this.atisYapabilirMi()) {
          const dx = px - cx, dy = py - cy, len = Math.hypot(dx, dy) || 1;
          mermiListesi.push(this._wraithSektir(new MermiClass(this.scene, cx, this.y - 10,
            dx / len * 5, dy / len * 5 - 3, 0xff8800, 22, false)));
          this.atisSifirla();
        }
        break;
      }
      case 'boss': {
        this.hizX = yonDusman * this.hizTaban;
        this.x += this.hizX * yavasCarpan;
        this.hizY += 0.6; this.y += this.hizY;
        if (this.y >= ZEMIN_Y - this.h) { this.y = ZEMIN_Y - this.h; this.hizY = 0; this.yerde = true; }
        if (this.atisYapabilirMi()) {
          const aci = Math.atan2(py - cy, px - cx);
          for (let k = 0; k < 3; k++) {
            const a = aci + (k - 1) * 0.28;
            mermiListesi.push(this._wraithSektir(new MermiClass(this.scene, cx, cy, Math.cos(a) * 5, Math.sin(a) * 5, 0xff4400, 18, false)));
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
            this._golgeCagir();
          } else {
            this.bossFaz = 'saldiri'; this.kalkanli = true; this.bossFazTimer = 260;
            this.desenIdx = (this.desenIdx + 1) % 4; this.atisTimer = 30;
          }
        }
        if (this.faz === 1 && this.can < this.maxCan * 0.5) { this.faz = 2; this._fazGecisEfekti(); }
        if (this.faz === 2 && this.can < this.maxCan * 0.2) { this.faz = 3; this._fazGecisEfekti(); }
        if (this.bossFaz === 'saldiri' && this.atisTimer <= 0) {
          this._finalbossAttack(px, py, cx, cy, mermiListesi, MermiClass);
          this.atisTimer = 60;
        }
        // Ground spikes — an independent hazard layered on top of whatever
        // bullet pattern is currently firing, telegraphed so it's dodgeable
        // by staying off the ground (jump/hook over it).
        if (this.bossFaz === 'saldiri') {
          this.dikenTimer--;
          if (this.dikenTimer <= 0) {
            this._dikenSaldirisiBaslat();
            this.dikenTimer = this.faz === 1 ? 240 : (this.faz === 2 ? 190 : 150);
          }
        }
        this._dikenlerGuncelle();
        // Full-width warning-then-sweep laser — a second independent hazard,
        // forces the player to be at the right height when it fires.
        if (this.bossFaz === 'saldiri') {
          this.lazerTimer--;
          if (this.lazerTimer <= 0) {
            this._lazerSaldirisiBaslat();
            this.lazerTimer = this.faz === 1 ? 300 : (this.faz === 2 ? 240 : 190);
          }
        }
        this._lazerlerGuncelle();
        break;
      }
      case 'ranged': {
        const dx = px - cx;
        this.hizX = Math.abs(dx) > RANGED_DURMA_MESAFESI ? yonDusman * this.hizTaban : 0;
        this.x += this.hizX * yavasCarpan;
        this.hizY += 0.4; this.y += this.hizY;
        if (this.y >= ZEMIN_Y - this.h) { this.y = ZEMIN_Y - this.h; this.hizY = 0; this.yerde = true; }
        if (this.atisYapabilirMi()) this._fireBasic(px, py, cx, cy, mermiListesi, MermiClass);
        break;
      }
      default: { // melee, shield — these are meant to close to melee range
        this.hizX = yonDusman * this.hizTaban;
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
        mermiListesi.push(this._wraithSektir(new MermiClass(this.scene, cx, cy, dx / len * 14, dy / len * 14, 0xff0000, 18, false)));
      }
      this.atisSifirla();
      return;
    }
    if (this.tip === 'gorunmez') { color = 0xb400ff; dmg = 12; }
    if (this.tip === 'hayalet') { speed = 3.2; color = 0xbeffff; dmg = 9; }
    mermiListesi.push(this._wraithSektir(new MermiClass(this.scene, cx, cy, dx / len * speed, dy / len * speed, color, dmg, false)));
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
        mermiListesi.push(this._wraithSektir(new MermiClass(this.scene, ex, ey, Math.cos(a) * sp, Math.sin(a) * sp, 0xff0066, hasar, false)));
      }
    } else if (this.desenIdx === 1) {
      const n = this.faz >= 2 ? 5 : 4;
      for (let k = 0; k < n; k++) {
        const yofs = (k - (n - 1) / 2) * 22;
        mermiListesi.push(this._wraithSektir(new MermiClass(this.scene, ex, ey + yofs, Math.cos(aci) * sp * 0.9, Math.sin(aci) * sp * 0.9, 0xff0066, hasar, false)));
      }
    } else if (this.desenIdx === 2) {
      const n = this.faz === 1 ? 2 : 3;
      for (let k = 0; k < n; k++) {
        const dx = px - ex, dy = py - ey, len = Math.hypot(dx, dy) || 1;
        mermiListesi.push(this._wraithSektir(new MermiClass(this.scene, ex, ey, dx / len * (sp + 3), dy / len * (sp + 3), 0xff0066, hasar + 5, false)));
      }
    } else {
      // Radial burst — the 4th, most overwhelming pattern, gets denser each phase.
      const n = this.faz === 1 ? 8 : (this.faz === 2 ? 12 : 16);
      for (let k = 0; k < n; k++) {
        const a = (2 * Math.PI * k) / n;
        mermiListesi.push(this._wraithSektir(new MermiClass(this.scene, ex, ey, Math.cos(a) * sp * 0.8, Math.sin(a) * sp * 0.8, 0xffaa00, hasar - 4, false)));
      }
    }
  }

  // Camera shake on phase transitions — a cheap, high-impact beat to sell the
  // stakes going up. Not in the original.
  _fazGecisEfekti() {
    const cam = this.scene?.cameras?.main;
    if (cam) cam.shake(220, 0.006);
  }

  // Ground spikes — telegraphed floor hazard (the "alttan çıkan sivri
  // taşlar" pattern): warning cracks glow for ~0.7s, then spikes erupt for
  // ~0.35s and hurt anyone standing over them. Purely avoidable by jumping
  // or grappling above the floor when they go off.
  _dikenSaldirisiBaslat() {
    const n = this.faz === 1 ? 3 : (this.faz === 2 ? 5 : 7);
    const marj = 60;
    for (let k = 0; k < n; k++) {
      const x = marj + Math.random() * (GENISLIK - marj * 2);
      this.dikenler.push({ x, timer: 42, evre: 'uyari', vuruldu: false });
    }
  }

  _dikenlerGuncelle() {
    const p = this.scene?.player;
    for (let i = this.dikenler.length - 1; i >= 0; i--) {
      const d = this.dikenler[i];
      d.timer--;
      if (d.evre === 'uyari' && d.timer <= 0) {
        d.evre = 'patlama'; d.timer = 22;
      } else if (d.evre === 'patlama') {
        if (!d.vuruldu && p && p.can > 0 && p.yerde && Math.abs((p.x + p.w / 2) - d.x) < 26) {
          p.hasarAl(16 + this.faz * 4);
          d.vuruldu = true;
        }
        if (d.timer <= 0) this.dikenler.splice(i, 1);
      }
    }
  }

  // Called once each time OMEGA-9 drops its shield and goes "yorgun" (weak) —
  // it can't fight back directly, so it calls in shadow reinforcements to
  // protect itself instead. Any regular enemy type can be summoned (the worm
  // was just one example) — each one comes back as a golge (shadow) variant.
  _golgeCagir() {
    if (!this.scene?.enemies) return;
    const n = this.faz === 1 ? 1 : (this.faz === 2 ? 2 : 3);
    const havuz = ['melee', 'ranged', 'shield', 'tank', 'suicide', 'gorunmez', 'hayalet', 'drone', 'sniper', 'mizrakli', 'solucan'];
    const bx = this.x + this.w / 2;
    for (let k = 0; k < n; k++) {
      const tip = havuz[Math.floor(Math.random() * havuz.length)];
      const side = Math.random() < 0.5 ? -1 : 1;
      if (tip === 'solucan') {
        if (this.scene.golgeSolucanlar) {
          const x = 60 + Math.random() * (GENISLIK - 120);
          this.scene.golgeSolucanlar.push(new Solucan(this.scene, x, { golge: true }));
        }
      } else {
        const x = Phaser.Math.Clamp(bx + side * 60, 20, GENISLIK - 60);
        this.scene.enemies.push(new Dusman(this.scene, tip, x, this.bolum, side, { golge: true }));
      }
    }
  }

  // Full-width telegraphed laser sweep — warns as a thin pulsing line for
  // ~0.8s, then fires a thick horizontal beam for ~0.3s. Dodged by not being
  // at that height when it fires (jump over it or stay grounded under it).
  _lazerSaldirisiBaslat() {
    const n = this.faz === 3 ? 2 : 1;
    const usedY = [];
    for (let k = 0; k < n; k++) {
      let y, tries = 0;
      do { y = 90 + Math.random() * (ZEMIN_Y - 130); tries++; } while (usedY.some(uy => Math.abs(uy - y) < 80) && tries < 10);
      usedY.push(y);
      this.lazerler.push({ y, timer: 50, evre: 'uyari' });
    }
  }

  _lazerlerGuncelle() {
    const p = this.scene?.player;
    const bandH = 34;
    for (let i = this.lazerler.length - 1; i >= 0; i--) {
      const L = this.lazerler[i];
      L.timer--;
      if (L.evre === 'uyari' && L.timer <= 0) {
        L.evre = 'ates'; L.timer = 18;
      } else if (L.evre === 'ates') {
        if (p && p.can > 0 && p.hasarTimer <= 0) {
          const py1 = p.y, py2 = p.y + p.h;
          if (py2 > L.y - bandH / 2 && py1 < L.y + bandH / 2) p.hasarAl(6 + this.faz * 2);
        }
        if (L.timer <= 0) this.lazerler.splice(i, 1);
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
        // Corrupted mirror of the RONIN hero's own silhouette (helmet spikes,
        // cape, samurai body) — pure black instead of near-black, crimson glow
        // instead of purple, so it reads as "evil" at a glance. Not in the original.
        const yon = this.hizX >= 0 ? 1 : -1;
        const isinlaniyor = this.isinlanmaKare > 0;
        const kizil = 0xff2222;
        const lf = this.animFrame === 0 ? 4 : 0;

        g.fillStyle(0x000000, 1);
        g.fillRect(px + 2, py + h - 14, 10, 14 + lf);
        g.fillRect(px + w - 12, py + h - 14, 10, 14 - lf);
        g.fillStyle(0x050308, 1);
        const govde = [[px + 3, py + 16], [px + w - 3, py + 16], [px + w - 1, py + h - 6], [px + w / 2, py + h + 2], [px + 1, py + h - 6]];
        this._poly(g, govde);
        g.lineStyle(1, kizil, 1);
        g.strokePoints(govde.map(p => ({ x: p[0], y: p[1] })), true);
        g.fillStyle(0x000000, 1);
        const kask = [[px + 3, py + 10], [px + w - 3, py + 10], [px + w - 2, py - 2], [px + w / 2, py + 6], [px + 2, py - 2]];
        this._poly(g, kask);
        g.lineStyle(1, kizil, 1);
        g.strokePoints(kask.map(p => ({ x: p[0], y: p[1] })), true);
        g.fillStyle(0x000000, 1);
        for (const dxSpike of [-6, 0, 6]) {
          const sx = px + w / 2 + dxSpike;
          this._poly(g, [[sx - 2, py - 4], [sx, py - 15 - Math.abs(dxSpike)], [sx + 2, py - 4]]);
        }
        g.lineStyle(1, kizil, 1);
        g.strokeCircle(px + w / 2, py - 2, 11);
        g.lineStyle(2, isinlaniyor ? 0xffaaaa : kizil, 1);
        g.lineBetween(px + w / 2, py - 1, px + w / 2, py + 8);
        g.fillStyle(0x030204, 1);
        const pelerin = [[px - 2, py + 18], [px - 17, py + 29], [px - 11, py + h + 8], [px - 2, py + h - 2]];
        this._poly(g, pelerin);
        g.lineStyle(1, kizil, 1);
        g.strokePoints(pelerin.map(p => ({ x: p[0], y: p[1] })), true);

        if (isinlaniyor) {
          g.lineStyle(2, kizil, 0.6);
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

        // Giant containment screen — foreshadows HEX eventually trapping OMEGA-9
        // in a physical screen for good. Bigger than before, with a monitor-style
        // bezel (corner brackets + scanlines) and cracks that spread as it takes damage.
        const panelX = px - 70, panelY = py - 50, panelW = w + 140, panelH = h + 100;
        g.fillStyle(0x060608, 1); g.fillRect(panelX, panelY, panelW, panelH);
        g.lineStyle(2, 0x28283c, 1); g.strokeRect(panelX, panelY, panelW, panelH);
        g.lineStyle(1, 0x141422, 1);
        for (let gx = panelX + 16; gx < panelX + panelW; gx += 24) g.lineBetween(gx, panelY, gx, panelY + panelH);
        for (let gy = panelY + 16; gy < panelY + panelH; gy += 24) g.lineBetween(panelX, gy, panelX + panelW, gy);

        // scanlines, slowly drifting
        g.lineStyle(1, 0x00fff7, 0.06);
        const scanOfs = Math.floor(zaman / 40) % 6;
        for (let sy = panelY + scanOfs; sy < panelY + panelH; sy += 6) g.lineBetween(panelX, sy, panelX + panelW, sy);

        // corner brackets
        const bl = 22;
        g.lineStyle(3, 0x00fff7, 0.8);
        const corners = [[panelX, panelY, 1, 1], [panelX + panelW, panelY, -1, 1], [panelX, panelY + panelH, 1, -1], [panelX + panelW, panelY + panelH, -1, -1]];
        for (const [cx0, cy0, sxs, sys] of corners) {
          g.lineBetween(cx0, cy0, cx0 + bl * sxs, cy0);
          g.lineBetween(cx0, cy0, cx0, cy0 + bl * sys);
        }

        // cracks — more of them the lower its HP gets
        const hasarOrani = 1 - hpOran;
        const crackCount = Math.floor(hasarOrani * 7);
        if (crackCount > 0) {
          const rnd = (seed) => { const x = Math.sin(seed * 999) * 10000; return x - Math.floor(x); };
          g.lineStyle(1, 0xff2244, 0.5);
          for (let ci = 0; ci < crackCount; ci++) {
            let cx0 = panelX + rnd(ci * 3 + 1) * panelW, cy0 = panelY + rnd(ci * 3 + 2) * panelH;
            for (let seg = 0; seg < 4; seg++) {
              const nx = cx0 + (rnd(ci * 13 + seg) - 0.5) * 40, ny = cy0 + (rnd(ci * 17 + seg) - 0.5) * 40;
              g.lineBetween(cx0, cy0, nx, ny);
              cx0 = nx; cy0 = ny;
            }
          }
        }

        // YZ's grinning face glows on the screen behind OMEGA-9 — a reminder
        // the AI is what's really driving this fight. Glitches worse and
        // grins wider as the panel takes damage.
        {
          const grinAlpha = 0.22 + 0.10 * Math.abs(Math.sin(zaman / 300)) + hasarOrani * 0.3;
          const jitter = (Math.random() - 0.5) * (hasarOrani * 6);
          const faceCx = panelX + panelW / 2 + jitter, faceCy = panelY + panelH * 0.32;
          const eyeSpacing = panelW * 0.17, eyeW = panelW * 0.11, eyeH = 9, tilt = 10;
          g.fillStyle(0x00fff7, grinAlpha);
          for (const side of [-1, 1]) {
            const ex = faceCx + side * eyeSpacing;
            this._poly(g, [
              [ex - side * eyeW / 2, faceCy + eyeH],
              [ex - side * eyeW / 2, faceCy - eyeH],
              [ex + side * eyeW / 2, faceCy - eyeH - tilt],
              [ex + side * eyeW / 2, faceCy + eyeH - tilt]
            ]);
          }
          g.fillStyle(0xffffff, Math.min(1, grinAlpha * 1.8));
          g.fillCircle(faceCx - eyeSpacing, faceCy - 2, 2);
          g.fillCircle(faceCx + eyeSpacing, faceCy - 2, 2);

          const grinY = faceCy + 30, grinW = panelW * 0.62, disler = 9;
          g.lineStyle(2, 0xff2244, grinAlpha * 1.4);
          g.beginPath();
          for (let k = 0; k <= disler; k++) {
            const tx = faceCx - grinW / 2 + k * grinW / disler;
            const dip = 12 * Math.sin((k / disler) * Math.PI);
            if (k === 0) g.moveTo(tx, grinY - dip); else g.lineTo(tx, grinY - dip);
          }
          g.strokePath();
          g.fillStyle(0xff2244, grinAlpha * 1.2);
          for (let k = 0; k < disler; k++) {
            const tx0 = faceCx - grinW / 2 + k * grinW / disler;
            const tx1 = tx0 + (grinW / disler) * 0.8;
            const dip = 12 * Math.sin((k / disler) * Math.PI);
            this._poly(g, [[tx0, grinY - dip], [tx1, grinY - dip], [(tx0 + tx1) / 2, grinY + 13 - dip]]);
          }
        }

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

        const durum = kalkanli ? t('kalkanliLabel') : t('zayifVurLabel');
        const durumRenk = kalkanli ? '#00fff7' : '#00ff64';
        if (!this._labelText) {
          this._labelText = this.scene.add.text(0, 0, '', { fontFamily: 'monospace', fontSize: '11px', fontStyle: 'bold' }).setDepth(9);
        }
        this._labelText.setText(`OMEGA-9  ${t('fazLabel')} ${faz}  [${durum}]`);
        this._labelText.setColor(durumRenk);
        this._labelText.setPosition(px + w / 2 - this._labelText.width / 2, py - 18);

        for (const d of this.dikenler) {
          if (d.evre === 'uyari') {
            const puls = 0.35 + 0.5 * Math.abs(Math.sin(zaman / 60));
            g.fillStyle(0xff2244, puls);
            g.fillRect(d.x - 20, ZEMIN_Y - 4, 40, 4);
            g.lineStyle(2, 0xff2244, puls);
            g.strokeRect(d.x - 20, ZEMIN_Y - 4, 40, 4);
          } else {
            const yukselme = Math.min(1, (22 - d.timer) / 6);
            const h2 = 46 * yukselme;
            g.fillStyle(0x8a8a96, 1);
            this._poly(g, [[d.x - 16, ZEMIN_Y], [d.x, ZEMIN_Y - h2], [d.x + 16, ZEMIN_Y]]);
            g.fillStyle(0xd8d8e0, 1);
            this._poly(g, [[d.x - 6, ZEMIN_Y], [d.x, ZEMIN_Y - h2], [d.x + 6, ZEMIN_Y]]);
          }
        }

        for (const L of this.lazerler) {
          if (L.evre === 'uyari') {
            const puls = 0.3 + 0.5 * Math.abs(Math.sin(zaman / 50));
            g.fillStyle(0xffaa00, puls * 0.5);
            g.fillRect(0, L.y - 2, GENISLIK, 4);
            g.lineStyle(1, 0xffaa00, puls);
            g.lineBetween(0, L.y, GENISLIK, L.y);
          } else {
            g.fillStyle(0xff6600, 0.5);
            g.fillRect(0, L.y - 17, GENISLIK, 34);
            g.fillStyle(0xffffff, 0.9);
            g.fillRect(0, L.y - 4, GENISLIK, 8);
          }
        }
        break;
      }
    }

    if (this.golge) {
      // Shadow-summon tint — reused across every regular type so any of
      // OMEGA-9's reinforcements reads as "one of its own" at a glance.
      g.fillStyle(0x090109, 0.45); g.fillRect(px, py, w, h);
      g.lineStyle(2, 0x8a2eff, 0.85); g.strokeRect(px, py, w, h);
      const pulse = 0.35 + 0.35 * Math.abs(Math.sin(zaman / 150));
      g.fillStyle(0xc86eff, pulse); g.fillCircle(px + w / 2, py + h * 0.28, 2.6);
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
