import Phaser from 'phaser';
import { GENISLIK, YUKSEKLIK } from '../data/constants.js';
import { GameState } from '../data/state.js';
import { drawThemedBackground } from '../systems/background.js';
import { makeButton } from '../systems/ui.js';
import { playThemeMusic, themeKeyForBolum } from '../systems/music.js';
import { t } from '../data/translations.js';

export class MenuScene extends Phaser.Scene {
  constructor() {
    super('Menu');
  }

  create() {
    drawThemedBackground(this);
    playThemeMusic(this, themeKeyForBolum(GameState.enYuksekBolum));
    // native asset is 1719x915 — the Python original scales it to width 260 before drawing.
    this.add.image(GENISLIK / 2, 90, 'revolt_logo_t').setDisplaySize(260, 260 * (915 / 1719));

    const items = [
      [t('oyna'), () => this.scene.start('Play', { bolum: 1, heroId: GameState.selectedHero })],
      [t('hayattaKal'), () => this.scene.start('HeroSelect', { forSurvival: true })],
      [t('kahramanlar'), () => this.scene.start('HeroSelect')],
      [t('bolumler'), () => this.scene.start('StageSelect')],
      [t('gorevler'), () => this.scene.start('Gorevler')],
      [t('kontroller'), () => this.scene.start('Controls')],
      [t('ayarlar'), () => this.scene.start('Settings')],
      [t('cikis'), () => {}]
    ];

    items.forEach(([label, action], i) => {
      const y = 190 + i * 34;
      makeButton(this, GENISLIK / 2, y, 220, 30, label, action);
    });

    this.add.text(GENISLIK - 16, YUKSEKLIK - 16, t('krediler'), {
      fontFamily: 'monospace', fontSize: '12px', color: '#666666'
    }).setOrigin(1).setInteractive({ useHandCursor: true }).on('pointerdown', () => this.scene.start('Credits'));

    this.add.text(GENISLIK / 2, YUKSEKLIK - 20, t('menuIpucu'), {
      fontFamily: 'monospace', fontSize: '12px', color: '#888888'
    }).setOrigin(0.5);
  }
}
