import { GameState } from './state.js';

// Turkish is the source of truth (matches the original game's text exactly).
// Full English translation; ES/FR/DE aren't translated yet so they fall back
// to English (closer to understandable for most players than raw Turkish).
const TR = {
  geri: '< GERI', kapat: '[ KAPAT ]', ac: 'AC', kapatKisa: 'KAPAT',
  oyna: 'OYNA', hayattaKal: 'HAYATTA KAL', kahramanlar: 'KAHRAMANLAR', bolumler: 'BOLUMLER',
  gorevler: 'GOREVLER', kontroller: 'KONTROLLER', ayarlar: 'AYARLAR', cikis: 'CIKIS', krediler: 'Krediler',
  menuIpucu: '↑↓ Sec   ENTER Onayla   veya Mouse ile Tikla',
  ayarlarBaslik: 'AYARLAR', sesEfekti: 'SES EFEKTI', muzik: 'MUZIK', dil: 'DIL',
  mobilKontroller: 'MOBIL KONTROLLER', pcKontrolleri: 'PC KONTROLLERI',
  acik: 'ACIK', kapali: 'KAPALI',
  imlecSekli: 'IMLEC SEKLI', imlecRengi: 'IMLEC RENGI', imleciGizle: 'IMLECI GIZLE',
  ayarlarIpucu: 'ESC Geri (otomatik kaydedilir)',
  kahramanSec: 'KAHRAMAN SEC', yukselt: 'YUKSELT', ustalik: 'USTALIK',
  gorevlerBaslik: 'GOREVLER', genelGorevler: 'GENEL GOREVLER', karakterGorevleri: 'KARAKTER GOREVLERI',
  karakterGorevAciklama: 'Her kahramanin kendi ustalik agaci var — hasar verdikce acilir.',
  kahramanUstalik: 'KAHRAMAN USTALIKLARINI GOR',
  kontrollerBaslik: 'KONTROLLER',
  kaybettin: 'KAYBETTIN', bolumTamamlandi: 'BOLUM TAMAMLANDI!', savasiKazandin: 'SAVASI KAZANDIN!',
  tekrarOyna: 'TEKRAR OYNA', sonrakiBolum: 'SONRAKI BOLUM', anaMenuyeDon: 'ANA MENUYE DON',
  krediler_altbaslik: 'Bu oyunda kullanilan sesler icin tesekkurler:',
  kontrolSatiri1: 'A / D veya SOL/SAG OK : Hareket Et',
  kontrolSatiri2: 'W / SPACE / YUKARI OK : Zipla',
  kontrolSatiri3: 'SOL TIK (basili tut) : Saldir',
  kontrolSatiri4: 'SAG TIK : Ozel Yetenek (kahramana gore degisir)',
  kontrolSatiri5: 'E : Ikincil Yetenek (kahramana gore degisir)',
  kontrolSatiri6: 'Q : Ulti (dolunca kullanilabilir)',
  kontrolSatiri7: 'ESC : Duraklat / Ana Menuye Don',
  kontrollerIpucu: 'ESC / ENTER Geri',
  krediler_baslik: 'KREDILER',
  temaSehir: 'METROPOL', temaUzay: 'DERIN UZAY', temaHarabe: 'HARABE',
  zaferAltyazi: 'OMEGA-9 yok edildi. REVOLT zafere ulasti.',
  devamEt: 'DEVAM ET', duraklatildi: 'DURAKLATILDI'
};

const EN = {
  geri: '< BACK', kapat: '[ CLOSE ]', ac: 'ON', kapatKisa: 'OFF',
  oyna: 'PLAY', hayattaKal: 'SURVIVE', kahramanlar: 'HEROES', bolumler: 'STAGES',
  gorevler: 'MISSIONS', kontroller: 'CONTROLS', ayarlar: 'SETTINGS', cikis: 'EXIT', krediler: 'Credits',
  menuIpucu: '↑↓ Select   ENTER Confirm   or Click with Mouse',
  ayarlarBaslik: 'SETTINGS', sesEfekti: 'SOUND FX', muzik: 'MUSIC', dil: 'LANGUAGE',
  mobilKontroller: 'MOBILE CONTROLS', pcKontrolleri: 'PC CONTROLS',
  acik: 'ON', kapali: 'OFF',
  imlecSekli: 'CURSOR SHAPE', imlecRengi: 'CURSOR COLOR', imleciGizle: 'HIDE CURSOR',
  ayarlarIpucu: 'ESC Back (auto-saved)',
  kahramanSec: 'CHOOSE HERO', yukselt: 'UPGRADE', ustalik: 'MASTERY',
  gorevlerBaslik: 'MISSIONS', genelGorevler: 'GENERAL MISSIONS', karakterGorevleri: 'CHARACTER MISSIONS',
  karakterGorevAciklama: 'Each hero has its own mastery tree — unlocked by dealing damage.',
  kahramanUstalik: 'VIEW HERO MASTERIES',
  kontrollerBaslik: 'CONTROLS',
  kaybettin: 'YOU DIED', bolumTamamlandi: 'STAGE COMPLETE!', savasiKazandin: 'YOU WON THE WAR!',
  tekrarOyna: 'TRY AGAIN', sonrakiBolum: 'NEXT STAGE', anaMenuyeDon: 'BACK TO MENU',
  krediler_altbaslik: 'Thanks for the sounds used in this game:',
  kontrolSatiri1: 'A / D or LEFT/RIGHT ARROW : Move',
  kontrolSatiri2: 'W / SPACE / UP ARROW : Jump',
  kontrolSatiri3: 'LEFT CLICK (hold) : Attack',
  kontrolSatiri4: 'RIGHT CLICK : Special Ability (varies by hero)',
  kontrolSatiri5: 'E : Secondary Ability (varies by hero)',
  kontrolSatiri6: 'Q : Ultimate (usable once full)',
  kontrolSatiri7: 'ESC : Pause / Back to Menu',
  kontrollerIpucu: 'ESC / ENTER Back',
  krediler_baslik: 'CREDITS',
  temaSehir: 'CITY', temaUzay: 'DEEP SPACE', temaHarabe: 'RUINS',
  zaferAltyazi: 'OMEGA-9 has been destroyed. REVOLT has won.',
  devamEt: 'RESUME', duraklatildi: 'PAUSED'
};

const TABLES = { tr: TR, en: EN, es: EN, fr: EN, de: EN };

export function t(key) {
  const table = TABLES[GameState.dil] || TR;
  return table[key] || TR[key] || key;
}
