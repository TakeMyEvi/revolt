import { GameState } from '../data/state.js';

const TRACKS = {
  metropol: { key: 'metropol_muzik', file: 'sesler/metropol_muzik.ogg' },
  derinUzay: { key: 'derin_uzay_muzik', file: 'sesler/derin_uzay_muzik.ogg' },
  harabe: { key: 'harabe_muzik', file: 'sesler/harabe_muzik.ogg' }
};

// Temporarily disabled at the user's request (overlapping tracks bug — see
// the loading-guard fix below for what caused it). Flip this back to true
// once re-enabled.
const MUSIC_ENABLED = false;

export function themeKeyForBolum(bolum) {
  if (bolum <= 10) return 'metropol';
  if (bolum <= 20) return 'derinUzay';
  return 'harabe';
}

// Loads a stage/theme music track on demand (matches the Python original's
// choice to only ever have one background track resident at a time) and
// plays it looped at a low ambient volume, matching MUZIK_SES_SEVIYESI=0.22.
export function playThemeMusic(scene, themeName) {
  if (!MUSIC_ENABLED) return;
  const track = TRACKS[themeName];
  if (!track) return;

  const g = scene.sys.game;
  if (g._currentMusicTheme === themeName && g._currentMusicSound?.isPlaying) return;
  // A load for this exact track is already in flight (e.g. the player
  // navigated menu->stageSelect->play before the first request finished) —
  // don't stack a second `filecomplete` listener, or both will fire and
  // start two overlapping copies of the same track.
  if (g._musicLoadingKey === track.key) return;

  const startPlayback = () => {
    g._musicLoadingKey = null;
    if (g._currentMusicSound) g._currentMusicSound.stop();
    const sound = scene.sound.add(track.key, { loop: true, volume: 0.22 * (GameState.muzikSeviyesi ?? 1) });
    sound.play();
    g._currentMusicSound = sound;
    g._currentMusicTheme = themeName;
  };

  if (scene.cache.audio.exists(track.key)) {
    startPlayback();
  } else {
    g._musicLoadingKey = track.key;
    scene.load.audio(track.key, track.file);
    scene.load.once(`filecomplete-audio-${track.key}`, startPlayback);
    scene.load.start();
  }
}

export function stopMusic(scene) {
  const g = scene.sys.game;
  if (g._currentMusicSound) g._currentMusicSound.stop();
  g._currentMusicTheme = null;
}
