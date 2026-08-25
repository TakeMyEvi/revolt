# REVOLT — Game Loop / Menus / Survival Mode Spec (lines 4700-7368, game (1).py)

## 1. Game state machine

Constants: GENISLIK=900, YUKSEKLIK=550, FPS=60, ZEMIN_Y=470.

Top driver `main()`: infinite loop —
```
ilk_acilis=True
loop:
  if ilk_acilis: hikaye_ekrani(); ilk_acilis=False   # story shown once
  baslangic = ana_menu()          # blocks, returns stage# or None
  if None: continue
  sonuc = oyun(baslangic, 0, [0], 0)
  if None: continue               # paused -> menu, no result screen
  durum, skor, para = sonuc       # durum: 'kazandin'/'kaybettin'
  show win/lose screen until Enter/Esc/click -> back to ana_menu
```
`ana_menu()`: only item 0 (Oyna→1) and item 3 (Bölümler→bolum_sec() stage#) return non-None bubbling up; others (Hayatta Kal, Kahramanlar, Kontroller, Ayarlar) are awaited inline, no bubble.

Screens table:
| Screen | Entry | Exit |
|---|---|---|
| Story/Intro | main(), once | ESC skip / auto after page 3 |
| Main Menu | loop top | Oyna→1, Bölümler→stage#, Çıkış→exit |
| Stage select | Menu item 3 | stage# 1-30 or None |
| Hero select | Menu item 2 | None always, side-effect sets secili_kahraman |
| Controls | Menu item 4 | return |
| Settings | Menu item 5 | return, saves if changed |
| Credits | bottom-right link | return |
| Story-mode play | Oyna/stage-select | None (paused) or (durum,skor,para) |
| Survival play | Menu item 1 | inline, no return value used |
| Pause overlay | ESC during play | resume or return None |
| Stage-clear panel | enemies=0 & worm dead | Geri→None, Devam→bolum+1 |
| Level-up card (survival) | XP fills | click card→apply, resume |
| Win/Lose result | oyun() returns tuple | →ana_menu; "Canlan"(revive)→re-call oyun() same loadout |

Note: "Tekrar Oyna" and "Ana Menüye Dön" both just go back to ana_menu (functionally identical). Only "Canlan" (revive) actually resumes the same run.

## 2. Main loop per-frame order (story mode `oyun()`)

Outer `while bolum<=30`, inner `while True` per stage. Order:
1. tick(FPS), zaman=ticks, sonraki_bolume_gec=False
2. Events: mobile injection, QUIT, KEYDOWN(ESC=pause,R=reload,E=special1,Q=ulti,1-0=weapon switch), MOUSEDOWN-left(pause/clear buttons or fare_basili=True), MOUSEDOWN-right(hero secondary: sword throw/recall, hex beam, raptor dash, wraith phase, reaper cone, overdrive hook, ronin throw), MOUSEUP(clear fare_basili/overdrive release)
3. break inner loop if sonraki_bolume_gec
4. mouse pos (remapped if mobile)
5. PAUSE: frozen screenshot+overlay+menu, flip, sleep(0), continue (skips sim)
6. read keys (mobile-wrapped)
7. Continuous-fire (fare_basili & !bolum_bitti): per-hero primary attack, cooldown-gated
8. Player update: hero updaters (overdrive_guncelle, ronin_guncelle w/ ulti pulse), hareket_et (skipped during overdrive grapple), kilic_guncelle, hex_kitap_guncelle, raptor_guncelle, wraith_guncelle, reaper_guncelle
9. Platforms: move (bounce sol/sag), one-way landing collision (unless holding Down)
10. Spawn: final-boss stage→trickle support enemies (melee/ranged/drone/sniper) while <6 alive & finalboss exists, timer max(70,150-bolum*2); else pop spawn_sira queue, timer max(40,100-bolum*2)
11. Mizrakli group wave: if config mizrakli>0 & none alive, spawn group size rand(MIZRAKLI_GRUP_MIN,MAX) alternating edges, interval rand(180,260) first then rand(260,380); sinirsiz=True, despawn past ±400px offscreen
12. Enemies: guncelle(), passive-death cleanup, melee/shield contact dmg(15, 55f iframes), other-type contact(10dmg,50f iframes), suicide explosion(28dmg in PATLAMA_YARICAP, 55f iframes), enemy ranged fire
13. Bullets: move/expire; player bullets vs enemies/worm (dmg, kill→score+coin+ulti charge+reaper soul); enemy bullets vs player (dmg, iframes, particles)
14. Skeletons: update, engage (melee tick or archer range), death→heal player +10
15. Sword hit detection (giden/donuyor), bounce-sword hits extra enemies once at sapli
16. Raptor dash collision pass
17. Debris rain: spawns if tema_bolum>10, timer rand(150,250); collides w/ player
18. Worm trap: spawns ahead of movement direction, timer SOLUCAN_ARALIK_MIN..MAX, persists HP across respawns until killed
19. Particle/damage-number pruning
20. Death check: clamp can[0,max], overdrive immortality grace, TEST_MODU forces can=1, else can<=0→return('kaybettin',skor,para)
21. Stage-clear check: kalan=(alive non-mizrakli)+(unspawned queue); final-boss stages need no finalboss alive+worm dead; normal need kalan<=0+worm dead. Sets bolum_bitti=True, clear sound, hero-unlock flag
22. Draw: bg(parallax by oyuncu.x, themed)→platforms→HUD→stop button→debris→worm→particles→skeletons→enemies→bullets→player→dmg numbers→crosshair→stage-clear panel if bolum_bitti→mobile overlay→achievement toast
23. flip(), await asyncio.sleep(0)
24. redundant bolum>30 check (unreachable, break happens earlier)

Stage-prep (per stage): updates en_yuksek_bolum high-water mark, builds spawn_listesi from bolum_ayar(bolum) counts (melee/ranged/drone/sniper/shield/tank/suicide/gorunmez/hayalet [+boss if configured]), shuffles→spawn_sira, resets entity lists/player state, picks aktif_platformlar by theme (tema_bolum<=10 city,<=20 station,else none), final stages spawn finalboss immediately.

## 3. Survival Mode — `hayatta_kal_modu()`

### World/camera
DUNYA_GENISLIK=2700 (finite, 3x screen width). Player starts dunya_x=1350 (world center). kamera_x clamps [0,DUNYA_GENISLIK-GENISLIK], follows dunya_x-GENISLIK/2. Player's screen x stays visually fixed — horizontal input moves dunya_x directly, not oyuncu.x. toplam_mesafe=dunya_x drives bg parallax.

### Leveling/XP formula (exact)
```
SURVIVOR_XP_BASE=20, SURVIVOR_XP_ARTIS=1.3
seviye=1, xp_dolu=0, xp_gerekli=20
on levelup (xp_dolu>=xp_gerekli):
    xp_dolu -= xp_gerekli; seviye+=1
    xp_gerekli = int(20 * 1.3**(seviye-1))
```
XP needed N→N+1 = floor(20*1.3^(N-1)): L1→2=20,2→3=26,3→4=33,4→5=43,5→6=57,6→7=73,7→8=95,8→9=124,9→10=161 (~30%/level growth).

XP drop: every enemy death → `for _ in range(rand(1,3)): spawn Xp(x,y)` (mirrored across all kill sites: sword/beam/claw/soulshot/cone/ult pulse/skeleton/bullet/passive). Xp.deger added to xp_dolu on overlap (player rect inflated ±24px), snd_para(). CanTopu drops 12% chance/kill (`random()<0.12`), heals to full max_can, snd_can().

On levelup: kart_bekleniyor=True, gameplay PAUSES (movement/attacks/spawns/AI/collision gated behind `if not kart_bekleniyor`) until card clicked. Pool = YUKSELTME_HAVUZU (5 generic) + not-yet-unlocked KAHRAMAN_KART_HAVUZU[secili_kahraman] cards (only heroes 0/1/6/7/8 have specific cards), random.sample(pool, min(3,len)).

**Generic upgrades (YUKSELTME_HAVUZU):**
- hasar: oyuncu_hasar_carpan *= 1.2 (+20% dmg, stacks)
- hiz: survivor_hiz_carpan *= 1.15 (+15% speed, stacks)
- can: max_can+=25, can+=25
- saldiri: oyuncu_saldiri_carpan = max(0.35, *0.85) (-15% cooldown, floor 0.35x = max ~65% total reduction)
- regen: survivor_can_yenileme += 0.03 (stacks additively)

Hero-specific cards: one-time unlock flags (aegis_pasif_kalkan_acik, aegis_kilic_menzil_carpan*=1.35, raptor_zehir_aktif+suresi=999999(permanent), raptor_dash_sinirsiz_acik, hex_kitap_max_ozel=HEX_KITAP_MAX_USTA(6), +50/+30 can flavors, wraith_hayalet_hasar_artis_acik, wraith_ruh_heal_acik, reaper_emici_acik).

### Difficulty/spawn scaling (exact)
```
SURVIVOR_ZORLUK_ARALIK=1200 (frames, ~20s @ 60fps) per virtual-stage step
gecen_kare += 1 (each active frame, not paused/card-screen)
sanal_bolum = min(29, 1 + gecen_kare // 1200)
if sanal_bolum == 5: sanal_bolum = 6   # stage 5 config skipped/remapped
```
Stage 1: 0-20s, stage2: 20-40s...stage4: ~60-80s, jumps to stage6 for 80-100s bracket (stage5 config unused), cap 29 reached at gecen_kare>=28*1200=33600 frames (560s≈9m20s), stays 29 forever.

Spawn (weighted random, not sequential):
```
spawn_timer -= 1
if <=0:
    ayar = bolum_ayar(sanal_bolum)   # same per-stage config as story mode
    havuz = [(type,weight) for type in [melee,ranged,drone,sniper,shield,tank,suicide,gorunmez,hayalet,mizrakli] if ayar.get(type,0)>0]
    tip = weighted random pick (weight = story-mode count for that type/stage)
    spawn 1 enemy (or mizrakli group alternating sides, size MIZRAKLI_GRUP_MIN..MAX) off edge, .sinirsiz=True
    spawn_timer = max(25, 70 - sanal_bolum*2)   # floor 25 frames (~0.42s)
```
sinirsiz enemies never despawn from "remaining count" (survival has no clear condition, endless).

**Mini-boss**: every SURVIVOR_ZORLUK_ARALIK*10=12000 frames (200s≈3m20s) [or 300f in TEST_MODU], spawn 'boss'-type Dusman from random edge. Fixed interval (not accelerating).

**Anti-kite rubber-band**: non-mizrakli enemies with |d.x-oyuncu.x|>400: excess beyond 400px closed by `d.x -= excess*0.03`/frame.

### Death
```
can = clamp(0,max_can)
if TEST_MODU and can<=0: can=1   # never actually die (debug)
elif can<=0: snd_karakter_olum(); break   # -> summary screen
```
No tuple returned (unlike story mode) — inline end screen.

### Score/tracking
- Local: oldurulen (kills), gecen_kare (frames→time), seviye. **No coin/skor economy** in survival (unlike story mode).
- On death: `EN_UZUN_HAYATTA_KALMA = max(EN_UZUN_HAYATTA_KALMA, gecen_kare/FPS)` — in-memory only, disk write happens later via kayit_kaydet() trigger (see §5).
- oldurulen kills also increment global TOPLAM_OLDURULEN via Dusman.can property setter (any can>0→<=0 transition, any mode) — also updates KAHRAMAN_HASAR[secili_kahraman] mastery tracker.
- **Summary screen**: elapsed MM:SS, level, kills. "Ana Menüye Dön"/ESC → None to ana_menu.

### Frame order parity with story mode
events→(pause short-circuit)→if !kart_bekleniyor: input/movement/camera-scroll/hero-updaters→ulti-charge-on-kill sync (oldurulen delta drives ulti_sarj_ekle/reaper_ruh_ekle)→skeletons→primary-attack branch→gecen_kare+=1→sanal_bolum recompute→spawn timer→mini-boss timer→enemies update/contact/attacks→bullets→XP pickup→health-orb pickup→particles/dmg-numbers→death clamp/check→levelup check→draw(bg/entities/HUD w/ can-bar,XP-bar,level,timer,kills/stop-button/crosshair/levelup-card overlay/mobile/toast)→flip()→sleep(0).

## 4. Menu screens

### Main Menu (7 buttons, 240x44px centered, y=165+i*52, Up/Down+Enter or mouse):
1. Oyna → returns 1 (start story stage1)
2. Hayatta Kal → hayatta_kal_modu()
3. Kahramanlar → kahraman_sec()
4. Bölümler → bolum_sec(), if non-None returns stage#
5. Kontroller → kontroller_ekrani()
6. Ayarlar → ayarlar_ekrani()
7. Çıkış → quit process

Bottom-right "Krediler" link → kredi_ekrani(). BG/music theme by en_yuksek_bolum: <=10 Metropol, <=20 Derin Uzay, else Harabe. Logo or fallback text. **After ANY mouse-click menu action → kayit_kaydet() unconditionally** (main persistence trigger). Keyboard(Enter) path does NOT save.

### Stage Select (3 pages METROPOL/DERIN UZAY/HARABE, 10 stages/page, 5x2 grid):
Chaos stages (triangle icon): page-local index 4,8 = absolute stages 5/15/25 and 9/19/29. Unlocked if TEST_MODU or bolum_no<=en_yuksek_bolum. Hero-unlock stages show hero name label above button. Arrows/wheel change page (wrap 0-2). ESC/Geri→None. Click unlocked→returns stage#.

### Hero Select
Full-screen team poster (EKIP_AFIS_GORSELLERI, chosen by unlock-cluster), 7 invisible click regions at EKIP_AFIS_FRACS fractions, order [0,1,6,7,8,5,9]. Color bar: green=selected,cyan=hover,gray=unlocked-unselected. Name or "?????" if locked (en_yuksek_bolum<acilis_bolum & !TEST_MODU). Click unlocked→sets secili_kahraman. "YUKSELT" button→modal w/ 2 tabs:
- KAHRAMANLAR: per-hero pill selector, mastery bar (KAHRAMAN_HASAR[id] vs tiered thresholds), unlockable ability rows (click toggles KAHRAMAN_YETENEK_KAPALI membership), Overdrive-only "SALINIM SISTEMI" row at OVERDRIVE_SALLANMA_ESIGI dmg.
- GENEL: GENEL_GOREVLER list, TAMAMLANDI/AÇIK DEĞİL via kontrol_fn() predicate.
ESC/D or Geri/Kapat closes.

### Settings
SFX vol(±10%), Music vol(±10%, also muzik_ses_guncelle()), crosshair color swatches, crosshair shape+preview, language selector(DILLER), "İmleç Gizle" toggle, "Mobil Kontroller" toggle (reveals draggable joystick/fire-button position editor writing AYAR_MOBIL_JOY_POS/AYAR_MOBIL_ATES_POS). Any change→kaydet_gerek=True. Exit(ESC/Geri/QUIT)→kayit_kaydet() iff kaydet_gerek.

### Controls
Static: title + 7 translated lines (kontrol_1..7). ESC/Enter/click/Geri→return.

### Credits
Scrolling-bg list from KREDI_LISTESI (name—artist, license tag right-aligned, ellipsis-truncated), "freesound.org" footer. ESC/Enter/click→return.

### Story/Intro
3 pages lore text, shown only on first launch (ilk_acilis flag). SPACE/Enter advance (auto-return after page3), ESC skip.

## 5. Save/load (`kayit.json`)

Path: web→relative 'kayit.json'; frozen exe→next to exe; dev→next to script.

`kayit_yukle()` (called once at import): populates globals, wrapped in broad except (missing keys/corrupt file → defaults):

| JSON key | Global | Notes |
|---|---|---|
| en_yuksek_bolum | en_yuksek_bolum | max(1,int(...)) |
| kahraman_hasar | KAHRAMAN_HASAR dict | merged key-by-key |
| toplam_oldurulen | TOPLAM_OLDURULEN | lifetime kills, drives "AVCI" achievement (>=150) |
| en_uzun_hayatta_kalma | EN_UZUN_HAYATTA_KALMA | best survival seconds |
| ses_seviyesi | AYAR_SES_SEVIYESI | clamp[0,1] |
| muzik_seviyesi | AYAR_MUZIK_SEVIYESI | clamp[0,1] |
| nisangah_renk_idx | AYAR_NISANGAH_RENK_IDX | clamped valid index |
| nisangah_sekil_idx | AYAR_NISANGAH_SEKIL_IDX | clamped valid index |
| imlec_gizli | AYAR_IMLEC_GIZLI | bool |
| mobil_kontrol | AYAR_MOBIL_KONTROL | bool |
| mobil_joy_pos | AYAR_MOBIL_JOY_POS | [x,y] validated |
| mobil_ates_pos | AYAR_MOBIL_ATES_POS | [x,y] validated |
| dil | AYAR_DIL | validated vs DILLER, default 'tr' |
| yetenek_kapali | KAHRAMAN_YETENEK_KAPALI set | "{hid}_{idx}" strings→tuples |

`kayit_kaydet()`: writes same key set (json.dump, no indent), swallows OSError.

**Write triggers (only 2 call sites):**
1. ayarlar_ekrani() on ESC/QUIT/Geri, iff kaydet_gerek (setting actually changed).
2. ana_menu() unconditionally after ANY mouse-click menu selection resolves. This is how oyun()/hayatta_kal_modu() progress (en_yuksek_bolum, KAHRAMAN_HASAR, TOPLAM_OLDURULEN, EN_UZUN_HAYATTA_KALMA) reaches disk — written next time player returns to menu and clicks with mouse. Keyboard-only nav does NOT trigger save (potential progress loss if player only uses keyboard then quits).

en_yuksek_bolum updated live at top of every stage: `en_yuksek_bolum=max(en_yuksek_bolum,bolum)` — but only persisted via the two triggers above.

## 6. main() entry point / async loop

```python
async def main():
    ilk_acilis=True
    while True:
        if ilk_acilis: await hikaye_ekrani(ekran); ilk_acilis=False
        baslangic = await ana_menu()
        if baslangic is None: continue
        sahip_silahlar=[0]; secili=0; toplam_para=0
        sonuc = await oyun(baslangic, toplam_para, sahip_silahlar, secili)
        if sonuc is None: continue
        durum, skor, para = sonuc
        # inline win/lose loop, own event poll/flip/sleep(0)
        # Tekrar Oyna / Ana Menüye Dön both just break -> ana_menu
        # Canlan (revive, lose only) re-calls oyun() same loadout, no menu bounce
asyncio.run(main())
```

Key points:
- EVERY screen/sub-loop (play, pause, stage-clear wait, levelup-card wait, summary, win/lose) is its own `while True`: tick(FPS)→build frame→flip()→**await asyncio.sleep(0)**→poll events. The sleep(0) after every flip is the pygbag/Emscripten requirement (yields to browser event loop each frame; no-op on desktop). Applied uniformly, no exceptions (including inside pause's continue path).
- saat.tick(FPS) enforces 60fps cap.
- Loadout hardcoded fresh each run in main(): sahip_silahlar=[0], secili=0, toplam_para=0 — NO persistent economy/loadout between runs. para/skor from a stage only carries forward via "Canlan" revive path, never written to kayit.json.
- pygame.quit();sys.exit() only exit path (menu Çıkış or any QUIT event).
- Module ends with bare `asyncio.run(main())`.
