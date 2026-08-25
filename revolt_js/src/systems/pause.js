import { GENISLIK, YUKSEKLIK } from '../data/constants.js';
import { t } from '../data/translations.js';
import { makeButton } from './ui.js';

// Top-right pause ("II") button + pause overlay, matching the Python original's
// `durdur_buton_rect` (26x26 at GENISLIK-34,8) and pause_devam_rect/pause_menu_rect.
export class PauseController {
  constructor(scene, onMenu) {
    this.scene = scene;
    this.onMenu = onMenu;
    this.paused = false;
    this.overlay = null;

    const bx = GENISLIK - 34 + 13, by = 8 + 13;
    this.btnBg = scene.add.rectangle(bx, by, 26, 26, 0x0a0a12).setStrokeStyle(2, 0x00fff7).setDepth(22).setInteractive({ useHandCursor: true });
    this.btnBg.on('pointerover', () => this.btnBg.setFillStyle(0x142d28).setStrokeStyle(2, 0x00ffc8));
    this.btnBg.on('pointerout', () => this.btnBg.setFillStyle(0x0a0a12).setStrokeStyle(2, 0x00fff7));
    this.btnBg.on('pointerdown', () => this.toggle());
    this.iconGfx = scene.add.graphics().setDepth(23);
    this.iconGfx.fillStyle(0xffffff, 1);
    this.iconGfx.fillRect(bx - 6, by - 7, 4, 14);
    this.iconGfx.fillRect(bx + 2, by - 7, 4, 14);
  }

  get active() { return this.paused; }

  toggle() { if (this.paused) this.hide(); else this.show(); }

  show() {
    if (this.paused) return;
    this.paused = true;
    const g = this.scene.add.container(0, 0).setDepth(60);
    this.overlay = g;
    g.add(this.scene.add.rectangle(GENISLIK / 2, YUKSEKLIK / 2, GENISLIK, YUKSEKLIK, 0x000000, 0.65));
    g.add(this.scene.add.text(GENISLIK / 2, YUKSEKLIK / 2 - 60, t('duraklatildi'), {
      fontFamily: 'monospace', fontSize: '26px', color: '#00fff7'
    }).setOrigin(0.5));
    const resumeBtn = makeButton(this.scene, GENISLIK / 2, YUKSEKLIK / 2 - 5, 220, 42, t('devamEt'), () => this.hide(), '16px');
    const menuBtn = makeButton(this.scene, GENISLIK / 2, YUKSEKLIK / 2 + 55, 220, 42, t('anaMenuyeDon'), () => this.onMenu(), '16px');
    g.add([resumeBtn.bg, resumeBtn.text, menuBtn.bg, menuBtn.text]);
  }

  hide() {
    if (!this.paused) return;
    this.paused = false;
    if (this.overlay) { this.overlay.destroy(true); this.overlay = null; }
  }

  destroy() {
    this.btnBg.destroy();
    this.iconGfx.destroy();
    if (this.overlay) this.overlay.destroy(true);
  }
}
