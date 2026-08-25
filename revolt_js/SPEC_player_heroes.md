# `class Oyuncu` — Player/Heroes Spec (lines 1136–2240, game (1).py)

## 1. Shared/Generic Player State (all heroes)

**Core fields:** `x=150.0, y=ZEMIN_Y-48` (float pos), `w=28,h=48` hitbox, `hiz_x=0,hiz_y=0` velocity, `yerde` grounded, `can=100,max_can=100`. `anim_frame` (0-3), advances every 8 frames. `hasar_timer`: while >0, ciz() skips drawing when `hasar_timer%6<3` (blink-on-hit). Generic gun: `silah_idx, sarjor, doluyor, dolum_timer, atis_timer`.

**Generic Shield:** `kalkan_baslat()`: if `kalkan_bekleme<=0` and inactive → active, `kalkan_kapasite=KALKAN_KAPASITE`(70), `kalkan_suresi=KALKAN_SURESI`(300). `kalkan_kapat()`: deactivate, `kalkan_bekleme=KALKAN_BEKLEME`(360). Ticks in hareket_et.

**Generic Ultimate (jetpack-style):** `ulti_sarj_ekle(m=ULTI_SARJ_OLUM)`: `ulti_dolu=min(ULTI_MAX,ulti_dolu+m)`. `ulti_kullan()`: if `ulti_dolu>=ULTI_MAX(100)` and inactive → active, `ulti_suresi=ULTI_SURESI`(480), `ulti_dolu=0`, `can=min(max_can,can+ULTI_CAN_ARTISI)`(+25). While active: FULL damage immunity, free-flight movement, ticks down, auto-deactivate at 0. Visual: pulsing gold aura radius `max(w,h)+26+nabiz`, nabiz=4+3*sin(ticks/90); jetpack flames under feet.

**`hasar_al(miktar)` damage pipeline (exact order):**
1. If `ulti_aktif` OR `raptor_kacis_aktif` OR `wraith_hayalet_aktif` → return 0 (full immune)
2. `aegis_hasarsiz_kare=0` (any hit resets AEGIS passive-shield charge timer)
3. If `aegis_pasif_kalkan>0`: absorb min(miktar,pasif) first; fully absorbed → return 0
4. Elif `wraith_ulti_aktif`: `can -= miktar*WRAITH_ULTI_HASAR_CARPAN`(0.1); return
5. Elif `ronin_itis_zirh>0`: `can -= miktar*0.3` (70% reduction); return
6. Elif `kalkan_aktif`: absorb min(miktar,kalkan_kapasite) from shield, remainder from can; closes shield if capacity hits 0
7. Else: `can -= miktar` directly

**`hareket_et(tuslar,fare_pos)` movement/physics (every frame):**
- Base speed: `raptor_hizli→RAPTOR_HIZ_X`(7), elif `wraith_yavas→WRAITH_HIZ`(3.5), elif `reaper_agir→REAPER_HIZ`(4), else `5`.
- Multipliers (order): ×RAPTOR_ULTI_HIZ_CARPAN(1.6) if raptor_ulti_aktif, elif ×RAPTOR_OFKE_HIZ_CARPAN(1.25) if raptor_ofke_aktif; ×WRAITH_ULTI_YAVAS_CARPAN(0.25) if wraith_ulti_aktif; ×OVERDRIVE_ULTI_YAVAS_CARPAN(0.18) if overdrive_ulti_aktif; ×survivor_hiz_carpan (Survival upgrade, 1.0 campaign).
- Horizontal: 0 unless raptor_kacis_aktif/raptor_dash_aktif (locked); else L/A→-speed, R/D→+speed.
- **Vertical — 3 branches:**
  - Free flight (`ulti_aktif` or `daima_ucar`[HEX]): `ucus_hiz=WRAITH_UCUS_HIZ(3) if wraith_yavas else 5`, ×WRAITH_ULTI_YAVAS_CARPAN if active. Up→hiz_y=-ucus_hiz, Down→+ucus_hiz, neither→hiz_y*=0.85. yerde=False. Y∈[44,ZEMIN_Y-h].
  - RAPTOR 3-tier jump: ground+Up→hiz_y=RAPTOR_ZIPLAMA_BASLANGIC(-9), start hold-tracking. While held & raptor_zip_kare<RAPTOR_ZIPLAMA_MAX_KARE(26) & rising: hiz_y=max(RAPTOR_ZIPLAMA_MIN_HIZ(-20), hiz_y+RAPTOR_ZIPLAMA_ITKI(-0.9)) per frame. Gravity +0.6/frame always.
  - Standard: ground+Up→hiz_y=-14; release early while hiz_y<-5→clip to -5 (short-hop). Gravity +0.6/frame.
- Integrate x+=hiz_x, y+=hiz_y. Floor clamp y>=ZEMIN_Y-h→yerde=True (non-flight); x always clamped [0,GENISLIK-w].
- Also ticks: hasar_timer, atis_timer, survivor_can_yenileme regen, AEGIS passive shield charge, shield/ulti/reload countdowns.

**`ates_et(fare_x,fare_y,mermi_listesi)` generic ranged basic attack** (plays snd_overdrive_ates — this IS Overdrive's left-click, reuses shared SILAHLAR weapon table):
- No-op if atis_timer>0 or doluyor. If sarjor<=0 → reload_baslat() and return.
- atis_timer = max(1,s['atis_hizi']//2) if overdrive_hizli_ates_acik else s['atis_hizi'].
- sarjor-=1; if overdrive_sinirsiz_mermi: sarjor=s['sarjor'] (infinite ammo refill).
- Origin cx=x+w/2, cy=y+h*0.38. Loop range(2 if cift else 1)×range(sacma): spread angle (i-(sacma-1)/2)*0.25 rad if sacma>1; spawn Mermi per pellet with weapon's renk/hasar/mermi_hizi.
- reload_baslat(): if not reloading and sarjor<full → doluyor=True, dolum_timer=s['dolum']; completes in hareket_et.

---

## 2. AEGIS (id 0)

**Sword state machine** (`kilic_durum`: beklemede/giden/sapli/donuyor):
- `kilic_el_konumu()` = (x+w/2, y+h*0.38) hand anchor.
- `kilic_firlat(hx,hy)` throw: no-op unless beklemede & atma_bekleme<=0. dir=normalize(target-hand). hiz=dir*KILIC_HIZI(17). state→giden, atma_bekleme=KILIC_ATMA_BEKLEME(300), sekme_yapildi=False.
- `kilic_geri_cagir()`: if giden/sapli → state=donuyor.
- `kilic_savur_rect(fx,fy)` melee swing (left-click): mesafe=30*menzil_carpan, boyut=48*menzil_carpan, hitbox at hand+dir*mesafe.
- `kilic_guncelle()`: giden state integrates position, sticks (sapli) at mesafe>=KILIC_MENZIL(480) or bounds exit. donuyor: homes to hand at KILIC_HIZI, catches (beklemede) at dist<20.
- `kilic_rect()` = Rect(kx-8,ky-8,16,16).

**Passive shield:** if aegis_pasif_kalkan_acik: hasarsiz_kare+=1/undamaged frame; at >=AEGIS_PASIF_KALKAN_ARALIK(300) resets counter, pasif_kalkan=min(AEGIS_PASIF_KALKAN_MAX(40), pasif+AEGIS_PASIF_KALKAN_ARTIS(8)). Reset to 0 on any damage.

**Masteries:** aegis_kilic_menzil_carpan (scales swing, def 1.0, AEGIS_KILIC_MENZIL_ARTIS=0.35/tier), aegis_kilic_sekme_acik (bounce, up to AEGIS_KILIC_SEKME_MAKS=5 enemies).

**Q=generic ulti. Right-click=generic shield.**

---

## 3. RAPTOR (id 1)

**Movement:** RAPTOR_HIZ_X(7), 3-tier jump (see §1).

**Dash:** while raptor_dash_aktif: x+=RAPTOR_DASH_HIZI(14)*yon/frame; raptor_dash_suresi(12) counts down; else raptor_dash_bekleme(90) cooldown. dash_vurulanlar tracks hit enemies (no double-hit).

**Claw (left-click, inferred):** raptor_pence_bekleme(12) cooldown. Damage RAPTOR_PENCE_HASAR(18), lifesteal RAPTOR_PENCE_YASAM_CALMA(0.3 of dmg).

**E — `raptor_kacis_baslat(yon)`:** comment confirms "E: only enters poison mode, no dash". Gated raptor_kacis_bekleme<=0 & not raptor_zehir_aktif. Sets kacis_bekleme=RAPTOR_KACIS_BEKLEME(240), zehir_aktif=True, zehir_suresi=RAPTOR_ZEHIR_SURESI(480). Green tint overlay while active. raptor_zehir_patlama_acik mastery (explosion, RAPTOR_ZEHIR_PATLAMA_YARICAP=110).
Note: separate unused-here `raptor_kacis_aktif` flag grants full immunity in hasar_al + locks hiz_x — an escape-dash variant exists in the immunity/movement code but E only triggers poison in this range.

**Rage (upgrade proc):** raptor_ofke_aktif: speed×RAPTOR_OFKE_HIZ_CARPAN(1.25), damage×RAPTOR_OFKE_CARPAN(1.3), duration RAPTOR_OFKE_SURESI(180). Gated raptor_ofke_acik mastery.

**Ulti (Q):** raptor_ulti_aktif/suresi(300). Speed×RAPTOR_ULTI_HIZ_CARPAN(1.6), claw dmg×RAPTOR_ULTI_PENCE_CARPAN(1.8). Green aura, radius max(w,h)+22+nabiz(3+2sin(t/80)).

---

## 4. WRAITH (id 7)

**Movement:** WRAITH_HIZ(3.5) ground, WRAITH_UCUS_HIZ(3) flight (since wraith_yavas true). ×WRAITH_ULTI_YAVAS_CARPAN(0.25) while ulti active.

**Soul (`wraith_ruh`, max WRAITH_RUH_MAX=100):** `wraith_ruh_ekle(m)`: ruh=min(max,ruh+m); if wraith_ruh_heal_acik mastery: can+=m*WRAITH_RUH_OTO_HEAL_ORAN(0.3) (passive lifesteal-on-soul-gain).

**Ghost mode (E, inferred) `wraith_hayalet_baslat()`:**
- If wraith_hayalet_usta_acik: only cooldown gate (no soul cost) → suresi=WRAITH_HAYALET_USTA_SURESI(480).
- Else: costs WRAITH_HAYALET_MALIYET(40) soul → suresi=WRAITH_HAYALET_SURESI(90).
- Full immunity + alpha 130 (transparency). On expiry (mastery variant): bekleme=WRAITH_HAYALET_USTA_BEKLEME(300).
- wraith_hayalet_hasar_artis_acik: +30% dmg while ghosted (WRAITH_HAYALET_HASAR_ARTIS_CARPAN=1.3, applied outside range).

**Heal (right-click, inferred) `wraith_heal_baslat()`:** if bekleme<=0 & ruh>0: can+=ruh*WRAITH_HEAL_ORAN(0.6), consumes ALL soul, bekleme=WRAITH_HEAL_BEKLEME(200).

**Ulti (Q):** suresi=WRAITH_ULTI_SURESI(240). Incoming dmg×WRAITH_ULTI_HASAR_CARPAN(0.1 — 90% reduction), speed×WRAITH_ULTI_YAVAS_CARPAN(0.25). Teal aura, radius max(w,h)+30+nabiz(4+3sin(t/100)).

---

## 5. REAPER (id 8)

**Movement:** REAPER_HIZ(4), reaper_agir flag.

**Soul-split:** reaper_ruh_bolme, `reaper_ruh_ekle()` +1, capped REAPER_RUH_BOLME_MAX(10) (governs summoned skeleton count, spawn logic outside class).

**Cooldowns/visuals:** reaper_vurus_bekleme(REAPER_VURUS_BEKLEME=45)+goster(8f anim, arc radius REAPER_VURUS_MENZIL(150)*(1-g/8), ±REAPER_VURUS_ACI(0.75)). reaper_atis_bekleme(REAPER_ATIS_BEKLEME=55)+goster (arc REAPER_ATIS_MENZIL(220)*(1-g/8), ±REAPER_ATIS_ACI(0.95)). reaper_e_bekleme(REAPER_E_BEKLEME=700), no goster. Eye sockets flash red while active.

**Masteries:** reaper_e_ek_iskelet_acik, reaper_atis_iskelet_acik, reaper_ulti_okcu_acik, reaper_emici_acik (REAPER_EMICI_ORAN=0.25 lifesteal card). No dedicated ulti state — reuses generic ulti_* or driven by external skeleton spawning.

---

## 6. OVERDRIVE (id 5)

**Grapple hook** (`kanca_durum` ∈ yok/ucuyor/bagli/sallaniyor):

- **sallaniyor (swinging):** yercekimi=0.6*(OVERDRIVE_ULTI_YAVAS_CARPAN if ulti else 1.0). ivme=(yercekimi/max(30,ip_uzunlugu))*cos(aci); acisal_hiz+=ivme. Pumping: yon_isaret=1 if sin(aci)>=0 else -1; R/D held→acisal_hiz-=OVERDRIVE_KANCA_POMPA(0.0022)*yon_isaret; L/A→+=. Damping ×0.999/frame. aci+=acisal_hiz. Pos=anchor+cos/sin(aci)*ip_uzunlugu (fixed rope length, true pendulum). x∈[0,GENISLIK-w], y∈[46,ZEMIN_Y-h].
- **ucuyor (flying to point):** moves at OVERDRIVE_KANCA_UCUS_HIZI(11)*(yavas_carpan if ulti), snaps+state=yok at arrival (travels path, not instant teleport).
- `overdrive_sallan()` release: sets durum=yok, keeps momentum.
- Ticks: kanca_bekleme(OVERDRIVE_KANCA_BEKLEME=34), e_bekleme/e_goster, ulti_aktif/suresi(OVERDRIVE_ULTI_SURESI=420), olumsuzluk_kalan (post-ulti death-proof grace, independent).

**Left-click = generic ates_et** (SILAHLAR table). overdrive_hizli_ates_acik (half cooldown), overdrive_sinirsiz_mermi (infinite ammo).

**E ability:** e_bekleme(OVERDRIVE_E_BEKLEME=130) cooldown; e_goster 10f anim, AoE ring radius OVERDRIVE_E_MENZIL(75)*(1-g/10). Damage OVERDRIVE_E_HASAR(55), self-heal OVERDRIVE_E_CAN_YENILEME(+20).

**Ulti (Q):** OVERDRIVE_ULTI_YAVAS_CARPAN(0.18) slows grapple/movement (bullet-time). overdrive_ulti_olumsuz_acik grants olumsuzluk_kalan grace ticks persisting after ulti ends. OVERDRIVE_ULTI_CAN_KAZANC=10 heal per kill while ulti active.

**Masteries:** overdrive_kanca_heal_acik, overdrive_ulti_olumsuz_acik, overdrive_hizli_ates_acik, overdrive_sinirsiz_mermi. OVERDRIVE_SALLANMA_ESIGI=2500 total dmg unlocks swing system.

**Visual:** dotted aim-line when durum==yok, 11px spacing from 16px, up to min(dist,OVERDRIVE_KANCA_MENZIL=3000). Yellow if bekleme<=0 else grey.

---

## 7. RONIN (id 9)

**Thrust:** ronin_itis_bekleme(RONIN_ITIS_BEKLEME=16). ronin_itis_zirh>0: dmg×0.3 (70% reduction) in hasar_al. itis_goster extends spear reach 26→40px. Dmg RONIN_ITIS_HASAR(22), menzil RONIN_ITIS_MENZIL(110), aci RONIN_ITIS_ACI(0.5).

**Throw:** ronin_firlat_bekleme(RONIN_FIRLAT_BEKLEME=65), firlat_goster (also extends reach to 40px). Dmg RONIN_FIRLAT_HASAR(34), menzil RONIN_FIRLAT_MENZIL(520).

**Stealth (E, inferred):** gizli_aktif/gizli_suresi(RONIN_E_SURESI=90), e_bekleme(RONIN_E_BEKLEME=280). Visor dims (170,120,255)→(90,60,140), alpha→110. Comment: "shadow-mode hits no longer immediately end stealth — lasts until timer expires (so shadow mastery can freeze multiple enemies)".

**Crit:** ronin_kritik_hazir flag (set elsewhere, likely post-stealth-attack). `ronin_hasar_carpani()`: if set, consume+return RONIN_E_KRITIK_CARPAN(2.6); else 1.0.

**Ulti (Q):** ulti_aktif/suresi(RONIN_ULTI_SURESI=480, 8s). 3-armed spinning spear-storm, radius RONIN_ULTI_YARICAP(66)*(2.0 if ronin_ulti_gelismis_acik else 1.0), rotation=(ticks_ms/90)%2π, arms spaced 2π/3. Dmg RONIN_ULTI_HASAR(9) per tick (~every 6 frames per spec elsewhere) to nearby enemies.

**Masteries:** ronin_menzil_carpan (range mult, applied outside), ronin_gizli_sersem_acik (stealth-attack stun), ronin_ulti_gelismis_acik (2x ulti radius).

---

## 8. HEX (id 6)

**Movement:** `daima_ucar=True` ALWAYS (permanent flight, not ulti-gated). Speed=5 (wraith_yavas false), up/down direct control, ×0.85 damping when neither pressed. y∈[44,ZEMIN_Y-h].

**Spellbook:** `hex_kitap_guncelle()`: while kitap_sayisi<kitap_max_ozel(default HEX_KITAP_MAX=3, HEX_KITAP_MAX_USTA=6 mastery), kitap_timer-=1; at 0, kitap_sayisi+=1, reset timer=HEX_KITAP_SURESI(180). Books orbit at radius 34, angle=t/300+i*(2π/max).

**Generic spell cooldown:** hex_buyu_bekleme ticks in kitap_guncelle (shared cast gate, HEX_BUYU_BEKLEME=40 base). Damage HEX_BUYU_HASAR(30), speed HEX_BUYU_HIZI(6, slow projectile).

**Heal (E, inferred) `hex_heal_baslat()`:** if heal_bekleme<=0 & inactive → active, suresi=HEX_HEAL_SURESI(180), bekleme=HEX_HEAL_BEKLEME(300). While active: can += HEX_HEAL_TOPLAM(40)/HEX_HEAL_SURESI EVERY FRAME (linear heal totaling exactly 40 over 180 frames).

**Beam (click, inferred, fields only):** hex_isin_bitis (endpoint), hex_isin_goster (visual timer), hex_isin_kitap_sayisi (books consumed, scales thickness: outer glow 5+3*count, inner core 2+2*count). Damage per book: HEX_ISIN_BIRIM_HASAR(25), menzil HEX_ISIN_MENZIL(1200, "infinite").

**Ulti mastery:** hex_ulti_ekran_temizle_acik (screen-clear ulti flag). HEX_ULTI_HASAR(20), HEX_ULTI_YAVAS_SURESI(180), HEX_ULTI_YAVAS_CARPAN(0.4) slow-on-hit.

---

## Draw-layer cross-reference (behaviorally relevant)
- Damage flash: sprite skipped entirely (hard blink, not fade) while hasar_timer>0, pattern `hasar_timer%6<3`.
- Alpha overrides: 130 during Wraith ghost, 110 during Ronin stealth, else 255.
- Weapon-tip aim anchor always `(x+w/2, y+h*0.38)`, oriented `atan2(fy-by,fx-bx)`.
- Each hero has fully distinct hand-drawn polygon body rig (no shared sprite sheet — vector-drawn shapes per frame).
