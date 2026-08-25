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
