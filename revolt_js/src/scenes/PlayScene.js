import Phaser from 'phaser';
import { GENISLIK, YUKSEKLIK, ZEMIN_Y, REAPER, WRAITH, PATLAMA_YARICAP, SOLUCAN, platformlarIcin, efektifTemaBolum } from '../data/constants.js';
import { bolumAyar } from '../data/constants.js';
import { drawThemedBackground, themeForBolum } from '../systems/background.js';
import { Player } from '../entities/Player.js';
import { Dusman } from '../entities/Enemy.js';
import { Mermi } from '../entities/Projectile.js';
import { Solucan } from '../entities/Solucan.js';
import { Enkaz } from '../entities/Enkaz.js';
import { Iskelet } from '../entities/Iskelet.js';
import { GameState, saveState } from '../data/state.js';
import { leftAttack, rightAction, rightRelease, eAbility, qUlti, handleSharedPerFrameEffects, hitTargets, getAim } from '../systems/heroActions.js';
import { MobileControls } from '../systems/mobileControls.js';
import { gameplayStart, gameplayStop, commercialBreak } from '../systems/poki.js';
import { Hud } from '../systems/hud.js';
import { Parca, HasarYazisi, patlama } from '../entities/Fx.js';
import { makeButton } from '../systems/ui.js';
import { playThemeMusic, themeKeyForBolum } from '../systems/music.js';
import { Crosshair } from '../systems/crosshair.js';
import { t } from '../data/translations.js';
import { PauseController } from '../systems/pause.js';

export class PlayScene extends Phaser.Scene {
  constructor() {
    super('Play');
  }

  init(data) {
    this.bolum = data?.bolum || 1;
    this.heroId = data?.heroId ?? 0;
  }

  create() {
    const temaBolum = this.temaBolum = efektifTemaBolum(this.bolum, GameState.testModu);
    const theme = themeForBolum(temaBolum);
    // Parallax scroll is tied to the player's own x, matching the original's
    // `fon_ciz(ekran, oyuncu.x, tema_bolum)` — the world visibly shifts as you move.
    drawThemedBackground(this, theme, () => this.player ? this.player.x : 0);
    playThemeMusic(this, themeKeyForBolum(temaBolum));

    this.platforms = platformlarIcin(temaBolum);
    this.platformGfx = this.add.graphics().setDepth(2);

    this.player = new Player(this, this.heroId);
    this.player.ustalikUygula();
    this.player.genelYukseltmeUygula();
    this.enemies = [];
    this.mermiler = [];
    this.fx = [];
    this.dmgTexts = [];
    this.skeletons = [];
    this.worm = null;
    this.wormTimer = Phaser.Math.Between(SOLUCAN.ARALIK_MIN, SOLUCAN.ARALIK_MAX);
    this.wormKilled = false;
    this.debris = [];
    this.debrisTimer = Phaser.Math.Between(150, 250);

    this.skor = 0;
    this.stageBitti = false;
    this.gameOver = false;

    const ayar = bolumAyar(this.bolum, GameState.testModu);
    this.ayarFinal = !!ayar.final;
    this.spawnSira = [];
    for (const tip of ['melee', 'ranged', 'drone', 'sniper', 'shield', 'tank', 'suicide', 'gorunmez', 'hayalet', 'mizrakli', 'golgeRonin']) {
      const n = ayar[tip] || 0;
      for (let i = 0; i < n; i++) this.spawnSira.push(tip);
    }
    if (ayar.boss) this.spawnSira.push('boss');
    if (ayar.final) this.spawnSira = ['finalboss'];
    Phaser.Utils.Array.Shuffle(this.spawnSira);
    this.spawnTimer = 30;
    this.kalanDusman = this.spawnSira.length;

    this._setupInput();
    this._setupHud();
    this.mobileControls = new MobileControls(this);
    this.crosshair = new Crosshair(this);
    this.pause = new PauseController(this, () => this.scene.start('Menu'));
    gameplayStart();

    this.events.once('shutdown', () => { gameplayStop(); this.crosshair.destroy(); this.pause.destroy(); });
  }

  applyDamage(d, amount) {
    if (d.dead) return;
    if (d.tip === 'finalboss' && d.kalkanli) return;
    d.can -= amount;
    this.dmgTexts.push(new HasarYazisi(this, d.x + d.w / 2, d.y, Math.round(amount), 0xffffff));
  }

  onWormKilled(w) {
    this.wormKilled = true;
    this.skor += Math.round(w.para);
    this.fx.push(...patlama(this, w.x + w.w / 2, ZEMIN_Y, 0xf5a623, 12));
  }

  // Mirrors the Python original's `Dusman.can` setter, which auto-feeds
  // ANY damage source (bullets, skeleton allies, splash) into the active
  // hero's mastery counter — see KAHRAMAN_YUKSELTMELERI / Player.ustalikUygula.
  onEnemyDamaged(d, delta) {
    const heroId = this.player.heroId;
    GameState.kahramanHasar[heroId] = (GameState.kahramanHasar[heroId] || 0) + delta;
    this.player.ustalikUygula();
  }

  onEnemyKilled(d) {
    if (d.tip === 'boss' || d.tip === 'finalboss') this.sound.play('boss_olum', { volume: 0.5 });
    this.skor += Math.round(d.para);
    this.player.ultiSarjEkle(8);
    if (this.player.heroId === 8) {
      this.player.reaperRuhBolme = Math.min(REAPER.RUH_BOLME_MAX, this.player.reaperRuhBolme + 1);
      if (this.player.reaperAtisIskeletAcik) this.skeletons.push(new Iskelet(this, d.x, d.y, false, false));
    }
    this.kalanDusman--;
    GameState.toplamOldurulen = (GameState.toplamOldurulen || 0) + 1;
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
      if (isTouch) return; // handled by MobileControls instead
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
    this.hud = new Hud(this);
    this.msgBox = this.add.rectangle(GENISLIK / 2, YUKSEKLIK / 2, 460, 240, 0x000000, 0.85)
      .setStrokeStyle(2, 0x00fff7).setDepth(29).setVisible(false);
    this.msgText = this.add.text(GENISLIK / 2, YUKSEKLIK / 2, '', { fontFamily: 'monospace', fontSize: '28px', color: '#00fff7' }).setOrigin(0.5).setDepth(30);
  }

  update() {
    if (this.gameOver || this.stageBitti) {
      if (Phaser.Input.Keyboard.JustDown(this.keys.esc)) this.scene.start('Menu');
      return;
    }

    if (Phaser.Input.Keyboard.JustDown(this.keys.esc)) this.pause.toggle();
    if (this.pause.active) return;

    const p = this.player;
    const mc = this.mobileControls;
    const mcKeys = mc.keys();
    const keyUp = this.keys.up.isDown || this.keys.w.isDown || this.keys.space.isDown || (mcKeys?.up ?? false);
    const keys = {
      left: this.keys.left.isDown || this.keys.a.isDown || (mcKeys?.left ?? false),
      right: this.keys.right.isDown || this.keys.d.isDown || (mcKeys?.right ?? false),
      up: keyUp,
      upJustDown: Phaser.Input.Keyboard.JustDown(this.keys.up) || Phaser.Input.Keyboard.JustDown(this.keys.w) ||
        Phaser.Input.Keyboard.JustDown(this.keys.space) || (mcKeys?.up && !this._mobileUpWasDown),
      down: this.keys.down.isDown || this.keys.s.isDown || (mcKeys?.down ?? false)
    };
    this._mobileUpWasDown = mcKeys?.up ?? false;

    if (Phaser.Input.Keyboard.JustDown(this.keys.e) || mc.consumeE()) eAbility(this);
    if (Phaser.Input.Keyboard.JustDown(this.keys.q) || mc.consumeQ()) qUlti(this);
    if (mc.consumeSpecial()) { const aim = getAim(this); rightAction(this, aim.x, aim.y); }
    if (this.mouseDown || mc.fireHeld) leftAttack(this);

    // platforms (movement + one-way landing collision), see game (1).py's
    // "Platformlar (hareket + tek yönlü çarpışma)" block for the source logic.
    const oncekiAyakY = p.y + p.h;
    for (const pl of this.platforms) {
      if (pl.hiz !== undefined) {
        pl.x += pl.hiz;
        if (pl.x <= pl.sol || pl.x + pl.w >= pl.sag) {
          pl.hiz *= -1;
          pl.x = Phaser.Math.Clamp(pl.x, pl.sol, pl.sag - pl.w);
        }
      }
      // ruins platforms start crumbling the instant they've been landed on,
      // and vanish for good once the countdown runs out
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

    // spawn
    if (this.spawnSira.length > 0) {
      this.spawnTimer--;
      if (this.spawnTimer <= 0) {
        const tip = this.spawnSira.pop();
        const side = Math.random() < 0.5 ? -1 : 1;
        const x = side === -1 ? 20 : GENISLIK - 60;
        this.enemies.push(new Dusman(this, tip, x, this.bolum, side));
        this.spawnTimer = Math.max(40, 100 - this.bolum * 2);
      }
    }

    // enemies
    for (const d of this.enemies) {
      if (d.dead) continue;
      d.guncelle(p.x + p.w / 2, p.y + p.h / 2, this.time.now, this.mermiler, Mermi);
      const dr = d.rect(), pr = p.rect();
      if (Phaser.Geom.Intersects.RectangleToRectangle(dr, pr)) {
        if (p.hasarTimer <= 0) {
          if (d.tip === 'melee' || d.tip === 'shield') p.hasarAl(15);
          else if (d.tip !== 'suicide') p.hasarAl(10);
        }
      }
      if (d.tip === 'suicide' && d.patlayacak) {
        const cx = d.x + d.w / 2, cy = d.y + d.h / 2;
        const dist = Math.hypot((p.x + p.w / 2) - cx, (p.y + p.h / 2) - cy);
        if (dist < PATLAMA_YARICAP && p.hasarTimer <= 0) p.hasarAl(28);
        d.can = 0;
      }
    }

    // worm hazard
    if (!this.worm) {
      this.wormTimer--;
      if (this.wormTimer <= 0) {
        const dir = p.hizX >= 0 ? 1 : -1;
        const spawnX = Phaser.Math.Clamp(p.x + p.w / 2 + dir * SOLUCAN.ONDEN_MESAFE, 30, GENISLIK - 30);
        this.worm = new Solucan(this, spawnX);
      }
    } else {
      this.worm.guncelle();
      if (this.worm.tehlikeliMi() && p.hasarTimer <= 0 &&
        Phaser.Geom.Intersects.RectangleToRectangle(this.worm.rect(), p.rect())) {
        p.hasarAl(this.worm.hasar);
      }
      if (this.worm.bittiMi()) {
        this.worm.destroy();
        this.worm = null;
        this.wormTimer = Phaser.Math.Between(SOLUCAN.ARALIK_MIN, SOLUCAN.ARALIK_MAX);
      }
    }

    // falling debris (higher-tier stages only) — ruins get them more often and bigger
    if (this.temaBolum > 10) {
      this.debrisTimer--;
      if (this.debrisTimer <= 0) {
        const x = Phaser.Math.Between(30, GENISLIK - 30);
        const harabe = this.temaBolum > 20;
        const buyuk = Math.random() < (harabe ? 0.75 : 0.5);
        this.debris.push(new Enkaz(this, x, buyuk, harabe ? 1.35 : 1));
        this.debrisTimer = harabe ? Phaser.Math.Between(70, 130) : Phaser.Math.Between(150, 250);
      }
    }
    for (const e of this.debris) {
      e.guncelle();
      if (e.dusuyor && !e.hit && p.hasarTimer <= 0 && Phaser.Geom.Intersects.RectangleToRectangle(e.rect(), p.rect())) {
        p.hasarAl(e.hasar);
        e.hit = true;
      }
    }
    this.debris = this.debris.filter(e => { if (e.bittiMi()) { e.destroy(); return false; } return true; });

    // skeletons (REAPER allies)
    for (const s of this.skeletons) s.guncelle(this.enemies, (d, amt) => this.applyDamage(d, amt));
    this.skeletons = this.skeletons.filter(s => {
      if (s.can <= 0) { s.destroy(); p.can = Math.min(p.maxCan, p.can + 10); return false; }
      return true;
    });

    // bullets
    for (const m of this.mermiler) {
      m.guncelle();
      const mr = m.rect();
      if (m.oyuncuMermisi) {
        for (const d of hitTargets(this)) {
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
      } else {
        if (p.hasarTimer <= 0 && Phaser.Geom.Intersects.RectangleToRectangle(mr, p.rect())) {
          p.hasarAl(m.hasar);
          m.dead = true;
        }
      }
    }
    this.mermiler = this.mermiler.filter(m => {
      if (m.dead) { m.destroy(); return false; }
      return true;
    });

    // onEnemyKilled already fired from the Dusman.can setter the instant health
    // crossed zero (see Enemy.js) — this pass only reclaims dead entities.
    const stillAlive = [];
    for (const d of this.enemies) {
      if (d.dead) d.destroy(); else stillAlive.push(d);
    }
    this.enemies = stillAlive;

    // particles + damage numbers
    for (const f of this.fx) f.guncelle();
    this.fx = this.fx.filter(f => { if (f.dead) { f.destroy(); return false; } return true; });
    for (const t of this.dmgTexts) t.guncelle();
    this.dmgTexts = this.dmgTexts.filter(t => { if (t.dead) { t.destroy(); return false; } return true; });

    // draw
    this.platformGfx.clear();
    const platRenk = this.temaBolum <= 10 ? 0x3c3c50 : (this.temaBolum <= 20 ? 0x281946 : 0x3c1410);
    for (const pl of this.platforms) {
      if (pl.kirildi) continue;
      const crumbling = pl.kirilir && pl.kirilmaKare > 0;
      const fillColor = crumbling ? 0xe94560 : platRenk;
      this.platformGfx.fillStyle(fillColor, crumbling ? (0.4 + 0.6 * (pl.kirilmaKare / 120)) : 1);
      this.platformGfx.fillRect(pl.x, pl.y, pl.w, pl.h);
      this.platformGfx.lineStyle(1, 0x00fff7, 1);
      this.platformGfx.strokeRect(pl.x, pl.y, pl.w, pl.h);
    }
    for (const e of this.debris) e.draw();
    if (this.worm) this.worm.draw();
    for (const s of this.skeletons) s.draw();
    { const aim = getAim(this); p.draw(aim.x, aim.y); this.crosshair.draw(aim.x, aim.y); }
    this.mobileControls.draw();
    for (const d of this.enemies) d.draw(this.time.now);
    for (const m of this.mermiler) m.draw();
    for (const f of this.fx) f.draw();
    for (const t of this.dmgTexts) t.draw();

    // HUD
    this.hud.update(this.bolum, this.kalanDusman, this.skor);

    if (p.can <= 0 && !this.gameOver) {
      this.gameOver = true;
      this.sound.play('karakter_olum', { volume: 0.6 });
      this.msgBox.setVisible(true);
      this.msgText.setText(t('kaybettin'));
      this._showEndButtons([
        [t('tekrarOyna'), () => this.scene.restart({ bolum: this.bolum, heroId: this.heroId })],
        [t('anaMenuyeDon'), () => this.scene.start('Menu')]
      ]);
    } else if (this.kalanDusman <= 0 && this.spawnSira.length === 0 && this.wormKilled && !this.stageBitti) {
      this.stageBitti = true;
      GameState.enYuksekBolum = Math.max(GameState.enYuksekBolum, this.bolum + 1);
      saveState();
      this.sound.play('bolum_tamam', { volume: 0.6 });
      this.msgBox.setVisible(true);
      const buttons = [];
      if (this.ayarFinal) {
        this.msgBox.setSize(560, 270);
        this.msgText.setText(t('savasiKazandin'));
        this.msgText.setColor('#f5a623').setFontSize(34);
        this.add.text(GENISLIK / 2, YUKSEKLIK / 2 + 40, t('zaferAltyazi'), {
          fontFamily: 'monospace', fontSize: '14px', color: '#dddddd'
        }).setOrigin(0.5).setDepth(30);
      } else {
        this.msgText.setText(t('bolumTamamlandi'));
        buttons.push([t('sonrakiBolum'), async () => {
          await commercialBreak();
          this.scene.restart({ bolum: this.bolum + 1, heroId: this.heroId });
        }]);
      }
      buttons.push([t('anaMenuyeDon'), () => this.scene.start('Menu')]);
      this._showEndButtons(buttons, this.ayarFinal ? 95 : 45);
    }
  }

  _showEndButtons(items, startY = 45) {
    items.forEach(([label, action], i) => {
      makeButton(this, GENISLIK / 2, YUKSEKLIK / 2 + startY + i * 44, 220, 34, label, action, '15px');
    });
  }
}
