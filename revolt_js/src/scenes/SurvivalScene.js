import Phaser from 'phaser';
import { GENISLIK, YUKSEKLIK, REAPER, WRAITH, PATLAMA_YARICAP, SURVIVOR, YUKSELTME_HAVUZU, bolumAyar, platformlarIcin } from '../data/constants.js';
import { Player } from '../entities/Player.js';
import { Dusman } from '../entities/Enemy.js';
import { Mermi } from '../entities/Projectile.js';
import { Xp, CanTopu } from '../entities/Pickups.js';
import { Iskelet } from '../entities/Iskelet.js';
import { GameState, saveState } from '../data/state.js';
import { leftAttack, rightAction, rightRelease, eAbility, qUlti, handleSharedPerFrameEffects, getAim } from '../systems/heroActions.js';
import { Parca, HasarYazisi, patlama } from '../entities/Fx.js';
import { makeButton } from '../systems/ui.js';
import { playThemeMusic, playSfx } from '../systems/music.js';
import { drawThemedBackground, themeForBolum } from '../systems/background.js';
import { MobileControls } from '../systems/mobileControls.js';
import { gameplayStart, gameplayStop, rewardedBreak, isPokiAvailable } from '../systems/poki.js';
import { Crosshair } from '../systems/crosshair.js';
import { t, randomOlumMesaji } from '../data/translations.js';
import { PauseController } from '../systems/pause.js';

// Simplified vs. the Python original: runs on the fixed 900x550 arena
// (no 2700px scrolling world/camera) — same leveling, spawn-weighting and
// difficulty-ramp formulas, see SPEC_gameloop_menus_survival.md §3.
export class SurvivalScene extends Phaser.Scene {
  constructor() {
    super('Survival');
  }

  init(data) {
    this.heroId = data?.heroId ?? 0;
  }

  create() {
    drawThemedBackground(this, themeForBolum(1), () => this.player ? this.player.x : 0);
    playThemeMusic(this, 'metropol');
    // Background stays city-themed, but the platform set still progresses with
    // difficulty (city -> station -> ruins) — see _updatePlatformTier().
    this._platformTier = 1;
    this.platforms = platformlarIcin(1);
    this.platformGfx = this.add.graphics().setDepth(2);

    this.player = new Player(this, this.heroId);
    this.player.ustalikUygula();
    this.player.genelYukseltmeUygula();
    this.enemies = [];
    this.mermiler = [];
    this.xpList = [];
    this.healList = [];
    this.fx = [];
    this.dmgTexts = [];
    this.skeletons = [];

    this.seviye = 1;
    this.xpDolu = 0;
    this.xpGerekli = SURVIVOR.XP_BASE;
    this.oldurulen = 0;
    this.gecenKare = 0;
    this.spawnTimer = 60;
    this.sonrakiMinibosKare = SURVIVOR.ZORLUK_ARALIK * 10;
    this.kartBekleniyor = false;
    this.gameOver = false;

    this._setupInput();
    this._setupHud();
    this.mobileControls = new MobileControls(this);
    this.crosshair = new Crosshair(this);
    this.pause = new PauseController(this, () => this.scene.start('Menu'));
    gameplayStart();

    this.events.once('shutdown', () => { gameplayStop(); this.crosshair.destroy(); this.pause.destroy(); });
  }

  // Regenerates the platform set (resetting any crumbled ruins platforms)
  // whenever the difficulty tier crosses a city/station/ruins boundary.
  _updatePlatformTier(sanalBolum) {
    const tier = sanalBolum <= 10 ? 1 : (sanalBolum <= 20 ? 11 : 21);
    if (tier !== this._platformTier) {
      this._platformTier = tier;
      this.platforms = platformlarIcin(tier);
    }
  }

  applyDamage(d, amount) {
    if (d.dead) return;
    if (d.tip === 'finalboss' && d.kalkanli) return;
    d.can -= amount;
    this.dmgTexts.push(new HasarYazisi(this, d.x + d.w / 2, d.y, Math.round(amount), 0xffffff));
  }

  onEnemyDamaged(d, delta) {
    const heroId = this.player.heroId;
    GameState.kahramanHasar[heroId] = (GameState.kahramanHasar[heroId] || 0) + delta;
    this.player.ustalikUygula();
  }

  onEnemyKilled(d) {
    this.oldurulen++;
    this.player.ultiSarjEkle(8);
    if (this.player.heroId === 8) {
      this.player.reaperRuhBolme = Math.min(REAPER.RUH_BOLME_MAX, this.player.reaperRuhBolme + 1);
      if (this.player.reaperAtisIskeletAcik) this.skeletons.push(new Iskelet(this, d.x, d.y, false, false));
    }
    const n = Phaser.Math.Between(1, 3);
    for (let i = 0; i < n; i++) this.xpList.push(new Xp(this, d.x + d.w / 2, d.y + d.h / 2));
    if (Math.random() < 0.12) this.healList.push(new CanTopu(this, d.x + d.w / 2, d.y + d.h / 2));
    this.fx.push(...patlama(this, d.x + d.w / 2, d.y + d.h / 2, 0xf5a623, 12));
  }

  _setupInput() {
    this.keys = this.input.keyboard.addKeys({
      left: Phaser.Input.Keyboard.KeyCodes.LEFT, a: Phaser.Input.Keyboard.KeyCodes.A,
      right: Phaser.Input.Keyboard.KeyCodes.RIGHT, d: Phaser.Input.Keyboard.KeyCodes.D,
      up: Phaser.Input.Keyboard.KeyCodes.UP, w: Phaser.Input.Keyboard.KeyCodes.W, space: Phaser.Input.Keyboard.KeyCodes.SPACE,
      down: Phaser.Input.Keyboard.KeyCodes.DOWN, s: Phaser.Input.Keyboard.KeyCodes.S,
      e: Phaser.Input.Keyboard.KeyCodes.E, q: Phaser.Input.Keyboard.KeyCodes.Q,
      esc: Phaser.Input.Keyboard.KeyCodes.ESC
    });
    this.mouseDown = false;
    const isTouch = this.sys.game.device.input.touch;
    this.input.on('pointerdown', (p) => {
      if (this.kartBekleniyor || isTouch) return;
      if (p.leftButtonDown()) this.mouseDown = true;
      if (p.rightButtonDown()) rightAction(this, p.worldX, p.worldY);
    });
    this.input.on('pointerup', (p) => {
      if (!p.leftButtonDown()) this.mouseDown = false;
      if (p.button === 2) rightRelease(this);
    });
    this.input.mouse?.disableContextMenu();
  }

  _setupHud() {
    this.hudHpFill = this.add.rectangle(11, 12, 118, 12, 0x00ff64).setOrigin(0, 0).setDepth(21);
    this.add.rectangle(10, 11, 120, 14, 0x1e1e1e).setOrigin(0, 0).setDepth(20);
    this.hudXpFill = this.add.rectangle(11, 30, 118, 6, 0x00ccff).setOrigin(0, 0).setDepth(21);
    this.add.rectangle(10, 29, 120, 8, 0x1e1e1e).setOrigin(0, 0).setDepth(20);
    this.hudText = this.add.text(GENISLIK / 2, 20, '', { fontFamily: 'monospace', fontSize: '14px', color: '#ffffff' }).setOrigin(0.5).setDepth(20);
    this.hudTime = this.add.text(GENISLIK - 20, 13, '', { fontFamily: 'monospace', fontSize: '14px', color: '#ffffff' }).setOrigin(1, 0).setDepth(20);
    this.msgBox = this.add.rectangle(GENISLIK / 2, YUKSEKLIK / 2, 500, 230, 0x000000, 0.85)
      .setStrokeStyle(2, 0x00fff7).setDepth(29).setVisible(false);
    this.msgText = this.add.text(GENISLIK / 2, YUKSEKLIK / 2, '', { fontFamily: 'monospace', fontSize: '26px', color: '#00fff7' }).setOrigin(0.5).setDepth(30);
    this.cardContainer = this.add.container(0, 0).setDepth(40);
    this._endScreenExtras = [];
  }

  _sanalBolum() {
    let sb = Math.min(29, 1 + Math.floor(this.gecenKare / SURVIVOR.ZORLUK_ARALIK));
    if (sb === 5) sb = 6;
    return sb;
  }

  _showLevelUpCards() {
    this.kartBekleniyor = true;
    gameplayStop();
    this.cardContainer.removeAll(true);
    const pool = Phaser.Utils.Array.Shuffle([...YUKSELTME_HAVUZU]).slice(0, 3);
    const overlay = this.add.rectangle(GENISLIK / 2, YUKSEKLIK / 2, GENISLIK, YUKSEKLIK, 0x000000, 0.75);
    this.cardContainer.add(overlay);
    const title = this.add.text(GENISLIK / 2, 140, t('seviyeAtladinKartSec'), { fontFamily: 'monospace', fontSize: '18px', color: '#ffee00' }).setOrigin(0.5);
    this.cardContainer.add(title);

    pool.forEach((card, i) => {
      const x = GENISLIK / 2 + (i - 1) * 230;
      const y = YUKSEKLIK / 2 + 20;
      const key = card.id.charAt(0).toUpperCase() + card.id.slice(1);
      const box = this.add.rectangle(x, y, 200, 160, 0x111122).setStrokeStyle(2, 0x00fff7).setInteractive({ useHandCursor: true });
      const name = this.add.text(x, y - 40, t(`yukseltme${key}Isim`), { fontFamily: 'monospace', fontSize: '15px', color: '#00fff7', align: 'center', wordWrap: { width: 180 } }).setOrigin(0.5);
      const desc = this.add.text(x, y + 10, t(`yukseltme${key}Aciklama`), { fontFamily: 'monospace', fontSize: '13px', color: '#dddddd', align: 'center', wordWrap: { width: 180 } }).setOrigin(0.5);
      box.on('pointerdown', () => this._applyCard(card.id));
      box.on('pointerover', () => box.setStrokeStyle(2, 0x00ffc8));
      box.on('pointerout', () => box.setStrokeStyle(2, 0x00fff7));
      this.cardContainer.add([box, name, desc]);
    });
  }

  _applyCard(id) {
    const p = this.player;
    if (id === 'hasar') p.hasarCarpan *= 1.2;
    else if (id === 'hiz') p.survivorHizCarpan *= 1.15;
    else if (id === 'can') { p.maxCan += 25; p.can += 25; }
    else if (id === 'saldiri') p.saldiriCarpan = Math.max(0.35, p.saldiriCarpan * 0.85);
    else if (id === 'regen') p.survivorCanYenileme += 0.03;
    this.cardContainer.removeAll(true);
    this.kartBekleniyor = false;
    gameplayStart();
  }

  update() {
    if (this.gameOver) {
      if (Phaser.Input.Keyboard.JustDown(this.keys.esc)) this.scene.start('Menu');
      return;
    }
    if (this.kartBekleniyor) return;

    if (Phaser.Input.Keyboard.JustDown(this.keys.esc)) this.pause.toggle();
    if (this.pause.active) return;

    const p = this.player;
    const mc = this.mobileControls;
    const mcKeys = mc.keys();
    const keys = {
      left: this.keys.left.isDown || this.keys.a.isDown || (mcKeys?.left ?? false),
      right: this.keys.right.isDown || this.keys.d.isDown || (mcKeys?.right ?? false),
      up: this.keys.up.isDown || this.keys.w.isDown || this.keys.space.isDown || (mcKeys?.up ?? false),
      upJustDown: Phaser.Input.Keyboard.JustDown(this.keys.up) || Phaser.Input.Keyboard.JustDown(this.keys.w) ||
        Phaser.Input.Keyboard.JustDown(this.keys.space) || (mcKeys?.up && !this._mobileUpWasDown),
      down: this.keys.down.isDown || this.keys.s.isDown || (mcKeys?.down ?? false)
    };
    this._mobileUpWasDown = mcKeys?.up ?? false;

    if (Phaser.Input.Keyboard.JustDown(this.keys.e) || mc.consumeE()) eAbility(this);
    if (Phaser.Input.Keyboard.JustDown(this.keys.q) || mc.consumeQ()) qUlti(this);
    if (mc.consumeSpecial()) { const aim = getAim(this); rightAction(this, aim.x, aim.y); }
    if (this.mouseDown || mc.fireHeld) leftAttack(this);

    this.gecenKare++;
    const sanalBolum = this._sanalBolum();
    this._updatePlatformTier(sanalBolum);

    // platforms (movement + one-way landing collision) — same rules as PlayScene
    const oncekiAyakY = p.y + p.h;
    for (const pl of this.platforms) {
      if (pl.hiz !== undefined) {
        pl.x += pl.hiz;
        if (pl.x <= pl.sol || pl.x + pl.w >= pl.sag) {
          pl.hiz *= -1;
          pl.x = Phaser.Math.Clamp(pl.x, pl.sol, pl.sag - pl.w);
        }
      }
      if (pl.kirilir && pl.kirilmaKare > 0) {
        pl.kirilmaKare--;
        if (pl.kirilmaKare === 0) pl.kirildi = true;
      }
    }

    p.hareketEt(keys);
    handleSharedPerFrameEffects(this);

    if (!keys.down && p.hizY >= 0) {
      const yeniAyakY = p.y + p.h;
      for (const pl of this.platforms) {
        if (pl.kirildi) continue;
        if (p.x + p.w > pl.x && p.x < pl.x + pl.w) {
          if (oncekiAyakY <= pl.y + 2 && yeniAyakY >= pl.y) {
            p.y = pl.y - p.h;
            p.hizY = 0;
            p.yerde = true;
            if (pl.kirilir && pl.kirilmaKare < 0) pl.kirilmaKare = 120;
            break;
          }
        }
      }
    }

    this.spawnTimer--;
    if (this.spawnTimer <= 0) {
      const ayar = bolumAyar(sanalBolum, GameState.testModu);
      const types = ['melee', 'ranged', 'drone', 'sniper', 'shield', 'tank', 'suicide', 'gorunmez', 'hayalet', 'mizrakli', 'golgeRonin'];
      const pool = types.filter(t => (ayar[t] || 0) > 0);
      const weighted = pool.flatMap(t => Array(ayar[t]).fill(t));
      if (weighted.length > 0) {
        const tip = Phaser.Utils.Array.GetRandom(weighted);
        const side = Math.random() < 0.5 ? -1 : 1;
        const x = side === -1 ? 20 : GENISLIK - 60;
        const d = new Dusman(this, tip, x, sanalBolum, side);
        d.sinirsiz = true;
        this.enemies.push(d);
      }
      this.spawnTimer = Math.max(25, 70 - sanalBolum * 2);
    }

    this.sonrakiMinibosKare -= 1;
    if (this.sonrakiMinibosKare <= 0) {
      const side = Math.random() < 0.5 ? -1 : 1;
      const x = side === -1 ? 20 : GENISLIK - 60;
      const d = new Dusman(this, 'boss', x, sanalBolum, side);
      d.sinirsiz = true;
      this.enemies.push(d);
      this.sonrakiMinibosKare = SURVIVOR.ZORLUK_ARALIK * 10;
    }

    // enemies
    for (const d of this.enemies) {
      if (d.dead) continue;
      d.guncelle(p.x + p.w / 2, p.y + p.h / 2, this.time.now, this.mermiler, Mermi);
      if (d.sinirsiz) {
        const excess = Math.abs(d.x - p.x) - 400;
        if (excess > 0) d.x -= Math.sign(d.x - p.x) * excess * 0.03;
      }
      const dr = d.rect(), pr = p.rect();
      if (Phaser.Geom.Intersects.RectangleToRectangle(dr, pr) && p.hasarTimer <= 0) {
        if (d.tip === 'melee' || d.tip === 'shield') p.hasarAl(15);
        else if (d.tip !== 'suicide') p.hasarAl(10);
      }
      if (d.tip === 'suicide' && d.patlayacak) {
        const cx = d.x + d.w / 2, cy = d.y + d.h / 2;
        const dist = Math.hypot((p.x + p.w / 2) - cx, (p.y + p.h / 2) - cy);
        if (dist < PATLAMA_YARICAP && p.hasarTimer <= 0) p.hasarAl(28);
        d.can = 0;
      }
    }

    // skeletons (REAPER allies)
    for (const s of this.skeletons) s.guncelle(this.enemies, (d, amt) => this.applyDamage(d, amt));
    this.skeletons = this.skeletons.filter(s => {
      if (s.can <= 0) { s.destroy(); p.can = Math.min(p.maxCan, p.can + 10); return false; }
      return true;
    });

    for (const m of this.mermiler) {
      m.guncelle();
      const mr = m.rect();
      if (m.oyuncuMermisi) {
        if (m.golgeGecikme > 0) { m.golgeGecikme--; continue; }
        for (const d of this.enemies) {
          if (d.dead) continue;
          if (Phaser.Geom.Intersects.RectangleToRectangle(mr, d.rect())) {
            const wasAlive = !d.dead;
            this.applyDamage(d, m.hasar);
            if (m.wraithMermisi && p.heroId === 7) {
              p.wraithRuhEkle(WRAITH.RUH_SARJ_VURUS);
              if (wasAlive && d.dead) p.wraithRuhEkle(WRAITH.RUH_SARJ_OLUM);
            }
            m.dead = true;
            break;
          }
        }
      } else if (p.hasarTimer <= 0 && Phaser.Geom.Intersects.RectangleToRectangle(mr, p.rect())) {
        p.hasarAl(m.hasar); m.dead = true;
      }
    }
    this.mermiler = this.mermiler.filter(m => { if (m.dead) { m.destroy(); return false; } return true; });

    // onEnemyKilled already fired from the Dusman.can setter the instant health
    // crossed zero (see Enemy.js) — this pass only reclaims dead entities.
    const stillAlive = [];
    for (const d of this.enemies) {
      if (d.dead) d.destroy(); else stillAlive.push(d);
    }
    this.enemies = stillAlive;

    // pickups
    for (const xp of this.xpList) {
      xp.guncelle();
      if (Phaser.Geom.Intersects.RectangleToRectangle(xp.rect(), p.rect())) { this.xpDolu += xp.deger; xp.dead = true; }
    }
    this.xpList = this.xpList.filter(x => { if (x.dead) { x.destroy(); return false; } return true; });

    for (const h of this.healList) {
      h.guncelle();
      if (Phaser.Geom.Intersects.RectangleToRectangle(h.rect(), p.rect())) { p.can = p.maxCan; h.dead = true; }
    }
    this.healList = this.healList.filter(h => { if (h.dead) { h.destroy(); return false; } return true; });

    if (this.xpDolu >= this.xpGerekli) {
      this.xpDolu -= this.xpGerekli;
      this.seviye++;
      this.xpGerekli = Math.floor(SURVIVOR.XP_BASE * Math.pow(SURVIVOR.XP_ARTIS, this.seviye - 1));
      this._showLevelUpCards();
    }

    // particles + damage numbers
    for (const f of this.fx) f.guncelle();
    this.fx = this.fx.filter(f => { if (f.dead) { f.destroy(); return false; } return true; });
    for (const t of this.dmgTexts) t.guncelle();
    this.dmgTexts = this.dmgTexts.filter(t => { if (t.dead) { t.destroy(); return false; } return true; });

    // draw
    this.platformGfx.clear();
    const platRenk = this._platformTier <= 10 ? 0x3c3c50 : (this._platformTier <= 20 ? 0x281946 : 0x3c1410);
    for (const pl of this.platforms) {
      if (pl.kirildi) continue;
      const crumbling = pl.kirilir && pl.kirilmaKare > 0;
      this.platformGfx.fillStyle(crumbling ? 0xe94560 : platRenk, crumbling ? (0.4 + 0.6 * (pl.kirilmaKare / 120)) : 1);
      this.platformGfx.fillRect(pl.x, pl.y, pl.w, pl.h);
      this.platformGfx.lineStyle(1, 0x00fff7, 1);
      this.platformGfx.strokeRect(pl.x, pl.y, pl.w, pl.h);
    }
    for (const s of this.skeletons) s.draw();
    { const aim = getAim(this); p.draw(aim.x, aim.y); this.crosshair.draw(aim.x, aim.y); }
    this.mobileControls.draw();
    for (const d of this.enemies) d.draw(this.time.now);
    for (const m of this.mermiler) m.draw();
    for (const xp of this.xpList) xp.draw();
    for (const h of this.healList) h.draw();
    for (const f of this.fx) f.draw();
    for (const t of this.dmgTexts) t.draw();

    const hpRatio = Phaser.Math.Clamp(p.can / p.maxCan, 0, 1);
    this.hudHpFill.width = 118 * hpRatio;
    this.hudHpFill.fillColor = hpRatio > 0.5 ? 0x00ff64 : (hpRatio > 0.25 ? 0xf5a623 : 0xe94560);
    this.hudXpFill.width = 118 * Phaser.Math.Clamp(this.xpDolu / this.xpGerekli, 0, 1);
    this.hudText.setText(`${t('seviyeLabel')} ${this.seviye}   ${t('oldurulenLabel')}:${this.oldurulen}`);
    const secs = Math.floor(this.gecenKare / 60);
    this.hudTime.setText(`${String(Math.floor(secs / 60)).padStart(2, '0')}:${String(secs % 60).padStart(2, '0')}`);

    if (p.can <= 0) {
      this.gameOver = true;
      playSfx(this, 'karakter_olum', { volume: 0.6 });
      const bestSecs = Math.max(GameState.enUzunHayattaKalma, secs);
      GameState.enUzunHayattaKalma = bestSecs;
      GameState.toplamOldurulen += this.oldurulen;
      saveState();
      const btnCount = isPokiAvailable() ? 2 : 1;
      this.msgBox.setSize(500, Math.max(230, 2 * (80 + (btnCount - 1) * 44 + 17) + 8)).setVisible(true);
      // Two-line title (~26px font, 2 lines) needs a bigger half-height than
      // a single-line one, and the same "everything hangs below center"
      // problem PlayScene had applies here too — center the content block.
      const titleHalf = 31;
      const subtitleOffset = 48;
      const buttonStartY = 80;
      const contentTop = -titleHalf;
      const lastButtonOffset = buttonStartY + (btnCount - 1) * 44;
      const contentBottom = lastButtonOffset + 17;
      const shift = -((contentTop + contentBottom) / 2);
      this.msgText.setPosition(GENISLIK / 2, YUKSEKLIK / 2 + shift);
      this.msgText.setText(`${t('hayattaKaldinLabel')}: ${String(Math.floor(secs / 60)).padStart(2, '0')}:${String(secs % 60).padStart(2, '0')}\n${t('seviyeLabel')} ${this.seviye}   ${t('oldurulenLabel')}:${this.oldurulen}`);
      const taunt = this.add.text(GENISLIK / 2, YUKSEKLIK / 2 + subtitleOffset + shift, randomOlumMesaji(), {
        fontFamily: 'monospace', fontSize: '12px', color: '#f5a623'
      }).setOrigin(0.5).setDepth(30);
      this._endScreenExtras.push(taunt);
      let y = YUKSEKLIK / 2 + buttonStartY + shift;
      if (isPokiAvailable()) {
        const revive = makeButton(this, GENISLIK / 2, y, 220, 34, t('reklamlaCanlan'), () => this._reviveFromAd(), '12px');
        // msgBox sits at depth 29 — without this, these default to depth 0
        // and render underneath it, making the buttons look washed-out.
        revive.bg.setDepth(30);
        revive.text.setDepth(31);
        this._endScreenExtras.push(revive.bg, revive.text);
        y += 44;
      }
      const menu = makeButton(this, GENISLIK / 2, y, 220, 34, t('anaMenuyeDon'), () => this.scene.start('Menu'), '15px');
      menu.bg.setDepth(30);
      menu.text.setDepth(31);
      this._endScreenExtras.push(menu.bg, menu.text);
    }
  }

  _clearEndScreen() {
    this.msgBox.setVisible(false);
    this.msgText.setText('');
    for (const o of this._endScreenExtras) o.destroy();
    this._endScreenExtras = [];
  }

  async _reviveFromAd() {
    const ok = await rewardedBreak();
    if (!ok) return;
    this._clearEndScreen();
    this.gameOver = false;
    this.player.can = Math.round(this.player.maxCan * 0.6);
    this.player.hasarTimer = 60;
  }
}
