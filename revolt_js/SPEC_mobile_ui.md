# REVOLT — Mobile Controls / UI Widgets / HUD / Menus Spec (lines 3420-4700, game (1).py)

Note: camera/level/boss logic is NOT in this range — it's inside `oyun()` at line 4700+, covered in SPEC_gameloop_menus_survival.md.

## A. Mobile/Touch controls (`_SanalTuslar`, `MobilKontrol`)

### A.1 `_SanalTuslar` — wraps pygame.key.get_pressed() so tuslar[K_x] works unmodified with virtual joystick OR'd in:
```
K_LEFT,K_a -> gercek[tus] OR sol
K_RIGHT,K_d -> gercek[tus] OR sag
K_UP,K_w,K_SPACE -> gercek[tus] OR yukari   (space aliased to jump/up)
K_DOWN,K_s -> gercek[tus] OR asagi
else -> gercek[tus]
```

### A.2 Layout
| Element | Center | Radius/Size |
|---|---|---|
| Movement joystick | AYAR_MOBIL_JOY_POS | 60px radius, user-repositionable |
| Fire/aim joystick | AYAR_MOBIL_ATES_POS | 60px radius, twin-stick continuous fire |
| SPECIAL button | rel to fire center (ax-129,ay+3) | 58x58, posts MOUSEBUTTONDOWN button=3 |
| E button | (ax-129,ay-83) | 50x50, posts KEYDOWN K_e |
| Q button | (ax-193,ay-45) | 50x50, posts KEYDOWN K_q |

### A.3 Hit-test: `hypot(x-cx,y-cy) <= radius*1.7` (102px catch zone on 60px stick, 70% generous margin)

### A.4 Direction mapping: `oran=min(1.0, dist/radius)`, output=(dx/dist*oran, dy/dist*oran). Full deflection reached at drag distance >= 60px (radius); beyond that no additional effect (visually clamped to ring).

### A.5 Touch lifecycle (priority order on touch-down):
1. Inside move-joystick → claim finger, compute joy_dx/dy
2. Inside SPECIAL rect → synthetic MOUSEBUTTONDOWN(button=3)
3. Inside E rect → synthetic KEYDOWN(K_e)
4. Inside Q rect → synthetic KEYDOWN(K_q)
5. Inside fire-joystick → claim finger, ates_basili=True
6. Else (only for real touch, not mouse) → claim as free-drag aim finger, aim_konum=(x,y)

Touch-move: updates matching finger's dx/dy or aim_konum. Touch-up: clears finger id, joystick self-centers instantly (no spring, dx/dy=0).
Each finger tracked independently — true multi-touch (hold move+fire+tap E/Q simultaneously). Mouse uses synthetic 'mouse' id through same handlers (single-cursor, sequential only).
Real touch coords: `olay.x*GENISLIK, olay.y*YUKSEKLIK` (normalized 0..1 from pygame FINGERDOWN/MOTION/UP).
Mouse can only start a drag if inside a stick/button hit zone (`_mouse_hedef_mi`) — mouse never populates free-drag aim (branch 6 unreachable from mouse).

### A.6 Digital dead zones (asymmetric!):
```
sol = joy_dx < -0.35
sag = joy_dx > 0.35
yukari = joy_dy < -0.40
asagi = joy_dy > 0.55   # down needs much bigger push than up — makes accidental crouch harder
```

### A.7 Aim resolution `nisan_konumu(def_x,def_y,player_cx,player_cy)` priority:
1. Fire-joystick held + player coords given → aim = player_center + (ates_dx,ates_dy)*400 (projects 400px in stick direction, twin-stick aiming)
2. Free-drag aim active → raw touch position
3. Fallback → passed default (mouse position on desktop)

### A.8 Rendering: translucent white ring (alpha70, 3px) + filled knob (24px radius) clamped to ring edge at full deflection. Move-stick knob=CYAN, fire-stick=SARI. Buttons: dark ellipse bg(alpha140)+outline+label — SPECIAL=TURUNCU, E=(120,220,255), Q=(255,120,220).

## B. Generic UI widgets

- `buton_ciz()`: reusable button, hover swaps colors (hover: text/border (0,255,200) fill(20,45,40); normal: TURUNCU/black). 2px border.
- `GERI_BUTON_RECT = Rect(10,10,92,32)` — fixed top-left back button, reused everywhere.
- `can_sayisi_ciz()`: draws numeric HP twice (filled-color + empty-color) with clip regions split at the health-bar fill boundary — digits change color exactly at the fill line.

## C. HUD (`hud_ciz`)

Top bar: black Rect(0,0,900,42), cyan 2px border.

**Health bar**: Rect(10,11,120,14), bg(30,30,30). Fill by ratio: YESIL>0.5, TURUNCU>0.25, else KIRMIZI. 1px cyan border.

**Secondary cooldown bar** (below health, Rect(10,27,120,8)) — one branch per hero mode:
| Mode | Constant | Ready color |
|---|---|---|
| aegis_modu | KILIC_ATMA_BEKLEME | CYAN |
| hex_modu | text "KITAP: n/max" instead of bar | MOR |
| raptor_modu | RAPTOR_DASH_BEKLEME | YESIL |
| wraith_modu | text "RUH: n/100" | — |
| reaper_modu | segmented pip bar, REAPER_RUH_BOLME_MAX boxes 11px+1px gap | (205,45,40) |
| overdrive_modu | OVERDRIVE_KANCA_BEKLEME | SARI (cooldown dim (110,90,0)) |
| ronin_modu | RONIN_FIRLAT_BEKLEME | (170,120,255) (cooldown (90,60,140)) |

Cooldown fill formula: `oran=1-bekleme_kalan/BEKLEME_SABIT`.

**Special-ability bar** (Rect(kx=175,ky=11,kw=80,kh=14)), per mode + label:
- reaper: REAPER_E_BEKLEME, "E:GUCLENDIR", (205,45,40)
- wraith: ratio min(1,ruh/WRAITH_HAYALET_MALIYET), (150,230,220) if enough else grey, "SAG:HAYALET E:IYILES"
- raptor: raptor_kacis_aktif full-white / RAPTOR_KACIS_BEKLEME, "E:KACIS", YESIL border
- hex: HEX_HEAL_SURESI active(green) / HEX_HEAL_BEKLEME cooldown(grey), "E:IYILESTIR", cyan border
- overdrive: OVERDRIVE_E_BEKLEME, "E:PATLAT", SARI
- ronin: RONIN_E_BEKLEME, "E:GIZLEN", (170,120,255)
- default(no hero mode): shield gauge — kalkan_aktif→kapasite/KALKAN_KAPASITE CYAN; else KALKAN_BEKLEME cooldown; "E:KALKAN"

**Ultimate bar** (Rect(560,11,60,14)):
- reaper: reaper_ruh_bolme/REAPER_RUH_BOLME_MAX, (205,45,40), "Q:ISKELET CAGIR"
- others: full gold (255,215,0) if ulti_aktif/raptor_ulti_aktif/wraith_ulti_aktif; else ulti_dolu/ULTI_MAX SARI. "Q:ULTI"

**Center text**: "{bölum} {n}/30  {düşman}:{count}" — **confirms 30 total stages**.
**Score**: "SKOR:{skor}" white, pos (GENISLIK-220,13).
**Bottom-left hint** (10,YUKSEKLIK-22): per-class static string (e.g. "KILIC - AEGIS" cyan, "SOL:BUYU SAG:ISIN - HEX" purple, "SOL:PENCE SAG:HAMLE - RAPTOR" green, "SOL:ALAN VURUSU SAG:ATIS - REAPER" red, "SOL:RUH CISMI SAG:HAYALET - WRAITH" teal, "SOL:ATES SAG:KANCA E:PATLAT - OVERDRIVE" yellow, "SOL:ITIS SAG:FIRLAT E:GIZLEN - RONIN" violet). Default: weapon charge-bar (44x6px above player) + weapon icon/name.

## D. Achievement toast (`basarim_bildirim_guncelle_ciz`)

Queue BASARIM_KUYRUGU, active slot [baslik,alt_yazi,kalan_frames=BASARIM_SURESI(220)]. Plays snd_kahraman_acildi() on show. Panel 300x62, base pos (16,YUKSEKLIK-62-16), bg alpha225, SARI 2px border.
Slide anim: entry (first 18f) slides in from left via `oran=(220-kalan)/18, kayma=(1-oran)*(w+24)`; exit (last 18f) same formula reversed. `x = 16-kayma`.
Icon: yellow medal circle r=17 w/ 5-pip pentagon pattern. Subtitle at (x+58,y+12) SARI, title at (x+58,y+32) BEYAZ.

## E. Story screen — see SPEC_gameloop_menus_survival.md §4 (already covered there)

## F. Settings screen — see SPEC_gameloop_menus_survival.md §4 (already covered there), additional pixel detail:
- SFX vol -/+ rects (560,96,34,30)/(690,96,34,30), 0.1 steps
- Music vol -/+ rects (560,150,34,30)/(690,150,34,30)
- Crosshair color swatches Rect(150+i*76,260,62,36)
- Crosshair shape rects Rect(150+i*140,340,124,38), live preview at (780,358) in 80x80 box
- Language rects Rect(150+i*72,388,64,28)
- Cursor-hide toggle Rect(150,424,460,30)
- Mobile toggle Rect(150,460,460,30)
- Mobile stick editor: preview rect (560,96,260,159), scale=260/900. Drag within 16px of scaled stick center to reposition; writes directly into AYAR_MOBIL_JOY_POS/AYAR_MOBIL_ATES_POS (same objects MobilKontrol reads).

## G. Level select — see SPEC_gameloop_menus_survival.md §4, additional pixel detail:
- 2 rows x 5 cols per page. spacing=GENISLIK/5. Row Y: ust=YUKSEKLIK/2-48, alt=YUKSEKLIK/2+48. Col x=spacing*(col+0.5). Button 62x56.
- Chaos-level triangles at local index 4,8 (global 5/15/25, 9/19/29).
- Locked overlay: alpha150 black, dim border/text (55,55,65)/(95,95,95).
- Nav arrows Rect(6,YUKSEKLIK/2-30,40,60) and Rect(GENISLIK-46,...,40,60), + MOUSEWHEEL, + 3 page-dot indicators. Wraps mod 3.

## H. Hero select / mastery panel — see SPEC_gameloop_menus_survival.md §4, additional pixel detail:
- Poster chosen: highest EKIP_AFIS_ACIK_KUMELERI[i] subset of unlocked-hero-id-set (poster art itself upgrades as heroes unlock, never shows colorized-locked hero).
- 7 hitboxes as FRACTIONS of poster width: EKIP_AFIS_SIRA=[0,1,6,7,8,5,9] at EKIP_AFIS_FRACS=[0.09,0.22,0.35,0.49,0.62,0.75,0.88]. Width=poster_w*0.125, height=poster_h*0.66, top=poster_top+poster_h*0.22.
- Mastery panel toggle button Rect(GENISLIK-150,6,130,28). Modal alpha190 over Rect(90,60,GENISLIK-180,YUKSEKLIK-120).
- Mastery progress: `(hasar_toplam-onceki_esik)/(sonraki_esik-onceki_esik)` clamped[0,1]. Tier rows 44px tall, 54px pitch.
- Hero 5(Overdrive) extra row: "SALINIM SISTEMI" at OVERDRIVE_SALLANMA_ESIGI(2500) dmg.

## Constants referenced (values defined elsewhere, already known):
AYAR_MOBIL_JOY_POS, AYAR_MOBIL_ATES_POS, AYAR_SES_SEVIYESI, AYAR_MUZIK_SEVIYESI, AYAR_NISANGAH_RENK_IDX, AYAR_NISANGAH_SEKIL_IDX, AYAR_IMLEC_GIZLI, AYAR_MOBIL_KONTROL, AYAR_DIL, NISANGAH_RENKLERI, NISANGAH_SEKILLERI, DILLER, DIL_ISIMLERI, KILIC_ATMA_BEKLEME, RAPTOR_DASH_BEKLEME, WRAITH_RUH_MAX, REAPER_RUH_BOLME_MAX, OVERDRIVE_KANCA_BEKLEME, RONIN_FIRLAT_BEKLEME, KALKAN_KAPASITE, KALKAN_BEKLEME, HEX_HEAL_SURESI, HEX_HEAL_BEKLEME, REAPER_E_BEKLEME, WRAITH_HAYALET_MALIYET, RAPTOR_KACIS_BEKLEME, OVERDRIVE_E_BEKLEME, RONIN_E_BEKLEME, ULTI_MAX, BASARIM_SURESI, TEST_MODU, KAHRAMANLAR, KAHRAMAN_YUKSELTMELERI, KAHRAMAN_HASAR, KAHRAMAN_YETENEK_KAPALI, GENEL_GOREVLER, OVERDRIVE_SALLANMA_ESIGI, EKIP_AFIS_GORSELLERI, EKIP_AFIS_ACIK_KUMELERI, GERI_BUTON_RECT, GENISLIK, YUKSEKLIK, FPS.
