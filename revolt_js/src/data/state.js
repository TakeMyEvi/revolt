// Web analog of kayit.json — persists progress to localStorage.
const KEY = 'revolt_save_v1';

function detectTouch() {
  try { return typeof navigator !== 'undefined' && navigator.maxTouchPoints > 0; } catch (e) { return false; }
}

const defaults = {
  enYuksekBolum: 1,
  selectedHero: 0,
  testModu: false,
  kahramanHasar: { 0: 0, 1: 0, 6: 0, 7: 0, 8: 0, 5: 0, 9: 0 },
  toplamOldurulen: 0,
  enUzunHayattaKalma: 0,
  sesSeviyesi: 1.0,
  muzikSeviyesi: 1.0,
  dil: 'tr',
  mobilKontrolAcik: detectTouch(), // plain on/off — defaults from device detection once, no visible "auto" mode
  imlecGizli: false,
  nisangahRenkIdx: 0,
  nisangahSekilIdx: 0,
  // Manually turned OFF mastery perks, as "heroId:tierIndex" strings — mirrors
  // the Python original's KAHRAMAN_YETENEK_KAPALI: reaching the damage
  // threshold unlocks a perk, but the player can still switch it back off.
  kapaliYetenekler: []
};

function load() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return { ...defaults };
    const parsed = JSON.parse(raw);
    return { ...defaults, ...parsed };
  } catch (e) {
    return { ...defaults };
  }
}

export const GameState = load();

// Developer-only: open the game with ?test=1 in the URL to unlock everything
// for testing. Never surfaced in any player-facing UI.
try {
  if (typeof location !== 'undefined' && new URLSearchParams(location.search).get('test') === '1') {
    GameState.testModu = true;
  }
} catch (e) { /* ignore */ }

export function saveState() {
  try {
    localStorage.setItem(KEY, JSON.stringify(GameState));
  } catch (e) { /* ignore quota/availability errors */ }
}
