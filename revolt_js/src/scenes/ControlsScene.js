import Phaser from 'phaser';
import { GENISLIK, YUKSEKLIK } from '../data/constants.js';
import { makeButton } from '../systems/ui.js';
import { t } from '../data/translations.js';

const LINE_KEYS = ['kontrolSatiri1', 'kontrolSatiri2', 'kontrolSatiri3', 'kontrolSatiri4', 'kontrolSatiri5', 'kontrolSatiri6', 'kontrolSatiri7'];

export class ControlsScene extends Phaser.Scene {
  constructor() { super('Controls'); }

  create() {
    this.cameras.main.setBackgroundColor('#05050f');
    this.add.text(GENISLIK / 2, 60, t('kontrollerBaslik'), { fontFamily: 'monospace', fontSize: '24px', color: '#00fff7' }).setOrigin(0.5);
    LINE_KEYS.forEach((key, i) => {
      this.add.text(GENISLIK / 2, 140 + i * 34, t(key), { fontFamily: 'monospace', fontSize: '15px', color: '#dddddd' }).setOrigin(0.5);
    });
    this.add.text(GENISLIK / 2, YUKSEKLIK - 30, t('kontrollerIpucu'), { fontFamily: 'monospace', fontSize: '13px', color: '#888888' }).setOrigin(0.5);
    makeButton(this, 60, 30, 100, 32, t('geri'), () => this.scene.start('Menu'), '13px');
    this.keyEsc = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ESC);
    this.keyEnter = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ENTER);
  }

  update() {
    if (Phaser.Input.Keyboard.JustDown(this.keyEsc) || Phaser.Input.Keyboard.JustDown(this.keyEnter)) this.scene.start('Menu');
  }
}
