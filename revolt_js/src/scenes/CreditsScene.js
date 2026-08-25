import Phaser from 'phaser';
import { GENISLIK, YUKSEKLIK } from '../data/constants.js';
import { makeButton } from '../systems/ui.js';
import { t } from '../data/translations.js';

const KREDI_LISTESI = [
  ['Retroclassic Game Music', 'ZHRO', 'CC BY 4.0'],
  ['Robot Toy Music 01 (Longtrack)', 'toam', 'CC BY 3.0'],
  ['Fantasy Classical Themes', 'TheoJT', 'CC BY 4.0'],
  ['Sci-Fi Soldier Death', 'Diasyl', 'CC BY 4.0'],
  ['Fantasy Achievement Unlock', 'TommasoMotteran', 'CC BY 4.0'],
  ['Fantasy UI Stinger - Level Up 03', 'TommasoMotteran', 'CC BY 4.0'],
  ['Video Game SFX - Positive Action', 'djlprojects', 'CC BY 4.0'],
  ['Engine Dying', 'Jofae', 'CC0']
];

export class CreditsScene extends Phaser.Scene {
  constructor() { super('Credits'); }

  create() {
    this.cameras.main.setBackgroundColor('#05050f');
    this.add.text(GENISLIK / 2, 50, t('krediler_baslik'), { fontFamily: 'monospace', fontSize: '24px', color: '#00fff7' }).setOrigin(0.5);
    this.add.text(GENISLIK / 2, 85, t('krediler_altbaslik'), { fontFamily: 'monospace', fontSize: '12px', color: '#888888' }).setOrigin(0.5);
    KREDI_LISTESI.forEach(([name, artist, lic], i) => {
      const y = 130 + i * 30;
      this.add.text(160, y, `${name} - ${artist}`, { fontFamily: 'monospace', fontSize: '13px', color: '#dddddd' });
      this.add.text(GENISLIK - 160, y, lic, { fontFamily: 'monospace', fontSize: '12px', color: '#00fff7' }).setOrigin(1, 0);
    });
    this.add.text(GENISLIK / 2, YUKSEKLIK - 40, 'freesound.org', { fontFamily: 'monospace', fontSize: '12px', color: '#666666' }).setOrigin(0.5);
    this.add.text(GENISLIK / 2, YUKSEKLIK - 20, t('kontrollerIpucu'), { fontFamily: 'monospace', fontSize: '13px', color: '#888888' }).setOrigin(0.5);
    makeButton(this, 60, 26, 100, 32, t('geri'), () => this.scene.start('Menu'), '13px');
    this.keyEsc = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ESC);
    this.keyEnter = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ENTER);
  }

  update() {
    if (Phaser.Input.Keyboard.JustDown(this.keyEsc) || Phaser.Input.Keyboard.JustDown(this.keyEnter)) this.scene.start('Menu');
  }
}
