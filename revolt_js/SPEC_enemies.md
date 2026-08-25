# REVOLT — Enemy/Projectile/Pickup Systems Technical Spec (source lines 2235–3420)

### Global constants referenced in this range
```
GENISLIK (screen width)        = 900
YUKSEKLIK (screen height)      = 550
ZEMIN_Y (ground Y)             = YUKSEKLIK - 80 = 470
PATLAMA_YARICAP (blast radius) = 55       # suicide robot AoE radius
FITIL_SURESI (fuse frames)     = 18       # frames armed-proximity before detonation
SOLUCAN_CAN                    = 75
SOLUCAN_HASAR                  = 35       # contact damage
SOLUCAN_YUKSEKLIK              = 220      # full-emerge height above ground
SOLUCAN_TEHLIKE_SURESI         = 55       # frames spent fully exposed/dangerous
MIZRAKLI_HAVADA_ESIK           = 55       # px above ground counted as "player airborne"
HEX_ULTI_YAVAS_CARPAN          = 0.4      # slow-effect speed multiplier (HEX ulti)
RAPTOR_ZEHIR_TIK               = 30       # poison damage tick interval (frames, ~0.5s@60fps)
RAPTOR_ZEHIR_HASAR              = 3       # poison damage per tick
REAPER_ISKELET_CAN             = 35
REAPER_ISKELET_HASAR           = 8
REAPER_ISKELET_HIZ             = 2.5
REAPER_ISKELET_MENZIL          = 40       # horizontal distance threshold to stop closing on target
REAPER_GUC_SURESI              = 600      # ~10s empowerment duration (E ability)
REAPER_GUC_CARPAN              = 1.8      # speed multiplier while empowered
REAPER_ULTI_ISKELET_RENK       = (26,14,17)
```
Damage-tracking side effect: both `Dusman.can` and `Solucan.can` are Python properties — any decrease auto-adds the delta to `KAHRAMAN_HASAR[secili_kahraman]` (mastery/damage-dealt tracker), calls `ustalik_kademe_kontrol(secili_kahraman)`, plays a hit sound (`snd_vurus()`) on non-lethal decrease, and on the frame health crosses from >0 to <=0 increments global `TOPLAM_OLDURULEN` (kill counter) and (Dusman only) plays `snd_dusman_olum(self.tip)`.

---

## `class Mermi` (Projectile)

**Fields:** `x,y` (float pos), `hiz_x,hiz_y` (velocity/frame), `renk` (color), `hasar` (damage), `oyuncu_mermisi` (bool: player-owned vs enemy-owned), `omur` (lifetime frames), `homing` (bool), `hedef_dusman` (homing target ref). Optional flags set externally: `mizrak_mermisi` (spear visual), `wraith_mermisi` (ghost-orb visual).

**Lifetime:** `omur = 80` if player bullet, else `omur = 100000` (effectively unlimited — enemy bullets live until off-screen instead of timing out). `omur` decremented by 1 every `guncelle()` call.

**Movement (`guncelle`)**
- If `homing` and `hedef_dusman` alive (`can > 0`): compute vector to target center `(hedef.x+w/2, hedef.y+h/2)`, normalize; current speed magnitude `hiz = hypot(hiz_x,hiz_y) or 5`; steer via exponential lerp: `hiz_x += (dx/len*hiz - hiz_x) * 0.15`, same for y (15% turn-rate per frame, homing does NOT change speed magnitude directly, only direction).
- Then unconditionally: `x += hiz_x; y += hiz_y; omur -= 1`.

**Collision / damage application:** NOT handled inside `Mermi` — external game-loop code checks `m.rect()` (a 6×6 px hitbox centered on position) against player/enemy rects, applies `m.hasar` on hit, removes projectiles when `m.omur <= 0` OR off-screen by 20px margin.

**Rendering (`ciz`)** — 3 visual variants selected by attribute flags:
- `mizrak_mermisi` (spear): 3px line + triangular arrowhead.
- `wraith_mermisi` (ghost orb): nested alpha circles (glow/mid/core/outline).
- default: solid 6×6 rect in `renk`.

`rect()` = `Rect(x-3, y-3, 6, 6)`.

---

## `class Dusman` (Enemy)

**Confirmed enemy type list:** `'melee'`, `'ranged'`, `'drone'`, `'sniper'`, `'shield'`, `'tank'`, `'suicide'`, `'gorunmez'` (invisible), `'hayalet'` (ghost), `'mizrakli'` (spear-thrower/group), `'boss'`, `'finalboss'`.

### Shared per-frame update pipeline (`guncelle(oyuncu_x, oyuncu_y, zaman)`)
1. If `dondu_kare > 0` (RONIN freeze): decrement and return — no processing at all.
2. If `cekim_kare > 0` (OVERDRIVE hook pull): decrement; lerp 35%/frame toward `(cekim_hedef_x, cekim_hedef_y)`; tick anim/atis_timer; return (skips normal AI).
3. `yavaslatildi` (slow debuff) decremented if >0; `yavas_carpan = 0.4` while active else `1.0` (horizontal movement only).
4. Poison (`zehir_kare`): if >0, decrement `zehir_kare`/`zehir_tik`; at `zehir_tik<=0` reset to 30, `can -= 3`.
5. Type-specific movement block.
6. `gorunmez`/`hayalet` phase toggles evaluated regardless of movement branch.
7. Screen-edge bounce (unless `sinirsiz`): clamp x to `[10, GENISLIK-w-10]`, flip `hiz_x`.
8. Flying types clamp y to `[44, ZEMIN_Y-h]`.
9. Animation: 10-frame/2-frame walk cycle for all.
10. `atis_timer` decremented if >0.

### Common spawn formula
`hm = 1 + (bolum-1)*0.11` (health mult), `sm = 1 + (bolum-1)*0.055` (speed mult), `mm = 1 + (bolum-1)*0.17` (money mult). `bolum` = stage number.

### Per-type stats & behavior

**melee** — 28×48, ground. HP `22*hm`. Speed `(2.4+bolum*0.14)*sm`. `para=60*mm`. Never attacks (`atis_timer=9999`). Generic ground-walker chase (re-aims each frame, gravity 0.4, lands at ZEMIN_Y-h).

**ranged** — 26×44, ground. HP `15*hm`. Speed `(1.0+bolum*0.07)*sm`. `para=80*mm`. Cooldown reset `70+rand(0,20)`. Fires 1 bullet at player: speed 3.5, color (255,51,102), dmg 8. Ground-walker chase.

**drone** — 34×24, airborne spawn `ZEMIN_Y-170-rand(0,60)`. HP `12*hm`. Speed `(1.5+bolum*0.11)*sm`. `para=100*mm`. True flier: horizontal chase + sinusoidal bob `sin(zaman/400+x*0.01)*1.2`, clamped y∈[44,ZEMIN_Y-h]. Cooldown `65+rand(0,20)`. Same 1-bullet attack as ranged (speed 3.5, dmg 8).

**sniper** — 22×30, spawn `ZEMIN_Y-220-rand(0,60)`. HP `10*hm`. Stationary horizontally (hiz_x=0 at spawn, stays put but bobs). `para=130*mm`. Cooldown `35+rand(0,20)`. Fires 3 bullets simultaneously (same angle/speed — stacked volley), speed 14, color red, dmg 18 each (up to 54 total).

**shield** — 32×50, ground. HP `40*hm`. Speed `(0.8+bolum*0.06)*sm`. `para=120*mm`. Never attacks. Ground-walker. Visual: cyan shield rect on the side facing direction of travel (blocks front).

**tank** — 52×60 (largest walker), ground. HP `90*hm`. Speed `(0.6+bolum*0.04)*sm` (slowest). `para=200*mm`. Cooldown `110+rand(0,20)` (slowest fire). Single lobbed cannon shot: `hiz=(dx/len*5, dy/len*5-3)` (arc), spawn y-10, color (255,136,0), dmg 22 (heaviest basic hit).

**suicide** — 26×40, ground. HP `18*hm`. `taban_hiz=(3.6+bolum*0.10)*sm` (fastest rush, no ramp). `para=90*mm`. Never shoots. Fuse: if within `PATLAMA_YARICAP+15=70px` of player, `fitil+=1`/frame; at `fitil>=FITIL_SURESI(18)` → `patlayacak=True` (external code triggers AoE dmg, radius 55). Leaving 70px ring resets fitil to 0. Visual: blinks yellow/orange every 3 frames while fusing; draws growing red telegraph circle + "!!!" label.

**gorunmez (invisible)** — 28×28, airborne spawn `ZEMIN_Y-150-rand(0,60)`. HP `14*hm`. Speed `(1.3+bolum*0.08)*sm`. `para=140*mm`. Shares drone/sniper movement branch but `hiz_carpani=2.0` while cloaked (2x speed invisible!). Stealth cycle: `faz_timer` counts down, toggles `gizli`. Cloak entry: `faz_timer=rand(90,150)`, `atis_timer=9999` (can't attack). Visible entry: `faz_timer=55`, `atis_timer=12` (attacks almost immediately on decloak). Cooldown base `55+rand(0,20)`. Attack: speed 4.5, color purple (180,0,255), dmg 12. Rendering: fully skipped (invisible, no silhouette) while cloaked; decloak flicker/fade-in outline for first portion of visible phase.

**hayalet (ghost)** — 30×34, airborne spawn `ZEMIN_Y-130-rand(0,50)`. HP `20*hm`. Speed `(1.1+bolum*0.07)*sm`. `para=150*mm`. Movement: if `hayalet_mod` (phased) → FLEES opposite direction at fixed 2.4 speed; else chases normally. Both get sinusoidal y bob. Panic-phase trigger: if not phased, cooldown expired, HP<40% max → instantly phase, heal +30% current HP, `faz_timer=80`. Normal toggle cycle also heals +30% on entering phase. Exiting phase: `faz_timer=rand(150,220)`, `atis_timer=20`, `hayalet_cooldown=100` (lockout before next panic-phase). Can't attack while phased. Cooldown base `65+rand(0,20)`. Attack: speed 3.2, color pale cyan (190,255,255), dmg 9 (weakest). Rendering: translucent (alpha 110/160) while phased; solid teal-bordered otherwise. NOTE: Iskelet AI explicitly ignores ghosts while `hayalet_mod` True (can't be targeted/meleed while phased-fleeing).

**mizrakli (spear rush)** — 30×46, ground. HP `9*hm` (glass cannon). `hiz_x` assigned externally by spawner (group rush direction/speed, doesn't self-determine). `para=45*mm`. `atis_timer=15` fixed. Movement: straight line at assigned hiz_x, NO re-aim, NO gravity (fixed lane charge). Tracks `hedef_havada = (ZEMIN_Y-player_y) > 55` every frame regardless of attack state. Throw condition (`atis_yapabilir` override): `hedef_havada` True AND `0.2*GENISLIK < x < 0.8*GENISLIK` (middle 60% "throw window") AND `not mizrak_atildi` (once-only) AND cooldown ready. Attack: single spear throw (latches `mizrak_atildi=True`, never throws again), speed 12 at player, color (200,200,80), dmg 14, flagged `mizrak_mermisi=True` for line+arrowhead rendering. After throwing, continues as pure body-blocker. Visual: red eye when hedef_havada True (tell), amber otherwise.

**boss** (regular mid-boss) — 60×80, ground. HP `200*hm`. Speed `(1.0+bolum*0.05)*sm`. `para=500*mm`. Cooldown `35+rand(0,20)`. Ground-walker chase (no special AI). Attack: 3-bullet fan, angle `aci+(k-1)*0.28` (±16° spread), speed 5, color (255,68,0), dmg 18 each. Uses SMALL floating health bar (not the big boss UI — that's finalboss-only).

**finalboss (OMEGA-9)** — 110×160 (largest), fixed spawn `x=GENISLIK//2-55, y=ZEMIN_Y-160` (ignores caller-supplied x, always arena center). HP fixed **1500** (no hm scaling). `hiz_x=0` — stationary, never walks. `para=3000`. State fields: `faz` (1/2/3 HP-tier, one-way escalation at <50%/<20% HP), `boss_faz` ('saldiri'/'yorgun'), `boss_faz_timer=260`, `kalkanli=True` (shield up), `desen_idx=0` (0-2, cycles).

Shield/attack loop (every frame, `boss_faz_timer -= 1`, at ≤0):
- saldiri→yorgun: `kalkanli=False` (vulnerable), `boss_faz_timer=150` (2.5s exposed), `atis_timer=9999` (can't attack while exhausted).
- yorgun→saldiri: `kalkanli=True`, `boss_faz_timer=260` (~4.3s), `desen_idx=(desen_idx+1)%3`, `atis_timer=30`.

Attack patterns (only fire during 'saldiri'): base `sp=4+faz*1.5` (5.5/7/8.5), color (255,0,102), `hasar=20+faz*5` (25/30/35).
- desen_idx=0 "Fan": n=3(faz1)/5(faz2)/8(faz3) bullets, spread angle 0.3rad(faz1) or 0.2rad(faz2-3) per step from aim angle.
- desen_idx=1 "Wall barrage": n=4(faz1)/5(faz2+) parallel bullets all same direction at sp*0.9, 22px vertical spacing (curtain, not aimed individually).
- desen_idx=2 "Targeted volley": n=2(faz1)/3(faz2+) bullets straight at player, speed sp+3, damage hasar+5 (highest dmg: 30/35/40).

Rendering: pulsating shield ellipse while kalkanli (alpha 55/160, stroke pulses via `6+4*sin(zaman/120)`), flashing core color (200ms toggle), status label "OMEGA-9 FAZ {faz} [{durum}]" where durum="KALKANLI" (shielded) or "ZAYIF - VUR!" (weak-hit-me, the vulnerability tell). Uses special full-width bottom-of-screen health bar with name/phase/status label instead of floating bar.

### Shared attack dispatch
- `atis_yapabilir()`: mizrakli has custom throw-window logic; always False for melee/shield/suicide; False while gizli or hayalet_mod; otherwise `atis_timer<=0`.
- Cooldown table (frames, + `rand(0,20)` jitter on all): ranged:70, drone:65, sniper:35, tank:110, boss:35, finalboss:20, gorunmez:55, hayalet:65, mizrakli:75; unlisted (melee/shield/suicide, irrelevant) defaults 60.

### Buffs/debuffs shared across all types
- `dondu_kare` (RONIN freeze): fully halts update.
- `cekim_kare` (OVERDRIVE hook): 35%/frame lerp pull.
- `yavaslatildi` (HEX ulti slow): 0.4x horizontal speed.
- `zehir_kare`/`zehir_tik` (RAPTOR poison): 3 dmg every 30 frames.
- Render tints: poison = green alpha90 (60,220,90,90); frozen = ice-blue alpha130 (150,220,255,130).

`rect()` = `Rect(x,y,w,h)` (full bbox, unlike Mermi's fixed 6x6).

---

## `class Iskelet` (REAPER's summoned skeleton minion)
- 22×34. `can=max_can=35`(REAPER_ISKELET_CAN). `hasar=8`. `hiz=2.5` base. Variants: `guclu` (ulti-summoned, black-red), `okcu` (mastery ranged archer, blue). `guc_suresi=0` (E-ability empower timer).
- `guclendir()`: instant full-heal + `guc_suresi=600` (10s empowerment, speed x1.8 via REAPER_GUC_CARPAN).
- Physics: gravity 0.6/frame, lands on ground or `aktif_platformlar` (foot-crossing check).
- AI: targets nearest Dusman (SKIPS ghosts currently in `hayalet_mod`). Chase if `|dx| > 40` (REAPER_ISKELET_MENZIL) at `hiz * (1.8 if empowered else 1)`. Jump-to-reach: if grounded, cooldown ready, target ≥20px above → `hiz_y=-14` fixed jump, 40-frame jump cooldown. Within 40px → presumably melee (dmg application external to this range).
- x clamped to full `[0, GENISLIK-w]` (no 10px margin unlike enemies).
- Color priority: empowered(guc_suresi>0)=near-black+red eyes > okcu=blue+lightblue eyes > guclu(not empowered)=REAPER_ULTI_ISKELET_RENK+red eyes > plain=bone-white+dark eyes. guclu draws 3 orbiting red particles. Small floating HP bar (green>40%, else red).

## `class Xp` (survival XP pickup)
- Spawn: `hiz_y=-3.5` pop, `hiz_x=uniform(-1.5,1.5)` scatter. `deger=1` default. `omur=260` frames.
- Gravity 0.4/frame, settles at `y=ZEMIN_Y-8`, x keeps drifting forever. Despawns at omur=0 regardless of collected/landed state.
- Visual: 10px green diamond. `rect()=Rect(x-10,y-10,20,20)`.

## `class CanTopu` (health orb pickup)
- Same physics as Xp but `omur=320` (longer-lived). No `deger` field (heal amount external).
- Visual: pulsating red circle (radius 8+nabiz outer/7+nabiz inner, nabiz=1+sin(zaman/120)), white "+" icon. `rect()=Rect(x-11,y-11,22,22)`.

## `class Enkaz` (falling debris hazard)
- `buyuk` flag: size 34/hasar 30/fall-speed 5.0 (big) or size 20/hasar 18/fall-speed 6.0 (small — falls FASTER than big). `uyari_kare=40` warning telegraph before falling. `dusuyor=False` initially.
- State: warning countdown 40 frames → `dusuyor=True`, starts falling. `bitti_mi()` True once fallen past `ZEMIN_Y+20`.
- Render: blinking red vertical line during warning (every 4 frames), blinks lane position; brown chunk rect while falling. `rect()=Rect(x-s/2,y-s*0.8,s,s*0.8)`.

## `class Parca` (generic particle FX)
- Random velocity uniform(-4,4) both axes, `omur=rand(15,28)`, `boyut=rand(2,5)`px. Gravity 0.2/frame. Solid square render (alpha fade computed but NOT applied — dead code, always full opacity).
- Helper `patlama(x,y,renk=(245,166,35),sayi=12)`: spawns 12 Parca as explosion burst (standard death/hit FX factory).

## `class HasarYazisi` (floating damage number)
- `deger`,`renk`,`art` (bool, prefixes "+" for heal/gain display). Direction-biased velocity: normalized `(yon_x,yon_y)` * 1.6, extra -0.4 y-bias always added (pushes up regardless of input dir). `omur=omur_max=34` frames.
- Physics: velocity damping *0.96/frame (decelerate-to-stop, no gravity).
- Render: text=`f"+{deger}"` if art else `str(deger)`. Font: larger (fnt_or) if `deger>50` else smaller (fnt_kk) — crits render bigger. Alpha fades linearly: `255*(omur/omur_max)`.

---

## Boss-specific logic recap
- **boss**: stat-boosted standard Dusman, ground-walker AI, unique 3-bullet fan attack (±16°, speed 5, dmg 18x3). Small floating health bar (NOT the big boss UI).
- **finalboss (OMEGA-9)**: only true state-machine boss. Shield/attack toggle loop (260f attack/150f vulnerable, desen_idx 0→1→2→0 cycling each loop). HP-gated faz escalation (1→2→3 at 50%/20% HP, one-way). 3 distinct bullet patterns scaling with faz. Fixed HP (1500, no stage scaling), fixed spawn position (arena center only). Unique full-width bottom-screen boss health bar with name/phase/status label ("KALKANLI" vs "ZAYIF - VUR!").
