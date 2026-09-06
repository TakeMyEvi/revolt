import { GameState } from '../data/state.js';

const TRACKS = {
  metropol: { key: 'metropol_muzik', file: 'sesler/metropol_muzik.ogg' },
  derinUzay: { key: 'derin_uzay_muzik', file: 'sesler/derin_uzay_muzik.ogg' },
  harabe: { key: 'harabe_muzik', file: 'sesler/harabe_muzik.ogg' }
};

const MUSIC_ENABLED = true;

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

  // Every request stamps a fresh token. If two DIFFERENT uncached themes are
  // requested back-to-back, the earlier one's load can still finish after the
  // later one's — its startPlayback must recognize it's stale and no-op
  // instead of stomping the track that's actually supposed to be playing now.
  const requestId = (g._musicRequestId = (g._musicRequestId || 0) + 1);
  const startPlayback = () => {
    if (g._musicLoadingKey === track.key) g._musicLoadingKey = null;
    if (g._musicRequestId !== requestId) return; // superseded by a newer request
    if (g._currentMusicSound) { g._currentMusicSound.stop(); g._currentMusicSound.destroy(); }
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

// Called by SettingsScene whenever the music slider changes, so an
// already-playing track's volume updates immediately instead of only taking
// effect the next time a *different* theme starts (which could be minutes
// away, or never, if the player stays in the same stage/menu).
export function refreshMusicVolume(scene) {
  const g = scene.sys.game;
  if (g._currentMusicSound) g._currentMusicSound.setVolume(0.22 * (GameState.muzikSeviyesi ?? 1));
}

// Every one-shot sound effect (hits, deaths, UI cues) should go through this
// instead of calling scene.sound.play() directly — otherwise the "sesEfekti"
// slider in Settings has literally nothing to multiply and does nothing.
export function playSfx(scene, key, opts = {}) {
  scene.sound.play(key, { ...opts, volume: (opts.volume ?? 1) * (GameState.sesSeviyesi ?? 1) });
}

export function stopMusic(scene) {
  const g = scene.sys.game;
  g._musicRequestId = (g._musicRequestId || 0) + 1; // invalidate any in-flight load
  if (g._currentMusicSound) { g._currentMusicSound.stop(); g._currentMusicSound.destroy(); g._currentMusicSound = null; }
  g._currentMusicTheme = null;
}
