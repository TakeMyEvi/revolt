// Poki SDK integration — every call is guarded so the game runs identically
// outside Poki (dev server, itch.io, etc.) where window.PokiSDK doesn't exist.
// Real usage: Poki injects the SDK script tag into index.html at hosting time;
// see https://sdk.poki.com/html5 for the exact snippet to add before deploy.

function sdk() {
  return typeof window !== 'undefined' ? window.PokiSDK : undefined;
}

// Lets UI code hide ad-gated buttons (revive, skip-level) outside Poki
// (dev server, itch.io) instead of showing a button that can never work.
export function isPokiAvailable() {
  return !!sdk();
}

export async function initPoki() {
  const s = sdk();
  if (!s) return false;
  try {
    await s.init();
    return true;
  } catch (e) {
    return false;
  }
}

export function gameLoadingFinished() {
  sdk()?.gameLoadingFinished?.();
}

// Call the instant a stage/run actually becomes playable by the player
// (first input matters more than scene-load) — required to fire on genuine
// gameplay start, not on menus.
export function gameplayStart() {
  sdk()?.gameplayStart?.();
}

// Call on any interruption: pause, menu return, level-clear panel, death screen.
export function gameplayStop() {
  sdk()?.gameplayStop?.();
}

// Natural ad break points: between stages / on game-over, never mid-combat.
export async function commercialBreak() {
  const s = sdk();
  if (!s) return;
  gameplayStop();
  try { await s.commercialBreak(); } catch (e) { /* ignore */ }
}

// Player-opted revive/bonus — only call from an explicit "watch ad" button,
// never automatically.
export async function rewardedBreak() {
  const s = sdk();
  if (!s) return false;
  gameplayStop();
  try {
    return await s.rewardedBreak();
  } catch (e) {
    return false;
  }
}
