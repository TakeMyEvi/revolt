import Phaser from 'phaser';
import { GENISLIK, YUKSEKLIK, GENEL_GOREVLER } from '../data/constants.js';
import { GameState } from '../data/state.js';
import { makeButton } from '../systems/ui.js';
import { t } from '../data/translations.js';

// Permanent lifetime-milestone missions — see GENEL_GOREVLER / Player.genelYukseltmeUygula.
// Character-specific missions live in the Kahramanlar screen's YUKSELT panel
// (per-hero mastery tiers unlocked by cumulative damage dealt).
export class GorevlerScene extends Phaser.Scene {
  constructor() { super('Gorevler'); }

  create() {
    this.cameras.main.setBackgroundColor('#05050f');
    makeButton(this, 60, 30, 100, 32, t('geri'), () => this.scene.start('Menu'), '13px');
    this.add.text(GENISLIK / 2, 36, t('gorevlerBaslik'), { fontFamily: 'monospace', fontSize: '22px', color: '#00fff7' }).setOrigin(0.5);

    this.add.text(GENISLIK / 2, 80, t('genelGorevler'), { fontFamily: 'monospace', fontSize: '15px', color: '#f5a623' }).setOrigin(0.5);
    GENEL_GOREVLER.forEach((gorev, i) => {
      const y = 120 + i * 62;
      const tamam = gorev.kontrol(GameState);
      this.add.rectangle(GENISLIK / 2, y + 14, 700, 52, 0x0a0a18, 0.9).setStrokeStyle(1, tamam ? 0x00ff88 : 0x333344);
      this.add.text(140, y, `${tamam ? '[X]' : '[ ]'} ${gorev.isim}`, {
        fontFamily: 'monospace', fontSize: '15px', color: tamam ? '#00ff88' : '#dddddd'
      });
      this.add.text(140, y + 20, gorev.aciklama, { fontFamily: 'monospace', fontSize: '11px', color: '#999999' });
      this.add.text(GENISLIK - 140, y + 10, this._etkiMetni(gorev.etki), {
        fontFamily: 'monospace', fontSize: '11px', color: '#00fff7'
      }).setOrigin(1, 0);
    });

    const karakterY = 120 + GENEL_GOREVLER.length * 62 + 20;
    this.add.text(GENISLIK / 2, karakterY, t('karakterGorevleri'), { fontFamily: 'monospace', fontSize: '15px', color: '#f5a623' }).setOrigin(0.5);
    this.add.text(GENISLIK / 2, karakterY + 24, t('karakterGorevAciklama'), {
      fontFamily: 'monospace', fontSize: '12px', color: '#999999'
    }).setOrigin(0.5);
    makeButton(this, GENISLIK / 2, karakterY + 60, 260, 34, t('kahramanUstalik'), () => {
      this.scene.start('HeroSelect', { openUstalik: true });
    }, '13px');

    this.keyEsc = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ESC);
  }

  _etkiMetni(etki) {
    const parts = [];
    if (etki.can) parts.push(`+${etki.can} CAN`);
    if (etki.hiz) parts.push(`+%${Math.round(etki.hiz * 100)} HIZ`);
    if (etki.regen) parts.push(`+${etki.regen} REGEN`);
    return parts.join('  ');
  }

  update() {
    if (Phaser.Input.Keyboard.JustDown(this.keyEsc)) this.scene.start('Menu');
  }
}
