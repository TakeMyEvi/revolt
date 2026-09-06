import Phaser from 'phaser';
import { GENISLIK, YUKSEKLIK, AEGIS, RAPTOR, HEX, WRAITH, REAPER, OVERDRIVE, RONIN,
  KALKAN_KAPASITE, KALKAN_BEKLEME, ULTI_MAX } from '../data/constants.js';
import { t } from '../data/translations.js';

const HINT_COLORS = { 0: '#00fff7', 1: '#00ff64', 6: '#aa00ff', 7: '#78dcc8', 8: '#e94560', 5: '#ffee00', 9: '#aa78ff' };

// Faithful port of the Python original's `hud_ciz` — same bars/labels/positions.
export class Hud {
  constructor(scene) {
    this.scene = scene;
    const s = scene.add;

    s.rectangle(GENISLIK / 2, 21, GENISLIK, 42, 0x000000).setDepth(19).setStrokeStyle(2, 0x00fff7);

    this.hpBg = s.rectangle(10, 11, 160, 16, 0x1e1e1e).setOrigin(0).setDepth(20).setStrokeStyle(1, 0x00fff7);
    this.hpFill = s.rectangle(10, 11, 158, 16, 0x00ff64).setOrigin(0).setDepth(20);
    this.hpBg.setDepth(21);
    this.hpText = s.text(90, 19, '', { fontFamily: 'monospace', fontSize: '12px', color: '#ffffff' }).setOrigin(0.5).setDepth(22);

    this.cdBg = s.rectangle(10, 27, 120, 8, 0x1e1e1e).setOrigin(0).setDepth(20);
    this.cdFill = s.rectangle(10, 27, 0, 8, 0x00fff7).setOrigin(0).setDepth(21);
    this.cdText = s.text(10, 31, '', { fontFamily: 'monospace', fontSize: '9px', color: '#dddddd' }).setOrigin(0, 0.5).setDepth(22);
    this.cdPips = [];
    for (let i = 0; i < REAPER.RUH_BOLME_MAX; i++) {
      this.cdPips.push(s.rectangle(10 + i * 12, 27, 11, 8, 0x1e1e1e).setOrigin(0).setDepth(21));
    }

    this.spBg = s.rectangle(175, 11, 158, 14, 0x1e1e1e).setOrigin(0).setDepth(20).setStrokeStyle(1, 0x00fff7);
    this.spFill = s.rectangle(175, 11, 0, 14, 0x00fff7).setOrigin(0).setDepth(21);
    this.spLabel = s.text(339, 18, '', { fontFamily: 'monospace', fontSize: '10px', color: '#dddddd' }).setOrigin(0, 0.5).setDepth(22);

    this.ultiBg = s.rectangle(560, 11, 60, 14, 0x1e1e1e).setOrigin(0).setDepth(20).setStrokeStyle(1, 0xffee00);
    this.ultiFill = s.rectangle(560, 11, 0, 14, 0xffee00).setOrigin(0).setDepth(21);
    this.ultiLabel = s.text(624, 18, '', { fontFamily: 'monospace', fontSize: '10px', color: '#dddddd' }).setOrigin(0, 0.5).setDepth(22);

    this.centerText = s.text(GENISLIK / 2, 21, '', { fontFamily: 'monospace', fontSize: '13px', color: '#ffffff' }).setOrigin(0.5).setDepth(22);
    this.scoreText = s.text(GENISLIK - 20, 18, '', { fontFamily: 'monospace', fontSize: '13px', color: '#ffffff' }).setOrigin(1, 0.5).setDepth(22);

    const hintStr = t(`hint${scene.heroId}`) !== `hint${scene.heroId}` ? t(`hint${scene.heroId}`) : t('hint0');
    const hintColor = HINT_COLORS[scene.heroId] || HINT_COLORS[0];
    this.hintText = s.text(10, YUKSEKLIK - 22, hintStr, { fontFamily: 'monospace', fontSize: '11px', color: hintColor }).setDepth(20);
  }

  update(bolum, kalanDusman, skor) {
    const p = this.scene.player;
    const hpRatio = Phaser.Math.Clamp(p.can / p.maxCan, 0, 1);
    this.hpFill.width = 158 * hpRatio;
    this.hpFill.fillColor = hpRatio > 0.5 ? 0x00ff64 : (hpRatio > 0.25 ? 0xf5a623 : 0xe94560);
    this.hpText.setText(`${Math.max(0, Math.round(p.can))}/${p.maxCan}`);

    this._updateSecondary(p);
    this._updateSpecial(p);
    this._updateUlti(p);

    this.centerText.setText(`${t('hudBolum')} ${bolum}/30   ${t('hudDusman')}:${Math.max(0, kalanDusman)}`);
    this.scoreText.setText(`${t('hudSkor')}:${skor}`);
  }

  _resetCd() {
    this.cdFill.setVisible(true); this.cdBg.setVisible(true); this.cdText.setText('');
    for (const pip of this.cdPips) pip.setVisible(false);
  }

  _updateSecondary(p) {
    this._resetCd();
    switch (p.heroId) {
      case 0: this._cdBar(p.kilicAtmaBekleme, AEGIS.KILIC_ATMA_BEKLEME, 0x00fff7); break;
      case 6:
        this.cdFill.setVisible(false);
        this.cdText.setText(`${t('hudKitap')}: ${p.hexKitapSayisi}/${p.hexKitapMaxOzel}`).setColor('#aa00ff');
        break;
      case 1: this._cdBar(p.raptorDashBekleme, RAPTOR.DASH_BEKLEME, 0x00ff64); break;
      case 7:
        this.cdFill.setVisible(false);
        this.cdText.setText(`${t('hudRuh')}: ${Math.round(p.wraithRuh)}/${WRAITH.RUH_MAX}`).setColor('#78dcc8');
        break;
      case 8:
        this.cdFill.setVisible(false); this.cdBg.setVisible(false);
        for (let i = 0; i < REAPER.RUH_BOLME_MAX; i++) {
          this.cdPips[i].setVisible(true);
          this.cdPips[i].fillColor = i < p.reaperRuhBolme ? 0xcd2d28 : 0x1e1e1e;
        }
        break;
      case 5: this._cdBar(p.kancaBekleme, OVERDRIVE.KANCA_BEKLEME, 0xffee00, 0x6e5a00); break;
      case 9: this._cdBar(p.roninFirlatBekleme, RONIN.FIRLAT_BEKLEME, 0xaa78ff, 0x5a3c8c); break;
    }
  }

  _cdBar(bekleme, sabit, color, dimColor) {
    const oran = 1 - Phaser.Math.Clamp(bekleme / sabit, 0, 1);
    this.cdFill.width = 120 * oran;
    this.cdFill.fillColor = bekleme > 0 && dimColor ? dimColor : color;
  }

  _updateSpecial(p) {
    this.spFill.setVisible(true);
    switch (p.heroId) {
      case 8: {
        const oran = 1 - Phaser.Math.Clamp(p.reaperEBekleme / REAPER.E_BEKLEME, 0, 1);
        this.spFill.width = 158 * oran; this.spFill.fillColor = 0xcd2d28;
        this.spLabel.setText(t('eGuclendir'));
        break;
      }
      case 7: {
        const oran = Math.min(1, p.wraithRuh / WRAITH.HAYALET_MALIYET);
        this.spFill.width = 158 * oran; this.spFill.fillColor = oran >= 1 ? 0x96e6dc : 0x5a5a5a;
        this.spLabel.setText(t('sagHayaletEIyilestir'));
        break;
      }
      case 1: {
        const oran = p.raptorKacisAktif ? 1 : 1 - Phaser.Math.Clamp(p.raptorKacisBekleme / RAPTOR.KACIS_BEKLEME, 0, 1);
        this.spFill.width = 158 * oran; this.spFill.fillColor = p.raptorKacisAktif ? 0xffffff : 0x00ff64;
        this.spLabel.setText(t('eKacis'));
        break;
      }
      case 6: {
        const oran = p.hexHealAktif ? p.hexHealSuresi / HEX.HEAL_SURESI : (1 - Phaser.Math.Clamp(p.hexHealBekleme / HEX.HEAL_BEKLEME, 0, 1));
        this.spFill.width = 158 * oran; this.spFill.fillColor = p.hexHealAktif ? 0x00ff64 : 0x5a5a5a;
        this.spLabel.setText(t('eIyilestir'));
        break;
      }
      case 5: {
        const oran = 1 - Phaser.Math.Clamp(p.overdriveEBekleme / OVERDRIVE.E_BEKLEME, 0, 1);
        this.spFill.width = 158 * oran; this.spFill.fillColor = 0xffee00;
        this.spLabel.setText(t('ePatlat'));
        break;
      }
      case 9: {
        const oran = 1 - Phaser.Math.Clamp(p.roninEBekleme / RONIN.E_BEKLEME, 0, 1);
        this.spFill.width = 158 * oran; this.spFill.fillColor = 0xaa78ff;
        this.spLabel.setText(t('eGizlen'));
        break;
      }
      default: { // AEGIS shield gauge
        const oran = p.kalkanAktif ? p.kalkanKapasite / KALKAN_KAPASITE : (1 - Phaser.Math.Clamp(p.kalkanBekleme / KALKAN_BEKLEME, 0, 1));
        this.spFill.width = 158 * oran; this.spFill.fillColor = 0x00fff7;
        this.spLabel.setText(t('eKalkan'));
      }
    }
  }

  _updateUlti(p) {
    if (p.heroId === 8) {
      const oran = p.reaperRuhBolme / REAPER.RUH_BOLME_MAX;
      this.ultiFill.width = 58 * oran; this.ultiFill.fillColor = 0xcd2d28;
      this.ultiLabel.setText(t('qIskeletCagir'));
      return;
    }
    if (p.ultiAktifMi()) {
      this.ultiFill.width = 58; this.ultiFill.fillColor = 0xffd700;
    } else {
      this.ultiFill.width = 58 * Phaser.Math.Clamp(p.ultiDolu / ULTI_MAX, 0, 1);
      this.ultiFill.fillColor = 0xffee00;
    }
    this.ultiLabel.setText(t('qUltiLabel'));
  }
}
