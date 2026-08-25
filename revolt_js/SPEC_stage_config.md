# Stage config (`bolum_ayar`) + general quests — game (1).py lines 1066-1135

## GENEL_GOREVLER (one-time permanent unlocks, checked every frame via kontrol_fn)
```
ilk_zafer    "ILK ZAFER"      "Bir bolumu bitir"                    en_yuksek_bolum>=2   -> +15 max_can (+15 can)
avci         "AVCI"           "Toplam 150 dusman oldur"             TOPLAM_OLDURULEN>=150 -> speed *1.08
hayatta_kalan "HAYATTA KALAN" "Survivor'da tek seferde 90sn hayatta kal" EN_UZUN_HAYATTA_KALMA>=90 -> regen += 2.0/60 per frame
kahraman     "KAHRAMAN"       "Bolum 15'e ulas"                     en_yuksek_bolum>=15  -> +25 max_can, speed*1.05
```
Applied every frame to player stats (idempotent-style re-application, not literally one-time consumed — `genel_yukseltme_uygula` loops all completed quests and reapplies their effect each call).

## bolum_ayar(bolum) — enemy spawn counts per stage (30 total stages)

Returns dict: melee,ranged,drone,sniper,shield,tank,suicide,gorunmez,hayalet,mizrakli (spawn counts for that stage), boss (bool), final (bool).

```
bolum<=3:    melee:8,ranged:2,drone:0,sniper:0,shield:0,tank:0,suicide:(1 if bolum>=3 else 0),gorunmez:0,hayalet:0,mizrakli:0, boss:False,final:False
bolum<=6:    melee:5,ranged:3,drone:2,sniper:(1 if bolum>=5 else 0),shield:0,tank:0,suicide:2,gorunmez:0,hayalet:0,mizrakli:1, boss:(bolum%5==0),final:False
bolum<=10:   melee:3,ranged:4,drone:2,sniper:2,shield:(2 if bolum>=8 else 0),tank:0,suicide:2,gorunmez:(1 if bolum>=7 else 0),hayalet:0,mizrakli:1, boss:(bolum%5==0),final:False
bolum<=15:   melee:2,ranged:3,drone:2,sniper:2,shield:2,tank:(1 if bolum>=12 else 0),suicide:3,gorunmez:2,hayalet:(1 if bolum>=13 else 0),mizrakli:2, boss:(bolum%5==0),final:False
bolum<=20:   melee:2,ranged:3,drone:2,sniper:2,shield:2,tank:2,suicide:3,gorunmez:2,hayalet:2,mizrakli:2, boss:(bolum%5==0),final:False
bolum<30:    melee:1,ranged:3,drone:2,sniper:3,shield:2,tank:3,suicide:4,gorunmez:3,hayalet:3,mizrakli:2, boss:(bolum%5==0),final:False
bolum==30:   all 0, boss:False, final:True   (OMEGA-9 final boss stage)
```

Note: boss:True triggers at every multiple of 5 EXCEPT stage 30 which is the dedicated final-boss stage instead (bolum==5,10,15,20,25 get a regular 'boss'-type enemy added to the mix; bolum==30 spawns 'finalboss'/OMEGA-9 exclusively with zero regular enemies).

Chaos-stage markers from stage-select UI (triangle icons) are at local page positions 4,8 -> absolute stages 5,15,25 and 9,19,29 — these overlap with but are NOT identical to the boss%5==0 stages (5,10,15,20,25 have bosses; 5,15,25 are ALSO chaos-marked; 9,19,29 are chaos-marked but have no boss). The "chaos" label appears to be purely a UI/visual flag in stage-select, not reflected in bolum_ayar's actual spawn table differences beyond the normal progression shown above.

TEST_MODU debug override (should NOT be ported — this is a dev-only cheat mode): bolum<=4 spawns 2 of every type; bolum==5 spawns only finalboss.
