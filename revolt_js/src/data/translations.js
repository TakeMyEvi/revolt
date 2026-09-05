import { GameState } from './state.js';

// Turkish is the source of truth (matches the original game's text exactly).
// TR/EN/ES/FR/DE keys shared with the Python original's own CEVIRI table were
// carried over from there; the rest (mastery panel, missions, pause overlay,
// stage themes, victory subtitle — all new in this port) were translated to
// match that table's tone and its no-diacritics convention.
const TR = {
  geri: '< GERI', kapat: '[ KAPAT ]', ac: 'AC', kapatKisa: 'KAPAT',
  oyna: 'OYNA', hayattaKal: 'HAYATTA KAL', kahramanlar: 'KAHRAMANLAR', bolumler: 'BOLUMLER',
  gorevler: 'GOREVLER', kontroller: 'KONTROLLER', ayarlar: 'AYARLAR', cikis: 'CIKIS', krediler: 'Krediler',
  menuIpucu: '↑↓ Sec   ENTER Onayla   veya Mouse ile Tikla',
  ayarlarBaslik: 'AYARLAR', sesEfekti: 'SES EFEKTI', muzik: 'MUZIK', dil: 'DIL',
  mobilKontroller: 'MOBIL KONTROLLER', pcKontrolleri: 'PC KONTROLLERI',
  acik: 'ACIK', kapali: 'KAPALI',
  imlecSekli: 'IMLEC SEKLI', imlecRengi: 'IMLEC RENGI', imleciGizle: 'IMLECI GIZLE',
  sekilArti: 'ARTI', sekilDaire: 'DAIRE', sekilNokta: 'NOKTA', sekilKare: 'KARE',
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
  zaferAltyazi: "YZ robotlari tek tek kontrol edebildi, ama 7'sinin birlikte\nbilinclenmis halini hic taklit edemedi — onu yenen buydu.",
  devamEt: 'DEVAM ET', duraklatildi: 'DURAKLATILDI',

  // HUD (savas ekrani ustu) — sik gorulur, her savasta surekli ekranda.
  hudBolum: 'BOLUM', hudDusman: 'DUSMAN', hudSkor: 'SKOR', hudKitap: 'KITAP', hudRuh: 'RUH',
  hint0: 'KILIC - AEGIS', hint1: 'SOL:PENCE  SAG:HAMLE - RAPTOR', hint6: 'SOL:BUYU  SAG:ISIN - HEX',
  hint7: 'SOL:RUH CISMI  SAG:HAYALET - WRAITH', hint8: 'SOL:ALAN VURUSU  SAG:ATIS - REAPER',
  hint5: 'SOL:ATES  SAG:KANCA  E:PATLAT - OVERDRIVE', hint9: 'SOL:ITIS  SAG:FIRLAT  E:GIZLEN - RONIN',
  eGuclendir: 'E:GUCLENDIR', sagHayaletEIyilestir: 'SAG:HAYALET E:IYILES', eKacis: 'E:KACIS',
  eIyilestir: 'E:IYILESTIR', ePatlat: 'E:PATLAT', eGizlen: 'E:GIZLEN', eKalkan: 'E:KALKAN',
  qIskeletCagir: 'Q:ISKELET CAGIR', qUltiLabel: 'Q:ULTI',

  // Final boss nameplate.
  kalkanliLabel: 'KALKANLI', zayifVurLabel: 'ZAYIF - VUR!', fazLabel: 'FAZ',

  // Survival mode.
  seviyeAtladinKartSec: 'SEVIYE ATLADIN! BIR KART SEC', seviyeLabel: 'SEVIYE',
  oldurulenLabel: 'OLDURULEN', hayattaKaldinLabel: 'HAYATTA KALDIN',

  // Hero select misc.
  bolumHintPrefix: 'Bolum', ustalikYokMetni: 'Bu kahraman icin ustalik yukseltmesi yok.',

  // Missions screen — stat-effect suffixes.
  statCan: 'CAN', statHiz: 'HIZ', statRegen: 'REGEN',

  // Mobile touch control button.
  mobileSag: 'SAG',

  // General missions (GENEL_GOREVLER).
  gorevIlkZaferIsim: 'ILK ZAFER', gorevIlkZaferAciklama: 'Bir bolumu bitir',
  gorevAvciIsim: 'AVCI', gorevAvciAciklama: 'Toplam 150 dusman oldur',
  gorevHayattaKalanIsim: 'HAYATTA KALAN', gorevHayattaKalanAciklama: "Survivor'da tek seferde 90 saniye hayatta kal",
  gorevKahramanIsim: 'KAHRAMAN', gorevKahramanAciklama: "Bolum 15'e ulas",

  // Survival level-up card pool (YUKSELTME_HAVUZU).
  yukseltmeHasarIsim: 'GUC ARTISI', yukseltmeHasarAciklama: '+%20 Hasar',
  yukseltmeHizIsim: 'HIZ ARTISI', yukseltmeHizAciklama: '+%15 Hareket Hizi',
  yukseltmeCanIsim: 'DAYANIKLILIK', yukseltmeCanAciklama: '+25 Can',
  yukseltmeSaldiriIsim: 'SALDIRGANLIK', yukseltmeSaldiriAciklama: '-%15 Saldiri Bekleme',
  yukseltmeRegenIsim: 'YENILENME', yukseltmeRegenAciklama: 'Pasif Can Yenileme',

  // Hero mastery perks (KAHRAMAN_YUKSELTMELERI), keyed perk{heroId}_{tier}.
  perk0_0Ad: 'KESKIN MENZIL', perk0_0Desc: 'Kilic sol tik (savurma) menzili +%35 artar.',
  perk0_1Ad: 'KORUYUCU AZIM', perk0_1Desc: '5 saniye hasar almazsan az canli bir kalkan kazanirsin.',
  perk0_2Ad: 'SEKEN KILIC', perk0_2Desc: 'Firlattigin kilic 5 dusmana kadar seker, sonra geri doner.',
  perk1_0Ad: 'ZEHIR BULUTU', perk1_0Desc: "E'ye basinca etrafindaki dusmanlara aninda zehir bulasir.",
  perk1_1Ad: 'KAN KOKUSU', perk1_1Desc: 'Her dash sonrasi birkac saniye pence/dash hasari +%30 artar.',
  perk1_2Ad: 'SINIRSIZ HAMLE', perk1_2Desc: 'Hamle (dash) bekleme suresi kalkar.',
  perk6_0Ad: 'BUYULU OZDIRENC', perk6_0Desc: "+50 Can (100'e cikar).",
  perk6_1Ad: 'USTA KITAPLIK', perk6_1Desc: 'Azami kitap sayisi artar, isin hasari da buna gore artar.',
  perk6_2Ad: 'GERCEKLIK KIRIMI', perk6_2Desc: 'Ulti artik ekrandaki her dusmani aninda oldurur.',
  perk7_0Ad: 'HAYALET AVCISI', perk7_0Desc: 'Hayaletken +%30 hasar verirsin.',
  perk7_1Ad: 'RUH BAGI', perk7_1Desc: 'Kazandigin her ruh, ulti barini doldururken aninda can da verir.',
  perk7_2Ad: 'SINIRSIZ HAYALET', perk7_2Desc: 'Hayalet suresi uzar, ruh maliyeti kalkar.',
  perk8_0Ad: 'RUH ORDUSU', perk8_0Desc: "E'ye basinca 3 ek delirmis iskelet cagirir.",
  perk8_1Ad: 'CANSIZ MIRAS', perk8_1Desc: 'Oldurdugun bir dusmanin yerinde bir iskelet belirir.',
  perk8_2Ad: 'OKCU LEJYONU', perk8_2Desc: 'Ultiden cikan tum iskeletler uzaktan vuran okcu olur.',
  perk5_0Ad: 'HIRSIZ SARJ', perk5_0Desc: 'Her kanca attiginda 10 can iyilesirsin.',
  perk5_1Ad: 'CEKIRDEK KALKANI', perk5_1Desc: 'Ulti aktifken 1 canin altina dusmezsin.',
  perk5_2Ad: 'CIFTE NAMLU', perk5_2Desc: 'Tabancanin ates hizi %100 artar.',
  perk9_0Ad: 'UZUN MIZRAK', perk9_0Desc: 'Mizragin (itis+firlatma) menzili %50 artar.',
  perk9_1Ad: 'GOLGE PENCESI', perk9_1Desc: 'Golge modundayken vurdugun dusmanlar 5 saniyeligine donar.',
  perk9_2Ad: 'FIRTINA USTASI', perk9_2Desc: 'Ultinin menzili %100 artar ve aktive olunca 50 can doldurur.',
  perk5_3Ad: 'KANCA SALINIMI', perk5_3Desc: 'Kanca sallanarak hareket etmeni saglar (acilana kadar hedefe duz ucar).',

  reklamlaCanlan: 'REKLAMLA CANLAN', reklamlaBolumGec: '2 REKLAMLA BOLUMU GEC'
};

const EN = {
  geri: '< BACK', kapat: '[ CLOSE ]', ac: 'ON', kapatKisa: 'OFF',
  oyna: 'PLAY', hayattaKal: 'SURVIVAL', kahramanlar: 'HEROES', bolumler: 'LEVELS',
  gorevler: 'MISSIONS', kontroller: 'CONTROLS', ayarlar: 'SETTINGS', cikis: 'QUIT', krediler: 'Credits',
  menuIpucu: '↑↓ Select   ENTER Confirm   or Click with Mouse',
  ayarlarBaslik: 'SETTINGS', sesEfekti: 'SOUND EFFECTS', muzik: 'MUSIC', dil: 'LANGUAGE',
  mobilKontroller: 'MOBILE CONTROLS', pcKontrolleri: 'PC CONTROLS',
  acik: 'ON', kapali: 'OFF',
  imlecSekli: 'CROSSHAIR SHAPE', imlecRengi: 'CROSSHAIR COLOR', imleciGizle: 'HIDE CURSOR',
  sekilArti: 'CROSS', sekilDaire: 'CIRCLE', sekilNokta: 'DOT', sekilKare: 'SQUARE',
  ayarlarIpucu: 'ESC Back (auto-saved)',
  kahramanSec: 'CHOOSE HERO', yukselt: 'UPGRADE', ustalik: 'MASTERY',
  gorevlerBaslik: 'MISSIONS', genelGorevler: 'GENERAL MISSIONS', karakterGorevleri: 'CHARACTER MISSIONS',
  karakterGorevAciklama: 'Each hero has its own mastery tree — unlocked by dealing damage.',
  kahramanUstalik: 'VIEW HERO MASTERIES',
  kontrollerBaslik: 'CONTROLS',
  kaybettin: 'GAME OVER', bolumTamamlandi: 'LEVEL COMPLETE!', savasiKazandin: 'YOU WON THE WAR!',
  tekrarOyna: 'PLAY AGAIN', sonrakiBolum: 'NEXT LEVEL', anaMenuyeDon: 'RETURN TO MENU',
  krediler_altbaslik: "Thanks to the artists behind this game's sounds:",
  kontrolSatiri1: 'LEFT / RIGHT ARROW or A / D : Move',
  kontrolSatiri2: 'UP ARROW / SPACE / W : Jump',
  kontrolSatiri3: 'LEFT CLICK (hold) : Attack',
  kontrolSatiri4: 'RIGHT CLICK : Special Ability (varies by hero)',
  kontrolSatiri5: 'E : Secondary Ability (varies by hero)',
  kontrolSatiri6: 'Q : Ultimate (usable when charged)',
  kontrolSatiri7: 'ESC : Pause / Return to Main Menu',
  kontrollerIpucu: 'ESC / ENTER Back',
  krediler_baslik: 'CREDITS',
  temaSehir: 'CITY', temaUzay: 'DEEP SPACE', temaHarabe: 'RUINS',
  zaferAltyazi: 'OMEGA-9 could control robots one by one, but never replicate\nseven minds awakened together — that unity is what beat it.',
  devamEt: 'RESUME', duraklatildi: 'PAUSED',

  hudBolum: 'LEVEL', hudDusman: 'ENEMIES', hudSkor: 'SCORE', hudKitap: 'BOOKS', hudRuh: 'SOUL',
  hint0: 'SWORD - AEGIS', hint1: 'LEFT:CLAW  RIGHT:DASH - RAPTOR', hint6: 'LEFT:SPELL  RIGHT:BEAM - HEX',
  hint7: 'LEFT:SOUL ORB  RIGHT:GHOST - WRAITH', hint8: 'LEFT:AREA STRIKE  RIGHT:SHOT - REAPER',
  hint5: 'LEFT:FIRE  RIGHT:HOOK  E:BLAST - OVERDRIVE', hint9: 'LEFT:THRUST  RIGHT:THROW  E:HIDE - RONIN',
  eGuclendir: 'E:EMPOWER', sagHayaletEIyilestir: 'RIGHT:GHOST E:HEAL', eKacis: 'E:ESCAPE',
  eIyilestir: 'E:HEAL', ePatlat: 'E:BLAST', eGizlen: 'E:HIDE', eKalkan: 'E:SHIELD',
  qIskeletCagir: 'Q:SUMMON SKELETON', qUltiLabel: 'Q:ULTIMATE',

  kalkanliLabel: 'SHIELDED', zayifVurLabel: 'WEAK - ATTACK!', fazLabel: 'PHASE',

  seviyeAtladinKartSec: 'LEVEL UP! CHOOSE A CARD', seviyeLabel: 'LEVEL',
  oldurulenLabel: 'KILLED', hayattaKaldinLabel: 'YOU SURVIVED',

  bolumHintPrefix: 'Level', ustalikYokMetni: 'No mastery upgrades for this hero.',

  statCan: 'HP', statHiz: 'SPEED', statRegen: 'REGEN',

  mobileSag: 'SPEC',

  gorevIlkZaferIsim: 'FIRST VICTORY', gorevIlkZaferAciklama: 'Finish a level',
  gorevAvciIsim: 'HUNTER', gorevAvciAciklama: 'Kill a total of 150 enemies',
  gorevHayattaKalanIsim: 'SURVIVOR', gorevHayattaKalanAciklama: 'Survive 90 seconds in a single Survival run',
  gorevKahramanIsim: 'HERO', gorevKahramanAciklama: 'Reach level 15',

  yukseltmeHasarIsim: 'POWER BOOST', yukseltmeHasarAciklama: '+20% Damage',
  yukseltmeHizIsim: 'SPEED BOOST', yukseltmeHizAciklama: '+15% Movement Speed',
  yukseltmeCanIsim: 'ENDURANCE', yukseltmeCanAciklama: '+25 Health',
  yukseltmeSaldiriIsim: 'AGGRESSION', yukseltmeSaldiriAciklama: '-15% Attack Cooldown',
  yukseltmeRegenIsim: 'REGENERATION', yukseltmeRegenAciklama: 'Passive Health Regen',

  perk0_0Ad: 'SHARP REACH', perk0_0Desc: 'Sword left-click (swing) range increases by +35%.',
  perk0_1Ad: 'PROTECTIVE RESOLVE', perk0_1Desc: 'Go 5 seconds without taking damage and you gain a small shield.',
  perk0_2Ad: 'RICOCHET BLADE', perk0_2Desc: 'Your thrown sword bounces to up to 5 enemies, then returns.',
  perk1_0Ad: 'POISON CLOUD', perk1_0Desc: 'Pressing E instantly poisons nearby enemies.',
  perk1_1Ad: 'SCENT OF BLOOD', perk1_1Desc: 'After every dash, claw/dash damage increases +30% for a few seconds.',
  perk1_2Ad: 'UNLIMITED DASH', perk1_2Desc: 'Dash cooldown is removed.',
  perk6_0Ad: 'MAGIC RESILIENCE', perk6_0Desc: '+50 Health (up to 100).',
  perk6_1Ad: 'MASTER LIBRARY', perk6_1Desc: 'Max book count increases, and beam damage scales with it.',
  perk6_2Ad: 'REALITY BREAK', perk6_2Desc: 'Ultimate now instantly kills every enemy on screen.',
  perk7_0Ad: 'GHOST HUNTER', perk7_0Desc: 'You deal +30% damage while in ghost form.',
  perk7_1Ad: 'SOUL BOND', perk7_1Desc: 'Every soul you gain fills the ulti bar and instantly heals you too.',
  perk7_2Ad: 'UNLIMITED GHOST', perk7_2Desc: 'Ghost duration is longer, soul cost is removed.',
  perk8_0Ad: 'SOUL ARMY', perk8_0Desc: 'Pressing E summons 3 extra frenzied skeletons.',
  perk8_1Ad: 'LIFELESS LEGACY', perk8_1Desc: 'A skeleton rises where an enemy you killed once stood.',
  perk8_2Ad: 'ARCHER LEGION', perk8_2Desc: 'All skeletons from the ultimate become ranged archers.',
  perk5_0Ad: "THIEF'S CHARGE", perk5_0Desc: 'You heal 10 health every time you fire the hook.',
  perk5_1Ad: 'CORE SHIELD', perk5_1Desc: "While the ultimate is active, your health can't drop below 1.",
  perk5_2Ad: 'DOUBLE BARREL', perk5_2Desc: "Your gun's fire rate increases by 100%.",
  perk9_0Ad: 'LONG SPEAR', perk9_0Desc: "Your spear's range (thrust+throw) increases by 50%.",
  perk9_1Ad: 'SHADOW GRASP', perk9_1Desc: 'Enemies you hit while in shadow mode freeze for 5 seconds.',
  perk9_2Ad: 'STORM MASTER', perk9_2Desc: 'Ultimate range increases by 100% and heals 50 health on activation.',
  perk5_3Ad: 'HOOK SWING', perk5_3Desc: 'Lets you swing on the hook to move (flies straight to the target until unlocked).',

  reklamlaCanlan: 'REVIVE WITH AD', reklamlaBolumGec: 'SKIP WITH 2 ADS'
};

const ES = {
  geri: '< ATRAS', kapat: '[ CERRAR ]', ac: 'ACT', kapatKisa: 'DES',
  oyna: 'JUGAR', hayattaKal: 'SUPERVIVENCIA', kahramanlar: 'HEROES', bolumler: 'NIVELES',
  gorevler: 'MISIONES', kontroller: 'CONTROLES', ayarlar: 'AJUSTES', cikis: 'SALIR', krediler: 'Creditos',
  menuIpucu: '↑↓ Elegir   ENTER Confirmar   o Clic con el Raton',
  ayarlarBaslik: 'AJUSTES', sesEfekti: 'EFECTOS DE SONIDO', muzik: 'MUSICA', dil: 'IDIOMA',
  mobilKontroller: 'CONTROLES MOVILES', pcKontrolleri: 'CONTROLES DE PC',
  acik: 'ACTIVADO', kapali: 'DESACTIVADO',
  imlecSekli: 'FORMA DE LA MIRA', imlecRengi: 'COLOR DE LA MIRA', imleciGizle: 'OCULTAR CURSOR',
  sekilArti: 'CRUZ', sekilDaire: 'CIRCULO', sekilNokta: 'PUNTO', sekilKare: 'CUADRADO',
  ayarlarIpucu: 'ESC Atras (guardado automatico)',
  kahramanSec: 'ELEGIR HEROE', yukselt: 'MEJORAR', ustalik: 'MAESTRIA',
  gorevlerBaslik: 'MISIONES', genelGorevler: 'MISIONES GENERALES', karakterGorevleri: 'MISIONES DE PERSONAJE',
  karakterGorevAciklama: 'Cada heroe tiene su propio arbol de maestria — se desbloquea al causar dano.',
  kahramanUstalik: 'VER MAESTRIAS DE HEROES',
  kontrollerBaslik: 'CONTROLES',
  kaybettin: 'GAME OVER', bolumTamamlandi: '¡NIVEL COMPLETADO!', savasiKazandin: '¡GANASTE LA GUERRA!',
  tekrarOyna: 'JUGAR DE NUEVO', sonrakiBolum: 'SIGUIENTE NIVEL', anaMenuyeDon: 'VOLVER AL MENU',
  krediler_altbaslik: 'Gracias a los artistas de los sonidos de este juego:',
  kontrolSatiri1: 'FLECHA IZQ / DER o A / D : Moverse',
  kontrolSatiri2: 'FLECHA ARRIBA / ESPACIO / W : Saltar',
  kontrolSatiri3: 'CLIC IZQUIERDO (mantener) : Atacar',
  kontrolSatiri4: 'CLIC DERECHO : Habilidad Especial (segun heroe)',
  kontrolSatiri5: 'E : Habilidad Secundaria (segun heroe)',
  kontrolSatiri6: 'Q : Definitiva (usable cuando esta cargada)',
  kontrolSatiri7: 'ESC : Pausar / Volver al Menu',
  kontrollerIpucu: 'ESC / ENTER Atras',
  krediler_baslik: 'CREDITOS',
  temaSehir: 'METROPOLI', temaUzay: 'ESPACIO PROFUNDO', temaHarabe: 'RUINAS',
  zaferAltyazi: 'OMEGA-9 podia controlar robots uno a uno, pero nunca replico\nsiete mentes despiertas juntas — esa union fue lo que lo vencio.',
  devamEt: 'REANUDAR', duraklatildi: 'PAUSADO',

  hudBolum: 'NIVEL', hudDusman: 'ENEMIGOS', hudSkor: 'PUNTOS', hudKitap: 'LIBROS', hudRuh: 'ALMA',
  hint0: 'ESPADA - AEGIS', hint1: 'IZQ:GARRA  DER:EMBESTIDA - RAPTOR', hint6: 'IZQ:HECHIZO  DER:RAYO - HEX',
  hint7: "IZQ:ORBE DE ALMA  DER:FANTASMA - WRAITH", hint8: 'IZQ:GOLPE DE AREA  DER:DISPARO - REAPER',
  hint5: 'IZQ:DISPARAR  DER:GANCHO  E:EXPLOTAR - OVERDRIVE', hint9: 'IZQ:EMPUJE  DER:LANZAR  E:OCULTAR - RONIN',
  eGuclendir: 'E:POTENCIAR', sagHayaletEIyilestir: 'DER:FANTASMA E:CURAR', eKacis: 'E:ESCAPE',
  eIyilestir: 'E:CURAR', ePatlat: 'E:EXPLOTAR', eGizlen: 'E:OCULTAR', eKalkan: 'E:ESCUDO',
  qIskeletCagir: 'Q:INVOCAR ESQUELETO', qUltiLabel: 'Q:DEFINITIVA',

  kalkanliLabel: 'ESCUDADO', zayifVurLabel: '¡DEBIL - ATACA!', fazLabel: 'FASE',

  seviyeAtladinKartSec: '¡SUBISTE DE NIVEL! ELIGE UNA CARTA', seviyeLabel: 'NIVEL',
  oldurulenLabel: 'ELIMINADOS', hayattaKaldinLabel: 'SOBREVIVISTE',

  bolumHintPrefix: 'Nivel', ustalikYokMetni: 'No hay mejoras de maestria para este heroe.',

  statCan: 'VIDA', statHiz: 'VELOCIDAD', statRegen: 'REGEN',

  mobileSag: 'ESP',

  gorevIlkZaferIsim: 'PRIMERA VICTORIA', gorevIlkZaferAciklama: 'Termina un nivel',
  gorevAvciIsim: 'CAZADOR', gorevAvciAciklama: 'Elimina un total de 150 enemigos',
  gorevHayattaKalanIsim: 'SUPERVIVIENTE', gorevHayattaKalanAciklama: 'Sobrevive 90 segundos en una sola partida de Supervivencia',
  gorevKahramanIsim: 'HEROE', gorevKahramanAciklama: 'Alcanza el nivel 15',

  yukseltmeHasarIsim: 'AUMENTO DE PODER', yukseltmeHasarAciklama: '+20% Dano',
  yukseltmeHizIsim: 'AUMENTO DE VELOCIDAD', yukseltmeHizAciklama: '+15% Velocidad de Movimiento',
  yukseltmeCanIsim: 'RESISTENCIA', yukseltmeCanAciklama: '+25 Vida',
  yukseltmeSaldiriIsim: 'AGRESIVIDAD', yukseltmeSaldiriAciklama: '-15% Tiempo de Espera de Ataque',
  yukseltmeRegenIsim: 'REGENERACION', yukseltmeRegenAciklama: 'Regeneracion Pasiva de Vida',

  perk0_0Ad: 'ALCANCE AFILADO', perk0_0Desc: 'El alcance del espadazo (clic izq.) aumenta +35%.',
  perk0_1Ad: 'RESOLUCION PROTECTORA', perk0_1Desc: 'Si pasas 5 segundos sin recibir dano, ganas un pequeno escudo.',
  perk0_2Ad: 'ESPADA REBOTANTE', perk0_2Desc: 'Tu espada lanzada rebota hasta 5 enemigos y luego regresa.',
  perk1_0Ad: 'NUBE VENENOSA', perk1_0Desc: 'Al pulsar E, envenenas al instante a los enemigos cercanos.',
  perk1_1Ad: 'OLOR A SANGRE', perk1_1Desc: 'Tras cada embestida, el dano de garra/embestida aumenta +30% por unos segundos.',
  perk1_2Ad: 'EMBESTIDA ILIMITADA', perk1_2Desc: 'El tiempo de espera de la embestida desaparece.',
  perk6_0Ad: 'RESILIENCIA MAGICA', perk6_0Desc: '+50 de Vida (hasta 100).',
  perk6_1Ad: 'BIBLIOTECA MAESTRA', perk6_1Desc: 'Aumenta el numero maximo de libros, y el dano del rayo escala con ello.',
  perk6_2Ad: 'FRACTURA DE REALIDAD', perk6_2Desc: 'La definitiva ahora mata al instante a todos los enemigos en pantalla.',
  perk7_0Ad: 'CAZADOR FANTASMA', perk7_0Desc: 'Infliges +30% de dano mientras estas en forma fantasma.',
  perk7_1Ad: 'VINCULO DE ALMA', perk7_1Desc: 'Cada alma que obtienes llena la barra de definitiva y tambien te cura al instante.',
  perk7_2Ad: 'FANTASMA ILIMITADO', perk7_2Desc: 'La duracion fantasma es mas larga, el costo de alma desaparece.',
  perk8_0Ad: 'EJERCITO DE ALMAS', perk8_0Desc: 'Al pulsar E, invocas 3 esqueletos enfurecidos adicionales.',
  perk8_1Ad: 'LEGADO SIN VIDA', perk8_1Desc: 'Un esqueleto aparece donde cayo un enemigo que mataste.',
  perk8_2Ad: 'LEGION DE ARQUEROS', perk8_2Desc: 'Todos los esqueletos de la definitiva se convierten en arqueros a distancia.',
  perk5_0Ad: 'CARGA LADRONA', perk5_0Desc: 'Recuperas 10 de vida cada vez que lanzas el gancho.',
  perk5_1Ad: 'ESCUDO NUCLEO', perk5_1Desc: 'Mientras la definitiva esta activa, tu vida no puede bajar de 1.',
  perk5_2Ad: 'DOBLE CANON', perk5_2Desc: 'La cadencia de disparo de tu arma aumenta 100%.',
  perk9_0Ad: 'LANZA LARGA', perk9_0Desc: 'El alcance de tu lanza (empuje+lanzamiento) aumenta 50%.',
  perk9_1Ad: 'GARRA DE SOMBRA', perk9_1Desc: 'Los enemigos golpeados en modo sombra se congelan durante 5 segundos.',
  perk9_2Ad: 'MAESTRO DE TORMENTA', perk9_2Desc: 'El alcance de la definitiva aumenta 100% y cura 50 de vida al activarse.',
  perk5_3Ad: 'BALANCEO DE GANCHO', perk5_3Desc: 'Te permite balancearte con el gancho para moverte (vuela recto al objetivo hasta desbloquearse).',

  reklamlaCanlan: 'REVIVIR CON ANUNCIO', reklamlaBolumGec: 'SALTAR CON 2 ANUNCIOS'
};

const FR = {
  geri: '< RETOUR', kapat: '[ FERMER ]', ac: 'ACT', kapatKisa: 'DES',
  oyna: 'JOUER', hayattaKal: 'SURVIE', kahramanlar: 'HEROS', bolumler: 'NIVEAUX',
  gorevler: 'MISSIONS', kontroller: 'COMMANDES', ayarlar: 'PARAMETRES', cikis: 'QUITTER', krediler: 'Credits',
  menuIpucu: '↑↓ Choisir   ENTREE Valider   ou Clic Souris',
  ayarlarBaslik: 'PARAMETRES', sesEfekti: 'EFFETS SONORES', muzik: 'MUSIQUE', dil: 'LANGUE',
  mobilKontroller: 'COMMANDES MOBILES', pcKontrolleri: 'COMMANDES PC',
  acik: 'ACTIVE', kapali: 'DESACTIVE',
  imlecSekli: 'FORME DU VISEUR', imlecRengi: 'COULEUR DU VISEUR', imleciGizle: 'MASQUER LE CURSEUR',
  sekilArti: 'CROIX', sekilDaire: 'CERCLE', sekilNokta: 'POINT', sekilKare: 'CARRE',
  ayarlarIpucu: 'ECHAP Retour (sauvegarde automatique)',
  kahramanSec: 'CHOISIR UN HEROS', yukselt: 'AMELIORER', ustalik: 'MAITRISE',
  gorevlerBaslik: 'MISSIONS', genelGorevler: 'MISSIONS GENERALES', karakterGorevleri: 'MISSIONS DE PERSONNAGE',
  karakterGorevAciklama: 'Chaque heros a son propre arbre de maitrise — debloque en infligeant des degats.',
  kahramanUstalik: 'VOIR LES MAITRISES DES HEROS',
  kontrollerBaslik: 'COMMANDES',
  kaybettin: 'GAME OVER', bolumTamamlandi: 'NIVEAU TERMINE !', savasiKazandin: 'VOUS AVEZ GAGNE LA GUERRE !',
  tekrarOyna: 'REJOUER', sonrakiBolum: 'NIVEAU SUIVANT', anaMenuyeDon: 'RETOUR AU MENU',
  krediler_altbaslik: 'Merci aux artistes des sons de ce jeu :',
  kontrolSatiri1: 'FLECHE GAUCHE / DROITE ou A / D : Se deplacer',
  kontrolSatiri2: 'FLECHE HAUT / ESPACE / W : Sauter',
  kontrolSatiri3: 'CLIC GAUCHE (maintenir) : Attaquer',
  kontrolSatiri4: 'CLIC DROIT : Capacite Speciale (selon le heros)',
  kontrolSatiri5: 'E : Capacite Secondaire (selon le heros)',
  kontrolSatiri6: 'Q : Ultime (utilisable une fois chargee)',
  kontrolSatiri7: 'ECHAP : Pause / Retour au Menu',
  kontrollerIpucu: 'ECHAP / ENTREE Retour',
  krediler_baslik: 'CREDITS',
  temaSehir: 'METROPOLE', temaUzay: 'ESPACE PROFOND', temaHarabe: 'RUINES',
  zaferAltyazi: "OMEGA-9 pouvait controler les robots un par un, mais n'a jamais reproduit\nsept esprits eveilles ensemble — cette union l'a vaincu.",
  devamEt: 'REPRENDRE', duraklatildi: 'PAUSE',

  hudBolum: 'NIVEAU', hudDusman: 'ENNEMIS', hudSkor: 'SCORE', hudKitap: 'LIVRES', hudRuh: 'AME',
  hint0: 'EPEE - AEGIS', hint1: 'GAUCHE:GRIFFE  DROITE:RUEE - RAPTOR', hint6: 'GAUCHE:SORT  DROITE:RAYON - HEX',
  hint7: "GAUCHE:ORBE D'AME  DROITE:FANTOME - WRAITH", hint8: 'GAUCHE:FRAPPE DE ZONE  DROITE:TIR - REAPER',
  hint5: 'GAUCHE:TIRER  DROITE:GRAPPIN  E:EXPLOSER - OVERDRIVE', hint9: 'GAUCHE:POUSSEE  DROITE:LANCER  E:CACHER - RONIN',
  eGuclendir: 'E:RENFORCER', sagHayaletEIyilestir: 'DROITE:FANTOME E:SOIN', eKacis: 'E:FUITE',
  eIyilestir: 'E:SOIGNER', ePatlat: 'E:EXPLOSER', eGizlen: 'E:CACHER', eKalkan: 'E:BOUCLIER',
  qIskeletCagir: 'Q:INVOQUER SQUELETTE', qUltiLabel: 'Q:ULTIME',

  kalkanliLabel: 'BOUCLIER ACTIF', zayifVurLabel: 'FAIBLE - ATTAQUE !', fazLabel: 'PHASE',

  seviyeAtladinKartSec: 'NIVEAU SUPERIEUR ! CHOISIS UNE CARTE', seviyeLabel: 'NIVEAU',
  oldurulenLabel: 'ELIMINES', hayattaKaldinLabel: 'TU AS SURVECU',

  bolumHintPrefix: 'Niveau', ustalikYokMetni: "Pas d'amelioration de maitrise pour ce heros.",

  statCan: 'PV', statHiz: 'VITESSE', statRegen: 'REGEN',

  mobileSag: 'SPE',

  gorevIlkZaferIsim: 'PREMIERE VICTOIRE', gorevIlkZaferAciklama: 'Termine un niveau',
  gorevAvciIsim: 'CHASSEUR', gorevAvciAciklama: 'Elimine un total de 150 ennemis',
  gorevHayattaKalanIsim: 'SURVIVANT', gorevHayattaKalanAciklama: 'Survis 90 secondes en une seule partie de Survie',
  gorevKahramanIsim: 'HEROS', gorevKahramanAciklama: 'Atteins le niveau 15',

  yukseltmeHasarIsim: 'AUGMENTATION DE PUISSANCE', yukseltmeHasarAciklama: '+20% Degats',
  yukseltmeHizIsim: 'AUGMENTATION DE VITESSE', yukseltmeHizAciklama: '+15% Vitesse de Deplacement',
  yukseltmeCanIsim: 'ENDURANCE', yukseltmeCanAciklama: '+25 PV',
  yukseltmeSaldiriIsim: 'AGRESSIVITE', yukseltmeSaldiriAciklama: "-15% Temps de Recharge d'Attaque",
  yukseltmeRegenIsim: 'REGENERATION', yukseltmeRegenAciklama: 'Regeneration Passive de Vie',

  perk0_0Ad: 'PORTEE AFFUTEE', perk0_0Desc: "La portee du coup d'epee (clic gauche) augmente de +35%.",
  perk0_1Ad: 'RESOLUTION PROTECTRICE', perk0_1Desc: 'Si tu restes 5 secondes sans subir de degats, tu gagnes un petit bouclier.',
  perk0_2Ad: 'EPEE RICOCHET', perk0_2Desc: "Ton epee lancee ricoche sur jusqu'a 5 ennemis, puis revient.",
  perk1_0Ad: 'NUAGE TOXIQUE', perk1_0Desc: 'Appuyer sur E empoisonne instantanement les ennemis proches.',
  perk1_1Ad: 'ODEUR DE SANG', perk1_1Desc: 'Apres chaque ruee, les degats de griffe/ruee augmentent de +30% pendant quelques secondes.',
  perk1_2Ad: 'RUEE ILLIMITEE', perk1_2Desc: 'Le temps de recharge de la ruee disparait.',
  perk6_0Ad: 'RESILIENCE MAGIQUE', perk6_0Desc: "+50 PV (jusqu'a 100).",
  perk6_1Ad: 'BIBLIOTHEQUE MAITRESSE', perk6_1Desc: 'Le nombre maximum de livres augmente, et les degats du rayon suivent.',
  perk6_2Ad: 'FRACTURE DE REALITE', perk6_2Desc: "L'ultime tue desormais instantanement tous les ennemis a l'ecran.",
  perk7_0Ad: 'CHASSEUR FANTOME', perk7_0Desc: 'Tu infliges +30% de degats sous forme fantomatique.',
  perk7_1Ad: "LIEN D'AME", perk7_1Desc: "Chaque ame gagnee remplit la barre d'ultime et te soigne aussi instantanement.",
  perk7_2Ad: 'FANTOME ILLIMITE', perk7_2Desc: 'La duree fantome est plus longue, le cout en ames disparait.',
  perk8_0Ad: "ARMEE D'AMES", perk8_0Desc: 'Appuyer sur E invoque 3 squelettes enrages supplementaires.',
  perk8_1Ad: 'HERITAGE SANS VIE', perk8_1Desc: "Un squelette apparait a l'endroit ou un ennemi que tu as tue est tombe.",
  perk8_2Ad: "LEGION D'ARCHERS", perk8_2Desc: "Tous les squelettes de l'ultime deviennent des archers a distance.",
  perk5_0Ad: 'CHARGE VOLEUSE', perk5_0Desc: 'Tu recuperes 10 PV a chaque tir du grappin.',
  perk5_1Ad: 'BOUCLIER NOYAU', perk5_1Desc: "Tant que l'ultime est active, tes PV ne peuvent pas descendre sous 1.",
  perk5_2Ad: 'DOUBLE CANON', perk5_2Desc: 'La cadence de tir de ton arme augmente de 100%.',
  perk9_0Ad: 'LANCE LONGUE', perk9_0Desc: 'La portee de ta lance (poussee+lancer) augmente de 50%.',
  perk9_1Ad: "GRIFFE D'OMBRE", perk9_1Desc: 'Les ennemis touches en mode ombre se figent pendant 5 secondes.',
  perk9_2Ad: 'MAITRE DE LA TEMPETE', perk9_2Desc: "La portee de l'ultime augmente de 100% et soigne 50 PV a l'activation.",
  perk5_3Ad: 'BALANCEMENT DU GRAPPIN', perk5_3Desc: "Te permet de te balancer avec le grappin pour te deplacer (vole tout droit vers la cible jusqu'au deblocage).",

  reklamlaCanlan: 'RESSUSCITER AVEC PUB', reklamlaBolumGec: 'PASSER AVEC 2 PUBS'
};

const DE = {
  geri: '< ZURUECK', kapat: '[ SCHLIESSEN ]', ac: 'AN', kapatKisa: 'AUS',
  oyna: 'SPIELEN', hayattaKal: 'UEBERLEBEN', kahramanlar: 'HELDEN', bolumler: 'LEVEL',
  gorevler: 'MISSIONEN', kontroller: 'STEUERUNG', ayarlar: 'EINSTELLUNGEN', cikis: 'BEENDEN', krediler: 'Credits',
  menuIpucu: '↑↓ Waehlen   ENTER Bestaetigen   oder Mausklick',
  ayarlarBaslik: 'EINSTELLUNGEN', sesEfekti: 'SOUNDEFFEKTE', muzik: 'MUSIK', dil: 'SPRACHE',
  mobilKontroller: 'MOBILE STEUERUNG', pcKontrolleri: 'PC-STEUERUNG',
  acik: 'AN', kapali: 'AUS',
  imlecSekli: 'FADENKREUZFORM', imlecRengi: 'FADENKREUZFARBE', imleciGizle: 'CURSOR AUSBLENDEN',
  sekilArti: 'KREUZ', sekilDaire: 'KREIS', sekilNokta: 'PUNKT', sekilKare: 'QUADRAT',
  ayarlarIpucu: 'ESC Zurueck (automatisch gespeichert)',
  kahramanSec: 'HELD WAEHLEN', yukselt: 'VERBESSERN', ustalik: 'MEISTERSCHAFT',
  gorevlerBaslik: 'MISSIONEN', genelGorevler: 'ALLGEMEINE MISSIONEN', karakterGorevleri: 'CHARAKTER-MISSIONEN',
  karakterGorevAciklama: 'Jeder Held hat seinen eigenen Meisterschaftsbaum — wird durch Schaden freigeschaltet.',
  kahramanUstalik: 'HELDEN-MEISTERSCHAFTEN ANSEHEN',
  kontrollerBaslik: 'STEUERUNG',
  kaybettin: 'GAME OVER', bolumTamamlandi: 'LEVEL GESCHAFFT!', savasiKazandin: 'DU HAST DEN KRIEG GEWONNEN!',
  tekrarOyna: 'NOCHMAL SPIELEN', sonrakiBolum: 'NAECHSTES LEVEL', anaMenuyeDon: 'ZURUECK ZUM MENUE',
  krediler_altbaslik: 'Danke an die Kuenstler der Sounds dieses Spiels:',
  kontrolSatiri1: 'LINKS / RECHTS PFEIL oder A / D : Bewegen',
  kontrolSatiri2: 'PFEIL HOCH / LEERTASTE / W : Springen',
  kontrolSatiri3: 'LINKSKLICK (halten) : Angreifen',
  kontrolSatiri4: 'RECHTSKLICK : Spezialfaehigkeit (je nach Held)',
  kontrolSatiri5: 'E : Zweitfaehigkeit (je nach Held)',
  kontrolSatiri6: 'Q : Ultimate (einsetzbar wenn aufgeladen)',
  kontrolSatiri7: 'ESC : Pause / Zurueck zum Menue',
  kontrollerIpucu: 'ESC / ENTER Zurueck',
  krediler_baslik: 'CREDITS',
  temaSehir: 'METROPOLE', temaUzay: 'TIEFER WELTRAUM', temaHarabe: 'RUINEN',
  zaferAltyazi: 'OMEGA-9 konnte Roboter einzeln kontrollieren, aber niemals sieben\nzugleich erwachte Geister nachbilden — diese Einheit besiegte es.',
  devamEt: 'FORTSETZEN', duraklatildi: 'PAUSIERT',

  hudBolum: 'LEVEL', hudDusman: 'GEGNER', hudSkor: 'PUNKTE', hudKitap: 'BUECHER', hudRuh: 'SEELE',
  hint0: 'SCHWERT - AEGIS', hint1: 'LINKS:KRALLE  RECHTS:DASH - RAPTOR', hint6: 'LINKS:ZAUBER  RECHTS:STRAHL - HEX',
  hint7: 'LINKS:SEELENKUGEL  RECHTS:GEIST - WRAITH', hint8: 'LINKS:FLAECHENSCHLAG  RECHTS:SCHUSS - REAPER',
  hint5: 'LINKS:FEUER  RECHTS:HAKEN  E:SPRENGEN - OVERDRIVE', hint9: 'LINKS:STOSS  RECHTS:WERFEN  E:VERSTECKEN - RONIN',
  eGuclendir: 'E:STAERKEN', sagHayaletEIyilestir: 'RECHTS:GEIST E:HEILEN', eKacis: 'E:FLUCHT',
  eIyilestir: 'E:HEILEN', ePatlat: 'E:SPRENGEN', eGizlen: 'E:VERSTECKEN', eKalkan: 'E:SCHILD',
  qIskeletCagir: 'Q:SKELETT BESCHWOEREN', qUltiLabel: 'Q:ULTIMATE',

  kalkanliLabel: 'GESCHUETZT', zayifVurLabel: 'SCHWACH - ANGRIFF!', fazLabel: 'PHASE',

  seviyeAtladinKartSec: 'LEVEL AUFGESTIEGEN! WAEHLE EINE KARTE', seviyeLabel: 'LEVEL',
  oldurulenLabel: 'GETOETET', hayattaKaldinLabel: 'DU HAST UEBERLEBT',

  bolumHintPrefix: 'Level', ustalikYokMetni: 'Keine Meisterschafts-Upgrades fuer diesen Helden.',

  statCan: 'LEBEN', statHiz: 'TEMPO', statRegen: 'REGEN',

  mobileSag: 'SPEZ',

  gorevIlkZaferIsim: 'ERSTER SIEG', gorevIlkZaferAciklama: 'Schliesse ein Level ab',
  gorevAvciIsim: 'JAEGER', gorevAvciAciklama: 'Toete insgesamt 150 Gegner',
  gorevHayattaKalanIsim: 'UEBERLEBENDER', gorevHayattaKalanAciklama: 'Ueberlebe 90 Sekunden in einem einzigen Ueberleben-Lauf',
  gorevKahramanIsim: 'HELD', gorevKahramanAciklama: 'Erreiche Level 15',

  yukseltmeHasarIsim: 'KRAFTSTEIGERUNG', yukseltmeHasarAciklama: '+20% Schaden',
  yukseltmeHizIsim: 'TEMPOSTEIGERUNG', yukseltmeHizAciklama: '+15% Bewegungsgeschwindigkeit',
  yukseltmeCanIsim: 'AUSDAUER', yukseltmeCanAciklama: '+25 Leben',
  yukseltmeSaldiriIsim: 'AGGRESSIVITAET', yukseltmeSaldiriAciklama: '-15% Angriffsabklingzeit',
  yukseltmeRegenIsim: 'REGENERATION', yukseltmeRegenAciklama: 'Passive Lebensregeneration',

  perk0_0Ad: 'SCHARFE REICHWEITE', perk0_0Desc: 'Die Reichweite des Schwerthiebs (Linksklick) steigt um +35%.',
  perk0_1Ad: 'SCHUETZENDE ENTSCHLOSSENHEIT', perk0_1Desc: '5 Sekunden ohne Schaden gewaehren dir ein kleines Schild.',
  perk0_2Ad: 'ABPRALLKLINGE', perk0_2Desc: 'Dein geworfenes Schwert prallt zu bis zu 5 Gegnern ab und kehrt dann zurueck.',
  perk1_0Ad: 'GIFTWOLKE', perk1_0Desc: 'E druecken vergiftet nahe Gegner sofort.',
  perk1_1Ad: 'BLUTGERUCH', perk1_1Desc: 'Nach jedem Dash steigt der Krallen-/Dash-Schaden fuer einige Sekunden um +30%.',
  perk1_2Ad: 'UNBEGRENZTER DASH', perk1_2Desc: 'Die Abklingzeit des Dashs entfaellt.',
  perk6_0Ad: 'MAGISCHE WIDERSTANDSKRAFT', perk6_0Desc: '+50 Leben (bis zu 100).',
  perk6_1Ad: 'MEISTERBIBLIOTHEK', perk6_1Desc: 'Die maximale Buchanzahl steigt, und der Strahlenschaden skaliert entsprechend.',
  perk6_2Ad: 'REALITAETSBRUCH', perk6_2Desc: 'Die Ultimate toetet jetzt sofort jeden Gegner auf dem Bildschirm.',
  perk7_0Ad: 'GEISTERJAEGER', perk7_0Desc: 'Du verursachst +30% Schaden in Geisterform.',
  perk7_1Ad: 'SEELENBUND', perk7_1Desc: 'Jede gewonnene Seele fuellt die Ultimate-Leiste und heilt dich sofort.',
  perk7_2Ad: 'UNBEGRENZTER GEIST', perk7_2Desc: 'Die Geisterdauer ist laenger, die Seelenkosten entfallen.',
  perk8_0Ad: 'SEELENARMEE', perk8_0Desc: 'E druecken beschwoert 3 zusaetzliche wuetende Skelette.',
  perk8_1Ad: 'LEBLOSES ERBE', perk8_1Desc: 'Ein Skelett erscheint dort, wo ein von dir getoeteter Gegner fiel.',
  perk8_2Ad: 'BOGENSCHUETZENLEGION', perk8_2Desc: 'Alle Skelette aus der Ultimate werden zu Fernkampf-Bogenschuetzen.',
  perk5_0Ad: 'DIEBESLADUNG', perk5_0Desc: 'Du heilst 10 Leben bei jedem Enterhaken-Wurf.',
  perk5_1Ad: 'KERNSCHILD', perk5_1Desc: "Waehrend die Ultimate aktiv ist, faellt dein Leben nicht unter 1.",
  perk5_2Ad: 'DOPPELLAUF', perk5_2Desc: 'Die Feuerrate deiner Waffe steigt um 100%.',
  perk9_0Ad: 'LANGER SPEER', perk9_0Desc: 'Die Reichweite deines Speers (Stoss+Wurf) steigt um 50%.',
  perk9_1Ad: 'SCHATTENGRIFF', perk9_1Desc: 'Im Schattenmodus getroffene Gegner erstarren fuer 5 Sekunden.',
  perk9_2Ad: 'STURMMEISTER', perk9_2Desc: 'Die Ultimate-Reichweite steigt um 100% und heilt bei Aktivierung 50 Leben.',
  perk5_3Ad: 'HAKENSCHWUNG', perk5_3Desc: 'Ermoeglicht Bewegung durch Schwingen am Haken (fliegt bis zur Freischaltung geradewegs zum Ziel).',

  reklamlaCanlan: 'MIT WERBUNG WIEDERBELEBEN', reklamlaBolumGec: 'MIT 2 WERBUNGEN UEBERSPRINGEN'
};

const TABLES = { tr: TR, en: EN, es: ES, fr: FR, de: DE };

export function t(key) {
  const table = TABLES[GameState.dil] || TR;
  return table[key] || TR[key] || key;
}

// Randomized defiant/encouraging lines for the death screen — not in the
// original (which just says KAYBETTIN), added per direct request.
const OLUM_MESAJLARI = {
  tr: ['PES ETME. TEKRAR DENE.', 'NEREDEYSE BASARIYORDUN.', 'YZ SENI BEKLIYOR — HAZIR OL.', 'BU SADECE BIR DENEMEYDI.', 'DUS, AMA KALK.'],
  en: ["DON'T GIVE UP. TRY AGAIN.", 'YOU WERE ALMOST THERE.', 'OMEGA-9 IS WAITING — GET READY.', 'THIS WAS JUST A TRIAL.', 'FALL, BUT RISE AGAIN.'],
  es: ['NO TE RINDAS. INTENTALO DE NUEVO.', 'ESTABAS CASI AHI.', 'OMEGA-9 TE ESPERA — PREPARATE.', 'ESTO FUE SOLO UNA PRUEBA.', 'CAE, PERO LEVANTATE.'],
  fr: ["N'ABANDONNE PAS. REESSAIE.", 'TU Y ETAIS PRESQUE.', "OMEGA-9 T'ATTEND — PREPARE-TOI.", "CE N'ETAIT QU'UN ESSAI.", 'TOMBE, MAIS RELEVE-TOI.'],
  de: ['GIB NICHT AUF. VERSUCH ES NOCHMAL.', 'DU WARST SO NAH DRAN.', 'OMEGA-9 WARTET — MACH DICH BEREIT.', 'DAS WAR NUR EIN VERSUCH.', 'FALL, ABER STEH WIEDER AUF.']
};

export function randomOlumMesaji() {
  const list = OLUM_MESAJLARI[GameState.dil] || OLUM_MESAJLARI.tr;
  return list[Math.floor(Math.random() * list.length)];
}
