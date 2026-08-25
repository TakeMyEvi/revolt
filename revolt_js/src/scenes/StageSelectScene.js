import Phaser from 'phaser';
import { GENISLIK, YUKSEKLIK, KAHRAMANLAR } from '../data/constants.js';
import { GameState } from '../data/state.js';
import { drawThemedBackground } from '../systems/background.js';
import { playThemeMusic, themeKeyForBolum } from '../systems/music.js';
import { makeButton } from '../systems/ui.js';
import { t } from '../data/translations.js';

const TEMA_ADI_ANAHTAR = ['temaSehir', 'temaUzay', 'temaHarabe'];
const TEMA_RENK = [0x46aaff, 0xaa5aff, 0xff503c];

export class StageSelectScene extends Phaser.Scene {
  constructor() {
    super('StageSelect');
  }

  create() {
    drawThemedBackground(this);
    playThemeMusic(this, themeKeyForBolum(GameState.enYuksekBolum));
    this.page = 0;
    this.container = this.add.container(0, 0);
    this._drawPage();

    makeButton(this, 60, 26, 100, 32, t('geri'), () => this.scene.start('Menu'), '13px');

    const leftArrow = this.add.text(20, YUKSEKLIK / 2, '<', { fontFamily: 'monospace', fontSize: '32px', color: '#00fff7' })
      .setInteractive({ useHandCursor: true }).on('pointerdown', () => this._changePage(-1));
    const rightArrow = this.add.text(GENISLIK - 30, YUKSEKLIK / 2, '>', { fontFamily: 'monospace', fontSize: '32px', color: '#00fff7' })
      .setInteractive({ useHandCursor: true }).on('pointerdown', () => this._changePage(1));

    this.input.on('wheel', (pointer, over, dx, dy) => {
      if (dy < 0) this._changePage(1); else if (dy > 0) this._changePage(-1);
    });

    this.keyEsc = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ESC);
  }

  update() {
    if (Phaser.Input.Keyboard.JustDown(this.keyEsc)) this.scene.start('Menu');
  }

  _changePage(dir) {
    this.page = (this.page + dir + 3) % 3;
    this._drawPage();
  }

  _drawPage() {
    this.container.removeAll(true);
    const themeColor = TEMA_RENK[this.page];
    this.container.add(this.add.text(GENISLIK / 2, 60, t(TEMA_ADI_ANAHTAR[this.page]), {
      fontFamily: 'monospace', fontSize: '22px', color: Phaser.Display.Color.IntegerToColor(themeColor).rgba
    }).setOrigin(0.5));

    const spacing = GENISLIK / 5;
    const ustY = YUKSEKLIK / 2 - 48;
    const altY = YUKSEKLIK / 2 + 48;

    for (let local = 0; local < 10; local++) {
      const stageNo = this.page * 10 + local + 1;
      const col = local % 5;
      const row = Math.floor(local / 5);
      const x = spacing * (col + 0.5);
      const y = row === 0 ? ustY : altY;
      const unlocked = GameState.testModu || stageNo <= GameState.enYuksekBolum;
      const isChaos = local === 4 || local === 8;

      const color = unlocked ? themeColor : 0x37373f;
      const hero = KAHRAMANLAR.find(h => h.acilis_bolum === stageNo && stageNo > 1);
      const g = this.add.graphics();
      if (hero) {
        // Hero-unlock stages get that hero's own "head" badge instead of the
        // generic tile shape — no separate name label needed, the badge says it.
        const headColor = unlocked ? hero.renk : 0x37373f;
        g.fillStyle(headColor, 1);
        g.fillCircle(x, y, 30);
        g.lineStyle(2, unlocked ? 0x000000 : 0x1a1a1a, 0.5);
        g.strokeCircle(x, y, 30);
      } else if (isChaos) {
        g.fillStyle(color, 1);
        g.fillTriangle(x, y - 28, x + 31, y + 28, x - 31, y + 28);
      } else {
        g.fillStyle(color, 1);
        g.fillRoundedRect(x - 31, y - 28, 62, 56, 8);
      }
      this.container.add(g);

      if (hero) {
        const monogram = this.add.text(x, y - 8, hero.isim.slice(0, 1), {
          fontFamily: 'monospace', fontSize: '20px', color: unlocked ? '#000000' : '#5f5f5f'
        }).setOrigin(0.5);
        this.container.add(monogram);
      }
      const label = this.add.text(x, hero ? y + 14 : y, String(stageNo), {
        fontFamily: 'monospace', fontSize: hero ? '12px' : '18px', color: unlocked ? '#000000' : '#5f5f5f'
      }).setOrigin(0.5);
      this.container.add(label);

      if (unlocked) {
        const hit = this.add.rectangle(x, y, 62, 56, 0xffffff, 0).setInteractive({ useHandCursor: true });
        hit.on('pointerdown', () => this.scene.start('Play', { bolum: stageNo, heroId: GameState.selectedHero }));
        this.container.add(hit);
      }
    }

    for (let i = 0; i < 3; i++) {
      const dot = this.add.circle(GENISLIK / 2 - 20 + i * 20, YUKSEKLIK - 30, 5, i === this.page ? 0x00fff7 : 0x333340);
      this.container.add(dot);
    }
  }
}
