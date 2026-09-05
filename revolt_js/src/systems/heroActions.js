import Phaser from 'phaser';
import { AEGIS, RAPTOR, HEX, WRAITH, REAPER, RONIN, OVERDRIVE, GENISLIK, ZEMIN_Y } from '../data/constants.js';
import { Mermi } from '../entities/Projectile.js';
import { Iskelet } from '../entities/Iskelet.js';
import { patlama } from '../entities/Fx.js';

// Shared hero input->action dispatch, used by both PlayScene and SurvivalScene.
// `scene` must expose: player, enemies, mermiler, applyDamage(d,amount), input.

// Everything a player attack can hit: regular enemies plus the worm hazard
// (story mode only), if it's currently above ground and vulnerable.
// Resolves the current aim point: the fire-joystick's projected point while
// a touch is driving it, otherwise the real mouse position.
export function getAim(scene) {
  const mc = scene.mobileControls;
  if (mc?.active) {
    const p = scene.player;
    const pt = mc.aimPoint(p.x + p.w / 2, p.y + p.h / 2);
    if (pt) return pt;
  }
  return { x: scene.input.activePointer.worldX, y: scene.input.activePointer.worldY };
}

export function hitTargets(scene) {
  let targets = scene.enemies;
  if (scene.worm && scene.worm.vurulabilirMi()) targets = targets.concat([scene.worm]);
  if (scene.golgeSolucanlar && scene.golgeSolucanlar.length) {
    targets = targets.concat(scene.golgeSolucanlar.filter(w => w.vurulabilirMi()));
  }
  return targets;
}

export function coneHit(scene, atk) {
  const p = scene.player;
  const { x: aimX, y: aimY } = getAim(scene);
  for (const d of hitTargets(scene)) {
    if (d.dead) continue;
    const dc = { x: d.x + d.w / 2, y: d.y + d.h / 2 };
    const dist = Math.hypot(dc.x - atk.cx, dc.y - atk.cy);
    if (dist > atk.menzil) continue;
    const angToEnemy = Math.atan2(dc.y - atk.cy, dc.x - atk.cx);
    const aim = Math.atan2(aimY - atk.cy, aimX - atk.cx);
    if (Math.abs(Phaser.Math.Angle.Wrap(angToEnemy - aim)) <= atk.aci) scene.applyDamage(d, atk.hasar);
  }
}

export function leftAttack(scene) {
  const p = scene.player;
  const { x: mx, y: my } = getAim(scene);
  switch (p.heroId) {
    case 0: {
      if (p.kilicSavurmaBekleme > 0) return;
      const rect = p.kilicSavurRect(mx, my);
      for (const d of hitTargets(scene)) {
        if (!d.dead && Phaser.Geom.Intersects.RectangleToRectangle(rect, d.rect())) scene.applyDamage(d, AEGIS.KILIC_HASAR * p.hasarCarpan);
      }
      p.kilicSavurmaBekleme = AEGIS.KILIC_SAVURMA_BEKLEME * p.saldiriCarpan;
      p.kilicSavurmaGoster = 8;
      break;
    }
    case 1: {
      if (p.raptorPenceBekleme > 0) return;
      const rect = p.raptorPenceRect(mx, my);
      for (const d of hitTargets(scene)) {
        if (!d.dead && Phaser.Geom.Intersects.RectangleToRectangle(rect, d.rect())) {
          const dmg = RAPTOR.PENCE_HASAR * p.hasarCarpan * (p.raptorUltiAktif ? RAPTOR.ULTI_PENCE_CARPAN : 1) * (p.raptorOfkeAktif ? RAPTOR.OFKE_CARPAN : 1);
          scene.applyDamage(d, dmg);
          p.can = Math.min(p.maxCan, p.can + dmg * RAPTOR.PENCE_YASAM_CALMA);
        }
      }
      p.raptorPenceBekleme = RAPTOR.PENCE_BEKLEME * p.saldiriCarpan;
      p.raptorPenceGoster = 6;
      break;
    }
    case 6:
      p.hexBuyuAt(mx, my, scene.mermiler, Mermi);
      break;
    case 7:
      p.wraithRuhAt(mx, my, scene.mermiler, Mermi);
      break;
    case 8: {
      const atk = p.reaperVurusBaslat();
      if (atk) coneHit(scene, atk);
      break;
    }
    case 5:
      p.atesEt(mx, my, scene.mermiler, Mermi);
      break;
    case 9: {
      if (!p.roninItisBaslat()) return;
      const atk = p.roninItisRect(mx, my);
      for (const d of hitTargets(scene)) {
        if (d.dead) continue;
        const dc = { x: d.x + d.w / 2, y: d.y + d.h / 2 };
        const dist = Math.hypot(dc.x - atk.cx, dc.y - atk.cy);
        if (dist > atk.menzil) continue;
        const angToEnemy = Math.atan2(dc.y - atk.cy, dc.x - atk.cx);
        const aim = Math.atan2(my - atk.cy, mx - atk.cx);
        if (Math.abs(Phaser.Math.Angle.Wrap(angToEnemy - aim)) <= atk.aci) {
          scene.applyDamage(d, atk.hasar * p.hasarCarpan);
          if (p.roninGizliAktif && p.roninGizliSersemAcik && 'donduKare' in d) d.donduKare = 300;
        }
      }
      break;
    }
  }
}

export function rightAction(scene, mx, my) {
  const p = scene.player;
  switch (p.heroId) {
    case 0:
      if (p.kilicDurum === 'beklemede') p.kilicFirlat(mx, my);
      else p.kilicGeriCagir();
      break;
    case 1:
      p.raptorDashBaslat(mx, my);
      break;
    case 6: {
      const beam = p.hexIsinBaslat(mx, my);
      if (beam) {
        const line = new Phaser.Geom.Line(beam.x1, beam.y1, beam.x2, beam.y2);
        for (const d of hitTargets(scene)) {
          if (d.dead) continue;
          if (Phaser.Geom.Intersects.LineToRectangle(line, d.rect())) scene.applyDamage(d, beam.hasar * p.hasarCarpan);
        }
      }
      break;
    }
    case 7:
      p.wraithHayaletBaslat();
      break;
    case 8: {
      const atk = p.reaperAtisBaslat();
      if (atk) coneHit(scene, atk);
      break;
    }
    case 5:
      p.overdriveKancaBaslat(mx, my, scene);
      break;
    case 9: {
      const atk = p.roninFirlatBaslat(mx, my);
      if (!atk) break;
      const vurulanlar = new Set();
      let sonX = atk.cx, sonY = atk.cy, mesafe = 0;
      while (mesafe < atk.menzil) {
        mesafe += 14;
        const nx = atk.cx + atk.ux * mesafe, ny = atk.cy + atk.uy * mesafe;
        if (nx < -20 || nx > GENISLIK + 20) break;
        sonX = nx; sonY = ny;
        for (const d of hitTargets(scene)) {
          if (d.dead || vurulanlar.has(d)) continue;
          if (d.tip === 'hayalet' && d.hayaletMod) continue;
          if (Phaser.Geom.Rectangle.Contains(d.rect(), nx, ny)) {
            vurulanlar.add(d);
            scene.applyDamage(d, atk.hasar);
            if (p.roninGizliAktif && p.roninGizliSersemAcik && 'donduKare' in d) d.donduKare = 300;
          }
        }
      }
      p.x = Phaser.Math.Clamp(sonX - p.w / 2, 0, GENISLIK - p.w);
      p.y = Phaser.Math.Clamp(sonY - p.h / 2, 46, ZEMIN_Y - p.h);
      p.hizX = 0; p.hizY = 0;
      if (scene.fx) scene.fx.push(...patlama(scene, sonX, sonY, 0xaa78ff, 10));
      break;
    }
  }
}

export function rightRelease(scene) {
  if (scene.player.heroId === 5) scene.player.overdriveSallanBirak();
}

export function eAbility(scene) {
  const p = scene.player;
  switch (p.heroId) {
    case 0: p.kalkanBaslat(); break;
    case 1: {
      const kacti = p.raptorKacisBaslat();
      if (kacti && p.raptorZehirPatlamaAcik) {
        const cx = p.x + p.w / 2, cy = p.y + p.h / 2;
        for (const d of hitTargets(scene)) {
          if (d.dead || !('zehirKare' in d)) continue;
          const dist = Math.hypot((d.x + d.w / 2) - cx, (d.y + d.h / 2) - cy);
          if (dist <= RAPTOR.ZEHIR_PATLAMA_YARICAP) d.zehirKare = RAPTOR.ZEHIR_DUSMAN_SURESI;
        }
      }
      break;
    }
    case 6: p.hexHealBaslat(); break;
    case 7: p.wraithHealBaslat(); break;
    case 8:
      if (p.reaperGuclendir()) {
        for (const s of scene.skeletons) s.guclendir();
        if (p.reaperEEkIskeletAcik) {
          for (let i = 0; i < 3; i++) {
            const x = Phaser.Math.Clamp(p.x + Phaser.Math.Between(-40, 40), 0, GENISLIK - 22);
            scene.skeletons.push(new Iskelet(scene, x, p.y, true, false));
          }
        }
      }
      break;
    case 5: {
      if (p.overdriveEBaslat()) {
        const cx = p.x + p.w / 2, cy = p.y + p.h / 2;
        for (const d of hitTargets(scene)) {
          if (d.dead) continue;
          const dist = Math.hypot((d.x + d.w / 2) - cx, (d.y + d.h / 2) - cy);
          if (dist <= OVERDRIVE.E_MENZIL) scene.applyDamage(d, OVERDRIVE.E_HASAR);
        }
      }
      break;
    }
    case 9: p.roninGizlenBaslat(); break;
  }
}

// Q — REAPER summons skeletons from its accumulated soul-split resource
// instead of the generic jetpack ulti (matches the HUD's "Q:ISKELET CAGIR").
export function qUlti(scene) {
  const p = scene.player;
  if (p.heroId === 8) {
    if (p.reaperRuhBolme <= 0) return;
    const n = p.reaperRuhBolme;
    p.reaperRuhBolme = 0;
    for (let i = 0; i < n; i++) {
      const x = Phaser.Math.Clamp(p.x + Phaser.Math.Between(-40, 40), 0, 900 - 22);
      scene.skeletons.push(new Iskelet(scene, x, p.y, true, p.reaperUltiOkcuAcik));
    }
    return;
  }
  p.ultiKullan();
}

export function handleSharedPerFrameEffects(scene) {
  const p = scene.player;
  if (p.heroId === 0 && (p.kilicDurum === 'giden' || p.kilicDurum === 'donuyor')) {
    const kr = p.kilicRect();
    for (const d of hitTargets(scene)) {
      if (d.dead || p.kilicVurulanlar.includes(d)) continue;
      if (Phaser.Geom.Intersects.RectangleToRectangle(kr, d.rect())) {
        scene.applyDamage(d, AEGIS.KILIC_HASAR * p.hasarCarpan);
        p.kilicVurulanlar.push(d);
      }
    }
  }
  if (p.heroId === 1 && p.raptorDashAktif) {
    const pr = p.rect();
    for (const d of hitTargets(scene)) {
      if (d.dead || p.raptorDashVurulanlar.includes(d)) continue;
      if (Phaser.Geom.Intersects.RectangleToRectangle(pr, d.rect())) {
        scene.applyDamage(d, RAPTOR.DASH_HASAR * p.hasarCarpan);
        p.raptorDashVurulanlar.push(d);
      }
    }
  }
  if (p.heroId === 9 && p.roninUltiAktif && p._roninUltiTikTimer === 6) {
    const cx = p.x + p.w / 2, cy = p.y + p.h / 2;
    const r = p.roninUltiRadius();
    for (const d of hitTargets(scene)) {
      if (d.dead) continue;
      const dist = Math.hypot((d.x + d.w / 2) - cx, (d.y + d.h / 2) - cy);
      if (dist <= r) scene.applyDamage(d, RONIN.ULTI_HASAR * p.hasarCarpan);
    }
  }
  if (p.heroId === 6 && p._pendingHexUlti) {
    p._pendingHexUlti = false;
    scene.sound.play('hex_ulti', { volume: 0.5 });
    for (const d of hitTargets(scene)) {
      if (d.dead) continue;
      if (p.hexUltiEkranTemizleAcik) scene.applyDamage(d, d.can + 99999);
      else {
        scene.applyDamage(d, HEX.ULTI_HASAR * p.hasarCarpan);
        d.yavaslatildi = HEX.ULTI_YAVAS_SURESI;
      }
    }
  }
}
