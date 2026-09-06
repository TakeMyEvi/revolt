// Ported 1:1 from game (1).py balance constants.
export const GENISLIK = 900;
export const YUKSEKLIK = 550;
export const FPS = 60;
export const ZEMIN_Y = YUKSEKLIK - 80; // 470

export const COLORS = {
  SIYAH: 0x000000,
  BEYAZ: 0xffffff,
  CYAN: 0x00fff7,
  TURUNCU: 0xf5a623,
  KIRMIZI: 0xe94560,
  LACIVERT: 0x1a44bb,
  KOYU: 0x05050f,
  ZEMIN_C: 0x0a0a1e,
  YESIL: 0x00ff64,
  MOR: 0xaa00ff,
  SARI: 0xffee00
};

export const PATLAMA_YARICAP = 55;
export const FITIL_SURESI = 18;
// How long the player is untouchable right after getting hit (in frames,
// 60/s) before another source can damage them again. Was 12 (0.2s) — felt
// too short, letting multiple overlapping hits/explosions chip away several
// ticks of damage in the same instant.
export const HASAR_DOKUNULMAZLIK_SURESI = 24;

export const SOLUCAN = {
  CAN: 75, HASAR: 35, YUKSEKLIK: 220, TEHLIKE_SURESI: 55,
  ONDEN_MESAFE: 180, ARALIK_MIN: 220, ARALIK_MAX: 340
};

export const MIZRAKLI = {
  HIZ: 5.2, GRUP_MIN: 5, GRUP_MAX: 6, HAVADA_ESIK: 55
};

export const KALKAN_KAPASITE = 70;
export const KALKAN_SURESI = 300;
export const KALKAN_BEKLEME = 360;

export const ULTI_MAX = 100;
export const ULTI_SARJ_OLUM = 8;
export const ULTI_SURESI = 480;
export const ULTI_CAN_ARTISI = 25;

export const AEGIS = {
  KILIC_HASAR: 35, KILIC_HIZI: 17, KILIC_MENZIL: 480,
  KILIC_ATMA_BEKLEME: 300, KILIC_SAVURMA_BEKLEME: 20,
  KILIC_MENZIL_ARTIS: 0.35,
  PASIF_KALKAN_ARALIK: 300, PASIF_KALKAN_ARTIS: 8, PASIF_KALKAN_MAX: 40,
  KILIC_SEKME_MAKS: 5
};

export const HEX = {
  MAX_CAN: 50, KITAP_MAX: 3, KITAP_SURESI: 180,
  BUYU_HASAR: 30, BUYU_HIZI: 6, BUYU_BEKLEME: 40,
  ISIN_BIRIM_HASAR: 25, ISIN_MENZIL: 1200,
  HEAL_SURESI: 180, HEAL_TOPLAM: 40, HEAL_BEKLEME: 300,
  ULTI_HASAR: 20, ULTI_YAVAS_SURESI: 180, ULTI_YAVAS_CARPAN: 0.4,
  CAN_YUKSELTME: 50, KITAP_MAX_USTA: 6
};

export const RAPTOR = {
  HIZ_X: 7, ZIPLAMA_BASLANGIC: -9, ZIPLAMA_ITKI: -0.9,
  ZIPLAMA_MAX_KARE: 26, ZIPLAMA_MIN_HIZ: -20,
  PENCE_HASAR: 18, PENCE_YASAM_CALMA: 0.3, PENCE_BEKLEME: 12,
  DASH_HIZI: 14, DASH_SURESI: 12, DASH_HASAR: 25, DASH_BEKLEME: 90,
  KACIS_SURESI: 20, KACIS_HIZ: 10, KACIS_BEKLEME: 240,
  ZEHIR_SURESI: 480, ZEHIR_TIK: 30, ZEHIR_HASAR: 3, ZEHIR_DUSMAN_SURESI: 180,
  ULTI_SURESI: 300, ULTI_PENCE_CARPAN: 1.8, ULTI_HIZ_CARPAN: 1.6,
  ZEHIR_PATLAMA_YARICAP: 110,
  OFKE_SURESI: 180, OFKE_CARPAN: 1.3, OFKE_HIZ_CARPAN: 1.25
};

export const WRAITH = {
  HAYALET_HASAR_ARTIS_CARPAN: 1.3, RUH_OTO_HEAL_ORAN: 0.3,
  HAYALET_USTA_SURESI: 480, HAYALET_USTA_BEKLEME: 300,
  MAX_CAN: 110, HIZ: 3.5, UCUS_HIZ: 3,
  RUH_MAX: 100, RUH_SARJ_VURUS: 8, RUH_SARJ_OLUM: 15,
  RUH_HASAR: 22, RUH_HIZI: 8, RUH_BEKLEME: 35,
  YASAM_CALMA_ORAN: 0.25, HAYALET_MALIYET: 40, HAYALET_SURESI: 90,
  HAYALET_YARI_CARPAN: 0.5, HEAL_ORAN: 0.6, HEAL_BEKLEME: 200,
  ULTI_SURESI: 240, ULTI_HASAR_CARPAN: 0.1, ULTI_YAVAS_CARPAN: 0.25,
  ULTI_RUH_RENGI: 0x50a0ff
};

export const REAPER = {
  MAX_CAN: 150, HIZ: 4, W: 36, H: 58, RUH_BOLME_MAX: 10,
  VURUS_MENZIL: 150, VURUS_ACI: 0.75, VURUS_HASAR: 22, VURUS_BEKLEME: 45,
  ATIS_MENZIL: 220, ATIS_ACI: 0.95, ATIS_HASAR: 46, ATIS_BEKLEME: 55,
  EMICI_ORAN: 0.25,
  ISKELET_CAN: 35, ISKELET_HASAR: 8, ISKELET_HIZ: 2.5,
  ISKELET_MENZIL: 40, ISKELET_ATIS_BEKLEME: 40, ISKELET_OKCU_MENZIL: 260,
  E_CAN_MALIYET: 10, GUC_SURESI: 600, GUC_CARPAN: 1.8, E_BEKLEME: 700,
  ULTI_ISKELET_RENK: 0x1a0e11
};

export const OVERDRIVE = {
  MAX_CAN: 90, KANCA_MENZIL: 3000, KANCA_UCUS_HIZI: 11, KANCA_BEKLEME: 34,
  SALLANMA_HIZ: 12, KANCA_POMPA: 0.0022, SALLANMA_ESIGI: 2500,
  E_HASAR: 55, E_MENZIL: 75, E_BEKLEME: 130, E_CAN_YENILEME: 20,
  ULTI_SURESI: 420, ULTI_YAVAS_CARPAN: 0.18, ULTI_CAN_KAZANC: 10
};

export const RONIN = {
  MAX_CAN: 120, ITIS_HASAR: 22, ITIS_MENZIL: 110, ITIS_ACI: 0.5, ITIS_BEKLEME: 16,
  FIRLAT_HASAR: 34, FIRLAT_MENZIL: 520, FIRLAT_ACI: 0.12, FIRLAT_BEKLEME: 65,
  E_SURESI: 90, E_BEKLEME: 280, E_KRITIK_CARPAN: 2.6,
  ULTI_SURESI: 480, ULTI_YARICAP: 66, ULTI_HASAR: 9
};

// Story-mode platforms — see game (1).py's PLATFORM_SEHIR/PLATFORM_ISTASYON.
// City stages (<=10) get static ledges; station stages (11-20) get ones that
// slide back and forth between sol/sag; ruins stages (>20) get platforms that
// crumble a short time after you land on them (kirilir — not in the original,
// added per direct request to make the ruins act more hazardous).
export const PLATFORM_SEHIR = [
  { x: 120, y: 370, w: 150, h: 14 },
  { x: 420, y: 300, w: 150, h: 14 },
  { x: 650, y: 370, w: 150, h: 14 }
];
export const PLATFORM_ISTASYON = [
  { x: 120, y: 370, w: 140, h: 14, hiz: 1.2, sol: 80, sag: 280 },
  { x: 420, y: 300, w: 140, h: 14, hiz: -1.0, sol: 350, sag: 600 },
  { x: 650, y: 370, w: 140, h: 14, hiz: 1.4, sol: 600, sag: 830 }
];
export const PLATFORM_HARABE = [
  { x: 120, y: 370, w: 130, h: 14, kirilir: true },
  { x: 420, y: 300, w: 130, h: 14, kirilir: true },
  { x: 650, y: 370, w: 130, h: 14, kirilir: true }
];
export function platformlarIcin(bolum) {
  if (bolum <= 10) return PLATFORM_SEHIR.map(p => ({ ...p }));
  if (bolum <= 20) return PLATFORM_ISTASYON.map(p => ({ ...p }));
  return PLATFORM_HARABE.map(p => ({ ...p, kirilmaKare: -1, kirildi: false }));
}

export const SURVIVOR = {
  XP_BASE: 20, XP_ARTIS: 1.3, ZORLUK_ARALIK: 1200,
  DUNYA_GENISLIK: 2700
};

export const SILAHLAR = [
  { id: 0, isim: 'LAZER TABANCA', ikon: '[L]', fiyat: 0, hasar: 10, atis_hizi: 12, mermi_hizi: 13, sarjor: 15, dolum: 90, renk: 0xf5a623, derece: 1 },
  { id: 1, isim: 'PLAZMA TABANCA', ikon: '[P]', fiyat: 300, hasar: 16, atis_hizi: 10, mermi_hizi: 14, sarjor: 18, dolum: 80, renk: 0x4488ff, derece: 1 },
  { id: 2, isim: 'NEON SHOTGUN', ikon: '[S]', fiyat: 700, hasar: 12, atis_hizi: 18, mermi_hizi: 11, sarjor: 8, dolum: 100, renk: 0xff44aa, derece: 2, sacma: 3 },
  { id: 3, isim: 'ION RIFLE', ikon: '[I]', fiyat: 1200, hasar: 28, atis_hizi: 20, mermi_hizi: 17, sarjor: 10, dolum: 110, renk: 0xffff00, derece: 2 },
  { id: 4, isim: 'PROTON BURST', ikon: '[B]', fiyat: 1800, hasar: 18, atis_hizi: 8, mermi_hizi: 12, sarjor: 20, dolum: 85, renk: 0xff8800, derece: 2, cift: true },
  { id: 5, isim: 'CYBER SMG', ikon: '[M]', fiyat: 2600, hasar: 9, atis_hizi: 4, mermi_hizi: 14, sarjor: 35, dolum: 95, renk: 0xff6600, derece: 3 },
  { id: 6, isim: 'VOID CANNON', ikon: '[V]', fiyat: 3600, hasar: 45, atis_hizi: 30, mermi_hizi: 10, sarjor: 5, dolum: 130, renk: 0xaa00ff, derece: 3 },
  { id: 7, isim: 'QUANTUM RIFLE', ikon: '[Q]', fiyat: 5000, hasar: 35, atis_hizi: 15, mermi_hizi: 20, sarjor: 12, dolum: 105, renk: 0x00fff7, derece: 3 },
  { id: 8, isim: 'NOVA LAUNCHER', ikon: '[N]', fiyat: 7000, hasar: 20, atis_hizi: 7, mermi_hizi: 11, sarjor: 16, dolum: 115, renk: 0xffee00, derece: 4, sacma: 4 },
  { id: 9, isim: 'OMEGA BLASTER', ikon: '[O]', fiyat: 10000, hasar: 60, atis_hizi: 10, mermi_hizi: 16, sarjor: 24, dolum: 75, renk: 0xff0066, derece: 4, cift: true }
];

// KAHRAMANLAR: id, isim, renk, acilis_bolum
export const KAHRAMANLAR = [
  { id: 0, isim: 'AEGIS', renk: 0x00fff7, acilis_bolum: 1 },
  { id: 1, isim: 'RAPTOR', renk: 0x00ff64, acilis_bolum: 5 },
  { id: 5, isim: 'OVERDRIVE', renk: 0xffee00, acilis_bolum: 20 },
  { id: 6, isim: 'HEX', renk: 0xaa00ff, acilis_bolum: 10 },
  { id: 7, isim: 'WRAITH', renk: 0x78dcc8, acilis_bolum: 15 },
  { id: 8, isim: 'REAPER', renk: 0xd2c8b4, acilis_bolum: 17 },
  { id: 9, isim: 'RONIN', renk: 0xaa78ff, acilis_bolum: 25 }
];

export const KAHRAMAN_USTALIK_ESIKLERI = {
  0: [3640, 3820, 4000],
  1: [3310, 3490, 3670],
  6: [2970, 3150, 3330],
  7: [2640, 2820, 3000],
  8: [2310, 2490, 2670],
  5: [1970, 2150, 2330],
  9: [1640, 1820, 2000]
};

// Per-hero mastery tiers, unlocked automatically as cumulative damage dealt
// with that hero (GameState.kahramanHasar) crosses KAHRAMAN_USTALIK_ESIKLERI.
export const KAHRAMAN_YUKSELTMELERI = {
  0: [
    { ad: 'KESKIN MENZIL', aciklama: 'Kilic sol tik (savurma) menzili +%35 artar.' },
    { ad: 'KORUYUCU AZIM', aciklama: '5 saniye hasar almazsan az canli bir kalkan kazanirsin.' },
    { ad: 'SEKEN KILIC', aciklama: 'Firlattigin kilic 5 dusmana kadar seker, sonra geri doner.' }
  ],
  1: [
    { ad: 'ZEHIR BULUTU', aciklama: "E'ye basinca etrafindaki dusmanlara aninda zehir bulasir." },
    { ad: 'KAN KOKUSU', aciklama: 'Her dash sonrasi birkac saniye pence/dash hasari +%30 artar.' },
    { ad: 'SINIRSIZ HAMLE', aciklama: 'Hamle (dash) bekleme suresi kalkar.' }
  ],
  6: [
    { ad: 'BUYULU OZDIRENC', aciklama: "+50 Can (100'e cikar)." },
    { ad: 'USTA KITAPLIK', aciklama: 'Azami kitap sayisi artar, isin hasari da buna gore artar.' },
    { ad: 'GERCEKLIK KIRIMI', aciklama: 'Ulti artik ekrandaki her dusmani aninda oldurur.' }
  ],
  7: [
    { ad: 'HAYALET AVCISI', aciklama: 'Hayaletken +%30 hasar verirsin.' },
    { ad: 'RUH BAGI', aciklama: 'Kazandigin her ruh, ulti barini doldururken aninda can da verir.' },
    { ad: 'SINIRSIZ HAYALET', aciklama: 'Hayalet suresi uzar, ruh maliyeti kalkar.' }
  ],
  8: [
    { ad: 'RUH ORDUSU', aciklama: "E'ye basinca 3 ek delirmis iskelet cagirir." },
    { ad: 'CANSIZ MIRAS', aciklama: 'Oldurdugun bir dusmanin yerinde bir iskelet belirir.' },
    { ad: 'OKCU LEJYONU', aciklama: 'Ultiden cikan tum iskeletler uzaktan vuran okcu olur.' }
  ],
  5: [
    { ad: 'HIRSIZ SARJ', aciklama: 'Her kanca attiginda 10 can iyilesirsin.' },
    { ad: 'CEKIRDEK KALKANI', aciklama: 'Ulti aktifken 1 canin altina dusmezsin.' },
    { ad: 'CIFTE NAMLU', aciklama: 'Tabancanin ates hizi %100 artar.' }
  ],
  9: [
    { ad: 'UZUN MIZRAK', aciklama: 'Mizragin (itis+firlatma) menzili %50 artar.' },
    { ad: 'GOLGE PENCESI', aciklama: 'Golge modundayken vurdugun dusmanlar 5 saniyeligine donar.' },
    { ad: 'FIRTINA USTASI', aciklama: 'Ultinin menzili %100 artar ve aktive olunca 50 can doldurur.' }
  ]
};

// 0-3: how many tiers are unlocked for this hero given cumulative damage dealt.
export function ustalikKademesi(heroId, hasar) {
  const esikler = KAHRAMAN_USTALIK_ESIKLERI[heroId];
  if (!esikler) return 0;
  let kademe = 0;
  for (const esik of esikler) { if (hasar >= esik) kademe++; else break; }
  return kademe;
}

// TEST_MODU icin: gercek bolum yerine hangi bolumun temasi/platformlari
// kullanilsin? Mirrors game (1).py's `tema_bolum = {1: 1, 2: 11, 3: 21}.get(bolum, 21)`.
export function efektifTemaBolum(bolum, testModu = false) {
  if (!testModu) return bolum;
  const harita = { 1: 1, 2: 11, 3: 21 };
  return harita[bolum] || 21;
}

// TEST_MODU: hizli test icin ilk 5 bolum sikistirilir — 1: sehir, 2: uzay,
// 3: harabe (her temayi hemen gormek icin), 4: mini boss, 5: final boss.
// Tema eslesmesi icin bkz. efektifTemaBolum().
export function bolumAyar(bolum, testModu = false) {
  if (testModu) {
    if (bolum <= 3) {
      return { melee: 3, ranged: 2, drone: 1, sniper: 1, shield: 1, tank: 0,
        suicide: 1, gorunmez: 1, hayalet: 1, mizrakli: 1, boss: false, final: false };
    } else if (bolum === 4) {
      return { melee: 0, ranged: 0, drone: 0, sniper: 0, shield: 0, tank: 0,
        suicide: 0, gorunmez: 0, hayalet: 0, mizrakli: 0, boss: true, final: false };
    } else if (bolum === 5) {
      return { melee: 0, ranged: 0, drone: 0, sniper: 0, shield: 0, tank: 0,
        suicide: 0, gorunmez: 0, hayalet: 0, mizrakli: 0, boss: false, final: true };
    }
  }
  if (bolum <= 3) {
    return { melee: 8, ranged: 2, drone: 0, sniper: 0, shield: 0, tank: 0,
      suicide: bolum >= 3 ? 1 : 0, gorunmez: 0, hayalet: 0, mizrakli: 0, boss: false, final: false };
  } else if (bolum <= 6) {
    return { melee: 5, ranged: 3, drone: 2, sniper: bolum >= 5 ? 1 : 0, shield: 0, tank: 0,
      suicide: 2, gorunmez: 0, hayalet: 0, mizrakli: 1, boss: bolum % 5 === 0, final: false };
  } else if (bolum <= 10) {
    return { melee: 3, ranged: 4, drone: 2, sniper: 2, shield: bolum >= 8 ? 2 : 0, tank: 0,
      suicide: 2, gorunmez: bolum >= 7 ? 1 : 0, hayalet: 0, mizrakli: 1, boss: bolum % 5 === 0, final: false };
  } else if (bolum <= 15) {
    return { melee: 2, ranged: 3, drone: 2, sniper: 2, shield: 2, tank: bolum >= 12 ? 1 : 0,
      suicide: 3, gorunmez: 2, hayalet: bolum >= 13 ? 1 : 0, mizrakli: 2, boss: bolum % 5 === 0, final: false };
  } else if (bolum <= 20) {
    return { melee: 2, ranged: 3, drone: 2, sniper: 2, shield: 2, tank: 2,
      suicide: 3, gorunmez: 2, hayalet: 2, mizrakli: 2, boss: bolum % 5 === 0, final: false };
  } else if (bolum < 30) {
    // golgeRonin: elite dark-mirror of the RONIN hero (spear + teleport), only
    // in the last 5 story stages (26-29 actually spawn it; 30 is the boss fight) —
    // not in the original, added per direct request.
    return { melee: 1, ranged: 3, drone: 2, sniper: 3, shield: 2, tank: 3,
      suicide: 4, gorunmez: 3, hayalet: 3, mizrakli: 2, golgeRonin: bolum >= 26 ? (bolum >= 28 ? 2 : 1) : 0,
      boss: bolum % 5 === 0, final: false };
  } else {
    return { melee: 0, ranged: 0, drone: 0, sniper: 0, shield: 0, tank: 0, suicide: 0,
      gorunmez: 0, hayalet: 0, mizrakli: 0, golgeRonin: 0, boss: false, final: true };
  }
}

export const GENEL_GOREVLER = [
  { id: 'ilk_zafer', isim: 'ILK ZAFER', aciklama: "Bir bolumu bitir",
    kontrol: (s) => s.enYuksekBolum >= 2, etki: { can: 15 } },
  { id: 'avci', isim: 'AVCI', aciklama: "Toplam 150 dusman oldur",
    kontrol: (s) => s.toplamOldurulen >= 150, etki: { hiz: 0.08 } },
  { id: 'hayatta_kalan', isim: 'HAYATTA KALAN', aciklama: "Survivor'da tek seferde 90 saniye hayatta kal",
    kontrol: (s) => s.enUzunHayattaKalma >= 90, etki: { regen: 2.0 } },
  { id: 'kahraman', isim: 'KAHRAMAN', aciklama: "Bolum 15'e ulas",
    kontrol: (s) => s.enYuksekBolum >= 15, etki: { can: 25, hiz: 0.05 } }
];

export const YUKSELTME_HAVUZU = [
  { id: 'hasar', isim: 'GUC ARTISI', aciklama: '+%20 Hasar' },
  { id: 'hiz', isim: 'HIZ ARTISI', aciklama: '+%15 Hareket Hizi' },
  { id: 'can', isim: 'DAYANIKLILIK', aciklama: '+25 Can' },
  { id: 'saldiri', isim: 'SALDIRGANLIK', aciklama: '-%15 Saldiri Bekleme' },
  { id: 'regen', isim: 'YENILENME', aciklama: 'Pasif Can Yenileme' }
];
