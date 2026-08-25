import pygame
import sys

# ── BAŞLANGIÇ ──
pygame.init()
pygame.mixer.init()

GENISLIK = 900
YUKSEKLIK = 550
FPS = 60

ekran = pygame.display.set_mode((GENISLIK, YUKSEKLIK))
pygame.display.set_caption("CYBER LEGEND 2099")
saat = pygame.time.Clock()

# ── RENKLER ──
SIYAH    = (0, 0, 0)
BEYAZ    = (255, 255, 255)
CYAN     = (0, 255, 247)
TURUNCU  = (245, 166, 35)
KIRMIZI  = (233, 69, 96)
LACIVERT = (26, 68, 187)
KOYU     = (5, 5, 15)
ZEMIN_C  = (10, 10, 30)

# ── ZEMİN ──
ZEMIN_Y = YUKSEKLIK - 80

# ── OYUNCU ──
class Oyuncu:
    def __init__(self):
        self.x = 150
        self.y = ZEMIN_Y - 48
        self.w = 28
        self.h = 48
        self.hiz_x = 0
        self.hiz_y = 0
        self.yerde = False
        self.can = 100
        self.max_can = 100
        self.anim_frame = 0
        self.anim_zamani = 0
        self.hasar_timer = 0

    def hareket_et(self, tuslar):
        self.hiz_x = 0
        if tuslar[pygame.K_LEFT] or tuslar[pygame.K_a]:
            self.hiz_x = -5
        if tuslar[pygame.K_RIGHT] or tuslar[pygame.K_d]:
            self.hiz_x = 5
        if (tuslar[pygame.K_UP] or tuslar[pygame.K_w] or tuslar[pygame.K_SPACE]) and self.yerde:
            self.hiz_y = -14
            self.yerde = False

        # Yerçekimi
        self.hiz_y += 0.6
        self.x += self.hiz_x
        self.y += self.hiz_y

        # Zemin kontrolü
        if self.y >= ZEMIN_Y - self.h:
            self.y = ZEMIN_Y - self.h
            self.hiz_y = 0
            self.yerde = True

        # Ekran sınırı
        self.x = max(0, min(GENISLIK - self.w, self.x))

        # Animasyon
        self.anim_zamani += 1
        if self.anim_zamani >= 8:
            self.anim_zamani = 0
            self.anim_frame = (self.anim_frame + 1) % 4

        if self.hasar_timer > 0:
            self.hasar_timer -= 1

    def ciz(self, ekran):
        # Hasar alınca yanıp söner
        if self.hasar_timer > 0 and self.hasar_timer % 6 < 3:
            return

        px, py = int(self.x), int(self.y)

        # Bacaklar
        lf = 5 if self.anim_frame % 2 == 0 else 0
        pygame.draw.rect(ekran, (13, 46, 136), (px+2, py+self.h-14, 10, 14+lf))
        pygame.draw.rect(ekran, (13, 46, 136), (px+self.w-12, py+self.h-14, 10, 14-lf))

        # Gövde
        pygame.draw.rect(ekran, LACIVERT, (px, py+16, self.w, self.h-16))

        # Kafa
        pygame.draw.rect(ekran, (34, 85, 221), (px+2, py, self.w-4, 18))

        # Vizör (cyan)
        pygame.draw.rect(ekran, CYAN, (px+4, py+5, self.w-8, 6))

        # Göğüs detayı
        pygame.draw.rect(ekran, (34, 85, 204), (px+6, py+20, self.w-12, 8))

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


# ── MERMİ ──
class Mermi:
    def __init__(self, x, y, hedef_x, hedef_y, renk, hasar):
        self.x = float(x)
        self.y = float(y)
        self.renk = renk
        self.hasar = hasar
        self.omur = 70
        import math
        dx = hedef_x - x
        dy = hedef_y - y
        uzunluk = math.sqrt(dx*dx + dy*dy) or 1
        hiz = 13
        self.hiz_x = dx / uzunluk * hiz
        self.hiz_y = dy / uzunluk * hiz

    def guncelle(self):
        self.x += self.hiz_x
        self.y += self.hiz_y
        self.omur -= 1

    def ciz(self, ekran):
        pygame.draw.rect(ekran, self.renk, (int(self.x)-3, int(self.y)-3, 6, 6))

    def rect(self):
        return pygame.Rect(self.x-3, self.y-3, 6, 6)


# ── DÜŞMAN ──
class Dusman:
    def __init__(self, x, tip='melee'):
        self.tip = tip
        self.x = float(x)
        self.y = float(ZEMIN_Y - 48)
        self.w = 28
        self.h = 48
        self.hiz_x = -2.0
        self.hiz_y = 0.0
        self.can = 30
        self.max_can = 30
        self.atis_timer = 80
        self.anim_frame = 0
        self.anim_zamani = 0
        self.para = 60

        if tip == 'ranged':
            self.can = 20
            self.max_can = 20
            self.hiz_x = -1.2
            self.para = 80

    def guncelle(self, oyuncu_x):
        # Oyuncuya doğru git
        if self.x > oyuncu_x:
            self.hiz_x = -abs(self.hiz_x)
        else:
            self.hiz_x = abs(self.hiz_x)

        self.hiz_y += 0.4
        self.x += self.hiz_x
        self.y += self.hiz_y

        if self.y >= ZEMIN_Y - self.h:
            self.y = ZEMIN_Y - self.h
            self.hiz_y = 0

        self.anim_zamani += 1
        if self.anim_zamani >= 10:
            self.anim_zamani = 0
            self.anim_frame = (self.anim_frame + 1) % 2

        if self.atis_timer > 0:
            self.atis_timer -= 1

    def ciz(self, ekran):
        px, py = int(self.x), int(self.y)
        hp_oran = self.can / self.max_can

        # Can barı
        pygame.draw.rect(ekran, (50, 50, 50), (px, py-8, self.w, 4))
        renk = (0, 255, 100) if hp_oran > 0.5 else (255, 68, 68)
        pygame.draw.rect(ekran, renk, (px, py-8, int(self.w * hp_oran), 4))

        if self.tip == 'melee':
            # Kırmızı melee robot
            pygame.draw.rect(ekran, (204, 34, 51), (px+2, py, self.w-4, self.h))
            pygame.draw.rect(ekran, (238, 51, 68), (px+3, py+2, self.w-6, 16))
            # Göz
            pygame.draw.rect(ekran, (255, 238, 0), (px+6, py+6, 4, 4))
            pygame.draw.rect(ekran, (255, 238, 0), (px+self.w-10, py+6, 4, 4))
            # Bacaklar
            lf = 4 if self.anim_frame == 0 else 0
            pygame.draw.rect(ekran, (136, 17, 34), (px+2, py+self.h-14, 10, 14+lf))
            pygame.draw.rect(ekran, (136, 17, 34), (px+self.w-12, py+self.h-14, 10, 14-lf))
            # Kılıç
            pygame.draw.rect(ekran, (200, 200, 200), (px-12, py+self.h//3, 12, 4))

        else:  # ranged
            pygame.draw.rect(ekran, (26, 68, 204), (px+2, py, self.w-4, self.h))
            pygame.draw.rect(ekran, (34, 85, 238), (px+3, py+2, self.w-6, 16))
            pygame.draw.rect(ekran, CYAN, (px+5, py+6, self.w-10, 4))
            lf = 4 if self.anim_frame == 0 else 0
            pygame.draw.rect(ekran, (13, 46, 136), (px+2, py+self.h-14, 10, 14+lf))
            pygame.draw.rect(ekran, (13, 46, 136), (px+self.w-12, py+self.h-14, 10, 14-lf))
            # Lazer tabanca
            pygame.draw.rect(ekran, (68, 170, 255), (px+self.w, py+self.h//3, 10, 4))

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


# ── PARA ──
class Para:
    def __init__(self, x, y, deger):
        self.x = float(x)
        self.y = float(y)
        self.hiz_y = -4.0
        self.hiz_x = (pygame.time.get_ticks() % 5) - 2.0
        self.deger = deger
        self.omur = 200

    def guncelle(self):
        self.hiz_y += 0.5
        self.x += self.hiz_x
        self.y += self.hiz_y
        if self.y >= ZEMIN_Y - 8:
            self.y = ZEMIN_Y - 8
            self.hiz_y = 0
        self.omur -= 1

    def ciz(self, ekran):
        px, py = int(self.x), int(self.y)
        pygame.draw.rect(ekran, TURUNCU, (px-4, py-4, 8, 8))
        pygame.draw.rect(ekran, (255, 200, 0), (px-2, py-6, 4, 4))


# ── FON ──
import random
binalar = []
for i in range(40):
    binalar.append({
        'x': i * 60 - 100,
        'w': 30 + random.randint(0, 40),
        'h': 60 + random.randint(0, 220),
        'layer': random.randint(0, 1)
    })
yildizlar = [(random.randint(0, GENISLIK), random.randint(0, YUKSEKLIK-140), random.randint(1,2)) for _ in range(80)]

def fon_ciz(ekran):
    ekran.fill(KOYU)

    # Yıldızlar
    for (sx, sy, sr) in yildizlar:
        pygame.draw.rect(ekran, (180, 180, 180), (sx, sy, sr, sr))

    # Uzak binalar
    for b in binalar:
        if b['layer'] == 0:
            bx = int((b['x']) % (GENISLIK + 200)) - 100
            pygame.draw.rect(ekran, (6, 6, 20), (bx, YUKSEKLIK-80-b['h'], b['w'], b['h']))
            # Pencereler
            for wy in range(YUKSEKLIK-80-b['h']+6, YUKSEKLIK-90, 12):
                for wx in range(bx+4, bx+b['w']-4, 8):
                    if random.random() < 0.15:
                        pygame.draw.rect(ekran, (0, 40, 50), (wx, wy, 4, 6))

    # Yakın binalar
    for b in binalar:
        if b['layer'] == 1:
            bx = int((b['x']) % (GENISLIK + 200)) - 100
            pygame.draw.rect(ekran, (10, 10, 30), (bx, YUKSEKLIK-80-b['h'], b['w'], b['h']))
            pygame.draw.rect(ekran, (0, 40, 50), (bx, YUKSEKLIK-80-b['h'], b['w'], b['h']), 1)

    # Zemin
    pygame.draw.rect(ekran, ZEMIN_C, (0, ZEMIN_Y, GENISLIK, 80))
    # Neon zemin çizgisi
    for x in range(0, GENISLIK, 6):
        pygame.draw.rect(ekran, CYAN, (x, ZEMIN_Y, 4, 2))


# ── HUD ──
font_kucuk = pygame.font.SysFont("couriernew", 14, bold=True)
font_orta  = pygame.font.SysFont("couriernew", 20, bold=True)
font_buyuk = pygame.font.SysFont("couriernew", 32, bold=True)

def hud_ciz(ekran, oyuncu, skor, para, dalga, mermi_sayisi, max_mermi, doluyor):
    # Üst bar arka plan
    pygame.draw.rect(ekran, (0,0,0), (0, 0, GENISLIK, 40))
    pygame.draw.rect(ekran, CYAN, (0, 0, GENISLIK, 40), 2)

    # Can barı
    pygame.draw.rect(ekran, (30,30,30), (10, 10, 120, 14))
    can_oran = oyuncu.can / oyuncu.max_can
    renk = (0,255,100) if can_oran > 0.5 else (255,165,0) if can_oran > 0.25 else (255,50,50)
    pygame.draw.rect(ekran, renk, (10, 10, int(120*can_oran), 14))
    pygame.draw.rect(ekran, CYAN, (10, 10, 120, 14), 1)
    can_yazi = font_kucuk.render("CAN", True, CYAN)
    ekran.blit(can_yazi, (136, 12))

    # Skor
    skor_yazi = font_kucuk.render(f"SKOR: {skor}", True, BEYAZ)
    ekran.blit(skor_yazi, (GENISLIK//2 - skor_yazi.get_width()//2, 12))

    # Dalga
    dalga_yazi = font_kucuk.render(f"DALGA {dalga}", True, TURUNCU)
    ekran.blit(dalga_yazi, (GENISLIK - 160, 12))

    # Mermi sayacı (oyuncunun üstünde)
    mermi_yazi = f"{'DOLDURUYOR...' if doluyor else str(mermi_sayisi)+'/'+str(max_mermi)}"
    renk2 = TURUNCU if doluyor else (CYAN if mermi_sayisi > max_mermi*0.25 else (255,100,0) if mermi_sayisi > 0 else (255,50,50))
    m_surf = font_kucuk.render(mermi_yazi, True, renk2)
    ekran.blit(m_surf, (int(oyuncu.x) - m_surf.get_width()//2 + oyuncu.w//2, int(oyuncu.y) - 22))

    # Para
    para_yazi = font_kucuk.render(f"${para}", True, TURUNCU)
    ekran.blit(para_yazi, (300, 12))


# ── ANA OYUN ──
def oyunu_baslat():
    oyuncu = Oyuncu()
    mermi_listesi = []
    dusman_listesi = []
    para_listesi = []

    skor = 0
    para = 0
    dalga = 1
    dalga_timer = 0
    spawn_timer = 60
    atis_timer = 0

    # Mermi sistemi
    sarjor = 15
    max_sarjor = 15
    doluyor = False
    dolum_timer = 0
    DOLUM_SURESI = 90

    calisyor = True
    oyun_bitti = False

    while calisyor:
        saat.tick(FPS)

        for olay in pygame.event.get():
            if olay.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if olay.type == pygame.KEYDOWN:
                if olay.key == pygame.K_ESCAPE:
                    calisyor = False
                if olay.key == pygame.K_r and not doluyor and sarjor < max_sarjor:
                    doluyor = True
                    dolum_timer = DOLUM_SURESI
            if olay.type == pygame.MOUSEBUTTONDOWN:
                if olay.button == 1 and not doluyor:
                    if sarjor > 0 and atis_timer <= 0:
                        mx, my = pygame.mouse.get_pos()
                        m = Mermi(
                            oyuncu.x + oyuncu.w//2,
                            oyuncu.y + oyuncu.h//3,
                            mx, my,
                            TURUNCU, 10
                        )
                        mermi_listesi.append(m)
                        sarjor -= 1
                        atis_timer = 12
                    elif sarjor <= 0:
                        doluyor = True
                        dolum_timer = DOLUM_SURESI

        tuslar = pygame.key.get_pressed()

        if not oyun_bitti:
            # Oyuncu
            oyuncu.hareket_et(tuslar)
            if atis_timer > 0:
                atis_timer -= 1

            # Dolum
            if doluyor:
                dolum_timer -= 1
                if dolum_timer <= 0:
                    doluyor = False
                    sarjor = max_sarjor

            # Spawn
            spawn_timer -= 1
            if spawn_timer <= 0:
                tip = 'ranged' if random.random() < 0.35 else 'melee'
                spawn_x = GENISLIK + 50 if random.random() > 0.5 else -50
                dusman_listesi.append(Dusman(spawn_x, tip))
                spawn_timer = max(30, 90 - dalga * 5)

            # Dalga
            dalga_timer += 1
            if dalga_timer >= 600:
                dalga_timer = 0
                dalga += 1

            # Düşmanlar
            for d in dusman_listesi[:]:
                d.guncelle(oyuncu.x)

                # Düşman atışı
                if d.tip == 'ranged' and d.atis_timer <= 0:
                    em = Mermi(
                        d.x + d.w//2, d.y + d.h//2,
                        oyuncu.x + oyuncu.w//2, oyuncu.y + oyuncu.h//2,
                        (255, 50, 100), 8
                    )
                    em.hiz_x *= 0.35
                    em.hiz_y *= 0.35
                    mermi_listesi.append(em)
                    d.atis_timer = 80

                # Melee temas
                if d.tip == 'melee' and d.rect().colliderect(oyuncu.rect()) and oyuncu.hasar_timer <= 0:
                    oyuncu.can -= 15
                    oyuncu.hasar_timer = 50

                # Ekran dışı
                if d.x < -200 or d.x > GENISLIK + 200:
                    dusman_listesi.remove(d)

            # Mermi çarpışmaları
            for m in mermi_listesi[:]:
                m.guncelle()
                if m.omur <= 0 or m.x < 0 or m.x > GENISLIK or m.y < 0 or m.y > YUKSEKLIK:
                    mermi_listesi.remove(m)
                    continue

                # Oyuncu mermisi düşmana çarptı mı?
                for d in dusman_listesi[:]:
                    if m.hasar == 10 and m.rect().colliderect(d.rect()):
                        d.can -= m.hasar
                        if m in mermi_listesi:
                            mermi_listesi.remove(m)
                        if d.can <= 0:
                            # Para düşür
                            for _ in range(3):
                                p = Para(d.x + d.w//2, d.y, d.para // 3)
                                para_listesi.append(p)
                            skor += d.para
                            dusman_listesi.remove(d)
                        break

                # Düşman mermisi oyuncuya çarptı mı?
                if m.hasar == 8 and m.rect().colliderect(oyuncu.rect()) and oyuncu.hasar_timer <= 0:
                    oyuncu.can -= m.hasar
                    oyuncu.hasar_timer = 45
                    if m in mermi_listesi:
                        mermi_listesi.remove(m)

            # Para toplama
            for p in para_listesi[:]:
                p.guncelle()
                if p.omur <= 0:
                    para_listesi.remove(p)
                    continue
                op = pygame.Rect(oyuncu.x-10, oyuncu.y-10, oyuncu.w+20, oyuncu.h+20)
                if op.collidepoint(p.x, p.y):
                    para += p.deger
                    para_listesi.remove(p)

            # Ölüm
            if oyuncu.can <= 0:
                oyun_bitti = True

        # ── ÇİZİM ──
        fon_ciz(ekran)

        for p in para_listesi:
            p.ciz(ekran)

        for d in dusman_listesi:
            d.ciz(ekran)

        for m in mermi_listesi:
            m.ciz(ekran)

        oyuncu.ciz(ekran)

        # Nişan çizgisi (crosshair)
        mx, my = pygame.mouse.get_pos()
        pygame.draw.rect(ekran, CYAN, (mx-10, my-1, 8, 2))
        pygame.draw.rect(ekran, CYAN, (mx+2,  my-1, 8, 2))
        pygame.draw.rect(ekran, CYAN, (mx-1, my-10, 2, 8))
        pygame.draw.rect(ekran, CYAN, (mx-1, my+2,  2, 8))
        pygame.draw.rect(ekran, CYAN, (mx-4, my-4, 8, 8), 1)

        hud_ciz(ekran, oyuncu, skor, para, dalga, sarjor, max_sarjor, doluyor)

        if oyun_bitti:
            karanlik = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)
            karanlik.fill((0, 0, 0, 160))
            ekran.blit(karanlik, (0, 0))
            go = font_buyuk.render("GAME OVER", True, KIRMIZI)
            ekran.blit(go, (GENISLIK//2 - go.get_width()//2, YUKSEKLIK//2 - 50))
            s = font_orta.render(f"SKOR: {skor}   PARA: ${para}", True, BEYAZ)
            ekran.blit(s, (GENISLIK//2 - s.get_width()//2, YUKSEKLIK//2))
            y = font_kucuk.render("Tekrar oynamak icin R'ye bas  |  Cikis: ESC", True, CYAN)
            ekran.blit(y, (GENISLIK//2 - y.get_width()//2, YUKSEKLIK//2 + 50))

            tuslar2 = pygame.key.get_pressed()
            if tuslar2[pygame.K_r]:
                oyunu_baslat()
                return

        # Kontroller (altta)
        k = font_kucuk.render("← → Koş   ↑/Space Zıpla   Sol Tık Ateş   R Doldur   ESC Çıkış", True, (60,60,60))
        ekran.blit(k, (GENISLIK//2 - k.get_width()//2, YUKSEKLIK - 20))

        pygame.display.flip()

oyunu_baslat()
