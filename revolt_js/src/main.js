import Phaser from 'phaser';
import { BootScene } from './scenes/BootScene.js';
import { MenuScene } from './scenes/MenuScene.js';
import { PlayScene } from './scenes/PlayScene.js';
import { SurvivalScene } from './scenes/SurvivalScene.js';
import { HeroSelectScene } from './scenes/HeroSelectScene.js';
import { StageSelectScene } from './scenes/StageSelectScene.js';
import { ControlsScene } from './scenes/ControlsScene.js';
import { SettingsScene } from './scenes/SettingsScene.js';
import { CreditsScene } from './scenes/CreditsScene.js';
import { GorevlerScene } from './scenes/GorevlerScene.js';
import { HikayeScene } from './scenes/HikayeScene.js';

// The game draws at a fixed 900x550 internal resolution and Scale.FIT then
// stretches that canvas up to fill whatever screen it's on — often well
// past 1:1. Everything gets softened a bit by that stretch, but Phaser Text
// objects are hit hardest: unless told otherwise they rasterize their glyphs
// at resolution 1 and THAT bitmap is what gets stretched, so letters go
// visibly mushy. Patching the factory here (once) instead of touching every
// scene's add.text(...) call makes every menu/HUD label render its glyphs at
// a higher source resolution first, so the later upscale stays crisp.
const TEXT_RESOLUTION = Math.max(2, window.devicePixelRatio || 1);
const originalTextFactory = Phaser.GameObjects.GameObjectFactory.prototype.text;
Phaser.GameObjects.GameObjectFactory.prototype.text = function (x, y, text, style) {
  const withResolution = { ...(style || {}) };
  if (withResolution.resolution === undefined) withResolution.resolution = TEXT_RESOLUTION;
  return originalTextFactory.call(this, x, y, text, withResolution);
};

const GENISLIK = 900;
const YUKSEKLIK = 550;

const config = {
  type: Phaser.AUTO,
  parent: 'game-container',
  width: GENISLIK,
  height: YUKSEKLIK,
  backgroundColor: '#05050f',
  pixelArt: false,
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH
  },
  // Movement everywhere is written as a fixed per-frame pixel amount (ported
  // from the Python original's clock.tick(60) model), not scaled by delta —
  // so the game visibly speeds up/slows down if the tick rate drifts from a
  // steady 60/s. requestAnimationFrame syncs to the DISPLAY's refresh rate,
  // which on phones with adaptive refresh (60-120Hz) varies during play;
  // forceSetTimeOut pins the loop to a fixed 60/s via setTimeout instead,
  // decoupling simulation speed from the screen's refresh rate.
  fps: { target: 60, forceSetTimeOut: true },
  // Mobile's on-screen stick + fire-stick + E/Q/Special buttons all rely on
  // separate simultaneous touches; Phaser only tracks 1 pointer by default.
  input: { activePointers: 5 },
  physics: {
    default: 'arcade',
    arcade: {
      gravity: { y: 0 },
      debug: false
    }
  },
  scene: [BootScene, HikayeScene, MenuScene, PlayScene, SurvivalScene, HeroSelectScene, StageSelectScene, ControlsScene, SettingsScene, CreditsScene, GorevlerScene]
};

window.__game = new Phaser.Game(config);

// The CSS in index.html rotates #game-container 90deg on portrait phones so
// the landscape game fills the screen instead of shrinking to a tiny strip.
// Phaser's Scale Manager doesn't always notice that swap on its own, so give
// it a nudge on every orientation/resize change. The short delay lets the
// browser finish applying the new CSS layout box before Phaser re-measures it.
window.addEventListener('orientationchange', () => {
  setTimeout(() => window.__game?.scale.refresh(), 100);
});
window.addEventListener('resize', () => {
  window.__game?.scale.refresh();
});

// Enables "Add to Home Screen" — only takes effect on a direct, top-level
// visit (registration silently fails/no-ops inside itch.io's iframe embed,
// which is harmless: the game just runs without install support there).
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  });
}
