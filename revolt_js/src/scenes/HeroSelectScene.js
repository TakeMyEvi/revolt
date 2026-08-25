import Phaser from 'phaser';
import { GENISLIK, YUKSEKLIK, KAHRAMANLAR, KAHRAMAN_YUKSELTMELERI, KAHRAMAN_USTALIK_ESIKLERI, ustalikKademesi, OVERDRIVE } from '../data/constants.js';
import { GameState, saveState } from '../data/state.js';
import { makeButton } from '../systems/ui.js';
import { t } from '../data/translations.js';

const EKIP_AFIS_SIRA = [0, 1, 6, 7, 8, 5, 9];
const EKIP_AFIS_FRACS = [0.09, 0.22, 0.35, 0.49, 0.62, 0.75, 0.88];
const EKIP_AFIS_ACIK_KUMELERI = [
  [0], [0, 1], [0, 1, 6], [0, 1, 6, 7], [0, 1, 6, 7, 8], [0, 1, 6, 7, 8, 5], [0, 1, 6, 7, 8, 5, 9]
];

function unlockedHeroIds() {
  if (GameState.testModu) return KAHRAMANLAR.map(h => h.id);
  return KAHRAMANLAR.filter(h => h.acilis_bolum <= GameState.enYuksekBolum).map(h => h.id);
}

function posterIndex() {
  const unlocked = new Set(unlockedHeroIds());
  let idx = 0;
  for (let i = 0; i < EKIP_AFIS_ACIK_KUMELERI.length; i++) {
    if (EKIP_AFIS_ACIK_KUMELERI[i].every(id => unlocked.has(id))) idx = i;
  }
  return idx;
}

export class HeroSelectScene extends Phaser.Scene {
  constructor() {
    super('HeroSelect');
  }

  init(data) {
    this._autoOpenUstalik = !!data?.openUstalik;
  }

  preload() {
    // Only the one poster this visibility state actually needs — the other
    // 6 team-poster JPEGs (~1.4MB combined) never touch the network.
    const key = `ekip_${posterIndex() + 1}`;
    if (!this.textures.exists(key)) this.load.image(key, `gorseller/${key}.jpg`);
  }

  create() {
    this.cameras.main.setBackgroundColor('#05050f');
    this.ustalikGroup = null; // scene instances are reused across restarts — don't carry a stale panel ref

    const afisIdx = posterIndex();
    const poster = this.add.image(GENISLIK / 2, YUKSEKLIK / 2, `ekip_${afisIdx + 1}`);
    const scale = Math.max(GENISLIK / poster.width, YUKSEKLIK / poster.height);
    poster.setScale(scale);
    const posterW = poster.width * scale;
    const posterLeft = GENISLIK / 2 - posterW / 2;
    const posterTop = YUKSEKLIK / 2 - (poster.height * scale) / 2;
    const posterH = poster.height * scale;

    this.add.rectangle(0, 0, GENISLIK, 70, 0x000000, 0.55).setOrigin(0);
    makeButton(this, 60, 30, 100, 32, t('geri'), () => this.scene.start('Menu'), '13px');
    this.add.text(GENISLIK / 2, 34, t('kahramanSec'), { fontFamily: 'monospace', fontSize: '20px', color: '#00fff7' }).setOrigin(0.5);
    makeButton(this, GENISLIK - 80, 30, 130, 32, t('yukselt'), () => this._showUstalikPanel(), '13px');

    const unlocked = new Set(unlockedHeroIds());

    EKIP_AFIS_SIRA.forEach((heroId, i) => {
      const hero = KAHRAMANLAR.find(h => h.id === heroId);
      const frac = EKIP_AFIS_FRACS[i];
      const cx = posterLeft + posterW * frac;
      const boxW = posterW * 0.125;
      const boxTop = posterTop + posterH * 0.22;
      const boxH = posterH * 0.66;
      const isUnlocked = unlocked.has(heroId);
      const isSelected = heroId === GameState.selectedHero;

      const hit = this.add.rectangle(cx, boxTop + boxH / 2, boxW, boxH, 0xffffff, 0);
      const barColor = isSelected ? 0x2288ff : (isUnlocked ? 0x555566 : 0x222228);
      const bar = this.add.rectangle(cx, boxTop + boxH + 10, boxW * 0.8, 5, barColor);

      const nameStr = isUnlocked ? hero.isim : '?????';
      const nameColor = isUnlocked ? Phaser.Display.Color.IntegerToColor(hero.renk).rgba : '#555555';
      const label = this.add.text(cx, boxTop + boxH + 24, nameStr, { fontFamily: 'monospace', fontSize: '12px', color: nameColor }).setOrigin(0.5);
      if (!isUnlocked) {
        this.add.text(cx, boxTop + boxH + 38, `Bolum ${hero.acilis_bolum}`, { fontFamily: 'monospace', fontSize: '9px', color: '#666666' }).setOrigin(0.5);
      }

      if (isUnlocked) {
        hit.setInteractive({ useHandCursor: true });
        hit.on('pointerover', () => { if (heroId !== GameState.selectedHero) bar.setFillStyle(0x00ffc8); });
        hit.on('pointerout', () => { if (heroId !== GameState.selectedHero) bar.setFillStyle(0x555566); });
        hit.on('pointerdown', () => {
          GameState.selectedHero = heroId;
          saveState();
          this.scene.restart();
        });
      }
    });

    this.keyEsc = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ESC);
    if (this._autoOpenUstalik) this._showUstalikPanel();
  }

  _showUstalikPanel() {
    if (this.ustalikGroup) { this.ustalikGroup.destroy(true); this.ustalikGroup = null; return; }
    this._ustalikHeroId = GameState.selectedHero;
    this.ustalikGroup = this.add.container(0, 0).setDepth(50);
    this._renderUstalikPanel();
  }

  // Redraws the whole modal for the currently-picked tab hero (this._ustalikHeroId) —
  // browsing here is independent of GameState.selectedHero, so every hero's
  // mastery tree can be inspected regardless of which one is actually equipped.
  _renderUstalikPanel() {
    const g = this.ustalikGroup;
    g.removeAll(true);

    const heroId = this._ustalikHeroId;
    const hero = KAHRAMANLAR.find(h => h.id === heroId);
    const tiers = KAHRAMAN_YUKSELTMELERI[heroId];
    const panelW = 620, panelH = heroId === 5 ? 460 : 420;
    const px = GENISLIK / 2 - panelW / 2, py = YUKSEKLIK / 2 - panelH / 2;

    g.add(this.add.rectangle(GENISLIK / 2, YUKSEKLIK / 2, GENISLIK, YUKSEKLIK, 0x000000, 0.78).setInteractive());
    g.add(this.add.rectangle(GENISLIK / 2, YUKSEKLIK / 2, panelW, panelH, 0x0a0a18, 0.97).setStrokeStyle(2, 0x00fff7));
    g.add(this.add.text(GENISLIK / 2, py + 24, `${t('ustalik')} — ${hero.isim}`, {
      fontFamily: 'monospace', fontSize: '17px', color: Phaser.Display.Color.IntegerToColor(hero.renk).rgba
    }).setOrigin(0.5));

    // hero tabs — only unlocked heroes are browsable here (locked ones aren't spoiled)
    const browsable = KAHRAMANLAR.filter(h => unlockedHeroIds().includes(h.id));
    const tabW = panelW / browsable.length;
    browsable.forEach((h, i) => {
      const tx = px + tabW * (i + 0.5);
      const ty = py + 54;
      const active = h.id === heroId;
      const tab = this.add.rectangle(tx, ty, tabW - 4, 24, active ? 0x2288ff : 0x111122)
        .setStrokeStyle(1, active ? 0x66bbff : 0x333344).setInteractive({ useHandCursor: true });
      const label = this.add.text(tx, ty, h.isim.slice(0, 4), {
        fontFamily: 'monospace', fontSize: '10px', color: active ? '#ffffff' : '#888888'
      }).setOrigin(0.5);
      tab.on('pointerdown', () => { this._ustalikHeroId = h.id; this._renderUstalikPanel(); });
      g.add(tab); g.add(label);
    });

    if (!tiers) {
      g.add(this.add.text(GENISLIK / 2, YUKSEKLIK / 2 + 20, 'Bu kahraman icin ustalik yukseltmesi yok.', {
        fontFamily: 'monospace', fontSize: '13px', color: '#888888'
      }).setOrigin(0.5));
    } else {
      const hasar = GameState.kahramanHasar[heroId] || 0;
      const esikler = KAHRAMAN_USTALIK_ESIKLERI[heroId] || [];
      const kademe = ustalikKademesi(heroId, hasar);

      // Reached tiers stay clickable to switch back off — mirrors the Python
      // original's KAHRAMAN_YETENEK_KAPALI (an unlocked perk can be toggled).
      const renderRow = (i, rowY, ad, aciklama, esik, prevEsik) => {
        const eristi = i === 3 ? hasar >= esik : i < kademe;
        const key = `${heroId}:${i}`;
        const kapali = (GameState.kapaliYetenekler || []).includes(key);
        const acikMi = eristi && !kapali;
        const oran = eristi ? 1 : Phaser.Math.Clamp((hasar - prevEsik) / Math.max(1, esik - prevEsik), 0, 1);
        const durumIsareti = acikMi ? '[X]' : (kapali ? '[-]' : '[ ]');
        const renk = acikMi ? '#00ff88' : (kapali ? '#f5a623' : '#dddddd');

        const baslik = this.add.text(px + 24, rowY, `${durumIsareti} ${ad}`, {
          fontFamily: 'monospace', fontSize: '15px', color: renk
        });
        g.add(baslik);
        g.add(this.add.text(px + 24, rowY + 22, aciklama, {
          fontFamily: 'monospace', fontSize: '11px', color: '#999999', wordWrap: { width: panelW - 48 }
        }));
        g.add(this.add.rectangle(px + 24, rowY + 62, panelW - 48, 8, 0x222233).setOrigin(0, 0.5));
        g.add(this.add.rectangle(px + 24, rowY + 62, (panelW - 48) * oran, 8, acikMi ? 0x00ff88 : (kapali ? 0xf5a623 : 0x00fff7)).setOrigin(0, 0.5));
        if (!eristi) {
          g.add(this.add.text(px + panelW - 24, rowY + 62, `${Math.floor(hasar)}/${esik}`, {
            fontFamily: 'monospace', fontSize: '10px', color: '#777777'
          }).setOrigin(1, 0.5));
        } else {
          baslik.setInteractive({ useHandCursor: true }).on('pointerdown', () => {
            const list = GameState.kapaliYetenekler || (GameState.kapaliYetenekler = []);
            const idx = list.indexOf(key);
            if (idx >= 0) list.splice(idx, 1); else list.push(key);
            saveState();
            this._renderUstalikPanel();
          });
          const hint = this.add.text(px + panelW - 24, rowY + 62, acikMi ? t('kapatKisa') : t('ac'), {
            fontFamily: 'monospace', fontSize: '10px', color: '#666666'
          }).setOrigin(1, 0.5);
          g.add(hint);
        }
      };

      tiers.forEach((tier, i) => {
        const esik = esikler[i] || 0;
        const prevEsik = i === 0 ? 0 : (esikler[i - 1] || 0);
        renderRow(i, py + 96 + i * 96, tier.ad, tier.aciklama, esik, prevEsik);
      });

      // Overdrive has a 4th, separate unlock outside the numbered tiers —
      // see OVERDRIVE.SALLANMA_ESIGI / game (1).py's overdrive_sallanma_acik.
      if (heroId === 5) {
        renderRow(3, py + 96 + tiers.length * 96, 'KANCA SALINIMI',
          'Kanca sallanarak hareket etmeni saglar (acilana kadar hedefe duz ucar).',
          OVERDRIVE.SALLANMA_ESIGI, 0);
      }
    }

    const close = this.add.text(GENISLIK / 2, py + panelH - 22, t('kapat'), {
      fontFamily: 'monospace', fontSize: '14px', color: '#f5a623'
    }).setOrigin(0.5).setInteractive({ useHandCursor: true });
    close.on('pointerdown', () => { g.destroy(true); this.ustalikGroup = null; });
    g.add(close);
  }

  update() {
    if (Phaser.Input.Keyboard.JustDown(this.keyEsc)) {
      if (this.ustalikGroup) { this.ustalikGroup.destroy(true); this.ustalikGroup = null; return; }
      this.scene.start('Menu');
    }
  }
}
