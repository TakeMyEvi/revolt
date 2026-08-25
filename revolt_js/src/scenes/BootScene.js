import Phaser from 'phaser';
import { initPoki, gameLoadingFinished } from '../systems/poki.js';

// Keep this preload list to only what's needed before the menu can render —
// everything else (team posters, stage/theme music) is loaded on demand by
// the scene that actually needs it, to keep the initial download small.
export class BootScene extends Phaser.Scene {
  constructor() {
    super('Boot');
  }

  init() {
    initPoki(); // fire-and-forget — never blocks asset loading
  }

  preload() {
    const w = this.scale.width, h = this.scale.height;
    this.add.rectangle(w / 2, h / 2, w, h, 0x05050f);
    this.add.text(w / 2, h / 2 + 30, 'Loading...', {
      fontFamily: 'monospace', fontSize: '16px', color: '#00fff7'
    }).setOrigin(0.5);
    this.add.rectangle(w / 2, h / 2, 300, 10, 0x222233).setOrigin(0.5);
    const bar = this.add.rectangle(w / 2 - 150, h / 2, 4, 10, 0x00fff7).setOrigin(0, 0.5);
    this.load.on('progress', (v) => { bar.width = 300 * v; });

    this.load.image('revolt_logo', 'gorseller/revolt_logo.jpg');

    this.load.audio('karakter_olum', 'sesler/karakter_olum.ogg');
    this.load.audio('kahraman_acildi', 'sesler/kahraman_acildi.ogg');
    this.load.audio('hex_ulti', 'sesler/hex_ulti.ogg');
    this.load.audio('bolum_tamam', 'sesler/bolum_tamam.ogg');
    this.load.audio('boss_olum', 'sesler/boss_olum.ogg');
  }

  create() {
    this._makeTransparentLogo();
    gameLoadingFinished();
    this.scene.start('Hikaye'); // shown once per page load — matches the original's `ilk_acilis` intro
  }

  // Mirrors the Python original's `_kenar_seffaflastir(yuzey, esik=40, yumusatma=35)` —
  // the JPEG's black background becomes transparent with a soft edge instead of a hard cut.
  _makeTransparentLogo() {
    const esik = 40, yumusatma = 35;
    const src = this.textures.get('revolt_logo').getSourceImage();
    const canvas = document.createElement('canvas');
    canvas.width = src.width; canvas.height = src.height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(src, 0, 0);
    const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const d = imgData.data;
    for (let i = 0; i < d.length; i += 4) {
      const parlaklik = Math.max(d[i], d[i + 1], d[i + 2]);
      let a;
      if (parlaklik <= esik) a = 0;
      else if (parlaklik >= esik + yumusatma) a = 255;
      else a = Math.round(255 * (parlaklik - esik) / yumusatma);
      d[i + 3] = a;
    }
    ctx.putImageData(imgData, 0, 0);
    this.textures.addCanvas('revolt_logo_t', canvas);
  }
}
