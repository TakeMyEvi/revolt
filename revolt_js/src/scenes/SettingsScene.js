import Phaser from 'phaser';
import { GENISLIK, YUKSEKLIK } from '../data/constants.js';
import { GameState, saveState } from '../data/state.js';
import { makeButton } from '../systems/ui.js';
import { NISANGAH_RENKLERI, NISANGAH_SEKILLERI, drawNisangah } from '../systems/crosshair.js';
import { t } from '../data/translations.js';

const DILLER = [
  { kod: 'tr', ad: 'TR' }, { kod: 'en', ad: 'EN' }, { kod: 'es', ad: 'ES' },
  { kod: 'fr', ad: 'FR' }, { kod: 'de', ad: 'DE' }
];
const SEKIL_ADLARI = { arti: 'ARTI', daire: 'DAIRE', nokta: 'NOKTA', kare: 'KARE' };

export class SettingsScene extends Phaser.Scene {
  constructor() { super('Settings'); }

  create() {
    this.cameras.main.setBackgroundColor('#05050f');
    this.add.text(GENISLIK / 2, 36, t('ayarlarBaslik'), { fontFamily: 'monospace', fontSize: '22px', color: '#00fff7' }).setOrigin(0.5);
    makeButton(this, 60, 30, 100, 32, t('geri'), () => this.scene.start('Menu'), '13px');

    this._slider(80, t('sesEfekti'), 'sesSeviyesi');
    this._slider(115, t('muzik'), 'muzikSeviyesi');

    this.add.text(200, 160, t('dil'), { fontFamily: 'monospace', fontSize: '14px', color: '#dddddd' }).setOrigin(0, 0.5);
    this.dilButonlari = DILLER.map((d, i) => makeButton(this, 420 + i * 52, 160, 46, 28, d.ad, () => {
      GameState.dil = d.kod; saveState(); this.scene.restart();
    }, '12px'));
    this._refreshDil();

    this.add.text(GENISLIK / 2, 205, t('mobilKontroller'), { fontFamily: 'monospace', fontSize: '14px', color: '#00fff7' }).setOrigin(0.5);
    this.mobilButonlari = [
      makeButton(this, GENISLIK / 2 - 60, 235, 100, 30, t('acik'), () => { GameState.mobilKontrolAcik = true; saveState(); this._refreshMobil(); }, '13px'),
      makeButton(this, GENISLIK / 2 + 60, 235, 100, 30, t('kapali'), () => { GameState.mobilKontrolAcik = false; saveState(); this._refreshMobil(); }, '13px')
    ];
    this._refreshMobil();

    this.add.text(GENISLIK / 2, 280, t('pcKontrolleri'), { fontFamily: 'monospace', fontSize: '14px', color: '#00fff7' }).setOrigin(0.5);

    this.add.text(200, 315, t('imlecSekli'), { fontFamily: 'monospace', fontSize: '13px', color: '#dddddd' }).setOrigin(0, 0.5);
    this.sekilButonlari = NISANGAH_SEKILLERI.map((s, i) => makeButton(this, 460 + i * 78, 315, 70, 28, SEKIL_ADLARI[s], () => {
      GameState.nisangahSekilIdx = i; saveState(); this._refreshSekil();
    }, '11px'));
    this._refreshSekil();

    // Live preview of the aiming reticle — matches the Python original's
    // in-settings nisangah_ciz(ekran, onizleme_x, onizleme_y) call.
    this.add.rectangle(800, 315, 60, 60, 0x000000).setStrokeStyle(1, 0x333344);
    this.onizlemeGfx = this.add.graphics();
    this._refreshOnizleme();

    this.add.text(200, 355, t('imlecRengi'), { fontFamily: 'monospace', fontSize: '13px', color: '#dddddd' }).setOrigin(0, 0.5);
    this.renkKutulari = NISANGAH_RENKLERI.map((r, i) => {
      const x = 420 + i * 40;
      const box = this.add.rectangle(x, 355, 26, 26, r.renk).setStrokeStyle(2, 0x000000).setInteractive({ useHandCursor: true });
      box.on('pointerdown', () => { GameState.nisangahRenkIdx = i; saveState(); this._refreshRenk(); });
      return box;
    });
    this._refreshRenk();

    this.add.text(200, 395, t('imleciGizle'), { fontFamily: 'monospace', fontSize: '13px', color: '#dddddd' }).setOrigin(0, 0.5);
    this.gizleButonlari = [
      makeButton(this, 460, 395, 90, 28, t('acik'), () => { GameState.imlecGizli = true; saveState(); this._refreshGizle(); }, '12px'),
      makeButton(this, 560, 395, 90, 28, t('kapali'), () => { GameState.imlecGizli = false; saveState(); this._refreshGizle(); }, '12px')
    ];
    this._refreshGizle();

    this.add.text(GENISLIK / 2, YUKSEKLIK - 20, t('ayarlarIpucu'), { fontFamily: 'monospace', fontSize: '13px', color: '#888888' }).setOrigin(0.5);
    this.keyEsc = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ESC);
  }

  _refreshDil() {
    DILLER.forEach((d, i) => this.dilButonlari[i].setSelected(GameState.dil === d.kod));
  }

  _refreshMobil() {
    this.mobilButonlari[0].setSelected(!!GameState.mobilKontrolAcik);
    this.mobilButonlari[1].setSelected(!GameState.mobilKontrolAcik);
  }

  _refreshSekil() {
    NISANGAH_SEKILLERI.forEach((s, i) => this.sekilButonlari[i].setSelected((GameState.nisangahSekilIdx || 0) === i));
    this._refreshOnizleme();
  }

  _refreshRenk() {
    const idx = GameState.nisangahRenkIdx || 0;
    this.renkKutulari.forEach((box, i) => box.setStrokeStyle(i === idx ? 3 : 2, i === idx ? 0x2288ff : 0x000000));
    this._refreshOnizleme();
  }

  _refreshOnizleme() {
    if (!this.onizlemeGfx) return;
    this.onizlemeGfx.clear();
    drawNisangah(this.onizlemeGfx, 800, 315, GameState.nisangahRenkIdx, GameState.nisangahSekilIdx);
  }

  _refreshGizle() {
    this.gizleButonlari[0].setSelected(!!GameState.imlecGizli);
    this.gizleButonlari[1].setSelected(!GameState.imlecGizli);
  }

  _slider(y, label, prop) {
    this.add.text(200, y, label, { fontFamily: 'monospace', fontSize: '14px', color: '#dddddd' }).setOrigin(0, 0.5);
    const minus = this.add.text(560, y, '-', { fontFamily: 'monospace', fontSize: '20px', color: '#f5a623' })
      .setOrigin(0.5).setInteractive({ useHandCursor: true });
    const plus = this.add.text(690, y, '+', { fontFamily: 'monospace', fontSize: '20px', color: '#f5a623' })
      .setOrigin(0.5).setInteractive({ useHandCursor: true });
    const barBg = this.add.rectangle(625, y, 40, 12, 0x222233).setOrigin(0.5);
    const bar = this.add.rectangle(605, y, 1, 12, 0x00fff7).setOrigin(0, 0.5);
    const pct = this.add.text(660, y, '', { fontFamily: 'monospace', fontSize: '12px', color: '#ffffff' }).setOrigin(0, 0.5);

    const refresh = () => {
      const v = GameState[prop];
      bar.width = 40 * v;
      pct.setText(`${Math.round(v * 100)}%`);
    };
    minus.on('pointerdown', () => { GameState[prop] = Math.max(0, Math.round((GameState[prop] - 0.1) * 10) / 10); saveState(); refresh(); });
    plus.on('pointerdown', () => { GameState[prop] = Math.min(1, Math.round((GameState[prop] + 0.1) * 10) / 10); saveState(); refresh(); });
    refresh();
  }

  update() {
    if (Phaser.Input.Keyboard.JustDown(this.keyEsc)) this.scene.start('Menu');
  }
}
