import Phaser from 'phaser';
import { GENISLIK, ZEMIN_Y, AEGIS, HEX, RAPTOR, WRAITH, REAPER, OVERDRIVE, RONIN,
  KALKAN_KAPASITE, KALKAN_SURESI, KALKAN_BEKLEME,
  ULTI_MAX, ULTI_SURESI, ULTI_CAN_ARTISI, SILAHLAR, ustalikKademesi, GENEL_GOREVLER, HASAR_DOKUNULMAZLIK_SURESI } from '../data/constants.js';
import { GameState } from '../data/state.js';

// Direct port of `class Oyuncu` — see SPEC_player_heroes.md for exact source formulas.
export class Player {
  constructor(scene, heroId) {
    this.scene = scene;
    this.heroId = heroId;

    this.x = 150.0;
    this.w = 28; this.h = 48;
    this.y = ZEMIN_Y - this.h;
    this.hizX = 0; this.hizY = 0;
    this.yerde = true;
    this.can = 100; this.maxCan = 100;
    this.animFrame = 0; this.animZamani = 0;
    this.hasarTimer = 0;
    this.facing = 1;

    this.silahIdx = 0;
    this.sarjor = SILAHLAR[0].sarjor;
    this.doluyor = false; this.dolumTimer = 0; this.atisTimer = 0;

    this.kalkanAktif = false; this.kalkanKapasite = 0;
    this.kalkanSuresi = 0; this.kalkanBekleme = 0;

    this.ultiAktif = false; this.ultiSuresi = 0; this.ultiDolu = 0;

    this.survivorHizCarpan = 1.0;
    this.survivorCanYenileme = 0;
    this.hasarCarpan = 1.0; // survival-mode "GUC ARTISI" card multiplier
    this.saldiriCarpan = 1.0; // survival-mode "SALDIRGANLIK" card multiplier (cooldowns)

    // ── AEGIS (id 0) ──
    this.kilicDurum = 'beklemede';
    this.kilicX = 0; this.kilicY = 0;
    this.kilicHizX = 0; this.kilicHizY = 0;
    this.kilicMesafe = 0;
    this.kilicVurulanlar = [];
    this.kilicAtmaBekleme = 0;
    this.kilicSavurmaBekleme = 0;
    this.kilicSavurmaGoster = 0;
    this.kilicSekmeYapildi = false;
    this.aegisKilicMenzilCarpan = 1.0;
    this.aegisKilicSekmeAcik = false;
    this.aegisPasifKalkanAcik = false;
    this.aegisPasifKalkan = 0;
    this.aegisHasarsizKare = 0;

    // ── RAPTOR (id 1) ──
    this.raptorHizli = heroId === 1;
    this.raptorZipTutuluyor = false; this.raptorZipKare = 0;
    this.raptorDashAktif = false; this.raptorDashSuresi = 0; this.raptorDashBekleme = 0;
    this.raptorDashYon = 1; this.raptorDashVurulanlar = [];
    this.raptorPenceBekleme = 0; this.raptorPenceGoster = 0;
    this.raptorKacisAktif = false; // escape-immunity variant (unused by current E binding, kept for parity)
    this.raptorKacisBekleme = 0;
    this.raptorZehirAktif = false; this.raptorZehirSuresi = 0;
    this.raptorOfkeAktif = false; this.raptorOfkeSuresi = 0; this.raptorOfkeAcik = false;
    this.raptorUltiAktif = false; this.raptorUltiSuresi = 0;
    this.raptorDashSinirsizAcik = false;
    this.raptorZehirPatlamaAcik = false;

    // ── HEX (id 6) ──
    this.daimaUcar = heroId === 6 || heroId === 7; // HEX and WRAITH both always fly — game (1).py:4721/4727
    this.hexKitapSayisi = HEX.KITAP_MAX;
    this.hexKitapMaxOzel = HEX.KITAP_MAX;
    this.hexKitapTimer = HEX.KITAP_SURESI;
    this.hexBuyuBekleme = 0;
    this.hexHealAktif = false; this.hexHealSuresi = 0; this.hexHealBekleme = 0;
    this.hexIsinBitis = { x: 0, y: 0 };
    this.hexIsinGoster = 0;
    this.hexIsinKitapSayisi = 0;
    this.hexUltiEkranTemizleAcik = false;

    // ── WRAITH (id 7) ──
    this.wraithYavas = heroId === 7;
    this.wraithRuh = 0;
    this.wraithHayaletAktif = false; this.wraithHayaletSuresi = 0; this.wraithHayaletBekleme = 0;
    this.wraithHealBekleme = 0;
    this.wraithUltiAktif = false; this.wraithUltiSuresi = 0;
    this.wraithHayaletUstaAcik = false; this.wraithRuhHealAcik = false;
    this.wraithHayaletHasarArtisAcik = false;

    // ── REAPER (id 8) ──
    this.reaperAgir = heroId === 8;
    this.reaperRuhBolme = 0;
    this.reaperVurusBekleme = 0; this.reaperVurusGoster = 0;
    this.reaperAtisBekleme = 0; this.reaperAtisGoster = 0;
    this.reaperEBekleme = 0;
    this.reaperEEkIskeletAcik = false; this.reaperAtisIskeletAcik = false; this.reaperUltiOkcuAcik = false;

    // ── OVERDRIVE (id 5) ──
    this.kancaDurum = 'yok';
    this.kancaAnchorX = 0; this.kancaAnchorY = 0;
    this.kancaAci = 0; this.kancaAcisalHiz = 0; this.kancaIpUzunlugu = 100;
    this.kancaBekleme = 0;
    this.overdriveEBekleme = 0; this.overdriveEGoster = 0;
    this.overdriveUltiAktif = false; this.overdriveUltiSuresi = 0;
    this.overdriveOlumsuzlukKalan = 0;
    this.overdriveHizliAtesAcik = false; this.overdriveSinirsizMermi = false;
    this.overdriveUltiOlumsuzAcik = false; this.overdriveKancaHealAcik = false;
    // Pendulum-swing is a separate unlock from the 3 numbered mastery tiers —
    // see OVERDRIVE.SALLANMA_ESIGI / game (1).py's `overdrive_sallanma_acik`.
    // Until unlocked, the hook flies straight to its target ('ucuyor'); no swing.
    this.overdriveSallanmaAcik = false;
    this.kancaUcusHedefX = 0; this.kancaUcusHedefY = 0;

    // ── RONIN (id 9) ──
    this.roninItisBekleme = 0; this.roninItisZirh = 0; this.roninItisGoster = 0;
    this.roninFirlatBekleme = 0; this.roninFirlatGoster = 0;
    this.roninGizliAktif = false; this.roninGizliSuresi = 0; this.roninEBekleme = 0;
    this.roninKritikHazir = false;
    this.roninUltiAktif = false; this.roninUltiSuresi = 0;
    this.roninUltiGelismisAcik = false; this.roninGizliSersemAcik = false;
    this.roninMenzilCarpan = 1.0;
    this._roninUltiTikTimer = 0;

    this._buildVisual();
  }

  _buildVisual() {
    this.gfx = this.scene.add.graphics();
    this.gfx.setDepth(10);
  }

  rect() { return new Phaser.Geom.Rectangle(this.x, this.y, this.w, this.h); }
  center() { return { x: this.x + this.w / 2, y: this.y + this.h / 2 }; }
  handPos() { return { x: this.x + this.w / 2, y: this.y + this.h * 0.38 }; }

  // Permanent meta-progression from lifetime milestones — see GENEL_GOREVLER.
  // Mirrors the Python original's `genel_yukseltme_uygula(oyuncu)`, called once
  // at spawn (unlike ustalikUygula this doesn't need to re-check mid-fight).
  genelYukseltmeUygula() {
    for (const g of GENEL_GOREVLER) {
      if (!g.kontrol(GameState)) continue;
      if (g.etki.can) { this.maxCan += g.etki.can; this.can += g.etki.can; }
      if (g.etki.hiz) this.survivorHizCarpan *= (1 + g.etki.hiz);
      if (g.etki.regen) this.survivorCanYenileme += g.etki.regen / 60;
    }
  }

  // Flips the perk flags for every mastery tier reached so far (kademe 0-3),
  // based on cumulative damage dealt with this hero — see KAHRAMAN_YUKSELTMELERI.
  // Idempotent: safe to call again as more damage accrues mid-fight.
  ustalikUygula() {
    const hasar = GameState.kahramanHasar?.[this.heroId] || 0;
    const kademe = ustalikKademesi(this.heroId, hasar);
    // reached its threshold AND not manually switched back off (KAHRAMAN_YETENEK_KAPALI)
    const acik = (i) => kademe >= i + 1 && !(GameState.kapaliYetenekler || []).includes(`${this.heroId}:${i}`);
    if (this.heroId === 5) {
      this.overdriveSallanmaAcik = hasar >= OVERDRIVE.SALLANMA_ESIGI &&
        !(GameState.kapaliYetenekler || []).includes('5:3');
    }
    if (kademe < 1) return;
    switch (this.heroId) {
      case 0:
        this.aegisKilicMenzilCarpan = acik(0) ? 1 + AEGIS.KILIC_MENZIL_ARTIS : 1.0;
        this.aegisPasifKalkanAcik = acik(1);
        this.aegisKilicSekmeAcik = acik(2);
        break;
      case 1:
        this.raptorZehirPatlamaAcik = acik(0);
        this.raptorOfkeAcik = acik(1);
        this.raptorDashSinirsizAcik = acik(2);
        break;
      case 6:
        this.maxCan = acik(0) ? HEX.MAX_CAN + HEX.CAN_YUKSELTME : HEX.MAX_CAN;
        this.can = Math.min(this.can, this.maxCan);
        this.hexKitapMaxOzel = acik(1) ? HEX.KITAP_MAX_USTA : HEX.KITAP_MAX;
        this.hexUltiEkranTemizleAcik = acik(2);
        break;
      case 7:
        this.wraithHayaletHasarArtisAcik = acik(0);
        this.wraithRuhHealAcik = acik(1);
        this.wraithHayaletUstaAcik = acik(2);
        break;
      case 8:
        this.reaperEEkIskeletAcik = acik(0);
        this.reaperAtisIskeletAcik = acik(1);
        this.reaperUltiOkcuAcik = acik(2);
        break;
      case 5:
        this.overdriveKancaHealAcik = acik(0);
        this.overdriveUltiOlumsuzAcik = acik(1);
        this.overdriveHizliAtesAcik = acik(2);
        break;
      case 9:
        this.roninMenzilCarpan = acik(0) ? 1.5 : 1.0;
        this.roninGizliSersemAcik = acik(1);
        this.roninUltiGelismisAcik = acik(2);
        break;
    }
  }

  isImmune() {
    return this.ultiAktif || this.raptorKacisAktif || this.wraithHayaletAktif;
  }

  // ── damage pipeline (exact order from spec) ──
  hasarAl(miktar) {
    if (this.isImmune()) return 0;
    this.aegisHasarsizKare = 0;
    if (this.aegisPasifKalkan > 0) {
      const emilen = Math.min(miktar, this.aegisPasifKalkan);
      this.aegisPasifKalkan -= emilen;
      miktar -= emilen;
      if (miktar <= 0) { this.hasarTimer = HASAR_DOKUNULMAZLIK_SURESI; return 0; }
    }
    if (this.wraithUltiAktif) {
      this.can -= miktar * WRAITH.ULTI_HASAR_CARPAN;
      this.hasarTimer = HASAR_DOKUNULMAZLIK_SURESI;
      return miktar;
    }
    if (this.roninItisZirh > 0) {
      this.can -= miktar * 0.3;
      this.hasarTimer = HASAR_DOKUNULMAZLIK_SURESI;
      return miktar;
    }
    if (this.kalkanAktif) {
      const emilen = Math.min(miktar, this.kalkanKapasite);
      this.kalkanKapasite -= emilen;
      miktar -= emilen;
      if (this.kalkanKapasite <= 0) this.kalkanKapat();
      this.can -= miktar;
      this.hasarTimer = HASAR_DOKUNULMAZLIK_SURESI;
      return miktar;
    }
    this.can -= miktar;
    this.hasarTimer = HASAR_DOKUNULMAZLIK_SURESI;
    return miktar;
  }

  kalkanBaslat() {
    if (this.kalkanBekleme <= 0 && !this.kalkanAktif) {
      this.kalkanAktif = true;
      this.kalkanKapasite = KALKAN_KAPASITE;
      this.kalkanSuresi = KALKAN_SURESI;
    }
  }

  kalkanKapat() {
    this.kalkanAktif = false;
    this.kalkanBekleme = KALKAN_BEKLEME;
  }

  ultiSarjEkle(miktar) {
    this.ultiDolu = Math.min(ULTI_MAX, this.ultiDolu + miktar);
  }

  ultiAktifMi() {
    return this.ultiAktif || this.raptorUltiAktif || this.wraithUltiAktif ||
      this.overdriveUltiAktif || this.roninUltiAktif;
  }

  // Q — dispatches to the hero's own ulti state; all heroes share the ultiDolu meter.
  ultiKullan() {
    if (this.ultiDolu < ULTI_MAX || this.ultiAktifMi()) return false;
    this.ultiDolu = 0;
    switch (this.heroId) {
      case 1:
        this.raptorUltiAktif = true; this.raptorUltiSuresi = RAPTOR.ULTI_SURESI;
        break;
      case 7:
        this.wraithUltiAktif = true; this.wraithUltiSuresi = WRAITH.ULTI_SURESI;
        break;
      case 5:
        this.overdriveUltiAktif = true; this.overdriveUltiSuresi = OVERDRIVE.ULTI_SURESI;
        break;
      case 9:
        this.roninUltiAktif = true; this.roninUltiSuresi = RONIN.ULTI_SURESI;
        if (this.roninUltiGelismisAcik) this.can = Math.min(this.maxCan, this.can + 50);
        break;
      default: // AEGIS, HEX, REAPER share the generic jetpack ulti
        this.ultiAktif = true; this.ultiSuresi = ULTI_SURESI;
        this.can = Math.min(this.maxCan, this.can + ULTI_CAN_ARTISI);
        if (this.heroId === 6) this._pendingHexUlti = true;
        break;
    }
    return true;
  }

  // ── AEGIS sword ──
  kilicFirlat(hx, hy) {
    if (this.kilicDurum !== 'beklemede' || this.kilicAtmaBekleme > 0) return;
    const hand = this.handPos();
    const dx = hx - hand.x, dy = hy - hand.y;
    const len = Math.hypot(dx, dy) || 1;
    this.kilicHizX = (dx / len) * AEGIS.KILIC_HIZI;
    this.kilicHizY = (dy / len) * AEGIS.KILIC_HIZI;
    this.kilicX = hand.x; this.kilicY = hand.y;
    this.kilicMesafe = 0;
    this.kilicVurulanlar = [];
    this.kilicDurum = 'giden';
    this.kilicAtmaBekleme = AEGIS.KILIC_ATMA_BEKLEME;
    this.kilicSekmeYapildi = false;
  }

  kilicGeriCagir() {
    if (this.kilicDurum === 'giden' || this.kilicDurum === 'sapli') {
      this.kilicDurum = 'donuyor';
      this.kilicVurulanlar = [];
    }
  }

  kilicSavurRect(fx, fy) {
    const hand = this.handPos();
    const dx = fx - hand.x, dy = fy - hand.y;
    const len = Math.hypot(dx, dy) || 1;
    const mesafe = 30 * this.aegisKilicMenzilCarpan;
    const boyut = 48 * this.aegisKilicMenzilCarpan;
    const cx = hand.x + (dx / len) * mesafe;
    const cy = hand.y + (dy / len) * mesafe;
    return new Phaser.Geom.Rectangle(cx - boyut / 2, cy - boyut / 2, boyut, boyut);
  }

  kilicRect() { return new Phaser.Geom.Rectangle(this.kilicX - 8, this.kilicY - 8, 16, 16); }

  kilicGuncelle() {
    if (this.kilicAtmaBekleme > 0) this.kilicAtmaBekleme--;
    if (this.kilicSavurmaBekleme > 0) this.kilicSavurmaBekleme--;
    if (this.kilicSavurmaGoster > 0) this.kilicSavurmaGoster--;

    if (this.kilicDurum === 'giden') {
      this.kilicX += this.kilicHizX;
      this.kilicY += this.kilicHizY;
      this.kilicMesafe += AEGIS.KILIC_HIZI;
      const outOfBounds = this.kilicX < 10 || this.kilicX > GENISLIK - 10 || this.kilicY < 44 || this.kilicY > ZEMIN_Y;
      if (this.kilicMesafe >= AEGIS.KILIC_MENZIL * this.aegisKilicMenzilCarpan || outOfBounds) {
        this.kilicX = Phaser.Math.Clamp(this.kilicX, 10, GENISLIK - 10);
        this.kilicY = Phaser.Math.Clamp(this.kilicY, 44, ZEMIN_Y);
        this.kilicDurum = 'sapli';
      }
    } else if (this.kilicDurum === 'donuyor') {
      const hand = this.handPos();
      const dx = hand.x - this.kilicX, dy = hand.y - this.kilicY;
      const len = Math.hypot(dx, dy) || 1;
      this.kilicHizX = (dx / len) * AEGIS.KILIC_HIZI;
      this.kilicHizY = (dy / len) * AEGIS.KILIC_HIZI;
      this.kilicX += this.kilicHizX;
      this.kilicY += this.kilicHizY;
      if (len < 20) this.kilicDurum = 'beklemede';
    }

    if (this.aegisPasifKalkanAcik) {
      this.aegisHasarsizKare++;
      if (this.aegisHasarsizKare >= AEGIS.PASIF_KALKAN_ARALIK) {
        this.aegisHasarsizKare = 0;
        this.aegisPasifKalkan = Math.min(AEGIS.PASIF_KALKAN_MAX, this.aegisPasifKalkan + AEGIS.PASIF_KALKAN_ARTIS);
      }
    }
  }

  // ── RAPTOR ──
  raptorPenceRect(fx, fy) {
    const hand = this.handPos();
    const dx = fx - hand.x, dy = fy - hand.y;
    const len = Math.hypot(dx, dy) || 1;
    const mesafe = 26;
    const cx = hand.x + (dx / len) * mesafe;
    const cy = hand.y + (dy / len) * mesafe;
    return new Phaser.Geom.Rectangle(cx - 20, cy - 20, 40, 40);
  }

  raptorDashBaslat(fx, fy) {
    if (this.raptorDashBekleme > 0 && !this.raptorDashSinirsizAcik) return;
    const hand = this.handPos();
    this.raptorDashYon = fx >= hand.x ? 1 : -1;
    this.raptorDashAktif = true;
    this.raptorDashSuresi = RAPTOR.DASH_SURESI;
    this.raptorDashVurulanlar = [];
    if (!this.raptorDashSinirsizAcik) this.raptorDashBekleme = RAPTOR.DASH_BEKLEME;
    if (this.raptorOfkeAcik) { this.raptorOfkeAktif = true; this.raptorOfkeSuresi = RAPTOR.OFKE_SURESI; }
  }

  raptorKacisBaslat() {
    if (this.raptorKacisBekleme > 0 || this.raptorZehirAktif) return false;
    this.raptorKacisBekleme = RAPTOR.KACIS_BEKLEME;
    this.raptorZehirAktif = true;
    this.raptorZehirSuresi = RAPTOR.ZEHIR_SURESI;
    return true;
  }

  raptorGuncelle() {
    if (this.raptorPenceBekleme > 0) this.raptorPenceBekleme--;
    if (this.raptorPenceGoster > 0) this.raptorPenceGoster--;
    if (this.raptorKacisBekleme > 0) this.raptorKacisBekleme--;

    if (this.raptorDashAktif) {
      this.x += RAPTOR.DASH_HIZI * this.raptorDashYon;
      this.x = Phaser.Math.Clamp(this.x, 0, GENISLIK - this.w);
      this.raptorDashSuresi--;
      if (this.raptorDashSuresi <= 0) this.raptorDashAktif = false;
    } else if (this.raptorDashBekleme > 0) {
      this.raptorDashBekleme--;
    }

    if (this.raptorZehirAktif) {
      this.raptorZehirSuresi--;
      if (this.raptorZehirSuresi <= 0) this.raptorZehirAktif = false;
    }
    if (this.raptorOfkeAktif) {
      this.raptorOfkeSuresi--;
      if (this.raptorOfkeSuresi <= 0) this.raptorOfkeAktif = false;
    }
    if (this.raptorUltiAktif) {
      this.raptorUltiSuresi--;
      if (this.raptorUltiSuresi <= 0) this.raptorUltiAktif = false;
    }
  }

  // ── HEX ──
  hexKitapGuncelle() {
    if (this.hexKitapSayisi < this.hexKitapMaxOzel) {
      this.hexKitapTimer--;
      if (this.hexKitapTimer <= 0) {
        this.hexKitapSayisi++;
        this.hexKitapTimer = HEX.KITAP_SURESI;
      }
    }
    if (this.hexBuyuBekleme > 0) this.hexBuyuBekleme--;
    if (this.hexIsinGoster > 0) this.hexIsinGoster--;

    if (this.hexHealAktif) {
      this.can = Math.min(this.maxCan, this.can + HEX.HEAL_TOPLAM / HEX.HEAL_SURESI);
      this.hexHealSuresi--;
      if (this.hexHealSuresi <= 0) this.hexHealAktif = false;
    } else if (this.hexHealBekleme > 0) {
      this.hexHealBekleme--;
    }
  }

  hexBuyuAt(fx, fy, mermiListesi, MermiClass) {
    if (this.hexBuyuBekleme > 0) return;
    const hand = this.handPos();
    const dx = fx - hand.x, dy = fy - hand.y, len = Math.hypot(dx, dy) || 1;
    mermiListesi.push(new MermiClass(this.scene, hand.x, hand.y,
      dx / len * HEX.BUYU_HIZI, dy / len * HEX.BUYU_HIZI, 0xaa00ff, HEX.BUYU_HASAR, true));
    this.hexBuyuBekleme = HEX.BUYU_BEKLEME * this.saldiriCarpan;
  }

  hexIsinBaslat(fx, fy) {
    if (this.hexKitapSayisi <= 0) return null;
    const hand = this.handPos();
    const dx = fx - hand.x, dy = fy - hand.y, len = Math.hypot(dx, dy) || 1;
    this.hexIsinBitis = { x: hand.x + (dx / len) * HEX.ISIN_MENZIL, y: hand.y + (dy / len) * HEX.ISIN_MENZIL };
    this.hexIsinKitapSayisi = this.hexKitapSayisi;
    const hasar = HEX.ISIN_BIRIM_HASAR * this.hexKitapSayisi;
    this.hexKitapSayisi = 0;
    this.hexIsinGoster = 15;
    return { x1: hand.x, y1: hand.y, x2: this.hexIsinBitis.x, y2: this.hexIsinBitis.y, hasar };
  }

  hexHealBaslat() {
    if (this.hexHealBekleme <= 0 && !this.hexHealAktif) {
      this.hexHealAktif = true;
      this.hexHealSuresi = HEX.HEAL_SURESI;
      this.hexHealBekleme = HEX.HEAL_BEKLEME;
    }
  }

  // ── WRAITH ──
  wraithRuhEkle(miktar) {
    this.wraithRuh = Math.min(WRAITH.RUH_MAX, this.wraithRuh + miktar);
    if (this.wraithRuhHealAcik) this.can = Math.min(this.maxCan, this.can + miktar * WRAITH.RUH_OTO_HEAL_ORAN);
  }

  wraithRuhAt(fx, fy, mermiListesi, MermiClass) {
    if (this.atisTimer > 0) return;
    const hand = this.handPos();
    const dx = fx - hand.x, dy = fy - hand.y, len = Math.hypot(dx, dy) || 1;
    const m = new MermiClass(this.scene, hand.x, hand.y, dx / len * WRAITH.RUH_HIZI, dy / len * WRAITH.RUH_HIZI, 0x50a0ff, WRAITH.RUH_HASAR, true);
    m.wraithMermisi = true;
    mermiListesi.push(m);
    this.atisTimer = WRAITH.RUH_BEKLEME * this.saldiriCarpan;
  }

  wraithHayaletBaslat() {
    if (this.wraithHayaletAktif) return;
    if (this.wraithHayaletUstaAcik) {
      if (this.wraithHayaletBekleme > 0) return;
      this.wraithHayaletAktif = true;
      this.wraithHayaletSuresi = WRAITH.HAYALET_USTA_SURESI;
    } else {
      if (this.wraithRuh < WRAITH.HAYALET_MALIYET) return;
      this.wraithRuh -= WRAITH.HAYALET_MALIYET;
      this.wraithHayaletAktif = true;
      this.wraithHayaletSuresi = WRAITH.HAYALET_SURESI;
    }
  }

  wraithHealBaslat() {
    if (this.wraithHealBekleme > 0 || this.wraithRuh <= 0) return;
    this.can = Math.min(this.maxCan, this.can + this.wraithRuh * WRAITH.HEAL_ORAN);
    this.wraithRuh = 0;
    this.wraithHealBekleme = WRAITH.HEAL_BEKLEME;
  }

  wraithGuncelle() {
    if (this.wraithHayaletAktif) {
      this.wraithHayaletSuresi--;
      if (this.wraithHayaletSuresi <= 0) {
        this.wraithHayaletAktif = false;
        if (this.wraithHayaletUstaAcik) this.wraithHayaletBekleme = WRAITH.HAYALET_USTA_BEKLEME;
      }
    } else if (this.wraithHealBekleme > 0) {
      // handled above only when not ghosted; matches source tick ordering closely enough
    }
    if (this.wraithHealBekleme > 0) this.wraithHealBekleme--;
    if (this.wraithUltiAktif) {
      this.wraithUltiSuresi--;
      if (this.wraithUltiSuresi <= 0) this.wraithUltiAktif = false;
    }
  }

  // ── REAPER ──
  reaperVurusRect() {
    const hand = this.handPos();
    return { cx: hand.x, cy: hand.y, menzil: REAPER.VURUS_MENZIL, aci: REAPER.VURUS_ACI, hasar: REAPER.VURUS_HASAR };
  }

  reaperAtisRect() {
    const hand = this.handPos();
    return { cx: hand.x, cy: hand.y, menzil: REAPER.ATIS_MENZIL, aci: REAPER.ATIS_ACI, hasar: REAPER.ATIS_HASAR };
  }

  reaperVurusBaslat() {
    if (this.reaperVurusBekleme > 0) return null;
    this.reaperVurusBekleme = REAPER.VURUS_BEKLEME * this.saldiriCarpan;
    this.reaperVurusGoster = 8;
    return this.reaperVurusRect();
  }

  reaperAtisBaslat() {
    if (this.reaperAtisBekleme > 0) return null;
    this.reaperAtisBekleme = REAPER.ATIS_BEKLEME;
    this.reaperAtisGoster = 8;
    return this.reaperAtisRect();
  }

  reaperGuclendir() {
    if (this.reaperEBekleme > 0) return false;
    this.reaperEBekleme = REAPER.E_BEKLEME;
    return true;
  }

  reaperGuncelle() {
    if (this.reaperVurusBekleme > 0) this.reaperVurusBekleme--;
    if (this.reaperVurusGoster > 0) this.reaperVurusGoster--;
    if (this.reaperAtisBekleme > 0) this.reaperAtisBekleme--;
    if (this.reaperAtisGoster > 0) this.reaperAtisGoster--;
    if (this.reaperEBekleme > 0) this.reaperEBekleme--;
  }

  // ── OVERDRIVE ──
  // Fires a ray from the player toward (fx,fy) and keeps travelling — not
  // stopping at the clicked point — until it actually hits something solid:
  // an enemy, a platform, a wall, the ceiling or the floor. A boss is too
  // heavy to reel in, so hitting one pulls the player to it instead of
  // pulling the boss to the player (regular enemies still get yanked in).
  overdriveKancaBaslat(fx, fy, scene) {
    if (this.kancaBekleme > 0 || this.kancaDurum !== 'yok') return;
    const cx = this.x + this.w / 2, cy = this.y + this.h / 2;
    const dx = fx - cx, dy = fy - cy;
    const uzunluk = Math.hypot(dx, dy) || 1;
    const ux = dx / uzunluk, uy = dy / uzunluk;

    let hx = null, hy = null, cekilecekDusman = null;
    const step = 12;
    let mesafe = 0;
    while (mesafe < OVERDRIVE.KANCA_MENZIL) {
      mesafe += step;
      const nx = cx + ux * mesafe, ny = cy + uy * mesafe;

      const dusman = scene?.enemies?.find(d => !d.dead && Phaser.Geom.Rectangle.Contains(d.rect(), nx, ny));
      if (dusman) {
        if (dusman.tip === 'boss' || dusman.tip === 'finalboss') { hx = nx; hy = ny; }
        else cekilecekDusman = dusman;
        break;
      }
      const plat = scene?.platforms?.find(p => nx >= p.x && nx <= p.x + p.w && ny >= p.y && ny <= p.y + p.h);
      if (plat) { hx = nx; hy = ny; break; }
      if (nx <= 0 || nx >= GENISLIK) { hx = Phaser.Math.Clamp(nx, 4, GENISLIK - 4); hy = ny; break; }
      if (ny <= 66) { hx = nx; hy = 70; break; }
      if (ny >= ZEMIN_Y - 2) { hx = nx; hy = ZEMIN_Y - 10; break; }
    }

    if (cekilecekDusman) {
      cekilecekDusman.cekimKare = 24;
      cekilecekDusman.cekimHedefX = cx + ux * 40;
      cekilecekDusman.cekimHedefY = cy + uy * 40;
      this.kancaBekleme = OVERDRIVE.KANCA_BEKLEME;
      if (this.overdriveKancaHealAcik) this.can = Math.min(this.maxCan, this.can + 10);
      return;
    }
    if (hx === null) {
      // Ray never hit anything solid (shouldn't happen inside the bounded
      // arena) — hook fails and can't latch onto empty space.
      this.kancaBekleme = OVERDRIVE.KANCA_BEKLEME;
      return;
    }

    const dist = Math.hypot(hx - cx, hy - cy) || 1;
    if (this.overdriveSallanmaAcik) {
      this.kancaAnchorX = hx; this.kancaAnchorY = hy;
      this.kancaIpUzunlugu = Math.max(30, dist);
      this.kancaAci = Math.atan2(cy - this.kancaAnchorY, cx - this.kancaAnchorX);
      this.kancaAcisalHiz = 0;
      this.kancaDurum = 'sallaniyor';
    } else {
      // Salinim henuz acilmadiysa (bkz. OVERDRIVE.SALLANMA_ESIGI): sallanmadan,
      // hedefe sabit hizda ucarak gider — game (1).py's `overdrive_kanca_direk_git`.
      this.kancaUcusHedefX = Phaser.Math.Clamp(hx - this.w / 2, 0, GENISLIK - this.w);
      this.kancaUcusHedefY = Phaser.Math.Clamp(hy - this.h, 46, ZEMIN_Y - this.h);
      this.kancaAnchorX = hx; this.kancaAnchorY = hy;
      this.kancaDurum = 'ucuyor';
    }
    if (this.overdriveKancaHealAcik) this.can = Math.min(this.maxCan, this.can + 10);
  }

  overdriveSallanBirak() {
    if (this.kancaDurum === 'sallaniyor' || this.kancaDurum === 'ucuyor') {
      this.kancaDurum = 'yok';
      this.kancaBekleme = OVERDRIVE.KANCA_BEKLEME;
    }
  }

  overdriveGuncelle(keys) {
    if (this.kancaDurum === 'sallaniyor') {
      const ultiCarpan = this.overdriveUltiAktif ? OVERDRIVE.ULTI_YAVAS_CARPAN : 1.0;
      const yercekimi = 0.6 * ultiCarpan;
      const ivme = (yercekimi / Math.max(30, this.kancaIpUzunlugu)) * Math.cos(this.kancaAci);
      this.kancaAcisalHiz += ivme;
      const yonIsaret = Math.sin(this.kancaAci) >= 0 ? 1 : -1;
      if (keys.right) this.kancaAcisalHiz -= OVERDRIVE.KANCA_POMPA * yonIsaret;
      if (keys.left) this.kancaAcisalHiz += OVERDRIVE.KANCA_POMPA * yonIsaret;
      this.kancaAcisalHiz *= 0.999;
      this.kancaAci += this.kancaAcisalHiz;
      const nx = this.kancaAnchorX + Math.cos(this.kancaAci) * this.kancaIpUzunlugu;
      const ny = this.kancaAnchorY + Math.sin(this.kancaAci) * this.kancaIpUzunlugu;
      this.hizX = nx - this.x; this.hizY = ny - this.y;
      this.x = Phaser.Math.Clamp(nx, 0, GENISLIK - this.w);
      this.y = Phaser.Math.Clamp(ny, 46, ZEMIN_Y - this.h);
    } else if (this.kancaDurum === 'ucuyor') {
      // No swing yet — flies straight to the hook point at a fixed speed
      // (not a teleport). game (1).py's `kanca_durum == 'ucuyor'` branch.
      const ultiCarpan = this.overdriveUltiAktif ? OVERDRIVE.ULTI_YAVAS_CARPAN : 1.0;
      const hiz = OVERDRIVE.KANCA_UCUS_HIZI * ultiCarpan;
      const dx = this.kancaUcusHedefX - this.x, dy = this.kancaUcusHedefY - this.y;
      const mesafe = Math.hypot(dx, dy);
      if (mesafe <= hiz) {
        this.x = this.kancaUcusHedefX; this.y = this.kancaUcusHedefY;
        this.hizX = 0; this.hizY = 0;
        this.kancaDurum = 'yok';
      } else {
        const ux = dx / mesafe, uy = dy / mesafe;
        this.hizX = ux * hiz; this.hizY = uy * hiz;
        this.x += this.hizX; this.y += this.hizY;
      }
      this.x = Phaser.Math.Clamp(this.x, 0, GENISLIK - this.w);
      this.y = Phaser.Math.Clamp(this.y, 46, ZEMIN_Y - this.h);
    }
    if (this.kancaBekleme > 0) this.kancaBekleme--;
    if (this.overdriveEBekleme > 0) this.overdriveEBekleme--;
    if (this.overdriveEGoster > 0) this.overdriveEGoster--;
    if (this.overdriveUltiAktif) {
      this.overdriveUltiSuresi--;
      if (this.overdriveUltiSuresi <= 0) {
        this.overdriveUltiAktif = false;
        if (this.overdriveUltiOlumsuzAcik) this.overdriveOlumsuzlukKalan = 120;
      }
    }
    if (this.overdriveOlumsuzlukKalan > 0) this.overdriveOlumsuzlukKalan--;
  }

  overdriveEBaslat() {
    if (this.overdriveEBekleme > 0) return false;
    this.overdriveEBekleme = OVERDRIVE.E_BEKLEME;
    this.overdriveEGoster = 10;
    this.can = Math.min(this.maxCan, this.can + OVERDRIVE.E_CAN_YENILEME);
    return true;
  }

  // ── RONIN ──
  roninHasarCarpani() {
    if (this.roninKritikHazir) { this.roninKritikHazir = false; return RONIN.E_KRITIK_CARPAN; }
    return 1.0;
  }

  roninItisRect(fx, fy) {
    const hand = this.handPos();
    const dx = fx - hand.x, dy = fy - hand.y, len = Math.hypot(dx, dy) || 1;
    const menzil = RONIN.ITIS_MENZIL * this.roninMenzilCarpan;
    return { cx: hand.x, cy: hand.y, dirX: dx / len, dirY: dy / len, menzil, aci: RONIN.ITIS_ACI, hasar: RONIN.ITIS_HASAR * this.roninHasarCarpani() };
  }

  roninItisBaslat() {
    if (this.roninItisBekleme > 0) return null;
    this.roninItisBekleme = RONIN.ITIS_BEKLEME * this.saldiriCarpan;
    this.roninItisGoster = 10;
    this.roninItisZirh = 10;
    return true;
  }

  // Instant piercing line-throw that teleports the player to where it stopped —
  // matches the original's `ronin_firlat()` (game (1).py:4788), NOT a slow projectile.
  // Returns the throw geometry for the caller to step along and hit-test; null if on cooldown.
  roninFirlatBaslat(fx, fy) {
    if (this.roninFirlatBekleme > 0) return null;
    const cx = this.x + this.w / 2, cy = this.y + this.h / 2;
    const dx = fx - cx, dy = fy - cy, len = Math.hypot(dx, dy) || 1;
    this.roninFirlatBekleme = RONIN.FIRLAT_BEKLEME;
    this.roninFirlatGoster = 10;
    return {
      cx, cy, ux: dx / len, uy: dy / len,
      menzil: RONIN.FIRLAT_MENZIL * this.roninMenzilCarpan,
      hasar: RONIN.FIRLAT_HASAR * this.roninHasarCarpani()
    };
  }

  roninGizlenBaslat() {
    if (this.roninEBekleme > 0 || this.roninGizliAktif) return;
    this.roninGizliAktif = true;
    this.roninGizliSuresi = RONIN.E_SURESI;
    this.roninEBekleme = RONIN.E_BEKLEME;
    this.roninKritikHazir = true;
  }

  roninGuncelle() {
    if (this.roninItisBekleme > 0) this.roninItisBekleme--;
    if (this.roninItisGoster > 0) this.roninItisGoster--;
    if (this.roninItisZirh > 0) this.roninItisZirh--;
    if (this.roninFirlatBekleme > 0) this.roninFirlatBekleme--;
    if (this.roninFirlatGoster > 0) this.roninFirlatGoster--;
    if (this.roninEBekleme > 0) this.roninEBekleme--;
    if (this.roninGizliAktif) {
      this.roninGizliSuresi--;
      if (this.roninGizliSuresi <= 0) this.roninGizliAktif = false;
    }
    if (this.roninUltiAktif) {
      this.roninUltiSuresi--;
      this._roninUltiTikTimer--;
      if (this._roninUltiTikTimer <= 0) this._roninUltiTikTimer = 6; // caller checks ===6 to apply pulse
      if (this.roninUltiSuresi <= 0) this.roninUltiAktif = false;
    }
  }

  roninUltiRadius() {
    return RONIN.ULTI_YARICAP * (this.roninUltiGelismisAcik ? 2.0 : 1.0);
  }

  // ── generic ranged (OVERDRIVE basic attack; usable as fallback) ──
  atesEt(fx, fy, mermiListesi, MermiClass) {
    const s = SILAHLAR[this.silahIdx];
    if (this.atisTimer > 0 || this.doluyor) return;
    if (this.sarjor <= 0) { this.reloadBaslat(); return; }
    this.atisTimer = (this.overdriveHizliAtesAcik ? Math.max(1, Math.floor(s.atis_hizi / 2)) : s.atis_hizi) * this.saldiriCarpan;
    this.sarjor -= 1;
    if (this.overdriveSinirsizMermi) this.sarjor = s.sarjor;
    const cx = this.x + this.w / 2, cy = this.y + this.h * 0.38;
    const aci = Math.atan2(fy - cy, fx - cx);
    const sacma = s.sacma || 1;
    const tekrar = s.cift ? 2 : 1;
    for (let t = 0; t < tekrar; t++) {
      for (let i = 0; i < sacma; i++) {
        const a = sacma > 1 ? aci + (i - (sacma - 1) / 2) * 0.25 : aci;
        mermiListesi.push(new MermiClass(this.scene, cx, cy,
          Math.cos(a) * s.mermi_hizi, Math.sin(a) * s.mermi_hizi,
          s.renk, s.hasar, true));
      }
    }
  }

  reloadBaslat() {
    const s = SILAHLAR[this.silahIdx];
    if (!this.doluyor && this.sarjor < s.sarjor) {
      this.doluyor = true;
      this.dolumTimer = s.dolum;
    }
  }

  // ── core physics/movement, direct port of hareket_et ──
  hareketEt(keys) {
    let hizTaban = 5;
    if (this.raptorHizli) hizTaban = RAPTOR.HIZ_X;
    else if (this.wraithYavas) hizTaban = WRAITH.HIZ;
    else if (this.reaperAgir) hizTaban = REAPER.HIZ;

    if (this.raptorUltiAktif) hizTaban *= RAPTOR.ULTI_HIZ_CARPAN;
    else if (this.raptorOfkeAktif) hizTaban *= RAPTOR.OFKE_HIZ_CARPAN;
    if (this.wraithUltiAktif) hizTaban *= WRAITH.ULTI_YAVAS_CARPAN;
    if (this.overdriveUltiAktif) hizTaban *= OVERDRIVE.ULTI_YAVAS_CARPAN;
    hizTaban *= this.survivorHizCarpan;

    const locked = this.raptorKacisAktif || this.raptorDashAktif || this.kancaDurum === 'sallaniyor' || this.kancaDurum === 'ucuyor';
    if (!locked) {
      this.hizX = 0;
      if (keys.left) this.hizX = -hizTaban;
      if (keys.right) this.hizX = hizTaban;
    }

    const flying = this.ultiAktif || this.daimaUcar;
    if (flying) {
      const ucusHiz = (this.wraithYavas ? WRAITH.UCUS_HIZ : 5) * (this.wraithUltiAktif ? WRAITH.ULTI_YAVAS_CARPAN : 1);
      if (keys.up) this.hizY = -ucusHiz;
      else if (keys.down) this.hizY = ucusHiz;
      else this.hizY *= 0.85;
      this.yerde = false;
      this.y = Phaser.Math.Clamp(this.y + this.hizY, 44, ZEMIN_Y - this.h);
    } else if (!locked) {
      if (this.raptorHizli) {
        if (this.yerde && keys.up) {
          this.hizY = RAPTOR.ZIPLAMA_BASLANGIC;
          this.yerde = false;
          this.raptorZipTutuluyor = true;
          this.raptorZipKare = 0;
        }
        if (this.raptorZipTutuluyor && keys.up && this.raptorZipKare < RAPTOR.ZIPLAMA_MAX_KARE && this.hizY < 0) {
          this.hizY = Math.max(RAPTOR.ZIPLAMA_MIN_HIZ, this.hizY + RAPTOR.ZIPLAMA_ITKI);
          this.raptorZipKare++;
        }
        if (!keys.up) this.raptorZipTutuluyor = false;
        this.hizY += 0.6;
        this.y += this.hizY;
      } else {
        if (this.yerde && keys.up) { this.hizY = -14; this.yerde = false; }
        if (!this.yerde && !keys.up && this.hizY < -5) this.hizY = -5;
        this.hizY += 0.6;
        this.y += this.hizY;
      }
      if (this.y >= ZEMIN_Y - this.h) {
        this.y = ZEMIN_Y - this.h;
        this.hizY = 0;
        this.yerde = true;
      }
    } else if (this.kancaDurum !== 'sallaniyor' && this.kancaDurum !== 'ucuyor') {
      this.y += this.hizY;
    }

    if (this.kancaDurum !== 'sallaniyor') {
      this.x = Phaser.Math.Clamp(this.x + this.hizX, 0, GENISLIK - this.w);
    }

    if (this.hasarTimer > 0) this.hasarTimer--;
    if (this.atisTimer > 0) this.atisTimer--;
    this.can = Math.min(this.can + this.survivorCanYenileme, this.maxCan);

    if (this.doluyor) {
      this.dolumTimer--;
      if (this.dolumTimer <= 0) { this.doluyor = false; this.sarjor = SILAHLAR[this.silahIdx].sarjor; }
    }

    if (this.kalkanAktif) {
      this.kalkanSuresi--;
      if (this.kalkanSuresi <= 0) this.kalkanKapat();
    } else if (this.kalkanBekleme > 0) {
      this.kalkanBekleme--;
    }

    if (this.ultiAktif) {
      this.ultiSuresi--;
      if (this.ultiSuresi <= 0) this.ultiAktif = false;
    }

    if (this.hizX > 0.1) this.facing = 1;
    else if (this.hizX < -0.1) this.facing = -1;

    this.animZamani++;
    if (this.animZamani >= 8) { this.animZamani = 0; this.animFrame = (this.animFrame + 1) % 4; }

    // hero-specific per-frame updaters
    if (this.heroId === 0) this.kilicGuncelle();
    if (this.heroId === 1) this.raptorGuncelle();
    if (this.heroId === 6) this.hexKitapGuncelle();
    if (this.heroId === 7) this.wraithGuncelle();
    if (this.heroId === 8) this.reaperGuncelle();
    if (this.heroId === 5) this.overdriveGuncelle(keys);
    if (this.heroId === 9) this.roninGuncelle();
  }

  // Faithful port of the Python original's `Oyuncu.ciz` — same polygons,
  // same colors, same coordinates (translated from the local px/py canvas
  // space used there into direct world-space Graphics calls here).
  _weaponColor() {
    if (this.heroId === 6) return 0xaa00ff; // MOR
    if (this.heroId === 1) return 0x00ff64; // YESIL
    if (this.heroId === 7) return 0x96e6dc; // (150,230,220)
    if (this.heroId === 8) return (this.reaperVurusGoster > 0 || this.reaperAtisGoster > 0) ? 0xff463c : 0xc81914;
    return SILAHLAR[this.silahIdx].renk;
  }

  draw(aimX, aimY) {
    const g = this.gfx;
    g.clear();
    if (this.hasarTimer > 0 && this.hasarTimer % 6 < 3) return;

    const px = this.x, py = this.y, w = this.w, h = this.h;
    const bx = px + w / 2, by = py + h * 0.38;
    if (aimX === undefined || aimY === undefined) { aimX = bx + this.facing * 40; aimY = by; }
    const aci = Math.atan2(aimY - by, aimX - bx);
    const lf = (this.animFrame % 2 === 0) ? 5 : 0;
    const vc = this._weaponColor();

    let alpha = 1.0;
    if (this.wraithHayaletAktif) alpha = 130 / 255;
    else if (this.roninGizliAktif) alpha = 110 / 255;

    // pre-body layers
    if (this.heroId === 7) this._wraithWings(g, px, py, w, h, alpha);
    if (this.heroId === 1) this._raptorTail(g, px, py, w, h, alpha);

    // body
    switch (this.heroId) {
      case 0: this._bodyAegis(g, px, py, w, h, lf, vc, alpha); break;
      case 1: this._bodyRaptor(g, px, py, w, h, lf, vc, alpha); break;
      case 6: this._bodyHex(g, px, py, w, h, lf, vc, alpha); break;
      case 7: this._bodyWraith(g, px, py, w, h, vc, alpha); break;
      case 8: this._bodyReaper(g, px, py, w, h, lf, alpha); break;
      case 9: this._bodyRonin(g, px, py, w, h, lf, vc, alpha); break;
      case 5: this._bodyOverdrive(g, px, py, w, h, lf, alpha); break;
      default: this._bodyGeneric(g, px, py, w, h, lf, vc, alpha);
    }

    // weapon-angle effect (local space, affected by alpha)
    this._weaponAngle(g, px, py, w, h, bx, by, aci, alpha);

    // shield
    if (this.kalkanAktif) {
      const t = this.scene.time.now;
      const nabiz = 4 + Math.floor(3 * Math.sin(t / 100));
      const cap = Math.max(w, h) + 30 + nabiz;
      const mcx = px + w / 2, mcy = py + h / 2;
      g.fillStyle(0x00fff7, 0.2 * alpha);
      g.fillEllipse(mcx, mcy, cap, cap);
      g.lineStyle(3, 0x00fff7, 0.67 * alpha);
      g.strokeEllipse(mcx, mcy, cap, cap);
    }

    // ulti (generic jetpack)
    if (this.ultiAktif) {
      const t = this.scene.time.now;
      const nabiz = 4 + Math.floor(3 * Math.sin(t / 90));
      const cap = Math.max(w, h) + 26 + nabiz;
      const mcx = px + w / 2, mcy = py + h / 2;
      g.fillStyle(0xffd700, 0.18 * alpha);
      g.fillEllipse(mcx, mcy, cap, cap);
      g.lineStyle(3, 0xffd700, 0.7 * alpha);
      g.strokeEllipse(mcx, mcy, cap, cap);
      const alevUzunluk = 10 + Math.floor(t / 40) % 6;
      g.fillStyle(0xffee00, alpha);
      g.fillRect(px + 4, py + h, 6, alevUzunluk);
      g.fillStyle(0xf5a623, alpha);
      g.fillRect(px + w - 10, py + h, 6, alevUzunluk);
      g.fillStyle(0xffee00, alpha);
      g.fillRect(px + w - 10, py + h, 6, Math.max(0, alevUzunluk - 4));
    }

    // hex orbiting books
    if (this.heroId === 6 && this.hexKitapSayisi > 0) {
      const t = this.scene.time.now;
      const mcx = px + w / 2, mcy = py + h / 2;
      for (let i = 0; i < this.hexKitapSayisi; i++) {
        const a = t / 300 + i * (2 * Math.PI / this.hexKitapMaxOzel);
        const kx = mcx + Math.cos(a) * 34, ky = mcy + Math.sin(a) * 34;
        g.fillStyle(0xaa5aff, alpha);
        g.fillRect(kx - 5, ky - 6, 10, 12);
        g.lineStyle(1, 0xe6c8ff, alpha);
        g.strokeRect(kx - 5, ky - 6, 10, 12);
      }
    }

    // raptor dash/kacis trail + ulti aura
    if (this.heroId === 1 && (this.raptorDashAktif || this.raptorKacisAktif)) {
      const izRenk = this.raptorKacisAktif ? 0xffffff : 0x96ffaa;
      const izYon = this.raptorDashAktif ? this.raptorDashYon : (this.hizX >= 0 ? 1 : -1);
      g.lineStyle(1, izRenk, alpha);
      for (let k = 1; k < 4; k++) g.strokeRect(px - k * 10 * izYon, py + 16, w, h - 16);
    }
    if (this.heroId === 1 && this.raptorUltiAktif) {
      const t = this.scene.time.now;
      const nabiz = 3 + Math.floor(2 * Math.sin(t / 80));
      const cap = Math.max(w, h) + 22 + nabiz;
      const mcx = px + w / 2, mcy = py + h / 2;
      g.fillStyle(0x00ff64, 0.2 * alpha);
      g.fillEllipse(mcx, mcy, cap, cap);
      g.lineStyle(3, 0x00ff64, 0.7 * alpha);
      g.strokeEllipse(mcx, mcy, cap, cap);
    }

    // wraith ulti aura (ghost mode itself has no aura, just alpha)
    if (this.heroId === 7 && this.wraithUltiAktif) {
      const t = this.scene.time.now;
      const nabiz = 4 + Math.floor(3 * Math.sin(t / 100));
      const cap = Math.max(w, h) + 30 + nabiz;
      const mcx = px + w / 2, mcy = py + h / 2;
      g.fillStyle(0x96e6dc, 0.22 * alpha);
      g.fillEllipse(mcx, mcy, cap, cap);
      g.lineStyle(3, 0xdcfffa, 0.7 * alpha);
      g.strokeEllipse(mcx, mcy, cap, cap);
    }

    // world-space overlays (full opacity, independent of ghost/stealth alpha)
    if (this.heroId === 1 && this.raptorZehirAktif) {
      g.fillStyle(0x3cdc5a, 90 / 255);
      g.fillRect(px, py, w, h);
    }
    if (this.heroId === 0 && this.kilicDurum !== 'beklemede') {
      const aciK = (this.kilicHizX || this.kilicHizY) ? Math.atan2(this.kilicHizY, this.kilicHizX) : 0;
      const kx = this.kilicX, ky = this.kilicY;
      const ucX = kx + Math.cos(aciK) * 14, ucY = ky + Math.sin(aciK) * 14;
      const kuyX = kx - Math.cos(aciK) * 14, kuyY = ky - Math.sin(aciK) * 14;
      g.lineStyle(4, 0xc8dcff, 1);
      g.lineBetween(kuyX, kuyY, ucX, ucY);
      g.fillStyle(0x00fff7, 1);
      g.fillCircle(kx, ky, 3);
    }
    if (this.heroId === 6 && this.hexIsinGoster > 0) {
      const hand = this.handPos();
      const outer = 5 + this.hexIsinKitapSayisi * 3, inner = 2 + this.hexIsinKitapSayisi * 2;
      g.lineStyle(outer, 0xdc96ff, 1);
      g.lineBetween(hand.x, hand.y, this.hexIsinBitis.x, this.hexIsinBitis.y);
      g.lineStyle(inner, 0xffffff, 1);
      g.lineBetween(hand.x, hand.y, this.hexIsinBitis.x, this.hexIsinBitis.y);
    }
    if (this.heroId === 8 && (this.reaperVurusGoster > 0 || this.reaperAtisGoster > 0)) {
      const mx = px + w / 2, my = py + h / 2;
      if (this.reaperVurusGoster > 0) {
        const r1 = Math.max(4, REAPER.VURUS_MENZIL * (1 - this.reaperVurusGoster / 8));
        g.lineStyle(2, 0xc81922, 1);
        this._strokeArc(g, mx, my, r1, aci - REAPER.VURUS_ACI, aci + REAPER.VURUS_ACI);
      }
      if (this.reaperAtisGoster > 0) {
        const r2 = Math.max(4, REAPER.ATIS_MENZIL * (1 - this.reaperAtisGoster / 8));
        g.lineStyle(3, 0xff2323, 1);
        this._strokeArc(g, mx, my, r2, aci - REAPER.ATIS_ACI, aci + REAPER.ATIS_ACI);
      }
    }
    if (this.heroId === 5 && this.kancaDurum === 'yok') {
      const mx = px + w / 2, my = py + h / 2;
      const dx = aimX - mx, dy = aimY - my;
      const uzunluk = Math.hypot(dx, dy) || 1;
      const ux = dx / uzunluk, uy = dy / uzunluk;
      const nokta = this.kancaBekleme <= 0 ? 0xffee00 : 0x787878;
      let mesafe = 16;
      g.fillStyle(nokta, 1);
      while (mesafe < Math.min(uzunluk, OVERDRIVE.KANCA_MENZIL)) {
        g.fillCircle(mx + ux * mesafe, my + uy * mesafe, 2);
        mesafe += 11;
      }
    }
    if (this.heroId === 5 && (this.kancaDurum === 'sallaniyor' || this.kancaDurum === 'ucuyor')) {
      const mx = px + w / 2, my = py + h / 2;
      g.lineStyle(4, 0x5a4600, 1);
      g.lineBetween(mx, my, this.kancaAnchorX, this.kancaAnchorY);
      g.lineStyle(2, 0xffee00, 1);
      g.lineBetween(mx, my, this.kancaAnchorX, this.kancaAnchorY);
      g.fillStyle(0xffee00, 1);
      g.fillCircle(this.kancaAnchorX, this.kancaAnchorY, 5);
    }
    if (this.heroId === 5 && this.overdriveEGoster > 0) {
      const mx = px + w / 2, my = py + h / 2;
      const rE = Math.max(4, OVERDRIVE.E_MENZIL * (1 - this.overdriveEGoster / 10));
      g.lineStyle(2, 0xffee00, 1);
      g.strokeCircle(mx, my, rE);
    }
    if (this.heroId === 9 && this.roninUltiAktif) {
      const r = this.roninUltiRadius();
      const mx = px + w / 2, my = py + h / 2;
      const rot = (this.scene.time.now / 90) % (Math.PI * 2);
      g.lineStyle(3, 0xaa78ff, 1);
      for (let kol = 0; kol < 3; kol++) {
        const a = rot + kol * (Math.PI * 2 / 3);
        const ucx = mx + Math.cos(a) * r, ucy = my + Math.sin(a) * r;
        g.lineBetween(mx, my, ucx, ucy);
        g.fillStyle(0xe6dcff, 1);
        g.fillCircle(ucx, ucy, 4);
      }
      g.lineStyle(1, 0xaa78ff, 1);
      g.strokeCircle(mx, my, r);
    }
  }

  _strokeArc(g, cx, cy, r, startAngle, endAngle) {
    const steps = 10;
    g.beginPath();
    for (let i = 0; i <= steps; i++) {
      const a = startAngle + (endAngle - startAngle) * (i / steps);
      const x = cx + Math.cos(a) * r, y = cy + Math.sin(a) * r;
      if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
    }
    g.strokePath();
  }

  _wraithWings(g, px, py, w, h, alpha) {
    g.fillStyle(0x2d5a58, alpha);
    g.lineStyle(1, 0x96e6dc, alpha);
    const sol = [[px, py + 12], [px - 24, py - 2], [px - 18, py + 18], [px - 20, py + 34], [px, py + 32]];
    const sag = [[px + w, py + 12], [px + w + 24, py - 2], [px + w + 18, py + 18], [px + w + 20, py + 34], [px + w, py + 32]];
    this._poly(g, sol, true); this._poly(g, sag, true);
  }

  _raptorTail(g, px, py, w, h, alpha) {
    const yon = this.hizX < 0 ? 1 : -1;
    g.fillStyle(0x0d6622, alpha);
    for (let i = 0; i < 4; i++) {
      const kx = px + w / 2 + yon * (12 + i * 9), ky = py + h - 8 + i * 4, b = 9 - i * 2;
      g.fillRect(kx - b / 2, ky - b / 2, b, b);
    }
  }

  _poly(g, pts, stroke) {
    g.beginPath();
    g.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]);
    g.closePath();
    g.fillPath();
    if (stroke) g.strokePath();
  }

  _bodyAegis(g, px, py, w, h, lf, vc, alpha) {
    g.fillStyle(0x0d2e88, alpha);
    g.fillRect(px + 2, py + h - 14, 10, 14 + lf);
    g.fillRect(px + w - 12, py + h - 14, 10, 14 - lf);
    g.fillStyle(0x1a44bb, alpha);
    g.fillRect(px, py + 16, w, h - 16);
    g.fillStyle(0x2255dd, alpha);
    g.fillRect(px + 2, py, w - 4, 18);
    g.fillStyle(vc, alpha);
    g.fillRect(px + 4, py + 5, w - 8, 6);
    g.fillStyle(0x2255cc, alpha);
    g.fillRect(px + 6, py + 20, w - 12, 8);
    g.fillStyle(0x0e3282, alpha);
    g.fillRect(px - 7, py + 14, 9, 13);
    g.fillRect(px + w - 2, py + 14, 9, 13);
    g.lineStyle(1, 0x00fff7, alpha);
    g.strokeRect(px - 7, py + 14, 9, 13);
    g.strokeRect(px + w - 2, py + 14, 9, 13);
  }

  _bodyGeneric(g, px, py, w, h, lf, vc, alpha) {
    g.fillStyle(0x0d2e88, alpha);
    g.fillRect(px + 2, py + h - 14, 10, 14 + lf);
    g.fillRect(px + w - 12, py + h - 14, 10, 14 - lf);
    g.fillStyle(0x1a44bb, alpha);
    g.fillRect(px, py + 16, w, h - 16);
    g.fillStyle(0x2255dd, alpha);
    g.fillRect(px + 2, py, w - 4, 18);
    g.fillStyle(vc, alpha);
    g.fillRect(px + 4, py + 5, w - 8, 6);
    g.fillStyle(0x2255cc, alpha);
    g.fillRect(px + 6, py + 20, w - 12, 8);
  }

  _bodyRaptor(g, px, py, w, h, lf, vc, alpha) {
    g.fillStyle(0x0d6622, alpha);
    g.fillRect(px + 2, py + h - 14, 10, 14 + lf);
    g.fillRect(px + w - 12, py + h - 14, 10, 14 - lf);
    g.fillStyle(0x0d5522, alpha);
    this._poly(g, [[px + 3, py + 16], [px + w - 3, py + 16], [px + w, py + h - 2], [px, py + h - 2]], false);
    g.lineStyle(1, 0x229944, alpha);
    g.strokePoints([{ x: px + 3, y: py + 16 }, { x: px + w - 3, y: py + 16 }, { x: px + w, y: py + h - 2 }, { x: px, y: py + h - 2 }], true);
    g.fillStyle(0x228833, alpha);
    this._poly(g, [[px + 2, py + 16], [px + w - 2, py + 16], [px + w - 3, py + 4], [px + 3, py + 4]], false);
    g.fillStyle(0x145a1e, alpha);
    for (let i = 0; i < 3; i++) {
      const ix = px + 5 + i * 7;
      this._poly(g, [[ix, py + 4], [ix + 3, py - 9 - (i % 2) * 3], [ix + 6, py + 4]], false);
    }
    g.fillStyle(vc, alpha);
    g.fillRect(px + 4, py + 5, w - 8, 5);
    g.fillStyle(0x229944, alpha);
    g.fillRect(px + 6, py + 19, w - 12, 7);
  }

  _bodyHex(g, px, py, w, h, lf, vc, alpha) {
    g.fillStyle(0x440d88, alpha);
    g.fillRect(px + 2, py + h - 14, 10, 14 + lf);
    g.fillRect(px + w - 12, py + h - 14, 10, 14 - lf);
    g.fillStyle(0x3a0066, alpha);
    this._poly(g, [[px + 5, py + 16], [px + w - 5, py + 16], [px + w - 2, py + h - 16], [px + 2, py + h - 16]], false);
    g.lineStyle(1, 0x9650dc, alpha);
    g.strokePoints([{ x: px + 5, y: py + 16 }, { x: px + w - 5, y: py + 16 }, { x: px + w - 2, y: py + h - 16 }, { x: px + 2, y: py + h - 16 }], true);
    g.fillStyle(0x1e0037, alpha);
    this._poly(g, [[px + 1, py + 3], [px + w - 1, py + 3], [px + w / 2, py - 13]], false);
    g.lineStyle(1, 0x9650dc, alpha);
    g.strokePoints([{ x: px + 1, y: py + 3 }, { x: px + w - 1, y: py + 3 }, { x: px + w / 2, y: py - 13 }], true);
    g.lineStyle(2, 0x9650dc, alpha);
    g.lineBetween(px - 6, py - 2, px + 2, py + 6);
    g.lineBetween(px + w + 6, py - 2, px + w - 2, py + 6);
    g.fillStyle(vc, alpha);
    g.fillRect(px + 5, py + 6, w - 10, 5);
    g.fillStyle(0xdc96ff, alpha);
    g.fillCircle(px + w / 2, py + 24, 4);
    g.fillStyle(0x280046, alpha);
    this._poly(g, [[px - 5, py + h], [px + w + 5, py + h], [px + w / 2, py + h - 22]], false);
  }

  _bodyWraith(g, px, py, w, h, vc, alpha) {
    g.fillStyle(0x28504e, alpha);
    this._poly(g, [[px + 2, py + h - 14], [px + 12, py + h - 14], [px + 9, py + h], [px + 1, py + h - 6]], false);
    this._poly(g, [[px + w - 12, py + h - 14], [px + w - 2, py + h - 14], [px + w - 1, py + h], [px + w - 9, py + h - 6]], false);
    g.fillStyle(0x193c3a, alpha);
    const govde = [[px + 3, py + 18], [px + w - 3, py + 18], [px + w - 6, py + h - 8], [px + w / 2, py + h], [px + 6, py + h - 8]];
    this._poly(g, govde, false);
    g.lineStyle(1, 0x96e6dc, alpha);
    g.strokePoints(govde.map(p => ({ x: p[0], y: p[1] })), true);
    g.fillStyle(0x3c6e69, alpha);
    const kafa = [[px + w / 2, py - 16], [px + w - 2, py + 16], [px + w / 2, py + 22], [px + 2, py + 16]];
    this._poly(g, kafa, false);
    g.lineStyle(1, 0x96e6dc, alpha);
    g.strokePoints(kafa.map(p => ({ x: p[0], y: p[1] })), true);
    g.fillStyle(0x0a1414, alpha);
    g.fillCircle(px + w / 2, py + 8, 4);
    g.fillStyle(vc, alpha);
    g.fillCircle(px + w / 2, py + 8, 2);
  }

  _bodyReaper(g, px, py, w, h, lf, alpha) {
    g.fillStyle(0x0e0a0b, alpha);
    g.fillRect(px + 2, py + h - 14, 10, 14 + lf);
    g.fillRect(px + w - 12, py + h - 14, 10, 14 - lf);
    g.fillStyle(0x100b0c, alpha);
    g.fillRect(px - 2, py + 16, w + 4, h - 16);
    g.fillStyle(0xd7c8af, alpha);
    const kafatasi = [[px + 3, py + 2], [px + w - 3, py + 2], [px + w - 1, py + 12], [px + w / 2 + 3, py + 20], [px + w / 2 - 3, py + 20], [px + 1, py + 12]];
    this._poly(g, kafatasi, false);
    g.lineStyle(1, 0x8c826e, alpha);
    g.strokePoints(kafatasi.map(p => ({ x: p[0], y: p[1] })), true);
    const gozR = (this.reaperVurusGoster > 0 || this.reaperAtisGoster > 0) ? 0xff3c32 : 0xc81914;
    g.fillStyle(0x0a0808, alpha);
    g.fillRect(px + 5, py + 6, 6, 7);
    g.fillRect(px + w - 11, py + 6, 6, 7);
    g.fillStyle(gozR, alpha);
    g.fillRect(px + 6, py + 7, 4, 5);
    g.fillRect(px + w - 10, py + 7, 4, 5);
    g.fillStyle(0x960f14, alpha);
    g.fillRect(px + w / 2 - 5, py + 24, 10, 8);
    g.fillStyle(0x120a0a, alpha);
    const pelerin = [[px - 6, py + h - 4], [px + w + 6, py + h - 4], [px + w + 2, py + h + 16], [px + w * 0.7, py + h + 8], [px + w * 0.5, py + h + 20], [px + w * 0.3, py + h + 8], [px - 2, py + h + 16]];
    this._poly(g, pelerin, false);
    g.lineStyle(1, 0x6e1416, alpha);
    g.strokePoints(pelerin.map(p => ({ x: p[0], y: p[1] })), true);
    g.fillStyle(0x191414, alpha);
    g.fillRect(px - 10, py + 15, 12, 16);
    g.fillRect(px + w - 2, py + 15, 12, 16);
    g.lineStyle(1, 0x961414, alpha);
    g.strokeRect(px - 10, py + 15, 12, 16);
    g.strokeRect(px + w - 2, py + 15, 12, 16);
  }

  _bodyRonin(g, px, py, w, h, lf, vc, alpha) {
    const koyu = 0x120f19, mor = 0xaa78ff;
    const gozR = this.roninGizliAktif ? 0x5a3c8c : mor;
    g.fillStyle(koyu, alpha);
    g.fillRect(px + 2, py + h - 14, 10, 14 + lf);
    g.fillRect(px + w - 12, py + h - 14, 10, 14 - lf);
    g.fillStyle(0x1c1824, alpha);
    const govde = [[px + 3, py + 16], [px + w - 3, py + 16], [px + w - 1, py + h - 6], [px + w / 2, py + h + 2], [px + 1, py + h - 6]];
    this._poly(g, govde, false);
    g.lineStyle(1, mor, alpha);
    g.strokePoints(govde.map(p => ({ x: p[0], y: p[1] })), true);
    g.fillStyle(0x0e0c14, alpha);
    const kask = [[px + 3, py + 10], [px + w - 3, py + 10], [px + w - 2, py - 2], [px + w / 2, py + 6], [px + 2, py - 2]];
    this._poly(g, kask, false);
    g.lineStyle(1, mor, alpha);
    g.strokePoints(kask.map(p => ({ x: p[0], y: p[1] })), true);
    g.fillStyle(0x0a080f, alpha);
    for (const dxSpike of [-6, 0, 6]) {
      const sx = px + w / 2 + dxSpike;
      this._poly(g, [[sx - 2, py - 4], [sx, py - 15 - Math.abs(dxSpike)], [sx + 2, py - 4]], false);
    }
    g.lineStyle(1, mor, alpha);
    g.strokeCircle(px + w / 2, py - 2, 11);
    g.lineStyle(2, gozR, alpha);
    g.lineBetween(px + w / 2, py - 1, px + w / 2, py + 8);
    g.fillStyle(0x14111c, alpha);
    const pelerinR = [[px - 2, py + 18], [px - 17, py + 29], [px - 11, py + h + 8], [px - 2, py + h - 2]];
    this._poly(g, pelerinR, false);
    g.lineStyle(1, mor, alpha);
    g.strokePoints(pelerinR.map(p => ({ x: p[0], y: p[1] })), true);
  }

  _bodyOverdrive(g, px, py, w, h, lf, alpha) {
    const koyu = 0x121212, sariAc = 0xffd73c, sariKoyu = 0x967800;
    const gozO = this.overdriveEGoster > 0 ? 0xff3c3c : 0xfff58c;

    g.fillStyle(sariKoyu, alpha);
    const solBacak = [[px + 3, py + h - 24], [px + 13, py + h - 24], [px + 11, py + h + lf - 2], [px + 2, py + h + lf - 6]];
    const sagBacak = [[px + w - 13, py + h - 24], [px + w - 3, py + h - 24], [px + w - 2, py + h - lf + 2], [px + w - 11, py + h - lf - 2]];
    this._poly(g, solBacak, false); this._poly(g, sagBacak, false);
    g.lineStyle(1, koyu, alpha);
    g.strokePoints(solBacak.map(p => ({ x: p[0], y: p[1] })), true);
    g.strokePoints(sagBacak.map(p => ({ x: p[0], y: p[1] })), true);

    g.fillStyle(0x8c6e00, alpha);
    const govde = [[px + 4, py + 16], [px + w - 4, py + 16], [px + w - 2, py + h - 22], [px + w / 2 + 4, py + h - 16], [px + w / 2 - 4, py + h - 16], [px + 2, py + h - 22]];
    this._poly(g, govde, false);
    g.lineStyle(1, koyu, alpha);
    g.strokePoints(govde.map(p => ({ x: p[0], y: p[1] })), true);
    g.fillStyle(sariKoyu, alpha);
    g.fillRect(px + w / 2 - 6, py + 24, 12, 10);

    g.fillStyle(sariAc, alpha);
    const kafa = [[px + w / 2, py - 12], [px + w - 1, py + 8], [px + w / 2, py + 18], [px + 1, py + 8]];
    this._poly(g, kafa, false);
    g.lineStyle(1, koyu, alpha);
    g.strokePoints(kafa.map(p => ({ x: p[0], y: p[1] })), true);
    g.fillStyle(koyu, alpha);
    g.fillCircle(px + w / 2, py + 7, 4);
    g.fillStyle(gozO, alpha);
    g.fillCircle(px + w / 2, py + 7, 2);

    g.fillStyle(sariKoyu, alpha);
    const solOmuz = [[px - 3, py + 13], [px - 14, py + 21], [px - 3, py + 30]];
    const sagOmuz = [[px + w + 3, py + 13], [px + w + 14, py + 21], [px + w + 3, py + 30]];
    this._poly(g, solOmuz, false); this._poly(g, sagOmuz, false);
    g.lineStyle(1, koyu, alpha);
    g.strokePoints(solOmuz.map(p => ({ x: p[0], y: p[1] })), true);
    g.strokePoints(sagOmuz.map(p => ({ x: p[0], y: p[1] })), true);

    g.fillStyle(0x5a4600, alpha);
    this._poly(g, [[px - 2, py + h - 8], [px - 10, py + h + 3], [px - 2, py + h - 1]], false);
    this._poly(g, [[px + w + 2, py + h - 8], [px + w + 10, py + h + 3], [px + w + 2, py + h - 1]], false);

    g.fillStyle(0x1e1e1e, alpha);
    g.fillRect(px + w + 2, py + 26, 14, 5);
    g.lineStyle(1, sariAc, alpha);
    g.strokeRect(px + w + 2, py + 26, 14, 5);

    if (this.overdriveOlumsuzlukKalan > 0) {
      const t = this.scene.time.now;
      const nabizO = 0.35 + 0.23 * Math.sin(t / 60);
      g.fillStyle(0xb4ffff, nabizO * alpha);
      g.fillRect(px - 4, py - 12, w + 8, h + 16);
    }
  }

  _weaponAngle(g, px, py, w, h, bx, by, aci, alpha) {
    if (this.heroId === 7) {
      const ucX = bx + Math.cos(aci) * 18, ucY = by + Math.sin(aci) * 18;
      g.fillStyle(0x96e6dc, alpha);
      g.fillCircle(ucX, ucY, 5);
      g.lineStyle(1, 0xdcfffa, alpha);
      g.strokeCircle(ucX, ucY, 5);
    } else if (this.heroId === 6) {
      const elX = bx + Math.cos(aci) * 20, elY = by + Math.sin(aci) * 20;
      g.lineStyle(4, 0x3c1459, alpha);
      g.lineBetween(bx, by, elX, elY);
      g.lineStyle(2, 0xdc96ff, alpha);
      for (let k = 0; k < 4; k++) {
        const pa = aci + (k - 1.5) * 0.35;
        g.lineBetween(elX, elY, elX + Math.cos(pa) * 8, elY + Math.sin(pa) * 8);
      }
      g.fillStyle(0x9650dc, alpha);
      g.fillCircle(elX, elY, 6);
      g.lineStyle(1, 0xdc96ff, alpha);
      g.strokeCircle(elX, elY, 6);
    } else if (this.heroId === 1) {
      const savuruyor = this.raptorPenceGoster > 0;
      const uzunlukP = savuruyor ? 34 : 18;
      const renkP = savuruyor ? 0xffffff : 0x96ffaa;
      g.lineStyle(2, renkP, alpha);
      for (let k = 0; k < 3; k++) {
        const offset = (k - 1) * (savuruyor ? 0.5 : 0.3);
        g.lineBetween(bx, by, bx + Math.cos(aci + offset) * uzunlukP, by + Math.sin(aci + offset) * uzunlukP);
      }
    } else if (this.heroId === 8) {
      const gosteriliyor = this.reaperVurusGoster > 0 || this.reaperAtisGoster > 0;
      const ucX = bx + Math.cos(aci) * 34, ucY = by + Math.sin(aci) * 34;
      g.lineStyle(4, 0x1e0f0f, alpha);
      g.lineBetween(bx, by, ucX, ucY);
      const kafatasiRenk = gosteriliyor ? 0xff463c : 0x4b1919;
      g.fillStyle(0x120c0c, alpha);
      g.fillCircle(ucX, ucY, 8);
      g.lineStyle(2, kafatasiRenk, alpha);
      g.strokeCircle(ucX, ucY, 8);
      g.fillStyle(0xff1e1e, alpha);
      g.fillCircle(ucX + Math.cos(aci + 1.5708) * 3, ucY + Math.sin(aci + 1.5708) * 3, 2);
      g.fillCircle(ucX + Math.cos(aci - 1.5708) * 3, ucY + Math.sin(aci - 1.5708) * 3, 2);
    } else if (this.heroId === 9) {
      const uzunR = (this.roninItisGoster > 0 || this.roninFirlatGoster > 0) ? 40 : 26;
      const ucX = bx + Math.cos(aci) * uzunR, ucY = by + Math.sin(aci) * uzunR;
      const renkMizrak = this.roninGizliAktif ? 0x8c78aa : 0xe6e6f0;
      g.lineStyle(3, 0x282332, alpha);
      g.lineBetween(bx, by, ucX, ucY);
      g.fillStyle(renkMizrak, alpha);
      this._poly(g, [
        [ucX + Math.cos(aci) * 10, ucY + Math.sin(aci) * 10],
        [ucX + Math.cos(aci + 2.5) * 5, ucY + Math.sin(aci + 2.5) * 5],
        [ucX + Math.cos(aci - 2.5) * 5, ucY + Math.sin(aci - 2.5) * 5]
      ], false);
      g.lineStyle(1, 0xaa78ff, alpha);
      g.strokeCircle(bx + Math.cos(aci) * (uzunR * 0.6), by + Math.sin(aci) * (uzunR * 0.6), 3);
    } else if (this.heroId === 0) {
      if (this.kilicDurum === 'beklemede') {
        if (this.kilicSavurmaGoster > 0) {
          const ilerleme = 1 - this.kilicSavurmaGoster / 8;
          const sallaAci = aci - 0.9 + ilerleme * 1.8;
          const ucX = bx + Math.cos(sallaAci) * 46, ucY = by + Math.sin(sallaAci) * 46;
          g.lineStyle(2, 0xc8dcff, alpha);
          this._strokeArc(g, bx, by, 46, aci - 0.9, aci + 0.9);
          g.lineStyle(5, 0xffffff, alpha);
          g.lineBetween(bx, by, ucX, ucY);
          g.fillStyle(0x787882, alpha);
          g.fillCircle(bx, by, 4);
        } else {
          const ucX = bx + Math.cos(aci) * 30, ucY = by + Math.sin(aci) * 30;
          g.lineStyle(4, 0xc8dcff, alpha);
          g.lineBetween(bx, by, ucX, ucY);
          g.fillStyle(0x787882, alpha);
          g.fillCircle(bx, by, 4);
        }
      }
    } else {
      g.fillStyle(vcFallback(this), alpha);
      g.fillRect(bx, by - 3, 24, 6);
      g.fillStyle(0x323232, alpha);
      g.fillRect(bx + 18, by - 5, 8, 10);
    }
  }
}

function vcFallback(p) { return p._weaponColor(); }
