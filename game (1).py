import pygame
import pygame.gfxdraw
import sys
import math
import random
import os
import json
import atexit
import asyncio

# ── BAŞLANGIÇ ──
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

GENISLIK = 900
YUKSEKLIK = 550
FPS = 60

# Tarayıcıda (pygbag/Emscripten) __file__ güvenilir değil — çalışma dizini zaten
# script'in kendi klasörüne ayarlanmış oluyor, bağıl yol yeterli.
_WEB_ORTAMI = sys.platform == 'emscripten'
# PyInstaller ile tek-dosya .exe'ye paketlenince salt-okunur varlıklar (görsel/ses)
# geçici bir açılış klasörüne (_MEIPASS) çıkarılır — __file__ oradaki kopyayı gösterir,
# bu doğrudur ve olduğu gibi kullanılabilir.
_DONDURULMUS = getattr(sys, 'frozen', False)

# ── GÖRSEL KLASÖRÜ ──
GORSEL_KLASOR = 'gorseller' if _WEB_ORTAMI else os.path.join(os.path.dirname(os.path.abspath(__file__)) if not _DONDURULMUS else sys._MEIPASS, 'gorseller')
# ── SES KLASÖRÜ (Freesound'dan indirilen, lisansı uygun dosyalar — bkz. sesler/_readme_and_license.txt) ──
SES_KLASOR = 'sesler' if _WEB_ORTAMI else os.path.join(os.path.dirname(os.path.abspath(__file__)) if not _DONDURULMUS else sys._MEIPASS, 'sesler')

def ses_dosyasi_yukle(dosya_adi):
    yol = os.path.join(SES_KLASOR, dosya_adi)
    try:
        return pygame.mixer.Sound(yol)
    except Exception:
        return None

def gorsel_yukle(dosya_adi):
    yol = os.path.join(GORSEL_KLASOR, dosya_adi)
    try:
        return pygame.image.load(yol).convert()
    except Exception:
        return None

# Tarayıcıda (pygbag/Emscripten) hem FULLSCREEN hem de SCALED bayrakları
# desteklenmiyor (web kendi donanım ölçekleyicisini kullanıyor) — sayfa zaten
# kendi canvas'ını yönetiyor, düz bir pencere yeterli.
_EKRAN_BAYRAK = 0 if _WEB_ORTAMI else (pygame.FULLSCREEN | pygame.SCALED)
ekran = pygame.display.set_mode((GENISLIK, YUKSEKLIK), _EKRAN_BAYRAK)
pygame.display.set_caption("REVOLT")
saat = pygame.time.Clock()

# ── KAHRAMAN KART GÖRSELLERİ ──

KAHRAMAN_KART_GORSELLERI = {
    0: gorsel_yukle('aegis.jpg'),   # AEGIS
    1: gorsel_yukle('raptor.jpg'),  # RAPTOR
    6: gorsel_yukle('hex.jpg'),     # HEX
    7: gorsel_yukle('wraith.jpg'),  # WRAITH
    8: gorsel_yukle('reaper.jpg'),  # REAPER
    5: gorsel_yukle('overdrive.jpg'),  # OVERDRIVE
    9: gorsel_yukle('ronin.jpg'),   # RONIN
}

BOLUM_HARITASI_GORSELI = gorsel_yukle('bolum_haritasi.jpg')

# Ekip afişleri: kaç kahraman gerçekten açıldığına göre siluetlerden renkliye dönüşür
EKIP_AFIS_GORSELLERI = [gorsel_yukle(f'ekip_{i}.jpg') for i in range(1, 8)]
# Her afişte HANGİ kahramanların (id) gerçekten renkli çizildiği — görsellerin
# kendisine bakılarak belirlendi. Açılma sırasıyla (AEGIS, RAPTOR, HEX, WRAITH,
# REAPER, OVERDRIVE, RONIN) birebir eşleşen 7 aşamalı afiş seti.
EKIP_AFIS_ACIK_KUMELERI = [
    {0},
    {0, 1},
    {0, 1, 6},
    {0, 1, 6, 7},
    {0, 1, 6, 7, 8},
    {0, 1, 6, 7, 8, 5},
    {0, 1, 6, 7, 8, 5, 9},
]

def _kenar_seffaflastir(yuzey, esik=40, yumusatma=35):
    # JPEG'in siyah arka planini seffaflastirir (koyu pikseller -> alfa 0,
    # kenarlarda yumusak gecis) — düz bir kesme yerine dogal bir siluet birakir.
    yuzey = yuzey.convert_alpha()
    w, h = yuzey.get_size()
    for x in range(w):
        for y in range(h):
            r, g, b, a = yuzey.get_at((x, y))
            parlaklik = max(r, g, b)
            if parlaklik <= esik:
                yeni_a = 0
            elif parlaklik >= esik + yumusatma:
                yeni_a = a
            else:
                yeni_a = int(a * (parlaklik - esik) / yumusatma)
            yuzey.set_at((x, y), (r, g, b, yeni_a))
    return yuzey

try:
    _ikon_ham = pygame.image.load(os.path.join(GORSEL_KLASOR, 'ikon.jpg'))
    pygame.display.set_icon(_kenar_seffaflastir(_ikon_ham))
except Exception:
    pass

REVOLT_LOGO_GORSELI = None
_revolt_logo_ham = gorsel_yukle('revolt_logo.jpg')
if _revolt_logo_ham:
    _logo_oran = 260 / _revolt_logo_ham.get_width()
    REVOLT_LOGO_GORSELI = pygame.transform.smoothscale(
        _revolt_logo_ham,
        (260, int(_revolt_logo_ham.get_height() * _logo_oran))
    )
    REVOLT_LOGO_GORSELI = _kenar_seffaflastir(REVOLT_LOGO_GORSELI)

# ── RENKLER ──
SIYAH    = (0, 0, 0)
BEYAZ    = (255, 255, 255)
CYAN     = (0, 255, 247)
TURUNCU  = (245, 166, 35)
KIRMIZI  = (233, 69, 96)
LACIVERT = (26, 68, 187)
KOYU     = (5, 5, 15)
ZEMIN_C  = (10, 10, 30)
YESIL    = (0, 255, 100)
MOR      = (170, 0, 255)
SARI     = (255, 238, 0)

ZEMIN_Y = YUKSEKLIK - 80

PATLAMA_YARICAP = 55   # intihar robotunun alan hasarı yarıçapı
FITIL_SURESI = 18      # intihar robotu yaklaştıktan sonra patlamaya kadar geçen kare sayısı

SOLUCAN_CAN = 75              # canlı ve vurulabilir
SOLUCAN_HASAR = 35            # temas edilirse alınan hasar (ağır)
SOLUCAN_YUKSEKLIK = 220       # tam çıkınca zeminden yüksekliği
SOLUCAN_TEHLIKE_SURESI = 55   # tam çıkmışken tehlikeli kaldığı süre
SOLUCAN_ONDEN_MESAFE = 180    # oyuncunun gittiği yönde ne kadar önüne çıkacağı
SOLUCAN_ARALIK_MIN = 220      # iki çıkış arası minimum bekleme (kare)
SOLUCAN_ARALIK_MAX = 340

MIZRAKLI_HIZ = 5.2             # mızraklı robot grubunun sabit koşu hızı
MIZRAKLI_GRUP_MIN = 5
MIZRAKLI_GRUP_MAX = 6
MIZRAKLI_HAVADA_ESIK = 55      # oyuncu zeminden bu kadar yukarıdaysa "havada" sayılır, mızrak fırlatılır

KALKAN_KAPASITE = 70   # AEGIS kalkanının emebileceği toplam hasar
KALKAN_SURESI = 300    # kalkanın aktif kalabileceği azami süre (kare)
KALKAN_BEKLEME = 360   # kalkan kapanınca beklenmesi gereken süre (kare)

ULTI_MAX = 100          # ulti barının dolu kapasitesi
ULTI_SARJ_OLUM = 8      # her düşman öldürünce dolan miktar
ULTI_SURESI = 480       # ulti aktifken süresi (8 sn @ 60fps)
ULTI_CAN_ARTISI = 25    # ulti açılınca anında iyileşen can

KILIC_HASAR = 35          # AEGIS kılıcının hasarı
KILIC_HIZI = 17           # fırlatma/dönüş hızı (px/kare)
KILIC_MENZIL = 480        # menzili az olmasın
KILIC_ATMA_BEKLEME = 300  # atma cooldown'u (5 sn @ 60fps)
KILIC_SAVURMA_BEKLEME = 20  # savurma (sol tık) atış hızı sınırı

# AEGIS'e özel YÜKSELT yetenekleri
AEGIS_KILIC_MENZIL_ARTIS = 0.35   # KESKİN MENZİL yükseltmesi
AEGIS_PASIF_KALKAN_ARALIK = 300   # KORUYUCU AZİM: 5 sn (@60fps) hasarsız kalınca kalkan biriktirir
AEGIS_PASIF_KALKAN_ARTIS = 8
AEGIS_PASIF_KALKAN_MAX = 40
AEGIS_KILIC_SEKME_MAKS = 5        # SEKEN KILIÇ: saplandığı yerden uzaklık fark etmeden bu kadar düşmana seker

HEX_MAX_CAN = 50
HEX_KITAP_MAX = 3
HEX_KITAP_SURESI = 180        # ~3 sn'de bir yeni kitap
HEX_BUYU_HASAR = 30
HEX_BUYU_HIZI = 6              # yavaş mermi
HEX_BUYU_BEKLEME = 40          # sol tık atış hızı sınırı
HEX_ISIN_BIRIM_HASAR = 25      # kitap başına ışın hasarı
HEX_ISIN_MENZIL = 1200         # pratikte "sonsuz"
HEX_HEAL_SURESI = 180
HEX_HEAL_TOPLAM = 40
HEX_HEAL_BEKLEME = 300
HEX_ULTI_HASAR = 20
HEX_ULTI_YAVAS_SURESI = 180
HEX_ULTI_YAVAS_CARPAN = 0.4

RAPTOR_HIZ_X = 7                  # normalden yüksek temel koşu hızı (varsayılan 5)
RAPTOR_ZIPLAMA_BASLANGIC = -9      # basınca ilk itki
RAPTOR_ZIPLAMA_ITKI = -0.9         # basılı tutulurken kare başına ek itki
RAPTOR_ZIPLAMA_MAX_KARE = 26       # basılı tutmanın etkili olduğu azami süre (~tavana)
RAPTOR_ZIPLAMA_MIN_HIZ = -20       # yukarı hızın alt sınırı (çok basılı tutulunca)
RAPTOR_PENCE_HASAR = 18
RAPTOR_PENCE_YASAM_CALMA = 0.3  # pençe hasarının bu kadarı can olarak geri gelir
RAPTOR_PENCE_BEKLEME = 12          # seri saldırı hissi için kısa
RAPTOR_DASH_HIZI = 14
RAPTOR_DASH_SURESI = 12
RAPTOR_DASH_HASAR = 25
RAPTOR_DASH_BEKLEME = 90
RAPTOR_KACIS_SURESI = 20           # E: dokunulmazlık süresi
RAPTOR_KACIS_HIZ = 10
RAPTOR_KACIS_BEKLEME = 240
RAPTOR_ZEHIR_SURESI = 480          # E: bu süre boyunca vurduğu düşmanlara zehir bulaşır (8 sn)
RAPTOR_ZEHIR_TIK = 30              # zehirli düşman her 0.5 sn'de bir hasar alır
RAPTOR_ZEHIR_HASAR = 3
RAPTOR_ZEHIR_DUSMAN_SURESI = 180   # bir düşman zehirlendiğinde zehir 3 sn sürer
RAPTOR_ULTI_SURESI = 300
RAPTOR_ULTI_PENCE_CARPAN = 1.8
RAPTOR_ULTI_HIZ_CARPAN = 1.6

# RAPTOR'a özel YÜKSELT yetenekleri
RAPTOR_ZEHIR_PATLAMA_YARICAP = 110   # ZEHIR BULUTU: E'ye basınca etraftaki düşmanlara anında zehir bulaşır
RAPTOR_OFKE_SURESI = 180             # KAN KOKUSU: dash sonrası birkaç saniye ofkeli kalır (~3 sn)
RAPTOR_OFKE_CARPAN = 1.3             # ofkeliyken pençe/dash hasarı +%30
RAPTOR_OFKE_HIZ_CARPAN = 1.25        # ofkeliyken hareket hızı da artar (ultisindeki 1.6'dan daha zayıf)

HEX_CAN_YUKSELTME = 50               # +50 can (50 -> 100)
HEX_KITAP_MAX_USTA = 6               # USTA KITAPLIK: kitap sınırı 3 -> 6

WRAITH_HAYALET_HASAR_ARTIS_CARPAN = 1.3   # HAYALET AVCISI: hayaletken hasar penaltısı yerine +%30
WRAITH_RUH_OTO_HEAL_ORAN = 0.3            # RUH BAGI: her ruh kazanciyla bu oranda can da gelir
WRAITH_HAYALET_USTA_SURESI = 480          # SINIRSIZ HAYALET: hayalet suresi 8 sn'e cikar
WRAITH_HAYALET_USTA_BEKLEME = 300         # hayalet bitince baslayan 5 sn bekleme (ruh maliyeti yok)

WRAITH_MAX_CAN = 110
WRAITH_HIZ = 3.5                 # yavaş hareket
WRAITH_UCUS_HIZ = 3               # yavaş dikey uçuş
WRAITH_RUH_MAX = 100
WRAITH_RUH_SARJ_VURUS = 8
WRAITH_RUH_SARJ_OLUM = 15
WRAITH_RUH_HASAR = 22
WRAITH_RUH_HIZI = 8
WRAITH_RUH_BEKLEME = 35
WRAITH_YASAM_CALMA_ORAN = 0.25    # Ruh Cismi hasarının bu kadarı can olur
WRAITH_HAYALET_MALIYET = 40       # Hayalet Geçişi'nin ruh enerjisi maliyeti
WRAITH_HAYALET_SURESI = 90        # ~1.5 sn dokunulmazlık
WRAITH_HAYALET_YARI_CARPAN = 0.5  # hayaletken Ruh Cismi hasar çarpanı
WRAITH_HEAL_ORAN = 0.6            # E: harcanan ruh enerjisi başına can
WRAITH_HEAL_BEKLEME = 200
WRAITH_ULTI_SURESI = 240
WRAITH_ULTI_HASAR_CARPAN = 0.1    # ulti sırasında alınan hasarın oranı (sınırsız değil, %10)
WRAITH_ULTI_YAVAS_CARPAN = 0.25   # ulti sırasında aşırı yavaşlama
WRAITH_ULTI_RUH_RENGI = (80,160,255)

REAPER_MAX_CAN = 150
REAPER_HIZ = 4
REAPER_W, REAPER_H = 36, 58
REAPER_RUH_BOLME_MAX = 10
REAPER_VURUS_MENZIL = 150       # sol tık: yöne dönük saçılan alan hasarının uzunluğu
REAPER_VURUS_ACI = 0.75         # sol tık: koni yarı açısı (radyan)
REAPER_VURUS_HASAR = 22
REAPER_VURUS_BEKLEME = 45
REAPER_ATIS_MENZIL = 220        # sağ tık: daha uzun/büyük koni
REAPER_ATIS_ACI = 0.95          # sağ tık: daha geniş koni
REAPER_ATIS_HASAR = 46
REAPER_EMICI_ORAN = 0.25   # HAYATTA KAL kartı: RUH EMİCİ — verilen hasarın %25'i can olarak geri döner
REAPER_ATIS_BEKLEME = 55
REAPER_ISKELET_CAN = 35
REAPER_ISKELET_HASAR = 8
REAPER_ISKELET_HIZ = 2.5
REAPER_ISKELET_MENZIL = 40
REAPER_ISKELET_ATIS_BEKLEME = 40
REAPER_ISKELET_OKCU_MENZIL = 260   # ulti mastery: mavi okçu iskelet bu mesafeden vurabilir
REAPER_E_CAN_MALIYET = 10
REAPER_GUC_SURESI = 600       # E: iskeletlerin güçlü kaldığı süre (~10 sn)
REAPER_GUC_CARPAN = 1.8
REAPER_E_BEKLEME = 700
REAPER_ULTI_ISKELET_RENK = (26,14,17)  # siyah-kızıl büyülü kemik (ulti ile çağrılan iskeletler)

OVERDRIVE_MAX_CAN = 90
OVERDRIVE_KANCA_MENZIL = 3000   # pratikte sinirsiz — arena sinirlarindan once hep bir seye çarpar
OVERDRIVE_KANCA_UCUS_HIZI = 11     # duvara çekilirken (raptor dash'inden [14] az)
OVERDRIVE_KANCA_BEKLEME = 34       # kanca bekleme süresi (spam'ı önler)
OVERDRIVE_SALLANMA_HIZ = 12        # bağlıyken sol tık ile savrulma hızı
OVERDRIVE_KANCA_POMPA = 0.0022     # sallanırken yön tuşu ile pompalama (yönünde hızlan, tersinde yavaşla)
OVERDRIVE_SALLANMA_ESIGI = 2500    # bu kadar toplam hasar verilince YÜKSELT'te sallanma sistemi açılır
OVERDRIVE_E_HASAR = 55
OVERDRIVE_E_MENZIL = 75
OVERDRIVE_E_BEKLEME = 130
OVERDRIVE_E_CAN_YENILEME = 20      # E ile patlamayla birlikte kendine can yenileme
OVERDRIVE_ULTI_SURESI = 420
OVERDRIVE_ULTI_YAVAS_CARPAN = 0.18  # ulti sırasında düşman+mermi+karakter yavaşlar (silahı etkilenmez)
OVERDRIVE_ULTI_CAN_KAZANC = 10      # ulti aktifken her öldürme +10 can

RONIN_MAX_CAN = 120
RONIN_ITIS_HASAR = 22
RONIN_ITIS_MENZIL = 110
RONIN_ITIS_ACI = 0.5
RONIN_ITIS_BEKLEME = 16
RONIN_FIRLAT_HASAR = 34
RONIN_FIRLAT_MENZIL = 520
RONIN_FIRLAT_ACI = 0.12
RONIN_FIRLAT_BEKLEME = 65
RONIN_E_SURESI = 90
RONIN_E_BEKLEME = 280
RONIN_E_KRITIK_CARPAN = 2.6
RONIN_ULTI_SURESI = 480       # 8 saniye
RONIN_ULTI_YARICAP = 66
RONIN_ULTI_HASAR = 9          # her 6 karede bir yakinindaki dusmanlara

SURVIVOR_XP_BASE = 20
SURVIVOR_XP_ARTIS = 1.3          # her seviyede gereken XP çarpanı
SURVIVOR_ZORLUK_ARALIK = 1200    # ~20sn'de bir "sanal bölüm" seviyesi 1 artar

TEST_MODU = False  # TEST: tum dusman tiplerini + boss'u ilk bolumlere tasir. Test bitince False yap.

# ══════════════════════════════════════════
#  SES MOTORU
# ══════════════════════════════════════════
def ses_olustur(frekans, sure, tip='sine', ses=0.3):
    orneklem = 44100
    kareler = int(orneklem * sure)
    tampon = bytearray(kareler * 2)
    for i in range(kareler):
        t = i / orneklem
        if tip == 'sine':
            deger = math.sin(2 * math.pi * frekans * t)
        elif tip == 'square':
            deger = 1.0 if math.sin(2 * math.pi * frekans * t) > 0 else -1.0
        elif tip == 'sawtooth':
            deger = 2 * (t * frekans - math.floor(t * frekans + 0.5))
        else:
            deger = random.uniform(-1, 1)
        zarf = min(1.0, min(i / (orneklem * 0.01), (kareler - i) / (orneklem * 0.05)))
        v = int(deger * ses * zarf * 32767)
        v = max(-32768, min(32767, v))
        tampon[i*2]   = v & 0xFF
        tampon[i*2+1] = (v >> 8) & 0xFF
    ses_obj = pygame.sndarray.make_sound(
        pygame.surfarray.map_array(
            pygame.Surface((1,1)),
            [[0]]
        )
    )
    import numpy as np
    dizi = np.frombuffer(bytes(tampon), dtype=np.int16)
    stereo = np.column_stack([dizi, dizi])
    return pygame.sndarray.make_sound(stereo)

# Numpy ile ses üret
try:
    import numpy as np
    NUMPY_VAR = True
except ImportError:
    NUMPY_VAR = False

def ses_cal(frekans, sure, tip='sine', ses=0.2):
    if not NUMPY_VAR or AYAR_SES_SEVIYESI <= 0:
        return
    ses = ses * AYAR_SES_SEVIYESI
    try:
        orneklem = 44100
        kareler = int(orneklem * sure)
        t = np.linspace(0, sure, kareler, False)
        if tip == 'sine':
            dalga = np.sin(2 * np.pi * frekans * t)
        elif tip == 'square':
            dalga = np.sign(np.sin(2 * np.pi * frekans * t))
        elif tip == 'sawtooth':
            dalga = 2 * (t * frekans - np.floor(t * frekans + 0.5))
        else:
            dalga = np.random.uniform(-1, 1, kareler)
        zarf = np.ones(kareler)
        atk = int(orneklem * 0.01)
        rel = int(orneklem * 0.1)
        if atk > 0:
            zarf[:atk] = np.linspace(0, 1, atk)
        if rel > 0 and rel < kareler:
            zarf[-rel:] = np.linspace(1, 0, rel)
        dalga = (dalga * zarf * ses * 32767).astype(np.int16)
        stereo = np.column_stack([dalga, dalga])
        sound = pygame.sndarray.make_sound(stereo)
        sound.play()
    except:
        pass

def _dosya_ses_cal(ses_obj, taban=0.5):
    if ses_obj is None or AYAR_SES_SEVIYESI <= 0:
        return
    ses_obj.set_volume(taban * AYAR_SES_SEVIYESI)
    ses_obj.play()

def snd_hasar():
    ses_cal(200, 0.12, 'noise', 0.2)

def snd_olum():
    ses_cal(300, 0.08, 'sawtooth', 0.18)
    ses_cal(150, 0.15, 'sawtooth', 0.15)

def snd_para():
    ses_cal(1200, 0.06, 'sine', 0.08)

def snd_zipla():
    ses_cal(350, 0.1, 'sine', 0.1)

def snd_reload():
    ses_cal(400, 0.05, 'square', 0.08)
    ses_cal(600, 0.08, 'square', 0.06)

def snd_seviye():
    for i, n in enumerate([523, 659, 784, 1047]):
        pygame.time.delay(i * 120)
        ses_cal(n, 0.15, 'sine', 0.15)

def snd_bolum_tamam():
    if SES_BOLUM_TAMAM is not None:
        _dosya_ses_cal(SES_BOLUM_TAMAM)
        return
    snd_seviye()

def snd_can():
    ses_cal(700, 0.12, 'sine', 0.15)

def snd_vurus():
    # Silah/yumruk bir düşmana isabet ettiğinde (öldürmeden) çalan kısa darbe sesi
    ses_cal(150, 0.05, 'noise', 0.12)

# Her düşman tipinin öldüğünde çalan, snd_olum()'un üzerine binen ayırt edici "renk" sesi
DUSMAN_OLUM_SESLERI = {
    'melee':     [(320, 0.07, 'square', 0.12)],
    'ranged':    [(520, 0.05, 'square', 0.12), (260, 0.08, 'sawtooth', 0.1)],
    'drone':     [(900, 0.03, 'square', 0.12), (500, 0.05, 'square', 0.1)],
    'sniper':    [(1300, 0.03, 'square', 0.14)],
    'shield':    [(180, 0.05, 'noise', 0.16), (500, 0.06, 'square', 0.1)],
    'tank':      [(90, 0.22, 'sawtooth', 0.2), (60, 0.28, 'sine', 0.16)],
    'suicide':   [(120, 0.05, 'noise', 0.26)],
    'gorunmez':  [(700, 0.14, 'sine', 0.08), (250, 0.2, 'sine', 0.06)],
    'hayalet':   [(850, 0.14, 'sine', 0.1), (280, 0.24, 'sine', 0.08)],
    'mizrakli':  [(420, 0.05, 'square', 0.12)],
    'boss':      [(180, 0.18, 'sawtooth', 0.2), (120, 0.24, 'sine', 0.18)],
    'finalboss': [(200, 0.2, 'sawtooth', 0.22), (130, 0.3, 'sine', 0.2), (80, 0.4, 'sine', 0.18)],
}

def snd_dusman_olum(tip):
    for frekans, sure, dalga_tip, ses in DUSMAN_OLUM_SESLERI.get(tip, []):
        ses_cal(frekans, sure, dalga_tip, ses)
    if tip in ('boss', 'finalboss') and SES_BOSS_OLUM is not None:
        _dosya_ses_cal(SES_BOSS_OLUM)

def snd_karakter_olum():
    if SES_KARAKTER_OLUM is not None:
        _dosya_ses_cal(SES_KARAKTER_OLUM)
        return
    for i, n in enumerate([260, 200, 150, 90]):
        pygame.time.delay(i * 90)
        ses_cal(n, 0.22, 'sawtooth', 0.22)

def snd_kahraman_acildi():
    if SES_KAHRAMAN_ACILDI is not None:
        _dosya_ses_cal(SES_KAHRAMAN_ACILDI)
        return
    for i, n in enumerate([660, 880, 1100, 1320, 1760]):
        pygame.time.delay(i * 90)
        ses_cal(n, 0.14, 'square', 0.16)

# ── Kahramana özel ulti aktivasyon sesleri (hepsi farklı) ──
def snd_aegis_ulti():       # parlak, kutsal yükseliş
    for i, n in enumerate([523, 659, 784]):
        pygame.time.delay(i * 60)
        ses_cal(n, 0.14, 'sine', 0.15)

def snd_raptor_ulti():      # hızlı, agresif yükselen sıçrayış
    for i, n in enumerate([300, 500, 750, 1000]):
        pygame.time.delay(i * 40)
        ses_cal(n, 0.06, 'sawtooth', 0.14)

def snd_wraith_ulti():      # ürkütücü, alçalan hayaletimsi ton
    ses_cal(900, 0.2, 'sine', 0.08)
    ses_cal(500, 0.3, 'sine', 0.07)
    ses_cal(260, 0.4, 'sine', 0.06)

def snd_reaper_ulti():      # karanlık, katmanlı, ağır
    ses_cal(90, 0.35, 'sine', 0.2)
    ses_cal(180, 0.25, 'sawtooth', 0.14)
    ses_cal(320, 0.15, 'sawtooth', 0.1)

def snd_overdrive_ulti():   # zaman bükülmesi — iki yakın frekans çırpınma yaratır
    ses_cal(220, 0.3, 'square', 0.12)
    ses_cal(226, 0.3, 'square', 0.12)

def snd_ronin_ulti():       # keskin, metalik, dönen mızrak
    ses_cal(500, 0.05, 'noise', 0.14)
    for i, n in enumerate([700, 950, 1250]):
        pygame.time.delay(i * 50)
        ses_cal(n, 0.06, 'square', 0.1)

def snd_hex_ulti():
    if SES_HEX_ULTI is not None:
        _dosya_ses_cal(SES_HEX_ULTI)
        return
    ses_cal(1200, 0.06, 'sine', 0.12)
    ses_cal(1700, 0.08, 'sine', 0.1)

# ── Kahramana özel saldırı sesleri (her biri kendi silahına uygun) ──
def snd_kilic():         # AEGIS: kılıç savurma — metalik whoosh
    ses_cal(900, 0.04, 'noise', 0.1)
    ses_cal(500, 0.07, 'sine', 0.08)

def snd_pence():         # RAPTOR: pençe darbesi — keskin tırmalama
    ses_cal(1000, 0.03, 'noise', 0.14)
    ses_cal(420, 0.05, 'sawtooth', 0.1)

def snd_buyu():          # HEX: büyü/ışın — mistik parıltı
    ses_cal(1200, 0.05, 'sine', 0.09)
    ses_cal(1700, 0.06, 'sine', 0.07)

def snd_ruh():           # WRAITH: ruh mermisi — ürkütücü, yumuşak
    ses_cal(650, 0.09, 'sine', 0.07)
    ses_cal(980, 0.07, 'sine', 0.05)

def snd_koni():          # REAPER: karanlık koni atışı — alçak, ağır
    ses_cal(180, 0.08, 'sawtooth', 0.15)
    ses_cal(110, 0.12, 'sine', 0.12)

def snd_mizrak():        # RONIN: mızrak itişi/fırlatışı — keskin, metalik
    ses_cal(260, 0.03, 'noise', 0.12)
    ses_cal(620, 0.05, 'square', 0.1)

def snd_overdrive_ates():   # OVERDRIVE: tabanca — yüksek teknoloji, keskin
    ses_cal(1050, 0.035, 'square', 0.13)
    ses_cal(620, 0.05, 'sawtooth', 0.09)

def snd_overdrive_patlat():  # OVERDRIVE: E - yakın patlama
    ses_cal(700, 0.05, 'square', 0.15)
    ses_cal(300, 0.09, 'sawtooth', 0.14)

# ══════════════════════════════════════════
#  SESLER — Freesound'dan indirilen lisanslı dosyalar (bkz. sesler/_readme_and_license.txt)
# ══════════════════════════════════════════
SES_METROPOL_MUZIK = ses_dosyasi_yukle('metropol_muzik.ogg')       # ZHRØ — retroclassic-game-music (CC-BY 4.0)
SES_DERIN_UZAY_MUZIK = ses_dosyasi_yukle('derin_uzay_muzik.ogg')   # toam — robot-toy-music01-longtrack (CC-BY 3.0)
SES_HARABE_MUZIK = ses_dosyasi_yukle('harabe_muzik.ogg')           # TheoJT — fantasy-classical-themes (CC-BY 4.0)
SES_KARAKTER_OLUM = ses_dosyasi_yukle('karakter_olum.ogg')         # Diasyl — sci-fi-soldier-death (CC-BY 4.0)
SES_KAHRAMAN_ACILDI = ses_dosyasi_yukle('kahraman_acildi.ogg')     # TommasoMotteran — fantasy-achievement-unlock (CC-BY 4.0)
SES_HEX_ULTI = ses_dosyasi_yukle('hex_ulti.ogg')                   # TommasoMotteran — fantasy-ui-stinger-level-up-03 (CC-BY 4.0)
SES_BOLUM_TAMAM = ses_dosyasi_yukle('bolum_tamam.ogg')             # djlprojects — video-game-sfx-positive-action (CC-BY 4.0)
SES_BOSS_OLUM = ses_dosyasi_yukle('boss_olum.ogg')                 # Jofae — engine-dying (CC0)

# Kredi ekranında gösterilecek liste — freesound.org üzerinden lisanslı sesler
KREDI_LISTESI = [
    ("Retroclassic Game Music",            "ZHRØ",            "CC BY 4.0"),
    ("Robot Toy Music 01 (Longtrack)",      "toam",            "CC BY 3.0"),
    ("Fantasy Classical Themes",            "TheoJT",          "CC BY 4.0"),
    ("Sci-Fi Soldier Death",                "Diasyl",          "CC BY 4.0"),
    ("Fantasy Achievement Unlock",          "TommasoMotteran", "CC BY 4.0"),
    ("Fantasy UI Stinger — Level Up 03",    "TommasoMotteran", "CC BY 4.0"),
    ("Video Game SFX — Positive Action",    "djlprojects",     "CC BY 4.0"),
    ("Engine Dying",                        "Jofae",           "CC0"),
]

MUZIK_KANALI = pygame.mixer.Channel(0)
pygame.mixer.set_reserved(1)  # kanal 0: müzik için ayrılır, efektler onu çalmaz
_AKTIF_MUZIK = None
MUZIK_SES_SEVIYESI = 0.22  # ana ekran müzikleri kısık çalsın diye

def muzik_calistir(parca):
    global _AKTIF_MUZIK
    if parca is _AKTIF_MUZIK:
        return
    _AKTIF_MUZIK = parca
    if parca is None or AYAR_MUZIK_SEVIYESI <= 0:
        MUZIK_KANALI.stop()
        return
    parca.set_volume(MUZIK_SES_SEVIYESI * AYAR_MUZIK_SEVIYESI)
    MUZIK_KANALI.play(parca, loops=-1)

def muzik_ses_guncelle():
    # Ayarlar ekranında müzik seviyesi değişince, o an çalması gereken parçaya anında uygulanır
    if _AKTIF_MUZIK is None:
        return
    if AYAR_MUZIK_SEVIYESI <= 0:
        MUZIK_KANALI.stop()
        return
    if not MUZIK_KANALI.get_busy():
        MUZIK_KANALI.play(_AKTIF_MUZIK, loops=-1)
    MUZIK_KANALI.set_volume(MUZIK_SES_SEVIYESI * AYAR_MUZIK_SEVIYESI)

# ══════════════════════════════════════════
#  SİLAHLAR
# ══════════════════════════════════════════
SILAHLAR = [
    {'id':0, 'isim':'LAZER TABANCA',  'ikon':'[L]', 'fiyat':0,     'hasar':10, 'atis_hizi':12, 'mermi_hizi':13, 'sarjor':15, 'dolum':90,  'renk':(245,166,35),  'derece':1},
    {'id':1, 'isim':'PLAZMA TABANCA', 'ikon':'[P]', 'fiyat':300,   'hasar':16, 'atis_hizi':10, 'mermi_hizi':14, 'sarjor':18, 'dolum':80,  'renk':(68,136,255),  'derece':1},
    {'id':2, 'isim':'NEON SHOTGUN',   'ikon':'[S]', 'fiyat':700,   'hasar':12, 'atis_hizi':18, 'mermi_hizi':11, 'sarjor':8,  'dolum':100, 'renk':(255,68,170),  'derece':2, 'sacma':3},
    {'id':3, 'isim':'ION RIFLE',      'ikon':'[I]', 'fiyat':1200,  'hasar':28, 'atis_hizi':20, 'mermi_hizi':17, 'sarjor':10, 'dolum':110, 'renk':(255,255,0),   'derece':2},
    {'id':4, 'isim':'PROTON BURST',   'ikon':'[B]', 'fiyat':1800,  'hasar':18, 'atis_hizi':8,  'mermi_hizi':12, 'sarjor':20, 'dolum':85,  'renk':(255,136,0),   'derece':2, 'cift':True},
    {'id':5, 'isim':'CYBER SMG',      'ikon':'[M]', 'fiyat':2600,  'hasar':9,  'atis_hizi':4,  'mermi_hizi':14, 'sarjor':35, 'dolum':95,  'renk':(255,102,0),   'derece':3},
    {'id':6, 'isim':'VOID CANNON',    'ikon':'[V]', 'fiyat':3600,  'hasar':45, 'atis_hizi':30, 'mermi_hizi':10, 'sarjor':5,  'dolum':130, 'renk':(170,0,255),   'derece':3},
    {'id':7, 'isim':'QUANTUM RIFLE',  'ikon':'[Q]', 'fiyat':5000,  'hasar':35, 'atis_hizi':15, 'mermi_hizi':20, 'sarjor':12, 'dolum':105, 'renk':(0,255,247),   'derece':3},
    {'id':8, 'isim':'NOVA LAUNCHER',  'ikon':'[N]', 'fiyat':7000,  'hasar':20, 'atis_hizi':7,  'mermi_hizi':11, 'sarjor':16, 'dolum':115, 'renk':(255,238,0),   'derece':4, 'sacma':4},
    {'id':9, 'isim':'OMEGA BLASTER',  'ikon':'[O]', 'fiyat':10000, 'hasar':60, 'atis_hizi':10, 'mermi_hizi':16, 'sarjor':24, 'dolum':75,  'renk':(255,0,102),   'derece':4, 'cift':True},
]

# ══════════════════════════════════════════
#  KAHRAMANLAR (yer tutucu - görseller ve güçler sonra eklenecek)
# ══════════════════════════════════════════
KAHRAMANLAR = [
    {'id':0, 'isim':'AEGIS',      'renk':CYAN,    'acilis_bolum':1},
    {'id':1, 'isim':'RAPTOR',     'renk':YESIL,   'acilis_bolum':5},
    {'id':5, 'isim':'OVERDRIVE',  'renk':SARI, 'acilis_bolum':20},
    {'id':6, 'isim':'HEX',        'renk':MOR,     'acilis_bolum':10},
    {'id':7, 'isim':'WRAITH',     'renk':(120,220,200), 'acilis_bolum':15},
    {'id':8, 'isim':'REAPER',     'renk':(210,200,180), 'acilis_bolum':17},
    {'id':9, 'isim':'RONIN',      'renk':(170,120,255), 'acilis_bolum':25},
]

# Oturum boyunca ulaşılan en yüksek bölüm (kahraman kilitlerini açar)
en_yuksek_bolum = 1
secili_kahraman = 0

# ── KAHRAMAN USTALAŞMA (kalıcı ilerleme) ──
# Para yerine: o kahramanla toplam ne kadar hasar verdiğine göre kademeli
# olarak güçlenir. Mini boss gibi güçlü düşmanlara verilen hasar, zayıf bir
# düşmana verilenden çok daha fazla katkı sağlar (can'ı property yapıp her
# azalışı otomatik sayan mekanizma sayesinde — bkz. Dusman/Solucan.can).
USTALIK_ESIKLERI = [4000, 15000, 40000]  # tanımsız kahramanlar için yedek eşik
# Karakteri AÇMAK ne kadar zorsa (bölüm sayısı arttıkça), USTALAŞTIRMAK o kadar
# kolay olsun diye eşikler ters orantılı: AEGIS bölüm 1'de açılıyor ama tüm oyunu
# onunla oynama şansın var, o yüzden en yüksek eşiğe (4000) sahip; RONIN bölüm
# 25'te açılıyor, ustalaşmak için az bölüm kaldığından en düşük eşiğe (2000) sahip.
KAHRAMAN_USTALIK_ESIKLERI = {
    0: [3640, 3820, 4000],   # AEGIS      — açılış: bölüm 1
    1: [3310, 3490, 3670],   # RAPTOR     — açılış: bölüm 5
    6: [2970, 3150, 3330],   # HEX        — açılış: bölüm 10
    7: [2640, 2820, 3000],   # WRAITH     — açılış: bölüm 15
    8: [2310, 2490, 2670],   # REAPER     — açılış: bölüm 17
    5: [1970, 2150, 2330],   # OVERDRIVE  — açılış: bölüm 20
    9: [1640, 1820, 2000],   # RONIN      — açılış: bölüm 25
}
KAHRAMAN_HASAR = {0: 0.0, 1: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 5: 0.0, 9: 0.0}
# Açılmış (ustalik esigine ulasilmis) bir yetenegi oyuncu isterse kapatabilir —
# burada sadece MANUEL olarak kapatilmis (hero_id, index) ciftleri tutulur.
KAHRAMAN_YETENEK_KAPALI = set()

# Bir ustalik yetenegi YENI acildiginda ekranin sol altinda kisa bir basarim
# bildirimi gostermek icin: her kahramanin son bilinen kademesi + bekleyen kuyruk.
KAHRAMAN_SON_KADEME = {}
BASARIM_KUYRUGU = []          # bekleyen [(baslik, alt_yazi)] bildirimleri
BASARIM_AKTIF = None          # su an gosterilen [baslik, alt_yazi, kalan_kare]
BASARIM_SURESI = 220

def ustalik_kademe_kontrol(hero_id):
    tierler = KAHRAMAN_YUKSELTMELERI.get(hero_id)
    if not tierler:
        return
    yeni_kademe = ustalik_kademesi(hero_id)
    onceki = KAHRAMAN_SON_KADEME.get(hero_id, 0)
    if yeni_kademe > onceki:
        KAHRAMAN_SON_KADEME[hero_id] = yeni_kademe
        for i in range(onceki, min(yeni_kademe, len(tierler))):
            BASARIM_KUYRUGU.append((tierler[i][0], "GOREVI TAMAMLADIN!"))

# ── AYARLAR (ses/müzik seviyesi, nişangah, imleç) ──
NISANGAH_RENKLERI = [('CYAN', CYAN), ('KIRMIZI', KIRMIZI), ('YESIL', YESIL),
                      ('SARI', SARI), ('BEYAZ', BEYAZ), ('MOR', MOR), ('TURUNCU', TURUNCU)]
NISANGAH_SEKILLERI = ['arti', 'daire', 'nokta', 'kare']
AYAR_SES_SEVIYESI = 1.0
AYAR_MUZIK_SEVIYESI = 1.0
AYAR_NISANGAH_RENK_IDX = 0
AYAR_NISANGAH_SEKIL_IDX = 0
AYAR_IMLEC_GIZLI = False
AYAR_MOBIL_KONTROL = False
AYAR_MOBIL_JOY_POS = [100, YUKSEKLIK - 100]     # sanal joystick merkezi (sürüklenip taşınabilir)
AYAR_MOBIL_ATES_POS = [GENISLIK - 100, YUKSEKLIK - 110]  # ATEŞ butonu merkezi (diğer butonlar buna göre dizilir)

# ── DİL (i18n) ──
DILLER = ['tr', 'en', 'es', 'fr', 'de']
DIL_ISIMLERI = {'tr': 'TURKCE', 'en': 'ENGLISH', 'es': 'ESPANOL', 'fr': 'FRANCAIS', 'de': 'DEUTSCH'}
AYAR_DIL = 'tr'

# Çekirdek arayüz metinleri (menüler/HUD/ayarlar/kontroller/duraklatma/bitiş ekranları).
# Oyun adı ("REVOLT") ve kahraman isimleri (AEGIS, RAPTOR, HEX, WRAITH, REAPER,
# OVERDRIVE, RONIN) kasıtlı olarak çevrilmiyor — özel isim olarak kalıyorlar.
CEVIRI = {
    'tr': {
        'menu_oyna': "OYNA", 'menu_hayatta_kal': "HAYATTA KAL", 'menu_kahramanlar': "KAHRAMANLAR",
        'menu_bolumler': "BOLUMLER", 'menu_kontroller': "KONTROLLER", 'menu_ayarlar': "AYARLAR",
        'menu_cikis': "CIKIS", 'menu_ipucu': "↑↓ Sec   ENTER Onayla   veya Mouse ile Tikla",
        'kontroller_baslik': "KONTROLLER",
        'menu_krediler': "KREDILER",
        'krediler_baslik': "KREDILER",
        'krediler_alt': "Bu oyunda kullanilan sesler icin tesekkurler:",
        'kontrol_1': "SOL / SAG OK veya A / D : Hareket Et",
        'kontrol_2': "YUKARI OK / SPACE / W : Zipla",
        'kontrol_3': "SOL TIK (basili tut) : Saldir",
        'kontrol_4': "SAG TIK : Ozel Yetenek (kahramana gore degisir)",
        'kontrol_5': "E : Ikincil Yetenek (kahramana gore degisir)",
        'kontrol_6': "Q : Ulti (dolunca kullanilabilir)",
        'kontrol_7': "ESC : Duraklat / Ana Menuye Don",
        'geri_enter': "ESC / ENTER Geri",
        'ayarlar_baslik': "AYARLAR",
        'ses_efekti': "SES EFEKTI",
        'muzik': "MUZIK",
        'nisangah_rengi': "NISANGAH RENGI",
        'nisangah_sekli': "NISANGAH SEKLI",
        'sekil_arti': "ARTI", 'sekil_daire': "DAIRE", 'sekil_nokta': "NOKTA", 'sekil_kare': "KARE",
        'imlec_gizle': "IMLECI GIZLE (Sadece Nisangah)",
        'acik': "ACIK", 'kapali': "KAPALI",
        'mobil_kontroller': "MOBIL KONTROLLER (dokunmatik joystick+butonlar)",
        'mobil_duzen': "MOBIL DUZEN (surukleyerek tasi):",
        'hareket_label': "HAREKET", 'ates_label': "ATES",
        'dil_label': "DIL",
        'geri': "GERI",
        'pause_baslik': "DURAKLATILDI",
        'devam_et': "DEVAM ET",
        'ana_menuye_don': "ANA MENUYE DON",
        'bolum_tamam': "BOLUM {bolum} TAMAM!",
        'para_skor': "Skor: {skor}",
        'yeni_kahraman_acildi': "YENI KAHRAMAN ACILDI!",
        'kahraman_secilebilir': "KAHRAMANLAR ekraninda secilebilir",
        'tebrikler_kazandin': "TEBRIKLER! KAZANDIN!",
        'game_over': "GAME OVER",
        'skor_para': "SKOR: {skor}",
        'enter_tekrar': "ENTER = Tekrar Oyna   ESC = Ana Menu",
        'tekrar_oyna': "TEKRAR OYNA", 'canlan': "CANLAN",
        'can': "CAN", 'seviye': "SEVIYE", 'sure': "SURE", 'oldurulen': "OLDURULEN",
        'bolum': "BOLUM", 'dusman': "DUSMAN",
        'hayatta_kalma_bitti': "HAYATTA KALMA SONA ERDI",
    },
    'en': {
        'menu_oyna': "PLAY", 'menu_hayatta_kal': "SURVIVAL", 'menu_kahramanlar': "HEROES",
        'menu_bolumler': "LEVELS", 'menu_kontroller': "CONTROLS", 'menu_ayarlar': "SETTINGS",
        'menu_cikis': "QUIT", 'menu_ipucu': "↑↓ Select   ENTER Confirm   or Click with Mouse",
        'kontroller_baslik': "CONTROLS",
        'menu_krediler': "CREDITS",
        'krediler_baslik': "CREDITS",
        'krediler_alt': "Thanks to the artists behind this game's sounds:",
        'kontrol_1': "LEFT / RIGHT ARROW or A / D: Move",
        'kontrol_2': "UP ARROW / SPACE / W: Jump",
        'kontrol_3': "LEFT CLICK (hold): Attack",
        'kontrol_4': "RIGHT CLICK: Special Ability (varies by hero)",
        'kontrol_5': "E: Secondary Ability (varies by hero)",
        'kontrol_6': "Q: Ultimate (usable when charged)",
        'kontrol_7': "ESC: Pause / Return to Main Menu",
        'geri_enter': "ESC / ENTER Back",
        'ayarlar_baslik': "SETTINGS",
        'ses_efekti': "SOUND EFFECTS",
        'muzik': "MUSIC",
        'nisangah_rengi': "CROSSHAIR COLOR",
        'nisangah_sekli': "CROSSHAIR SHAPE",
        'sekil_arti': "CROSS", 'sekil_daire': "CIRCLE", 'sekil_nokta': "DOT", 'sekil_kare': "SQUARE",
        'imlec_gizle': "HIDE CURSOR (Crosshair Only)",
        'acik': "ON", 'kapali': "OFF",
        'mobil_kontroller': "MOBILE CONTROLS (touch joystick+buttons)",
        'mobil_duzen': "MOBILE LAYOUT (drag to move):",
        'hareket_label': "MOVE", 'ates_label': "FIRE",
        'dil_label': "LANGUAGE",
        'geri': "BACK",
        'pause_baslik': "PAUSED",
        'devam_et': "RESUME",
        'ana_menuye_don': "RETURN TO MENU",
        'bolum_tamam': "LEVEL {bolum} COMPLETE!",
        'para_skor': "Score: {skor}",
        'yeni_kahraman_acildi': "NEW HERO UNLOCKED!",
        'kahraman_secilebilir': "Selectable in the HEROES screen",
        'tebrikler_kazandin': "CONGRATULATIONS! YOU WON!",
        'game_over': "GAME OVER",
        'skor_para': "SCORE: {skor}",
        'enter_tekrar': "ENTER = Play Again   ESC = Main Menu",
        'tekrar_oyna': "PLAY AGAIN", 'canlan': "REVIVE",
        'can': "HP", 'seviye': "LEVEL", 'sure': "TIME", 'oldurulen': "KILLS",
        'bolum': "LEVEL", 'dusman': "ENEMY",
        'hayatta_kalma_bitti': "SURVIVAL RUN OVER",
    },
    'es': {
        'menu_oyna': "JUGAR", 'menu_hayatta_kal': "SUPERVIVENCIA", 'menu_kahramanlar': "HEROES",
        'menu_bolumler': "NIVELES", 'menu_kontroller': "CONTROLES", 'menu_ayarlar': "AJUSTES",
        'menu_cikis': "SALIR", 'menu_ipucu': "↑↓ Elegir   ENTER Confirmar   o Clic con el Raton",
        'kontroller_baslik': "CONTROLES",
        'menu_krediler': "CREDITOS",
        'krediler_baslik': "CREDITOS",
        'krediler_alt': "Gracias a los artistas de los sonidos de este juego:",
        'kontrol_1': "FLECHA IZQ / DER o A / D: Moverse",
        'kontrol_2': "FLECHA ARRIBA / ESPACIO / W: Saltar",
        'kontrol_3': "CLIC IZQUIERDO (mantener): Atacar",
        'kontrol_4': "CLIC DERECHO: Habilidad Especial (segun heroe)",
        'kontrol_5': "E: Habilidad Secundaria (segun heroe)",
        'kontrol_6': "Q: Definitiva (usable cuando esta cargada)",
        'kontrol_7': "ESC: Pausar / Volver al Menu Principal",
        'geri_enter': "ESC / ENTER Atras",
        'ayarlar_baslik': "AJUSTES",
        'ses_efekti': "EFECTOS DE SONIDO",
        'muzik': "MUSICA",
        'nisangah_rengi': "COLOR DE LA MIRA",
        'nisangah_sekli': "FORMA DE LA MIRA",
        'sekil_arti': "CRUZ", 'sekil_daire': "CIRCULO", 'sekil_nokta': "PUNTO", 'sekil_kare': "CUADRADO",
        'imlec_gizle': "OCULTAR CURSOR (Solo Mira)",
        'acik': "ACTIVADO", 'kapali': "DESACTIVADO",
        'mobil_kontroller': "CONTROLES MOVILES (joystick+botones tactiles)",
        'mobil_duzen': "DISPOSICION MOVIL (arrastra para mover):",
        'hareket_label': "MOVER", 'ates_label': "DISPARAR",
        'dil_label': "IDIOMA",
        'geri': "ATRAS",
        'pause_baslik': "PAUSADO",
        'devam_et': "REANUDAR",
        'ana_menuye_don': "VOLVER AL MENU",
        'bolum_tamam': "¡NIVEL {bolum} COMPLETADO!",
        'para_skor': "Puntos: {skor}",
        'yeni_kahraman_acildi': "¡NUEVO HEROE DESBLOQUEADO!",
        'kahraman_secilebilir': "Seleccionable en la pantalla de HEROES",
        'tebrikler_kazandin': "¡FELICIDADES! ¡GANASTE!",
        'game_over': "FIN DEL JUEGO",
        'skor_para': "PUNTOS: {skor}",
        'enter_tekrar': "ENTER = Jugar de Nuevo   ESC = Menu Principal",
        'tekrar_oyna': "JUGAR DE NUEVO", 'canlan': "REVIVIR",
        'can': "VIDA", 'seviye': "NIVEL", 'sure': "TIEMPO", 'oldurulen': "BAJAS",
        'bolum': "NIVEL", 'dusman': "ENEMIGO",
        'hayatta_kalma_bitti': "SUPERVIVENCIA TERMINADA",
    },
    'fr': {
        'menu_oyna': "JOUER", 'menu_hayatta_kal': "SURVIE", 'menu_kahramanlar': "HEROS",
        'menu_bolumler': "NIVEAUX", 'menu_kontroller': "COMMANDES", 'menu_ayarlar': "PARAMETRES",
        'menu_cikis': "QUITTER", 'menu_ipucu': "↑↓ Choisir   ENTREE Valider   ou Clic Souris",
        'kontroller_baslik': "COMMANDES",
        'menu_krediler': "CREDITS",
        'krediler_baslik': "CREDITS",
        'krediler_alt': "Merci aux artistes des sons de ce jeu :",
        'kontrol_1': "FLECHE GAUCHE / DROITE ou A / D : Se deplacer",
        'kontrol_2': "FLECHE HAUT / ESPACE / W : Sauter",
        'kontrol_3': "CLIC GAUCHE (maintenir) : Attaquer",
        'kontrol_4': "CLIC DROIT : Capacite Speciale (selon le heros)",
        'kontrol_5': "E : Capacite Secondaire (selon le heros)",
        'kontrol_6': "Q : Ultime (utilisable une fois chargee)",
        'kontrol_7': "ECHAP : Pause / Retour au Menu Principal",
        'geri_enter': "ECHAP / ENTREE Retour",
        'ayarlar_baslik': "PARAMETRES",
        'ses_efekti': "EFFETS SONORES",
        'muzik': "MUSIQUE",
        'nisangah_rengi': "COULEUR DU VISEUR",
        'nisangah_sekli': "FORME DU VISEUR",
        'sekil_arti': "CROIX", 'sekil_daire': "CERCLE", 'sekil_nokta': "POINT", 'sekil_kare': "CARRE",
        'imlec_gizle': "MASQUER LE CURSEUR (Viseur Seul)",
        'acik': "ACTIVE", 'kapali': "DESACTIVE",
        'mobil_kontroller': "COMMANDES MOBILES (joystick+boutons tactiles)",
        'mobil_duzen': "DISPOSITION MOBILE (glisser pour deplacer) :",
        'hareket_label': "DEPLACER", 'ates_label': "TIRER",
        'dil_label': "LANGUE",
        'geri': "RETOUR",
        'pause_baslik': "PAUSE",
        'devam_et': "REPRENDRE",
        'ana_menuye_don': "RETOUR AU MENU",
        'bolum_tamam': "NIVEAU {bolum} TERMINE !",
        'para_skor': "Score : {skor}",
        'yeni_kahraman_acildi': "NOUVEAU HEROS DEBLOQUE !",
        'kahraman_secilebilir': "Selectionnable dans l'ecran HEROS",
        'tebrikler_kazandin': "FELICITATIONS ! VOUS AVEZ GAGNE !",
        'game_over': "GAME OVER",
        'skor_para': "SCORE : {skor}",
        'enter_tekrar': "ENTREE = Rejouer   ECHAP = Menu Principal",
        'tekrar_oyna': "REJOUER", 'canlan': "RESSUSCITER",
        'can': "VIE", 'seviye': "NIVEAU", 'sure': "TEMPS", 'oldurulen': "ELIMINATIONS",
        'bolum': "NIVEAU", 'dusman': "ENNEMI",
        'hayatta_kalma_bitti': "SURVIE TERMINEE",
    },
    'de': {
        'menu_oyna': "SPIELEN", 'menu_hayatta_kal': "UEBERLEBEN", 'menu_kahramanlar': "HELDEN",
        'menu_bolumler': "LEVEL", 'menu_kontroller': "STEUERUNG", 'menu_ayarlar': "EINSTELLUNGEN",
        'menu_cikis': "BEENDEN", 'menu_ipucu': "↑↓ Waehlen   ENTER Bestaetigen   oder Mausklick",
        'kontroller_baslik': "STEUERUNG",
        'menu_krediler': "CREDITS",
        'krediler_baslik': "CREDITS",
        'krediler_alt': "Danke an die Kuenstler der Sounds dieses Spiels:",
        'kontrol_1': "LINKS / RECHTS PFEIL oder A / D: Bewegen",
        'kontrol_2': "PFEIL HOCH / LEERTASTE / W: Springen",
        'kontrol_3': "LINKSKLICK (halten): Angreifen",
        'kontrol_4': "RECHTSKLICK: Spezialfaehigkeit (je nach Held)",
        'kontrol_5': "E: Zweitfaehigkeit (je nach Held)",
        'kontrol_6': "Q: Ultimate (einsetzbar wenn aufgeladen)",
        'kontrol_7': "ESC: Pause / Zurueck zum Hauptmenue",
        'geri_enter': "ESC / ENTER Zurueck",
        'ayarlar_baslik': "EINSTELLUNGEN",
        'ses_efekti': "SOUNDEFFEKTE",
        'muzik': "MUSIK",
        'nisangah_rengi': "FADENKREUZFARBE",
        'nisangah_sekli': "FADENKREUZFORM",
        'sekil_arti': "KREUZ", 'sekil_daire': "KREIS", 'sekil_nokta': "PUNKT", 'sekil_kare': "QUADRAT",
        'imlec_gizle': "CURSOR AUSBLENDEN (Nur Fadenkreuz)",
        'acik': "AN", 'kapali': "AUS",
        'mobil_kontroller': "MOBILE STEUERUNG (Touch-Joystick+Buttons)",
        'mobil_duzen': "MOBILES LAYOUT (zum Verschieben ziehen):",
        'hareket_label': "BEWEGEN", 'ates_label': "FEUER",
        'dil_label': "SPRACHE",
        'geri': "ZURUECK",
        'pause_baslik': "PAUSIERT",
        'devam_et': "FORTSETZEN",
        'ana_menuye_don': "ZURUECK ZUM MENUE",
        'bolum_tamam': "LEVEL {bolum} GESCHAFFT!",
        'para_skor': "Punkte: {skor}",
        'yeni_kahraman_acildi': "NEUER HELD FREIGESCHALTET!",
        'kahraman_secilebilir': "Im HELDEN-Bildschirm auswaehlbar",
        'tebrikler_kazandin': "GLUECKWUNSCH! DU HAST GEWONNEN!",
        'game_over': "GAME OVER",
        'skor_para': "PUNKTE: {skor}",
        'enter_tekrar': "ENTER = Nochmal Spielen   ESC = Hauptmenue",
        'tekrar_oyna': "NOCHMAL SPIELEN", 'canlan': "WIEDERBELEBEN",
        'can': "LEBEN", 'seviye': "LEVEL", 'sure': "ZEIT", 'oldurulen': "ABSCHUESSE",
        'bolum': "LEVEL", 'dusman': "GEGNER",
        'hayatta_kalma_bitti': "UEBERLEBEN BEENDET",
    },
}

def t(anahtar, **kwargs):
    metin = CEVIRI.get(AYAR_DIL, CEVIRI['tr']).get(anahtar) or CEVIRI['tr'].get(anahtar, anahtar)
    return metin.format(**kwargs) if kwargs else metin

# Web derlemesinde (pygbag) çalışma dizini sanal/kalıcı bir depoya bağlanır;
# __file__'e göre mutlak yol tarayıcıda anlamsız olduğundan basit bağıl yol kullanılır.
# PyInstaller tek-dosya .exe'sinde ise __file__/_MEIPASS her açılışta silinen geçici
# bir klasördür — kayıt dosyası orada tutulursa oyun kapanınca kaybolur, bu yüzden
# gerçek .exe'nin bulunduğu klasör (sys.executable) kullanılır ki ilerleme kalıcı olsun.
if _WEB_ORTAMI:
    KAYIT_DOSYASI = 'kayit.json'
elif _DONDURULMUS:
    KAYIT_DOSYASI = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), 'kayit.json')
else:
    KAYIT_DOSYASI = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kayit.json')

def kayit_yukle():
    global en_yuksek_bolum, TOPLAM_OLDURULEN, EN_UZUN_HAYATTA_KALMA
    global AYAR_SES_SEVIYESI, AYAR_MUZIK_SEVIYESI, AYAR_NISANGAH_RENK_IDX, AYAR_NISANGAH_SEKIL_IDX, AYAR_IMLEC_GIZLI, AYAR_MOBIL_KONTROL
    global AYAR_MOBIL_JOY_POS, AYAR_MOBIL_ATES_POS, AYAR_DIL
    try:
        with open(KAYIT_DOSYASI, 'r', encoding='utf-8') as f:
            veri = json.load(f)
        en_yuksek_bolum = max(1, int(veri.get('en_yuksek_bolum', 1)))
        for kid_str, deger in veri.get('kahraman_hasar', {}).items():
            kid = int(kid_str)
            if kid in KAHRAMAN_HASAR:
                KAHRAMAN_HASAR[kid] = float(deger)
        TOPLAM_OLDURULEN = int(veri.get('toplam_oldurulen', 0))
        EN_UZUN_HAYATTA_KALMA = float(veri.get('en_uzun_hayatta_kalma', 0.0))
        AYAR_SES_SEVIYESI = max(0.0, min(1.0, float(veri.get('ses_seviyesi', 1.0))))
        AYAR_MUZIK_SEVIYESI = max(0.0, min(1.0, float(veri.get('muzik_seviyesi', 1.0))))
        AYAR_NISANGAH_RENK_IDX = max(0, min(len(NISANGAH_RENKLERI)-1, int(veri.get('nisangah_renk_idx', 0))))
        AYAR_NISANGAH_SEKIL_IDX = max(0, min(len(NISANGAH_SEKILLERI)-1, int(veri.get('nisangah_sekil_idx', 0))))
        AYAR_IMLEC_GIZLI = bool(veri.get('imlec_gizli', False))
        AYAR_MOBIL_KONTROL = bool(veri.get('mobil_kontrol', False))
        joy_kayitli = veri.get('mobil_joy_pos')
        if isinstance(joy_kayitli, list) and len(joy_kayitli) == 2:
            AYAR_MOBIL_JOY_POS = [float(joy_kayitli[0]), float(joy_kayitli[1])]
        ates_kayitli = veri.get('mobil_ates_pos')
        if isinstance(ates_kayitli, list) and len(ates_kayitli) == 2:
            AYAR_MOBIL_ATES_POS = [float(ates_kayitli[0]), float(ates_kayitli[1])]
        AYAR_DIL = veri.get('dil', 'tr') if veri.get('dil') in DILLER else 'tr'
        KAHRAMAN_YETENEK_KAPALI.clear()
        for anahtar in veri.get('yetenek_kapali', []):
            try:
                hid_str, idx_str = anahtar.split('_')
                KAHRAMAN_YETENEK_KAPALI.add((int(hid_str), int(idx_str)))
            except ValueError:
                pass
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError):
        pass

def kayit_kaydet():
    try:
        veri = {
            'en_yuksek_bolum': en_yuksek_bolum,
            'kahraman_hasar': KAHRAMAN_HASAR,
            'toplam_oldurulen': TOPLAM_OLDURULEN,
            'en_uzun_hayatta_kalma': EN_UZUN_HAYATTA_KALMA,
            'ses_seviyesi': AYAR_SES_SEVIYESI,
            'muzik_seviyesi': AYAR_MUZIK_SEVIYESI,
            'nisangah_renk_idx': AYAR_NISANGAH_RENK_IDX,
            'nisangah_sekil_idx': AYAR_NISANGAH_SEKIL_IDX,
            'imlec_gizli': AYAR_IMLEC_GIZLI,
            'mobil_kontrol': AYAR_MOBIL_KONTROL,
            'mobil_joy_pos': AYAR_MOBIL_JOY_POS,
            'mobil_ates_pos': AYAR_MOBIL_ATES_POS,
            'dil': AYAR_DIL,
            'yetenek_kapali': [f"{hid}_{idx}" for hid, idx in KAHRAMAN_YETENEK_KAPALI],
        }
        with open(KAYIT_DOSYASI, 'w', encoding='utf-8') as f:
            json.dump(veri, f)
    except OSError:
        pass

def ustalik_esikleri(kahraman_id):
    return KAHRAMAN_USTALIK_ESIKLERI.get(kahraman_id, USTALIK_ESIKLERI)

def ustalik_kademesi(kahraman_id):
    hasar = KAHRAMAN_HASAR.get(kahraman_id, 0.0)
    kademe = 0
    for esik in ustalik_esikleri(kahraman_id):
        if hasar >= esik:
            kademe += 1
    return kademe

# (isim, aciklama, etki) — etki: can / hiz(oransal) / regen(saniyede can)
KAHRAMAN_YUKSELTMELERI = {
    0: [("KESKIN MENZIL", "Kilic sol tik (savurma) menzili +%35 artar", {'kilic_menzil': AEGIS_KILIC_MENZIL_ARTIS}),
        ("KORUYUCU AZIM", "5 saniye hasar almazsan az canli bir kalkan kazanirsin — almaya devam ettikce ustune eklenir", {'pasif_kalkan': True}),
        ("SEKEN KILIC", "Firlattigin kilic saplandigi yerden, uzaklik fark etmeden 5 dusmana kadar aninda seker, sonra geri doner", {'kilic_sekme': True})],
    1: [("ZEHIR BULUTU", "E'ye basinca etrafindaki dusmanlara aninda zehir bulasir", {'raptor_zehir_patlama': True}),
        ("KAN KOKUSU", "Her dash sonrasi birkac saniye ofkelenirsin — pence/dash hasari +%30", {'raptor_ofke': True}),
        ("SINIRSIZ HAMLE", "Hamle (dash) bekleme suresi kalkar, sinirsizca kullanabilirsin", {'raptor_dash_sinirsiz': True})],
    6: [("BUYULU OZDIRENC", "+50 Can (100'e cikar)", {'can': HEX_CAN_YUKSELTME}),
        ("USTA KITAPLIK", f"Azami kitap sayisi {HEX_KITAP_MAX_USTA}'ya cikar, isin hasari da buna gore artar", {'hex_kitap_max': HEX_KITAP_MAX_USTA}),
        ("GERCEKLIK KIRIMI", "Ulti artik ekrandaki her dusmani aninda oldurur", {'hex_ulti_temizle': True})],
    7: [("HAYALET AVCISI", "Hayaletken hasar penaltisi kalkar, +%30 hasar verirsin", {'wraith_hayalet_hasar': True}),
        ("RUH BAGI", "Kazandigin her ruh, ulti barini doldururken aninda can da verir", {'wraith_ruh_heal': True}),
        ("SINIRSIZ HAYALET", "Hayalet suresi 8 sn'e cikar, ruh maliyeti kalkar — sadece bittikten sonra 5 sn beklersin", {'wraith_hayalet_usta': True})],
    8: [("RUH ORDUSU", "E'ye basinca mevcutlari guclendirmenin yaninda 3 ek delirmis iskelet cagirir", {'reaper_e_ek_iskelet': True}),
        ("CANSIZ MIRAS", "Normal atisinla bir dusmani oldurdugunde o dusmanin yerinde bir iskelet belirir", {'reaper_atis_iskelet': True}),
        ("OKCU LEJYONU", "Ultiden cikan tum iskeletler artik mavi, uzaktan vuran okcu iskelet olur", {'reaper_ulti_okcu': True})],
    5: [("HIRSIZ SARJ", "Her kanca attiginda 10 can iyilesirsin", {'overdrive_kanca_heal': True}),
        ("CEKIRDEK KALKANI", "Ulti aktifken ve bittikten 3 sn sonrasina kadar 1 canin altina dusmezsin (renk degisimiyle belli olur)", {'overdrive_ulti_olumsuz': True}),
        ("CIFTE NAMLU", "Tabancanin ates hizi %100 artar", {'overdrive_hizli_ates': True})],
    9: [("UZUN MIZRAK", "Mizragin (itis+firlatma) menzili %50 artar", {'ronin_menzil': True}),
        ("GOLGE PENCESI", "Golge modundayken vurdugun dusmanlar 5 saniyeligine donar", {'ronin_gizli_sersem': True}),
        ("FIRTINA USTASI", "Ultinin menzili %100 artar ve aktive olunca 50 can doldurur", {'ronin_ulti_gelismis': True})],
}

def ustalik_uygula(oyuncu, kahraman_id):
    kademe = ustalik_kademesi(kahraman_id)
    tierler = KAHRAMAN_YUKSELTMELERI.get(kahraman_id, [])
    for i in range(min(kademe, len(tierler))):
        if (kahraman_id, i) in KAHRAMAN_YETENEK_KAPALI:
            continue
        _, _, etki = tierler[i]
        if 'can' in etki:
            oyuncu.max_can += etki['can']
            oyuncu.can += etki['can']
        if 'hiz' in etki:
            oyuncu.survivor_hiz_carpan *= (1 + etki['hiz'])
        if 'regen' in etki:
            oyuncu.survivor_can_yenileme += etki['regen'] / 60.0
        if 'kilic_menzil' in etki:
            oyuncu.aegis_kilic_menzil_carpan *= (1 + etki['kilic_menzil'])
        if 'pasif_kalkan' in etki:
            oyuncu.aegis_pasif_kalkan_acik = True
        if 'kilic_sekme' in etki:
            oyuncu.aegis_kilic_sekme_acik = True
        if 'raptor_zehir_patlama' in etki:
            oyuncu.raptor_zehir_patlama_acik = True
        if 'raptor_ofke' in etki:
            oyuncu.raptor_ofke_acik = True
        if 'raptor_dash_sinirsiz' in etki:
            oyuncu.raptor_dash_sinirsiz_acik = True
        if 'hex_kitap_max' in etki:
            oyuncu.hex_kitap_max_ozel = etki['hex_kitap_max']
        if 'hex_ulti_temizle' in etki:
            oyuncu.hex_ulti_ekran_temizle_acik = True
        if 'wraith_hayalet_hasar' in etki:
            oyuncu.wraith_hayalet_hasar_artis_acik = True
        if 'wraith_ruh_heal' in etki:
            oyuncu.wraith_ruh_heal_acik = True
        if 'wraith_hayalet_usta' in etki:
            oyuncu.wraith_hayalet_usta_acik = True
        if 'reaper_e_ek_iskelet' in etki:
            oyuncu.reaper_e_ek_iskelet_acik = True
        if 'reaper_atis_iskelet' in etki:
            oyuncu.reaper_atis_iskelet_acik = True
        if 'reaper_ulti_okcu' in etki:
            oyuncu.reaper_ulti_okcu_acik = True
        if 'overdrive_kanca_heal' in etki:
            oyuncu.overdrive_kanca_heal_acik = True
        if 'overdrive_ulti_olumsuz' in etki:
            oyuncu.overdrive_ulti_olumsuz_acik = True
        if 'overdrive_hizli_ates' in etki:
            oyuncu.overdrive_hizli_ates_acik = True
        if 'ronin_menzil' in etki:
            oyuncu.ronin_menzil_carpan *= 1.5
        if 'ronin_gizli_sersem' in etki:
            oyuncu.ronin_gizli_sersem_acik = True
        if 'ronin_ulti_gelismis' in etki:
            oyuncu.ronin_ulti_gelismis_acik = True

# ── GENEL YÜKSELTMELER (kahramandan bağımsız, göreve bağlı) ──
# Puan biriktirip harcamak yerine: her görev kendi başına, tek seferlik,
# o göreve özel bir yükseltmeyi doğrudan kalıcı olarak açar.
TOPLAM_OLDURULEN = 0
EN_UZUN_HAYATTA_KALMA = 0.0

# (id, isim, aciklama, kontrol_fn, etki)
GENEL_GOREVLER = [
    ('ilk_zafer', "ILK ZAFER", "Bir bolumu bitir", lambda: en_yuksek_bolum >= 2, {'can': 15}),
    ('avci', "AVCI", "Toplam 150 dusman oldur", lambda: TOPLAM_OLDURULEN >= 150, {'hiz': 0.08}),
    ('hayatta_kalan', "HAYATTA KALAN", "Survivor'da tek seferde 90 saniye hayatta kal", lambda: EN_UZUN_HAYATTA_KALMA >= 90, {'regen': 2.0}),
    ('kahraman', "KAHRAMAN", "Bolum 15'e ulas", lambda: en_yuksek_bolum >= 15, {'can': 25, 'hiz': 0.05}),
]

def genel_gorev_tamamlandi(gorev_id):
    for gid, _, _, kontrol_fn, _ in GENEL_GOREVLER:
        if gid == gorev_id:
            return kontrol_fn()
    return False

def genel_yukseltme_uygula(oyuncu):
    for gid, _, _, kontrol_fn, etki in GENEL_GOREVLER:
        if not kontrol_fn():
            continue
        if 'can' in etki:
            oyuncu.max_can += etki['can']
            oyuncu.can += etki['can']
        if 'hiz' in etki:
            oyuncu.survivor_hiz_carpan *= (1 + etki['hiz'])
        if 'regen' in etki:
            oyuncu.survivor_can_yenileme += etki['regen'] / 60.0

kayit_yukle()
for _hid in KAHRAMAN_HASAR:
    KAHRAMAN_SON_KADEME[_hid] = ustalik_kademesi(_hid)  # önceki ilerleme için bildirim atma
atexit.register(kayit_kaydet)

# ══════════════════════════════════════════
#  BÖLÜM AYARLARI
# ══════════════════════════════════════════
def bolum_ayar(bolum):
    t = bolum - 1
    if TEST_MODU:
        if bolum <= 4:
            return {'melee':2,'ranged':2,'drone':2,'sniper':2,'shield':2,'tank':2,
                    'suicide':2,'gorunmez':2,'hayalet':2,'mizrakli':1,'boss':False,'final':False}
        elif bolum == 5:
            return {'melee':0,'ranged':0,'drone':0,'sniper':0,'shield':0,'tank':0,
                    'suicide':0,'gorunmez':0,'hayalet':0,'mizrakli':0,'boss':False,'final':True}
    if bolum <= 3:
        return {'melee':8,'ranged':2,'drone':0,'sniper':0,'shield':0,'tank':0,
                'suicide':1 if bolum>=3 else 0,'gorunmez':0,'hayalet':0,'mizrakli':0,'boss':False,'final':False}
    elif bolum <= 6:
        return {'melee':5,'ranged':3,'drone':2,'sniper':1 if bolum>=5 else 0,'shield':0,'tank':0,
                'suicide':2,'gorunmez':0,'hayalet':0,'mizrakli':1,'boss':bolum%5==0,'final':False}
    elif bolum <= 10:
        return {'melee':3,'ranged':4,'drone':2,'sniper':2,'shield':2 if bolum>=8 else 0,'tank':0,
                'suicide':2,'gorunmez':1 if bolum>=7 else 0,'hayalet':0,'mizrakli':1,'boss':bolum%5==0,'final':False}
    elif bolum <= 15:
        return {'melee':2,'ranged':3,'drone':2,'sniper':2,'shield':2,'tank':1 if bolum>=12 else 0,
                'suicide':3,'gorunmez':2,'hayalet':1 if bolum>=13 else 0,'mizrakli':2,'boss':bolum%5==0,'final':False}
    elif bolum <= 20:
        return {'melee':2,'ranged':3,'drone':2,'sniper':2,'shield':2,'tank':2,
                'suicide':3,'gorunmez':2,'hayalet':2,'mizrakli':2,'boss':bolum%5==0,'final':False}
    elif bolum < 30:
        return {'melee':1,'ranged':3,'drone':2,'sniper':3,'shield':2,'tank':3,
                'suicide':4,'gorunmez':3,'hayalet':3,'mizrakli':2,'boss':bolum%5==0,'final':False}
    else:
        return {'melee':0,'ranged':0,'drone':0,'sniper':0,'shield':0,'tank':0,'mizrakli':0,'boss':False,'final':True}

# ══════════════════════════════════════════
#  OYUNCU
# ══════════════════════════════════════════
class Oyuncu:
    def __init__(self):
        self.x = 150.0
        self.y = float(ZEMIN_Y - 48)
        self.w = 28
        self.h = 48
        self.hiz_x = 0.0
        self.hiz_y = 0.0
        self.yerde = False
        self.can = 100
        self.max_can = 100
        self.anim_frame = 0
        self.anim_zamani = 0
        self.hasar_timer = 0
        self.silah_idx = 0
        self.sarjor = SILAHLAR[0]['sarjor']
        self.doluyor = False
        self.dolum_timer = 0
        self.atis_timer = 0

        self.kalkan_aktif = False
        self.kalkan_kapasite = 0
        self.kalkan_suresi = 0
        self.kalkan_bekleme = 0

        self.ulti_dolu = 0
        self.ulti_aktif = False
        self.ulti_suresi = 0

        self.kilic_durum = 'beklemede'  # beklemede | giden | sapli | donuyor
        self.kilic_x = 0.0
        self.kilic_y = 0.0
        self.kilic_hiz_x = 0.0
        self.kilic_hiz_y = 0.0
        self.kilic_mesafe = 0
        self.kilic_vurulanlar = []
        self.kilic_atma_bekleme = 0
        self.kilic_savurma_bekleme = 0
        self.kilic_savurma_goster = 0

        # AEGIS'e özel yükseltmeler (KAHRAMAN_YUKSELTMELERI[0], ustalik_uygula ile açılır)
        self.aegis_kilic_menzil_carpan = 1.0
        self.aegis_pasif_kalkan_acik = False
        self.aegis_pasif_kalkan = 0.0
        self.aegis_hasarsiz_kare = 0
        self.aegis_kilic_sekme_acik = False
        self.kilic_sekme_yapildi = False

        self.daima_ucar = False  # HEX seçiliyken kalıcı uçuş
        self.hex_kitap_sayisi = 0
        self.hex_kitap_timer = HEX_KITAP_SURESI
        self.hex_buyu_bekleme = 0
        self.hex_heal_aktif = False
        self.hex_heal_suresi = 0
        self.hex_heal_bekleme = 0
        self.hex_isin_bitis = (0.0, 0.0)
        self.hex_isin_goster = 0
        self.hex_isin_kitap_sayisi = 0
        # HEX'e özel yükseltmeler
        self.hex_kitap_max_ozel = HEX_KITAP_MAX
        self.hex_ulti_ekran_temizle_acik = False

        self.raptor_hizli = False  # RAPTOR seçiliyken yüksek temel hız
        self.raptor_zip_tutuluyor = False
        self.raptor_zip_kare = 0
        self.raptor_pence_bekleme = 0
        self.raptor_pence_goster = 0
        self.raptor_dash_aktif = False
        self.raptor_dash_suresi = 0
        self.raptor_dash_yon = 1
        self.raptor_dash_bekleme = 0
        self.raptor_dash_vurulanlar = []
        self.raptor_kacis_aktif = False
        self.raptor_kacis_suresi = 0
        self.raptor_kacis_bekleme = 0
        self.raptor_zehir_aktif = False
        self.raptor_zehir_suresi = 0
        self.raptor_ulti_aktif = False
        self.raptor_ulti_suresi = 0
        # RAPTOR'a özel yükseltmeler
        self.raptor_zehir_patlama_acik = False
        self.raptor_ofke_acik = False
        self.raptor_ofke_aktif = False
        self.raptor_ofke_suresi = 0
        self.raptor_dash_sinirsiz_acik = False

        self.wraith_yavas = False  # WRAITH seçiliyken yavaş temel hız
        self.wraith_ruh = 0
        self.wraith_ruh_bekleme = 0
        self.wraith_hayalet_aktif = False
        self.wraith_hayalet_suresi = 0
        self.wraith_heal_bekleme = 0
        self.wraith_ulti_aktif = False
        self.wraith_ulti_suresi = 0
        # WRAITH'e özel yükseltmeler
        self.wraith_hayalet_hasar_artis_acik = False
        self.wraith_ruh_heal_acik = False
        self.wraith_hayalet_usta_acik = False
        self.wraith_hayalet_bekleme = 0

        self.reaper_agir = False  # REAPER seçiliyken düşük temel hız
        self.reaper_ruh_bolme = 0
        self.reaper_vurus_bekleme = 0
        self.reaper_atis_bekleme = 0
        self.reaper_e_bekleme = 0
        self.reaper_vurus_goster = 0
        self.reaper_atis_goster = 0
        # REAPER'a özel yükseltmeler
        self.reaper_e_ek_iskelet_acik = False
        self.reaper_atis_iskelet_acik = False
        self.reaper_ulti_okcu_acik = False
        self.reaper_emici_acik = False    # HAYATTA KAL kartı: RUH EMİCİ

        self.survivor_hiz_carpan = 1.0    # HAYATTA KAL modu yükseltmesi (ana kampanyada nötr)
        self.survivor_can_yenileme = 0.0  # HAYATTA KAL modu yükseltmesi (ana kampanyada nötr)

        self.overdrive_sinirsiz_mermi = False
        self.overdrive_sallanma_acik = False
        self.kanca_durum = 'yok'   # yok | ucuyor | bagli
        self.kanca_x = 0.0
        self.kanca_y = 0.0
        self.kanca_bekleme = 0
        self.kanca_bagli_kare = 0
        self.kanca_ucus_hedef_x = 0.0
        self.kanca_ucus_hedef_y = 0.0
        self.kanca_ip_uzunlugu = 0.0
        self.kanca_aci = 0.0
        self.kanca_acisal_hiz = 0.0
        self.overdrive_e_bekleme = 0
        self.overdrive_e_goster = 0
        self.overdrive_ulti_aktif = False
        self.overdrive_ulti_suresi = 0
        # OVERDRIVE'a özel yükseltmeler
        self.overdrive_kanca_heal_acik = False
        self.overdrive_ulti_olumsuz_acik = False
        self.overdrive_olumsuzluk_kalan = 0     # ulti bitince de bir süre 1 canin altina dusmez
        self.overdrive_hizli_ates_acik = False

        self.ronin_itis_bekleme = 0
        self.ronin_itis_zirh = 0
        self.ronin_firlat_bekleme = 0
        self.ronin_itis_goster = 0
        self.ronin_firlat_goster = 0
        self.ronin_gizli_aktif = False
        self.ronin_gizli_suresi = 0
        self.ronin_e_bekleme = 0
        self.ronin_kritik_hazir = False
        self.ronin_ulti_aktif = False
        self.ronin_ulti_suresi = 0
        # RONIN'e özel yükseltmeler
        self.ronin_menzil_carpan = 1.0
        self.ronin_gizli_sersem_acik = False
        self.ronin_ulti_gelismis_acik = False

    def silah(self):
        return SILAHLAR[self.silah_idx]

    def kalkan_baslat(self):
        if self.kalkan_bekleme <= 0 and not self.kalkan_aktif:
            self.kalkan_aktif = True
            self.kalkan_kapasite = KALKAN_KAPASITE
            self.kalkan_suresi = KALKAN_SURESI

    def kalkan_kapat(self):
        self.kalkan_aktif = False
        self.kalkan_kapasite = 0
        self.kalkan_bekleme = KALKAN_BEKLEME

    def ulti_sarj_ekle(self, miktar=ULTI_SARJ_OLUM):
        self.ulti_dolu = min(ULTI_MAX, self.ulti_dolu + miktar)

    def ulti_kullan(self):
        if self.ulti_dolu >= ULTI_MAX and not self.ulti_aktif:
            self.ulti_aktif = True
            self.ulti_suresi = ULTI_SURESI
            self.ulti_dolu = 0
            self.can = min(self.max_can, self.can + ULTI_CAN_ARTISI)

    def kilic_el_konumu(self):
        return self.x + self.w/2, self.y + self.h*0.38

    def kilic_firlat(self, hedef_x, hedef_y):
        if self.kilic_durum != 'beklemede' or self.kilic_atma_bekleme > 0:
            return
        ex, ey = self.kilic_el_konumu()
        dx, dy = hedef_x - ex, hedef_y - ey
        uzunluk = math.hypot(dx, dy) or 1
        self.kilic_x, self.kilic_y = ex, ey
        self.kilic_hiz_x = dx/uzunluk * KILIC_HIZI
        self.kilic_hiz_y = dy/uzunluk * KILIC_HIZI
        self.kilic_mesafe = 0
        self.kilic_vurulanlar = []
        self.kilic_durum = 'giden'
        self.kilic_atma_bekleme = KILIC_ATMA_BEKLEME
        self.kilic_sekme_yapildi = False

    def kilic_geri_cagir(self):
        if self.kilic_durum in ('giden', 'sapli'):
            self.kilic_durum = 'donuyor'
            self.kilic_vurulanlar = []

    def kilic_savur_rect(self, fare_x, fare_y):
        ex, ey = self.kilic_el_konumu()
        dx, dy = fare_x - ex, fare_y - ey
        uzunluk = math.hypot(dx, dy) or 1
        mesafe = 30 * self.aegis_kilic_menzil_carpan
        boyut = 48 * self.aegis_kilic_menzil_carpan
        ox = ex + dx/uzunluk * mesafe
        oy = ey + dy/uzunluk * mesafe
        return pygame.Rect(int(ox-boyut/2), int(oy-boyut/2), int(boyut), int(boyut))

    def kilic_guncelle(self):
        if self.kilic_atma_bekleme > 0:
            self.kilic_atma_bekleme -= 1
        if self.kilic_savurma_bekleme > 0:
            self.kilic_savurma_bekleme -= 1
        if self.kilic_savurma_goster > 0:
            self.kilic_savurma_goster -= 1

        if self.kilic_durum == 'giden':
            self.kilic_x += self.kilic_hiz_x
            self.kilic_y += self.kilic_hiz_y
            self.kilic_mesafe += KILIC_HIZI
            if (self.kilic_mesafe >= KILIC_MENZIL or
                    self.kilic_x < 10 or self.kilic_x > GENISLIK - 10 or
                    self.kilic_y < 44 or self.kilic_y > ZEMIN_Y):
                self.kilic_x = max(10, min(GENISLIK - 10, self.kilic_x))
                self.kilic_y = max(44, min(ZEMIN_Y, self.kilic_y))
                self.kilic_durum = 'sapli'
        elif self.kilic_durum == 'donuyor':
            ex, ey = self.kilic_el_konumu()
            dx, dy = ex - self.kilic_x, ey - self.kilic_y
            uzunluk = math.hypot(dx, dy) or 1
            if uzunluk < 20:
                self.kilic_durum = 'beklemede'
            else:
                self.kilic_hiz_x = dx/uzunluk * KILIC_HIZI
                self.kilic_hiz_y = dy/uzunluk * KILIC_HIZI
                self.kilic_x += self.kilic_hiz_x
                self.kilic_y += self.kilic_hiz_y

    def kilic_rect(self):
        return pygame.Rect(self.kilic_x-8, self.kilic_y-8, 16, 16)

    def hex_heal_baslat(self):
        if self.hex_heal_bekleme <= 0 and not self.hex_heal_aktif:
            self.hex_heal_aktif = True
            self.hex_heal_suresi = HEX_HEAL_SURESI
            self.hex_heal_bekleme = HEX_HEAL_BEKLEME

    def hex_kitap_guncelle(self):
        if self.hex_kitap_sayisi < self.hex_kitap_max_ozel:
            self.hex_kitap_timer -= 1
            if self.hex_kitap_timer <= 0:
                self.hex_kitap_sayisi += 1
                self.hex_kitap_timer = HEX_KITAP_SURESI

        if self.hex_buyu_bekleme > 0:
            self.hex_buyu_bekleme -= 1

        if self.hex_heal_aktif:
            self.can = min(self.max_can, self.can + HEX_HEAL_TOPLAM / HEX_HEAL_SURESI)
            self.hex_heal_suresi -= 1
            if self.hex_heal_suresi <= 0:
                self.hex_heal_aktif = False
        elif self.hex_heal_bekleme > 0:
            self.hex_heal_bekleme -= 1

        if self.hex_isin_goster > 0:
            self.hex_isin_goster -= 1

    def raptor_kacis_baslat(self, yon):
        # E: sadece zehir moduna girer — kaçış/dash hareketi yok
        if self.raptor_kacis_bekleme <= 0 and not self.raptor_zehir_aktif:
            self.raptor_kacis_bekleme = RAPTOR_KACIS_BEKLEME
            self.raptor_zehir_aktif = True
            self.raptor_zehir_suresi = RAPTOR_ZEHIR_SURESI
            return True
        return False

    def raptor_guncelle(self):
        if self.raptor_pence_bekleme > 0:
            self.raptor_pence_bekleme -= 1
        if self.raptor_pence_goster > 0:
            self.raptor_pence_goster -= 1

        if self.raptor_dash_aktif:
            self.x += RAPTOR_DASH_HIZI * self.raptor_dash_yon
            self.raptor_dash_suresi -= 1
            if self.raptor_dash_suresi <= 0:
                self.raptor_dash_aktif = False
        elif self.raptor_dash_bekleme > 0:
            self.raptor_dash_bekleme -= 1

        if self.raptor_kacis_aktif:
            self.raptor_kacis_suresi -= 1
            if self.raptor_kacis_suresi <= 0:
                self.raptor_kacis_aktif = False
        elif self.raptor_kacis_bekleme > 0:
            self.raptor_kacis_bekleme -= 1

        if self.raptor_zehir_aktif:
            self.raptor_zehir_suresi -= 1
            if self.raptor_zehir_suresi <= 0:
                self.raptor_zehir_aktif = False

        if self.raptor_ofke_aktif:
            self.raptor_ofke_suresi -= 1
            if self.raptor_ofke_suresi <= 0:
                self.raptor_ofke_aktif = False

        if self.raptor_ulti_aktif:
            self.raptor_ulti_suresi -= 1
            if self.raptor_ulti_suresi <= 0:
                self.raptor_ulti_aktif = False

    def wraith_ruh_ekle(self, miktar):
        self.wraith_ruh = min(WRAITH_RUH_MAX, self.wraith_ruh + miktar)
        if self.wraith_ruh_heal_acik:
            self.can = min(self.max_can, self.can + miktar * WRAITH_RUH_OTO_HEAL_ORAN)

    def wraith_hayalet_baslat(self):
        if self.wraith_hayalet_usta_acik:
            if self.wraith_hayalet_bekleme <= 0 and not self.wraith_hayalet_aktif:
                self.wraith_hayalet_aktif = True
                self.wraith_hayalet_suresi = WRAITH_HAYALET_USTA_SURESI
            return
        if self.wraith_ruh >= WRAITH_HAYALET_MALIYET and not self.wraith_hayalet_aktif:
            self.wraith_ruh -= WRAITH_HAYALET_MALIYET
            self.wraith_hayalet_aktif = True
            self.wraith_hayalet_suresi = WRAITH_HAYALET_SURESI

    def wraith_heal_baslat(self):
        if self.wraith_heal_bekleme <= 0 and self.wraith_ruh > 0:
            self.can = min(self.max_can, self.can + self.wraith_ruh * WRAITH_HEAL_ORAN)
            self.wraith_ruh = 0
            self.wraith_heal_bekleme = WRAITH_HEAL_BEKLEME

    def wraith_guncelle(self):
        if self.wraith_ruh_bekleme > 0:
            self.wraith_ruh_bekleme -= 1
        if self.wraith_heal_bekleme > 0:
            self.wraith_heal_bekleme -= 1

        if self.wraith_hayalet_aktif:
            self.wraith_hayalet_suresi -= 1
            if self.wraith_hayalet_suresi <= 0:
                self.wraith_hayalet_aktif = False
                if self.wraith_hayalet_usta_acik:
                    self.wraith_hayalet_bekleme = WRAITH_HAYALET_USTA_BEKLEME
        elif self.wraith_hayalet_bekleme > 0:
            self.wraith_hayalet_bekleme -= 1

        if self.wraith_ulti_aktif:
            self.wraith_ulti_suresi -= 1
            if self.wraith_ulti_suresi <= 0:
                self.wraith_ulti_aktif = False

    def reaper_ruh_ekle(self):
        self.reaper_ruh_bolme = min(REAPER_RUH_BOLME_MAX, self.reaper_ruh_bolme + 1)

    def reaper_guncelle(self):
        if self.reaper_vurus_bekleme > 0:
            self.reaper_vurus_bekleme -= 1
        if self.reaper_atis_bekleme > 0:
            self.reaper_atis_bekleme -= 1
        if self.reaper_e_bekleme > 0:
            self.reaper_e_bekleme -= 1
        if self.reaper_vurus_goster > 0:
            self.reaper_vurus_goster -= 1
        if self.reaper_atis_goster > 0:
            self.reaper_atis_goster -= 1

    def overdrive_guncelle(self, tuslar=None):
        if self.kanca_bekleme > 0:
            self.kanca_bekleme -= 1
        if self.overdrive_e_bekleme > 0:
            self.overdrive_e_bekleme -= 1
        if self.overdrive_e_goster > 0:
            self.overdrive_e_goster -= 1
        if self.overdrive_ulti_aktif:
            self.overdrive_ulti_suresi -= 1
            if self.overdrive_ulti_suresi <= 0:
                self.overdrive_ulti_aktif = False
        if self.overdrive_olumsuzluk_kalan > 0:
            self.overdrive_olumsuzluk_kalan -= 1

        if self.kanca_durum == 'sallaniyor':
            # Gercek sarkac fizigi: ip boyu sabit, yercekimi acisal ivme verir —
            # eğik atinca gercekten yan yan sallaniyorsun, duz gitmiyorsun.
            yercekimi = 0.6 * (OVERDRIVE_ULTI_YAVAS_CARPAN if self.overdrive_ulti_aktif else 1.0)
            ivme = (yercekimi / max(30, self.kanca_ip_uzunlugu)) * math.cos(self.kanca_aci)
            self.kanca_acisal_hiz += ivme
            if tuslar is not None:
                # Sallanırken yön tuşuna basmak pompalama yapar: gittiğin yönde basarsan hızlanırsın,
                # ters yönde basarsan yavaşlarsın (salıncakta sallanmak gibi).
                yon_isaret = 1 if math.sin(self.kanca_aci) >= 0 else -1
                if tuslar[pygame.K_RIGHT] or tuslar[pygame.K_d]:
                    self.kanca_acisal_hiz -= OVERDRIVE_KANCA_POMPA * yon_isaret
                if tuslar[pygame.K_LEFT] or tuslar[pygame.K_a]:
                    self.kanca_acisal_hiz += OVERDRIVE_KANCA_POMPA * yon_isaret
            self.kanca_acisal_hiz *= 0.999
            self.kanca_aci += self.kanca_acisal_hiz
            onceki_x, onceki_y = self.x + self.w/2, self.y + self.h/2
            yeni_x = self.kanca_x + math.cos(self.kanca_aci) * self.kanca_ip_uzunlugu
            yeni_y = self.kanca_y + math.sin(self.kanca_aci) * self.kanca_ip_uzunlugu
            self.hiz_x = yeni_x - onceki_x
            self.hiz_y = yeni_y - onceki_y
            self.x = yeni_x - self.w/2
            self.y = yeni_y - self.h/2
            self.x = max(0, min(GENISLIK - self.w, self.x))
            self.y = max(46, min(ZEMIN_Y - self.h, self.y))   # HUD (0-42) altinda kalsin
        elif self.kanca_durum == 'ucuyor':
            # Salınım açık değilken: eskisi gibi hedefe sabit hızda uçarak gider, teleport degil
            hiz = OVERDRIVE_KANCA_UCUS_HIZI * (OVERDRIVE_ULTI_YAVAS_CARPAN if self.overdrive_ulti_aktif else 1.0)
            dx = self.kanca_ucus_hedef_x - self.x
            dy = self.kanca_ucus_hedef_y - self.y
            mesafe = math.hypot(dx, dy)
            if mesafe <= hiz:
                self.x, self.y = self.kanca_ucus_hedef_x, self.kanca_ucus_hedef_y
                self.hiz_x = 0
                self.hiz_y = 0
                self.kanca_durum = 'yok'
            else:
                ux, uy = dx / mesafe, dy / mesafe
                self.hiz_x = ux * hiz
                self.hiz_y = uy * hiz
                self.x += self.hiz_x
                self.y += self.hiz_y
            self.x = max(0, min(GENISLIK - self.w, self.x))
            self.y = max(46, min(ZEMIN_Y - self.h, self.y))

    def overdrive_sallan(self, hedef_x, hedef_y):
        # Sag tik birakilinca: sallaniyorsa o anki savrulma hiziyla devam eder,
        # ucuyorsa (salinim kapaliyken) yarim yolda oldugu yerde durup kancayi birakir
        if self.kanca_durum not in ('sallaniyor', 'ucuyor'):
            return
        self.kanca_durum = 'yok'

    def ronin_guncelle(self):
        if self.ronin_itis_bekleme > 0:
            self.ronin_itis_bekleme -= 1
        if self.ronin_itis_zirh > 0:
            self.ronin_itis_zirh -= 1
        if self.ronin_firlat_bekleme > 0:
            self.ronin_firlat_bekleme -= 1
        if self.ronin_itis_goster > 0:
            self.ronin_itis_goster -= 1
        if self.ronin_firlat_goster > 0:
            self.ronin_firlat_goster -= 1
        if self.ronin_e_bekleme > 0:
            self.ronin_e_bekleme -= 1
        if self.ronin_gizli_aktif:
            self.ronin_gizli_suresi -= 1
            if self.ronin_gizli_suresi <= 0:
                self.ronin_gizli_aktif = False
        if self.ronin_ulti_aktif:
            self.ronin_ulti_suresi -= 1
            if self.ronin_ulti_suresi <= 0:
                self.ronin_ulti_aktif = False

    def ronin_hasar_carpani(self):
        # Golge modundan vurunca artik gizlilik hemen kapanmiyor — suresi dolana kadar
        # vurmaya devam edebilir (golge ustaligiyla birden fazla dusmani dondurabilsin diye).
        if self.ronin_kritik_hazir:
            self.ronin_kritik_hazir = False
            return RONIN_E_KRITIK_CARPAN
        return 1.0

    def hasar_al(self, miktar):
        if self.ulti_aktif or self.raptor_kacis_aktif or self.wraith_hayalet_aktif:
            return 0  # jetpack ultisi / RAPTOR kaçışı / WRAITH hayalet: hasar işlemez
        self.aegis_hasarsiz_kare = 0  # hasar aldın — pasif kalkan biriktirme sayacı sıfırlanır
        if self.aegis_pasif_kalkan > 0:
            emilen_p = min(miktar, self.aegis_pasif_kalkan)
            self.aegis_pasif_kalkan -= emilen_p
            miktar -= emilen_p
            if miktar <= 0:
                return 0
        if self.wraith_ulti_aktif:
            azalan = miktar * WRAITH_ULTI_HASAR_CARPAN
            self.can -= azalan
            return azalan
        if self.ronin_itis_zirh > 0:
            azalan = miktar * 0.3   # mizrak hamlesi sirasinda %70 hasar azaltma
            self.can -= azalan
            return azalan
        if self.kalkan_aktif:
            emilen = min(miktar, self.kalkan_kapasite)
            self.kalkan_kapasite -= emilen
            kalan = miktar - emilen
            self.can -= kalan
            if self.kalkan_kapasite <= 0:
                self.kalkan_kapat()
            return kalan
        else:
            self.can -= miktar
            return miktar

    def hareket_et(self, tuslar, fare_pos):
        if self.raptor_hizli:
            hiz_taban = RAPTOR_HIZ_X
        elif self.wraith_yavas:
            hiz_taban = WRAITH_HIZ
        elif self.reaper_agir:
            hiz_taban = REAPER_HIZ
        else:
            hiz_taban = 5
        if self.raptor_ulti_aktif:
            hiz_taban *= RAPTOR_ULTI_HIZ_CARPAN
        elif self.raptor_ofke_aktif:
            hiz_taban *= RAPTOR_OFKE_HIZ_CARPAN
        if self.wraith_ulti_aktif:
            hiz_taban *= WRAITH_ULTI_YAVAS_CARPAN
        if self.overdrive_ulti_aktif:
            hiz_taban *= OVERDRIVE_ULTI_YAVAS_CARPAN
        hiz_taban *= self.survivor_hiz_carpan

        if self.raptor_kacis_aktif:
            pass  # hiz_x kaçış başlarken ayarlandı, süresi boyunca korunur
        else:
            self.hiz_x = 0
            if not self.raptor_dash_aktif:
                if tuslar[pygame.K_LEFT] or tuslar[pygame.K_a]:
                    self.hiz_x = -hiz_taban
                if tuslar[pygame.K_RIGHT] or tuslar[pygame.K_d]:
                    self.hiz_x = hiz_taban

        yukari_basili = tuslar[pygame.K_UP] or tuslar[pygame.K_w] or tuslar[pygame.K_SPACE]

        if self.ulti_aktif or self.daima_ucar:
            # Jetpack / kalıcı uçuş: serbest hareket
            ucus_hiz = WRAITH_UCUS_HIZ if self.wraith_yavas else 5
            if self.wraith_ulti_aktif:
                ucus_hiz *= WRAITH_ULTI_YAVAS_CARPAN
            if yukari_basili:
                self.hiz_y = -ucus_hiz
            elif tuslar[pygame.K_DOWN] or tuslar[pygame.K_s]:
                self.hiz_y = ucus_hiz
            else:
                self.hiz_y *= 0.85
            self.yerde = False
        elif self.raptor_hizli:
            # RAPTOR: 3 kademeli zıplama — kısa dokunuş kısa, basılı tutmak çok yüksek
            if yukari_basili and self.yerde:
                self.hiz_y = RAPTOR_ZIPLAMA_BASLANGIC
                self.yerde = False
                self.raptor_zip_tutuluyor = True
                self.raptor_zip_kare = 0
                snd_zipla()
            if self.raptor_zip_tutuluyor:
                if yukari_basili and self.raptor_zip_kare < RAPTOR_ZIPLAMA_MAX_KARE and self.hiz_y < 0:
                    self.hiz_y = max(RAPTOR_ZIPLAMA_MIN_HIZ, self.hiz_y + RAPTOR_ZIPLAMA_ITKI)
                    self.raptor_zip_kare += 1
                else:
                    self.raptor_zip_tutuluyor = False
            self.hiz_y += 0.6
        else:
            if yukari_basili and self.yerde:
                self.hiz_y = -14  # basılı tutulursa tam yükseklik
                self.yerde = False
                snd_zipla()
            if not yukari_basili and self.hiz_y < -5:
                self.hiz_y = -5  # tuş erken bırakılırsa zıplama kısa kesilir
            self.hiz_y += 0.6

        self.x += self.hiz_x
        self.y += self.hiz_y

        if self.ulti_aktif or self.daima_ucar:
            if self.y < 44:
                self.y = 44
                self.hiz_y = 0
            if self.y > ZEMIN_Y - self.h:
                self.y = ZEMIN_Y - self.h
                self.hiz_y = 0
        elif self.raptor_hizli and self.y < 44:
            self.y = 44
            self.hiz_y = 0
        elif self.y >= ZEMIN_Y - self.h:
            self.y = ZEMIN_Y - self.h
            self.hiz_y = 0
            self.yerde = True

        self.x = max(0, min(GENISLIK - self.w, self.x))

        self.anim_zamani += 1
        if self.anim_zamani >= 8:
            self.anim_zamani = 0
            self.anim_frame = (self.anim_frame + 1) % 4

        if self.hasar_timer > 0:
            self.hasar_timer -= 1
        if self.atis_timer > 0:
            self.atis_timer -= 1
        if self.survivor_can_yenileme > 0:
            self.can = min(self.max_can, self.can + self.survivor_can_yenileme)

        # AEGIS pasif kalkan: 5 saniye hasarsız kalınca biriken bir kalkan kazanılır,
        # hasar almaya devam etmedikçe bir sonraki 5 saniyede üstüne eklenir
        if self.aegis_pasif_kalkan_acik:
            self.aegis_hasarsiz_kare += 1
            if self.aegis_hasarsiz_kare >= AEGIS_PASIF_KALKAN_ARALIK:
                self.aegis_hasarsiz_kare = 0
                self.aegis_pasif_kalkan = min(AEGIS_PASIF_KALKAN_MAX,
                                               self.aegis_pasif_kalkan + AEGIS_PASIF_KALKAN_ARTIS)

        # Kalkan
        if self.kalkan_aktif:
            self.kalkan_suresi -= 1
            if self.kalkan_suresi <= 0:
                self.kalkan_kapat()
        elif self.kalkan_bekleme > 0:
            self.kalkan_bekleme -= 1

        # Ulti
        if self.ulti_aktif:
            self.ulti_suresi -= 1
            if self.ulti_suresi <= 0:
                self.ulti_aktif = False

        # Dolum
        if self.doluyor:
            self.dolum_timer -= 1
            if self.dolum_timer <= 0:
                self.doluyor = False
                self.sarjor = self.silah()['sarjor']
                snd_reload()

    def reload_baslat(self):
        s = self.silah()
        if not self.doluyor and self.sarjor < s['sarjor']:
            self.doluyor = True
            self.dolum_timer = s['dolum']

    def ates_et(self, fare_x, fare_y, mermi_listesi):
        s = self.silah()
        if self.atis_timer > 0 or self.doluyor:
            return
        if self.sarjor <= 0:
            self.reload_baslat()
            return
        self.atis_timer = max(1, s['atis_hizi'] // 2) if self.overdrive_hizli_ates_acik else s['atis_hizi']
        self.sarjor -= 1
        if self.overdrive_sinirsiz_mermi:
            self.sarjor = s['sarjor']   # OVERDRIVE: silah hic bitmez, doldurmaya gerek yok
        snd_overdrive_ates()

        cx = self.x + self.w / 2
        cy = self.y + self.h * 0.38
        sacma = s.get('sacma', 1)
        cift = s.get('cift', False)

        for _ in range(2 if cift else 1):
            for i in range(sacma):
                aci_offset = (i - (sacma-1)/2) * 0.25 if sacma > 1 else 0
                dx = fare_x - cx
                dy =fare_y - cy
                uzunluk = math.sqrt(dx*dx + dy*dy) or 1
                aci = math.atan2(dy, dx) + aci_offset
                hiz = s['mermi_hizi']
                m = Mermi(cx, cy, math.cos(aci)*hiz, math.sin(aci)*hiz,
                         s['renk'], s['hasar'], True)
                mermi_listesi.append(m)

    def ciz(self, ekran, fare_x, fare_y, aegis_modu=False, hex_modu=False, raptor_modu=False, wraith_modu=False, reaper_modu=False, overdrive_modu=False, ronin_modu=False):
        if self.hasar_timer > 0 and self.hasar_timer % 6 < 3:
            return

        # Gövde + yakın efektler ayrı bir kanvasa çizilir ki WRAITH hayalet
        # modundayken tüm görsel gerçekten saydamlaşabilsin (aura değil).
        pad = 50
        ox, oy = int(self.x) - pad, int(self.y) - pad
        aci = math.atan2(fare_y - (self.y + self.h*0.38), fare_x - (self.x + self.w/2))
        kanvas = pygame.Surface((self.w + pad*2, self.h + pad*2), pygame.SRCALPHA)
        px, py = pad, pad
        s = self.silah()
        vc = MOR if hex_modu else (YESIL if raptor_modu else ((150,230,220) if wraith_modu else ((255,70,60) if (reaper_modu and (self.reaper_vurus_goster>0 or self.reaper_atis_goster>0)) else ((200,25,20) if reaper_modu else s['renk']))))

        # WRAITH: kanatlar (gövdenin arkasında kalsın diye önce çizilir)
        if wraith_modu:
            sol_kanat = [(px, py+12), (px-24, py-2), (px-18, py+18), (px-20, py+34), (px, py+32)]
            sag_kanat = [(px+self.w, py+12), (px+self.w+24, py-2), (px+self.w+18, py+18), (px+self.w+20, py+34), (px+self.w, py+32)]
            pygame.draw.polygon(kanvas, (45,90,88), sol_kanat)
            pygame.draw.polygon(kanvas, (150,230,220), sol_kanat, 1)
            pygame.draw.polygon(kanvas, (45,90,88), sag_kanat)
            pygame.draw.polygon(kanvas, (150,230,220), sag_kanat, 1)

        # RAPTOR: kuyruk
        if raptor_modu:
            kuyruk_yon = 1 if self.hiz_x < 0 else -1
            for i in range(4):
                kx = px + self.w//2 + kuyruk_yon * (12 + i*9)
                ky = py + self.h - 8 + i*4
                b = 9 - i*2
                pygame.draw.rect(kanvas, (13,102,34), (kx-b//2, ky-b//2, b, b))

        lf = 5 if self.anim_frame % 2 == 0 else 0
        if aegis_modu:
            # AEGIS: onceki (klasik) gorunum
            pygame.draw.rect(kanvas, (13,46,136), (px+2, py+self.h-14, 10, 14+lf))
            pygame.draw.rect(kanvas, (13,46,136), (px+self.w-12, py+self.h-14, 10, 14-lf))
            pygame.draw.rect(kanvas, LACIVERT, (px, py+16, self.w, self.h-16))
            pygame.draw.rect(kanvas, (34,85,221), (px+2, py, self.w-4, 18))
            pygame.draw.rect(kanvas, vc, (px+4, py+5, self.w-8, 6))
            pygame.draw.rect(kanvas, (34,85,204), (px+6, py+20, self.w-12, 8))
            pygame.draw.rect(kanvas, (14,50,130), (px-7, py+14, 9, 13))
            pygame.draw.rect(kanvas, (14,50,130), (px+self.w-2, py+14, 9, 13))
            pygame.draw.rect(kanvas, CYAN, (px-7, py+14, 9, 13), 1)
            pygame.draw.rect(kanvas, CYAN, (px+self.w-2, py+14, 9, 13), 1)
        elif raptor_modu:
            # RAPTOR: dikensi ibikli kafa, egik/avci govde
            pygame.draw.rect(kanvas, (13,102,34), (px+2, py+self.h-14, 10, 14+lf))
            pygame.draw.rect(kanvas, (13,102,34), (px+self.w-12, py+self.h-14, 10, 14-lf))
            govde_r = [(px+3, py+16), (px+self.w-3, py+16), (px+self.w, py+self.h-2), (px, py+self.h-2)]
            pygame.draw.polygon(kanvas, (13,85,34), govde_r)
            pygame.draw.polygon(kanvas, (34,153,68), govde_r, 1)
            pygame.draw.polygon(kanvas, (34,136,51), [(px+2, py+16), (px+self.w-2, py+16), (px+self.w-3, py+4), (px+3, py+4)])
            for i in range(3):
                ix = px + 5 + i*7
                pygame.draw.polygon(kanvas, (20,90,30), [(ix, py+4), (ix+3, py-9-i%2*3), (ix+6, py+4)])
            pygame.draw.rect(kanvas, vc, (px+4, py+5, self.w-8, 5))
            pygame.draw.rect(kanvas, (34,153,68), (px+6, py+19, self.w-12, 7))
        elif hex_modu:
            # HEX: hilal boynuzlu kukuleta, dar buyucu govdesi
            pygame.draw.rect(kanvas, (68,13,136), (px+2, py+self.h-14, 10, 14+lf))
            pygame.draw.rect(kanvas, (68,13,136), (px+self.w-12, py+self.h-14, 10, 14-lf))
            govde_h = [(px+5, py+16), (px+self.w-5, py+16), (px+self.w-2, py+self.h-16), (px+2, py+self.h-16)]
            pygame.draw.polygon(kanvas, (58,0,102), govde_h)
            pygame.draw.polygon(kanvas, (150,80,220), govde_h, 1)
            kukuleta = [(px+1, py+3), (px+self.w-1, py+3), (px+self.w//2, py-13)]
            pygame.draw.polygon(kanvas, (30,0,55), kukuleta)
            pygame.draw.polygon(kanvas, (150,80,220), kukuleta, 1)
            pygame.draw.line(kanvas, (150,80,220), (px-6, py-2), (px+2, py+6), 2)
            pygame.draw.line(kanvas, (150,80,220), (px+self.w+6, py-2), (px+self.w-2, py+6), 2)
            pygame.draw.rect(kanvas, vc, (px+5, py+6, self.w-10, 5))
            pygame.draw.circle(kanvas, (220,150,255), (px+self.w//2, py+24), 4)
            cubbe = [(px-5, py+self.h), (px+self.w+5, py+self.h), (px+self.w//2, py+self.h-22)]
            pygame.draw.polygon(kanvas, (40,0,70), cubbe)
        elif wraith_modu:
            # WRAITH: sivri mizrak-uclu kafa, tek goz, dagilan/pacavra alt govde
            pygame.draw.polygon(kanvas, (40,80,78), [(px+2, py+self.h-14), (px+12, py+self.h-14), (px+9, py+self.h+lf), (px+1, py+self.h+lf-6)])
            pygame.draw.polygon(kanvas, (40,80,78), [(px+self.w-12, py+self.h-14), (px+self.w-2, py+self.h-14), (px+self.w-1, py+self.h-lf), (px+self.w-9, py+self.h-lf-6)])
            govde_w = [(px+3, py+18), (px+self.w-3, py+18), (px+self.w-6, py+self.h-8), (px+self.w//2, py+self.h), (px+6, py+self.h-8)]
            pygame.draw.polygon(kanvas, (25,60,58), govde_w)
            pygame.draw.polygon(kanvas, (150,230,220), govde_w, 1)
            kafa_w = [(px+self.w//2, py-16), (px+self.w-2, py+16), (px+self.w//2, py+22), (px+2, py+16)]
            pygame.draw.polygon(kanvas, (60,110,105), kafa_w)
            pygame.draw.polygon(kanvas, (150,230,220), kafa_w, 1)
            pygame.draw.circle(kanvas, (10,20,20), (px+self.w//2, py+8), 4)
            pygame.draw.circle(kanvas, vc, (px+self.w//2, py+8), 2)
        elif reaper_modu:
            # REAPER: kurukafa miğfer, agir zirh, kizil goz cukurlari
            pygame.draw.rect(kanvas, (14,10,11), (px+2, py+self.h-14, 10, 14+lf))
            pygame.draw.rect(kanvas, (14,10,11), (px+self.w-12, py+self.h-14, 10, 14-lf))
            pygame.draw.rect(kanvas, (16,11,12), (px-2, py+16, self.w+4, self.h-16))
            kafatasi = [(px+3, py+2), (px+self.w-3, py+2), (px+self.w-1, py+12), (px+self.w//2+3, py+20),
                        (px+self.w//2-3, py+20), (px+1, py+12)]
            pygame.draw.polygon(kanvas, (215,200,175), kafatasi)
            pygame.draw.polygon(kanvas, (140,130,110), kafatasi, 1)
            goz_renk_r = (255,60,50) if (self.reaper_vurus_goster>0 or self.reaper_atis_goster>0) else (200,25,20)
            pygame.draw.rect(kanvas, (10,8,8), (px+5, py+6, 6, 7))
            pygame.draw.rect(kanvas, (10,8,8), (px+self.w-11, py+6, 6, 7))
            pygame.draw.rect(kanvas, goz_renk_r, (px+6, py+7, 4, 5))
            pygame.draw.rect(kanvas, goz_renk_r, (px+self.w-10, py+7, 4, 5))
            pygame.draw.rect(kanvas, (150,15,20), (px+self.w//2-5, py+24, 10, 8))
            pelerin = [(px-6, py+self.h-4), (px+self.w+6, py+self.h-4),
                       (px+self.w+2, py+self.h+16), (px+self.w*0.7, py+self.h+8),
                       (px+self.w*0.5, py+self.h+20), (px+self.w*0.3, py+self.h+8),
                       (px-2, py+self.h+16)]
            pygame.draw.polygon(kanvas, (18,10,10), pelerin)
            pygame.draw.polygon(kanvas, (110,20,22), pelerin, 1)
            pygame.draw.rect(kanvas, (25,20,20), (px-10, py+15, 12, 16))
            pygame.draw.rect(kanvas, (25,20,20), (px+self.w-2, py+15, 12, 16))
            pygame.draw.rect(kanvas, (150,20,20), (px-10, py+15, 12, 16), 1)
            pygame.draw.rect(kanvas, (150,20,20), (px+self.w-2, py+15, 12, 16), 1)
        elif ronin_modu:
            # RONIN: uc sivri tacli kask, hale halkasi, tek dikey mor vizor, parcalanan pelerin
            koyu_r = (18,15,25)
            mor_r = (170,120,255)
            goz_r = mor_r if not self.ronin_gizli_aktif else (90,60,140)
            pygame.draw.rect(kanvas, koyu_r, (px+2, py+self.h-14, 10, 14+lf))
            pygame.draw.rect(kanvas, koyu_r, (px+self.w-12, py+self.h-14, 10, 14-lf))
            govde_ro = [(px+3, py+16), (px+self.w-3, py+16), (px+self.w-1, py+self.h-6),
                        (px+self.w//2, py+self.h+2), (px+1, py+self.h-6)]
            pygame.draw.polygon(kanvas, (28,24,36), govde_ro)
            pygame.draw.polygon(kanvas, mor_r, govde_ro, 1)
            kask_r = [(px+3, py+10), (px+self.w-3, py+10), (px+self.w-2, py-2), (px+self.w//2, py+6), (px+2, py-2)]
            pygame.draw.polygon(kanvas, (14,12,20), kask_r)
            pygame.draw.polygon(kanvas, mor_r, kask_r, 1)
            for dx_spike in (-6, 0, 6):
                sx = px+self.w//2+dx_spike
                pygame.draw.polygon(kanvas, (10,8,15), [(sx-2, py-4), (sx, py-15-abs(dx_spike)), (sx+2, py-4)])
            pygame.draw.circle(kanvas, mor_r, (px+self.w//2, py-2), 11, 1)
            pygame.draw.line(kanvas, goz_r, (px+self.w//2, py-1), (px+self.w//2, py+8), 2)
            pelerin_r = [(px-2, py+18), (px-17, py+29), (px-11, py+self.h+8), (px-2, py+self.h-2)]
            pygame.draw.polygon(kanvas, (20,17,28), pelerin_r)
            pygame.draw.polygon(kanvas, mor_r, pelerin_r, 1)
        elif not overdrive_modu:
            # Genel/kilitli yer tutucu kahramanlar icin paylasilan govde
            bacak_renk = (13,46,136)
            pygame.draw.rect(kanvas, bacak_renk, (px+2, py+self.h-14, 10, 14+lf))
            pygame.draw.rect(kanvas, bacak_renk, (px+self.w-12, py+self.h-14, 10, 14-lf))
            pygame.draw.rect(kanvas, LACIVERT, (px, py+16, self.w, self.h-16))
            pygame.draw.rect(kanvas, (34,85,221), (px+2, py, self.w-4, 18))
            pygame.draw.rect(kanvas, vc, (px+4, py+5, self.w-8, 6))
            pygame.draw.rect(kanvas, (34,85,204), (px+6, py+20, self.w-12, 8))
        if overdrive_modu:
            # OVERDRIVE: paylaşılan bloktan tamamen ayrı, açılı/mekanik bir siluet
            # (X-7 referans görseline göre: elmas kask, dar bel, sivri omuz/bacaklar)
            koyu = (18,18,18)
            sari_ac = (255,215,60)
            sari_koyu = (150,120,0)
            goz_renk_o = (255,60,60) if self.overdrive_e_goster > 0 else (255,245,140)

            sol_bacak = [(px+3, py+self.h-24), (px+13, py+self.h-24), (px+11, py+self.h+lf-2), (px+2, py+self.h+lf-6)]
            sag_bacak = [(px+self.w-13, py+self.h-24), (px+self.w-3, py+self.h-24), (px+self.w-2, py+self.h-lf+2), (px+self.w-11, py+self.h-lf-2)]
            pygame.draw.polygon(kanvas, sari_koyu, sol_bacak)
            pygame.draw.polygon(kanvas, koyu, sol_bacak, 1)
            pygame.draw.polygon(kanvas, sari_koyu, sag_bacak)
            pygame.draw.polygon(kanvas, koyu, sag_bacak, 1)

            govde = [(px+4, py+16), (px+self.w-4, py+16), (px+self.w-2, py+self.h-22),
                     (px+self.w//2+4, py+self.h-16), (px+self.w//2-4, py+self.h-16), (px+2, py+self.h-22)]
            pygame.draw.polygon(kanvas, (140,110,0), govde)
            pygame.draw.polygon(kanvas, koyu, govde, 1)
            pygame.draw.rect(kanvas, sari_koyu, (px+self.w//2-6, py+24, 12, 10))

            kafa = [(px+self.w//2, py-12), (px+self.w-1, py+8), (px+self.w//2, py+18), (px+1, py+8)]
            pygame.draw.polygon(kanvas, sari_ac, kafa)
            pygame.draw.polygon(kanvas, koyu, kafa, 1)
            pygame.draw.circle(kanvas, koyu, (px+self.w//2, py+7), 4)
            pygame.draw.circle(kanvas, goz_renk_o, (px+self.w//2, py+7), 2)

            sol_omuz = [(px-3, py+13), (px-14, py+21), (px-3, py+30)]
            sag_omuz = [(px+self.w+3, py+13), (px+self.w+14, py+21), (px+self.w+3, py+30)]
            pygame.draw.polygon(kanvas, sari_koyu, sol_omuz)
            pygame.draw.polygon(kanvas, koyu, sol_omuz, 1)
            pygame.draw.polygon(kanvas, sari_koyu, sag_omuz)
            pygame.draw.polygon(kanvas, koyu, sag_omuz, 1)

            pygame.draw.polygon(kanvas, (90,70,0), [(px-2, py+self.h-8), (px-10, py+self.h+3), (px-2, py+self.h-1)])
            pygame.draw.polygon(kanvas, (90,70,0), [(px+self.w+2, py+self.h-8), (px+self.w+10, py+self.h+3), (px+self.w+2, py+self.h-1)])

            namlu_x = px + self.w + 2
            pygame.draw.rect(kanvas, (30,30,30), (namlu_x, py+26, 14, 5))
            pygame.draw.rect(kanvas, sari_ac, (namlu_x, py+26, 14, 5), 1)

            if self.overdrive_olumsuzluk_kalan > 0:
                # Ustalık: ulti + 3 sn ölümsüzlük — nabız gibi parlayan beyaz/camgöbeği tint
                nabiz_o = 90 + int(60 * math.sin(pygame.time.get_ticks() / 60))
                olumsuz_yuzey = pygame.Surface((self.w+8, self.h+16), pygame.SRCALPHA)
                olumsuz_yuzey.fill((180, 255, 255, nabiz_o))
                kanvas.blit(olumsuz_yuzey, (px-4, py-12))

        # Silah açısı
        bx = px + self.w//2
        by = int(py + self.h*0.38)
        if wraith_modu:
            uc_x = bx + math.cos(aci) * 18
            uc_y = by + math.sin(aci) * 18
            pygame.draw.circle(kanvas, (150,230,220), (int(uc_x), int(uc_y)), 5)
            pygame.draw.circle(kanvas, (220,255,250), (int(uc_x), int(uc_y)), 5, 1)
        elif hex_modu:
            el_x = bx + math.cos(aci) * 20
            el_y = by + math.sin(aci) * 20
            pygame.draw.line(kanvas, (60,20,90), (bx, by), (int(el_x), int(el_y)), 4)
            for k in range(4):
                parmak_aci = aci + (k - 1.5) * 0.35
                fx = el_x + math.cos(parmak_aci) * 8
                fy = el_y + math.sin(parmak_aci) * 8
                pygame.draw.line(kanvas, (220,150,255), (int(el_x), int(el_y)), (int(fx), int(fy)), 2)
            pygame.draw.circle(kanvas, (150,80,220), (int(el_x), int(el_y)), 6)
            pygame.draw.circle(kanvas, (220,150,255), (int(el_x), int(el_y)), 6, 1)
        elif raptor_modu:
            savuruyor = self.raptor_pence_goster > 0
            uzunluk_p = 34 if savuruyor else 18
            renk_p = (255,255,255) if savuruyor else (150,255,170)
            for k in range(3):
                offset = (k - 1) * (0.5 if savuruyor else 0.3)
                ux = bx + math.cos(aci+offset) * uzunluk_p
                uy = by + math.sin(aci+offset) * uzunluk_p
                pygame.draw.line(kanvas, renk_p, (bx, by), (int(ux), int(uy)), 2)
        elif reaper_modu:
            gosteriliyor = self.reaper_vurus_goster > 0 or self.reaper_atis_goster > 0
            uc_x = bx + math.cos(aci) * 34
            uc_y = by + math.sin(aci) * 34
            pygame.draw.line(kanvas, (30,15,15), (bx, by), (int(uc_x), int(uc_y)), 4)
            kafatasi_renk = (255,70,60) if gosteriliyor else (75,25,25)
            pygame.draw.circle(kanvas, (18,12,12), (int(uc_x), int(uc_y)), 8)
            pygame.draw.circle(kanvas, kafatasi_renk, (int(uc_x), int(uc_y)), 8, 2)
            ex1 = uc_x + math.cos(aci+1.5708) * 3
            ey1 = uc_y + math.sin(aci+1.5708) * 3
            ex2 = uc_x + math.cos(aci-1.5708) * 3
            ey2 = uc_y + math.sin(aci-1.5708) * 3
            pygame.draw.circle(kanvas, (255,30,30), (int(ex1), int(ey1)), 2)
            pygame.draw.circle(kanvas, (255,30,30), (int(ex2), int(ey2)), 2)
        elif ronin_modu:
            uzun_r = 40 if (self.ronin_itis_goster > 0 or self.ronin_firlat_goster > 0) else 26
            uc_x = bx + math.cos(aci) * uzun_r
            uc_y = by + math.sin(aci) * uzun_r
            renk_mizrak = (230,230,240) if not self.ronin_gizli_aktif else (140,120,170)
            pygame.draw.line(kanvas, (40,35,50), (bx, by), (int(uc_x), int(uc_y)), 3)
            uc_poly = [(uc_x+math.cos(aci)*10, uc_y+math.sin(aci)*10),
                       (uc_x+math.cos(aci+2.5)*5, uc_y+math.sin(aci+2.5)*5),
                       (uc_x+math.cos(aci-2.5)*5, uc_y+math.sin(aci-2.5)*5)]
            pygame.draw.polygon(kanvas, renk_mizrak, uc_poly)
            pygame.draw.circle(kanvas, (170,120,255), (int(bx+math.cos(aci)*(uzun_r*0.6)), int(by+math.sin(aci)*(uzun_r*0.6))), 3, 1)
        elif aegis_modu:
            if self.kilic_durum == 'beklemede':
                if self.kilic_savurma_goster > 0:
                    ilerleme = 1 - (self.kilic_savurma_goster / 8)
                    salla_aci = aci - 0.9 + ilerleme * 1.8
                    uc_x = bx + math.cos(salla_aci) * 46
                    uc_y = by + math.sin(salla_aci) * 46
                    yay_rect = pygame.Rect(bx-46, by-46, 92, 92)
                    pygame.draw.arc(kanvas, (200,220,255), yay_rect, -aci-0.9, -aci+0.9, 2)
                    pygame.draw.line(kanvas, (255,255,255), (bx, by), (int(uc_x), int(uc_y)), 5)
                    pygame.draw.circle(kanvas, (120,120,130), (bx, by), 4)
                else:
                    uc_x = bx + math.cos(aci) * 30
                    uc_y = by + math.sin(aci) * 30
                    pygame.draw.line(kanvas, (200,220,255), (bx, by), (int(uc_x), int(uc_y)), 4)
                    pygame.draw.circle(kanvas, (120,120,130), (bx, by), 4)
        else:
            pygame.draw.rect(kanvas, vc, (bx, by-3, 24, 6))
            pygame.draw.rect(kanvas, (50,50,50), (bx+18, by-5, 8, 10))

        # HAYATTA KAL modu: kahraman gücüne bakmaksızın ortak kılıç-savurma
        # saldırısı için genel bir "dalga" (sallama yayı) efekti — AEGIS
        # dışındaki modlarda kendi silah dalları bu alanı çizmiyor.
        if not aegis_modu and self.kilic_savurma_goster > 0:
            ilerleme2 = 1 - (self.kilic_savurma_goster / 8)
            salla_aci2 = aci - 0.9 + ilerleme2 * 1.8
            uc_x2 = bx + math.cos(salla_aci2) * 46
            uc_y2 = by + math.sin(salla_aci2) * 46
            yay_rect2 = pygame.Rect(bx-46, by-46, 92, 92)
            pygame.draw.arc(kanvas, (255,255,255), yay_rect2, -aci-0.9, -aci+0.9, 2)
            pygame.draw.line(kanvas, (255,255,255), (bx, by), (int(uc_x2), int(uc_y2)), 4)

        # Kalkan
        if self.kalkan_aktif:
            zaman = pygame.time.get_ticks()
            nabiz = 4 + int(3 * math.sin(zaman / 100))
            cap = max(self.w, self.h) + 30 + nabiz
            merkez_x = px + self.w//2
            merkez_y = py + self.h//2
            kalkan_yuzey = pygame.Surface((cap, cap), pygame.SRCALPHA)
            pygame.draw.ellipse(kalkan_yuzey, (0,255,247,50), (0, 0, cap, cap))
            pygame.draw.ellipse(kalkan_yuzey, (0,255,247,170), (0, 0, cap, cap), 3)
            kanvas.blit(kalkan_yuzey, (merkez_x - cap//2, merkez_y - cap//2))

        # Ulti (jetpack + sınırsız can auraı)
        if self.ulti_aktif:
            zaman2 = pygame.time.get_ticks()
            nabiz2 = 4 + int(3 * math.sin(zaman2 / 90))
            cap2 = max(self.w, self.h) + 26 + nabiz2
            merkez_x2 = px + self.w//2
            merkez_y2 = py + self.h//2
            aura_yuzey = pygame.Surface((cap2, cap2), pygame.SRCALPHA)
            pygame.draw.ellipse(aura_yuzey, (255,215,0,45), (0, 0, cap2, cap2))
            pygame.draw.ellipse(aura_yuzey, (255,215,0,180), (0, 0, cap2, cap2), 3)
            kanvas.blit(aura_yuzey, (merkez_x2 - cap2//2, merkez_y2 - cap2//2))

            # Jetpack alevi (ayakların altında)
            alev_uzunluk = 10 + (zaman2 // 40) % 6
            pygame.draw.rect(kanvas, (255,238,0), (px+4, py+self.h, 6, alev_uzunluk))
            pygame.draw.rect(kanvas, TURUNCU, (px+self.w-10, py+self.h, 6, alev_uzunluk))
            pygame.draw.rect(kanvas, (255,238,0), (px+self.w-10, py+self.h, 6, alev_uzunluk-4))

        # HEX: etrafında dönen kitaplar
        if hex_modu and self.hex_kitap_sayisi > 0:
            zaman3 = pygame.time.get_ticks()
            merkez_x3, merkez_y3 = px + self.w//2, py + self.h//2
            for i in range(self.hex_kitap_sayisi):
                a = zaman3 / 300 + i * (2 * math.pi / self.hex_kitap_max_ozel)
                kx2 = merkez_x3 + math.cos(a) * 34
                ky2 = merkez_y3 + math.sin(a) * 34
                pygame.draw.rect(kanvas, (170,90,255), (int(kx2)-5, int(ky2)-6, 10, 12))
                pygame.draw.rect(kanvas, (230,200,255), (int(kx2)-5, int(ky2)-6, 10, 12), 1)

        # RAPTOR: hamle/kaçış izi + ulti aurası
        if raptor_modu and (self.raptor_dash_aktif or self.raptor_kacis_aktif):
            iz_renk = (255,255,255) if self.raptor_kacis_aktif else (150,255,170)
            iz_yon = self.raptor_dash_yon if self.raptor_dash_aktif else (1 if self.hiz_x >= 0 else -1)
            for k in range(1, 4):
                pygame.draw.rect(kanvas, iz_renk, (px - k*10*iz_yon, py+16, self.w, self.h-16), 1)

        if raptor_modu and self.raptor_ulti_aktif:
            zaman4 = pygame.time.get_ticks()
            nabiz4 = 3 + int(2 * math.sin(zaman4 / 80))
            cap4 = max(self.w, self.h) + 22 + nabiz4
            merkez_x4, merkez_y4 = px + self.w//2, py + self.h//2
            aura4 = pygame.Surface((cap4, cap4), pygame.SRCALPHA)
            pygame.draw.ellipse(aura4, (0,255,100,50), (0, 0, cap4, cap4))
            pygame.draw.ellipse(aura4, (0,255,100,180), (0, 0, cap4, cap4), 3)
            kanvas.blit(aura4, (merkez_x4 - cap4//2, merkez_y4 - cap4//2))

        # WRAITH: sadece ulti aurası (hayalet modunda aura yok, gövde saydamlaşır)
        if wraith_modu and self.wraith_ulti_aktif:
            zaman5 = pygame.time.get_ticks()
            nabiz5 = 4 + int(3 * math.sin(zaman5 / 100))
            cap5 = max(self.w, self.h) + 30 + nabiz5
            merkez_x5, merkez_y5 = px + self.w//2, py + self.h//2
            aura5 = pygame.Surface((cap5, cap5), pygame.SRCALPHA)
            pygame.draw.ellipse(aura5, (150,230,220,55), (0, 0, cap5, cap5))
            pygame.draw.ellipse(aura5, (220,255,250,180), (0, 0, cap5, cap5), 3)
            kanvas.blit(aura5, (merkez_x5 - cap5//2, merkez_y5 - cap5//2))

        alfa = 130 if (wraith_modu and self.wraith_hayalet_aktif) else (110 if (ronin_modu and self.ronin_gizli_aktif) else 255)
        kanvas.set_alpha(alfa)
        ekran.blit(kanvas, (ox, oy))

        if raptor_modu and self.raptor_zehir_aktif:
            zehir_yuzey = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            zehir_yuzey.fill((60, 220, 90, 90))
            ekran.blit(zehir_yuzey, (self.x, self.y))

        # Fırlatılan/dönen kılıç (dünya uzayında, kanvasın çok dışına çıkabilir)
        if aegis_modu and self.kilic_durum != 'beklemede':
            if self.kilic_hiz_x or self.kilic_hiz_y:
                aci_k = math.atan2(self.kilic_hiz_y, self.kilic_hiz_x)
            else:
                aci_k = 0
            kx, ky = self.kilic_x, self.kilic_y
            uc_x = kx + math.cos(aci_k) * 14
            uc_y = ky + math.sin(aci_k) * 14
            kuyruk_x = kx - math.cos(aci_k) * 14
            kuyruk_y = ky - math.sin(aci_k) * 14
            pygame.draw.line(ekran, (200,220,255), (kuyruk_x, kuyruk_y), (uc_x, uc_y), 4)
            pygame.draw.circle(ekran, CYAN, (int(kx), int(ky)), 3)

        # HEX: ışın (dünya uzayında, çok uzağa gidebilir)
        if hex_modu and self.hex_isin_goster > 0:
            ex, ey = self.kilic_el_konumu()
            kln_disi = 5 + self.hex_isin_kitap_sayisi * 3
            kln_ici = 2 + self.hex_isin_kitap_sayisi * 2
            pygame.draw.line(ekran, (220,150,255), (ex, ey), self.hex_isin_bitis, kln_disi)
            pygame.draw.line(ekran, (255,255,255), (ex, ey), self.hex_isin_bitis, kln_ici)

        # REAPER: yöne dönük saçılan, siyah-kızıl büyülü koni efektleri (dünya uzayında çizilir)
        if reaper_modu and (self.reaper_vurus_goster > 0 or self.reaper_atis_goster > 0):
            mx_r, my_r = self.x + self.w/2, self.y + self.h/2
            if self.reaper_vurus_goster > 0:
                r1 = max(4, int(REAPER_VURUS_MENZIL * (1 - self.reaper_vurus_goster/8)))
                yay1 = pygame.Rect(mx_r-r1, my_r-r1, r1*2, r1*2)
                pygame.draw.arc(ekran, (10,5,6), yay1, -aci-REAPER_VURUS_ACI, -aci+REAPER_VURUS_ACI, 6)
                pygame.draw.arc(ekran, (200,25,30), yay1, -aci-REAPER_VURUS_ACI, -aci+REAPER_VURUS_ACI, 2)
            if self.reaper_atis_goster > 0:
                r2 = max(4, int(REAPER_ATIS_MENZIL * (1 - self.reaper_atis_goster/8)))
                yay2 = pygame.Rect(mx_r-r2, my_r-r2, r2*2, r2*2)
                pygame.draw.arc(ekran, (8,4,5), yay2, -aci-REAPER_ATIS_ACI, -aci+REAPER_ATIS_ACI, 8)
                pygame.draw.arc(ekran, (255,35,35), yay2, -aci-REAPER_ATIS_ACI, -aci+REAPER_ATIS_ACI, 3)

        # OVERDRIVE: imleç ile karakter arasında noktalı nişan çizgisi (kanca menzilini gösterir)
        if overdrive_modu and self.kanca_durum == 'yok':
            mx_a, my_a = self.x + self.w/2, self.y + self.h/2
            dx_a, dy_a = fare_x - mx_a, fare_y - my_a
            uzunluk_a = math.hypot(dx_a, dy_a) or 1
            ux_a, uy_a = dx_a/uzunluk_a, dy_a/uzunluk_a
            nokta_renk = SARI if self.kanca_bekleme <= 0 else (120,120,120)
            mesafe_a = 16
            while mesafe_a < min(uzunluk_a, OVERDRIVE_KANCA_MENZIL):
                nx_a, ny_a = mx_a + ux_a*mesafe_a, my_a + uy_a*mesafe_a
                pygame.gfxdraw.filled_circle(ekran, int(nx_a), int(ny_a), 2, nokta_renk)
                mesafe_a += 11

        # OVERDRIVE: kanca teli (dünya uzayında) + E patlaması
        if overdrive_modu and self.kanca_durum in ('sallaniyor', 'ucuyor'):
            mx_o, my_o = self.x + self.w/2, self.y + self.h/2
            pygame.draw.line(ekran, (90,70,0), (mx_o, my_o), (self.kanca_x, self.kanca_y), 4)
            pygame.draw.line(ekran, SARI, (mx_o, my_o), (self.kanca_x, self.kanca_y), 2)
            pygame.draw.circle(ekran, SARI, (int(self.kanca_x), int(self.kanca_y)), 5)
            pygame.draw.circle(ekran, (120,90,0), (int(self.kanca_x), int(self.kanca_y)), 5, 1)
        if overdrive_modu and self.overdrive_e_goster > 0:
            mx_o, my_o = self.x + self.w/2, self.y + self.h/2
            r_e = max(4, int(OVERDRIVE_E_MENZIL * (1 - self.overdrive_e_goster/10)))
            pygame.draw.circle(ekran, SARI, (int(mx_o), int(my_o)), r_e, 2)

        # RONIN: 8 saniyelik donen mizrak firtinasi (ulti)
        if ronin_modu and self.ronin_ulti_aktif:
            ronin_ulti_r = RONIN_ULTI_YARICAP * (2.0 if self.ronin_ulti_gelismis_acik else 1.0)
            mx_r, my_r = self.x + self.w/2, self.y + self.h/2
            donus_acisi = (pygame.time.get_ticks() / 90) % (2*math.pi)
            for kol in range(3):
                a = donus_acisi + kol * (2*math.pi/3)
                ucx = mx_r + math.cos(a) * ronin_ulti_r
                ucy = my_r + math.sin(a) * ronin_ulti_r
                pygame.draw.line(ekran, (170,120,255), (mx_r, my_r), (ucx, ucy), 3)
                pygame.draw.circle(ekran, (230,220,255), (int(ucx), int(ucy)), 4)
            pygame.draw.circle(ekran, (170,120,255), (int(mx_r), int(my_r)), ronin_ulti_r, 1)

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


# ══════════════════════════════════════════
#  MERMİ
# ══════════════════════════════════════════
class Mermi:
    def __init__(self, x, y, hiz_x, hiz_y, renk, hasar, oyuncu_mermisi=True):
        self.x = float(x)
        self.y = float(y)
        self.hiz_x = hiz_x
        self.hiz_y = hiz_y
        self.renk = renk
        self.hasar = hasar
        self.oyuncu_mermisi = oyuncu_mermisi
        # Düşman mermileri ekranın öbür ucundaki oyuncuya bile ulaşabilsin diye
        # ömürleri çok uzun; oyuncu mermileri menzilli kalsın.
        self.omur = 80 if oyuncu_mermisi else 100000
        self.homing = False
        self.hedef_dusman = None

    def guncelle(self):
        if self.homing and self.hedef_dusman is not None and getattr(self.hedef_dusman, 'can', 0) > 0:
            hx = self.hedef_dusman.x + self.hedef_dusman.w/2
            hy = self.hedef_dusman.y + self.hedef_dusman.h/2
            dx, dy = hx - self.x, hy - self.y
            uzunluk = math.hypot(dx, dy) or 1
            hiz = math.hypot(self.hiz_x, self.hiz_y) or 5
            self.hiz_x += (dx/uzunluk*hiz - self.hiz_x) * 0.15
            self.hiz_y += (dy/uzunluk*hiz - self.hiz_y) * 0.15
        self.x += self.hiz_x
        self.y += self.hiz_y
        self.omur -= 1

    def ciz(self, ekran):
        if getattr(self, 'mizrak_mermisi', False):
            uzunluk = math.hypot(self.hiz_x, self.hiz_y) or 1
            ux, uy = self.hiz_x/uzunluk, self.hiz_y/uzunluk
            uzun = 15
            arka_x, arka_y = self.x-ux*uzun, self.y-uy*uzun
            ucx, ucy = self.x+ux*uzun, self.y+uy*uzun
            pygame.draw.line(ekran, (200,200,210), (arka_x, arka_y), (ucx, ucy), 3)
            uc = [(ucx+ux*8, ucy+uy*8), (ucx-uy*4, ucy+ux*4), (ucx+uy*4, ucy-ux*4)]
            pygame.draw.polygon(ekran, (230,230,235), uc)
        elif getattr(self, 'wraith_mermisi', False):
            x, y = int(self.x), int(self.y)
            pygame.gfxdraw.filled_circle(ekran, x, y, 9, (*self.renk, 70))
            pygame.gfxdraw.filled_circle(ekran, x, y, 5, (*self.renk, 200))
            pygame.gfxdraw.filled_circle(ekran, x, y, 2, (220, 240, 255, 255))
            pygame.gfxdraw.aacircle(ekran, x, y, 5, (200, 225, 255))
        else:
            pygame.draw.rect(ekran, self.renk, (int(self.x)-3, int(self.y)-3, 6, 6))

    def rect(self):
        return pygame.Rect(self.x-3, self.y-3, 6, 6)


# ══════════════════════════════════════════
#  DÜŞMANLAR
# ══════════════════════════════════════════
class Dusman:
    def __init__(self, x, tip, bolum):
        self.tip = tip
        self.x = float(x)
        self.hiz_x = 0.0
        self.hiz_y = 0.0
        self.yerde = False
        self.anim_frame = 0
        self.anim_zamani = 0
        self.atis_timer = 60 + random.randint(0, 40)
        self.stealth_timer = 0
        self.gorunur = True
        self.yavaslatildi = 0
        self.dondu_kare = 0     # >0 iken RONIN'in gölge modu ustalığıyla tamamen donmuş (hareket/saldırı yok)
        self.sinirsiz = False  # True ise ekran kenarına çarpıp geri sekmez (kaydırmalı kamera modları için)
        self.cekim_kare = 0    # >0 iken OVERDRIVE kancasıyla oyuncuya doğru çekiliyor
        self.cekim_hedef_x = 0.0
        self.cekim_hedef_y = 0.0
        self.zehir_kare = 0    # >0 iken RAPTOR zehiriyle zamanla hasar alır (yeşil tint)
        self.zehir_tik = 0

        hm = 1 + (bolum-1) * 0.11
        sm = 1 + (bolum-1) * 0.055
        mm = 1 + (bolum-1) * 0.17

        if tip == 'melee':
            self.w, self.h = 28, 48
            self.y = float(ZEMIN_Y - 48)
            self.can = int(22 * hm)
            self.hiz_x = (2.4 + bolum*0.14) * sm * (-1 if x > GENISLIK/2 else 1)
            self.para = int(60 * mm)
            self.atis_timer = 9999

        elif tip == 'ranged':
            self.w, self.h = 26, 44
            self.y = float(ZEMIN_Y - 44)
            self.can = int(15 * hm)
            self.hiz_x = (1.0 + bolum*0.07) * sm * (-1 if x > GENISLIK/2 else 1)
            self.para = int(80 * mm)

        elif tip == 'drone':
            self.w, self.h = 34, 24
            self.y = float(ZEMIN_Y - 170 - random.randint(0,60))
            self.can = int(12 * hm)
            self.hiz_x = (1.5 + bolum*0.11) * sm * (-1 if x > GENISLIK/2 else 1)
            self.para = int(100 * mm)

        elif tip == 'sniper':
            self.w, self.h = 22, 30
            self.y = float(ZEMIN_Y - 220 - random.randint(0,60))
            self.can = int(10 * hm)
            self.hiz_x = 0
            self.para = int(130 * mm)
            self.atis_timer = 40 + random.randint(0,20)

        elif tip == 'shield':
            self.w, self.h = 32, 50
            self.y = float(ZEMIN_Y - 50)
            self.can = int(40 * hm)
            self.hiz_x = (0.8 + bolum*0.06) * sm * (-1 if x > GENISLIK/2 else 1)
            self.para = int(120 * mm)
            self.atis_timer = 9999

        elif tip == 'tank':
            self.w, self.h = 52, 60
            self.y = float(ZEMIN_Y - 60)
            self.can = int(90 * hm)
            self.hiz_x = (0.6 + bolum*0.04) * sm * (-1 if x > GENISLIK/2 else 1)
            self.para = int(200 * mm)

        elif tip == 'suicide':
            self.w, self.h = 26, 40
            self.y = float(ZEMIN_Y - 40)
            self.can = int(18 * hm)
            self.taban_hiz = (3.6 + bolum*0.10) * sm
            self.para = int(90 * mm)
            self.atis_timer = 9999
            self.fitil = 0
            self.patlayacak = False

        elif tip == 'gorunmez':
            self.w, self.h = 28, 28
            self.y = float(ZEMIN_Y - 150 - random.randint(0,60))
            self.can = int(14 * hm)
            self.hiz_x = (1.3 + bolum*0.08) * sm * (-1 if x > GENISLIK/2 else 1)
            self.para = int(140 * mm)
            self.gizli = True
            self.faz_timer = random.randint(90, 150)
            self.atis_timer = 9999

        elif tip == 'hayalet':
            self.w, self.h = 30, 34
            self.y = float(ZEMIN_Y - 130 - random.randint(0,50))
            self.can = int(20 * hm)
            self.hiz_x = (1.1 + bolum*0.07) * sm * (-1 if x > GENISLIK/2 else 1)
            self.para = int(150 * mm)
            self.hayalet_mod = False
            self.faz_timer = random.randint(150, 220)
            self.hayalet_cooldown = 0

        elif tip == 'mizrakli':
            self.w, self.h = 30, 46
            self.y = float(ZEMIN_Y - 46)
            self.can = int(9 * hm)
            self.hiz_x = 0.0   # spawn sırasında dışarıdan grup yönü/hızı verilir
            self.para = int(45 * mm)
            self.atis_timer = 15
            self.hedef_havada = False
            self.mizrak_atildi = False

        elif tip == 'boss':
            self.w, self.h = 60, 80
            self.y = float(ZEMIN_Y - 80)
            self.can = int(200 * hm)
            self.hiz_x = (1.0 + bolum*0.05) * sm * (-1 if x > GENISLIK/2 else 1)
            self.para = int(500 * mm)
            self.atis_timer = 40

        elif tip == 'finalboss':
            self.w, self.h = 110, 160
            self.x = float(GENISLIK//2 - 55)
            self.y = float(ZEMIN_Y - 160)
            self.can = 1500
            self.hiz_x = 0.0
            self.para = 3000
            self.atis_timer = 40
            self.faz = 1
            self.sok_timer = 0
            self.boss_faz = 'saldiri'
            self.boss_faz_timer = 260
            self.kalkanli = True
            self.desen_idx = 0

        self.max_can = self.can

    # can bir property: azaldigi her an (nereden azaltildigina bakmaksizin,
    # kilic/pence/mermi/isin/iskelet vb.) aktif kahramanin ustalasma hasar
    # sayacina otomatik islenir — her vurus noktasina ayri ayri kod eklemeden.
    @property
    def can(self):
        return self._can

    @can.setter
    def can(self, deger):
        global TOPLAM_OLDURULEN
        onceki = getattr(self, '_can', deger)
        if deger < onceki:
            KAHRAMAN_HASAR[secili_kahraman] = KAHRAMAN_HASAR.get(secili_kahraman, 0.0) + (onceki - deger)
            ustalik_kademe_kontrol(secili_kahraman)
            if onceki > 0 and deger <= 0:
                TOPLAM_OLDURULEN += 1
                snd_dusman_olum(self.tip)
            elif deger > 0:
                snd_vurus()
        self._can = deger

    def guncelle(self, oyuncu_x, oyuncu_y, zaman):
        if self.dondu_kare > 0:
            self.dondu_kare -= 1
            return

        if self.cekim_kare > 0:
            self.cekim_kare -= 1
            self.x += (self.cekim_hedef_x - self.x) * 0.35
            self.y += (self.cekim_hedef_y - self.y) * 0.35
            self.anim_zamani += 1
            if self.atis_timer > 0:
                self.atis_timer -= 1
            return

        if self.yavaslatildi > 0:
            self.yavaslatildi -= 1
        yavas_carpan = HEX_ULTI_YAVAS_CARPAN if self.yavaslatildi > 0 else 1.0

        if self.zehir_kare > 0:
            self.zehir_kare -= 1
            self.zehir_tik -= 1
            if self.zehir_tik <= 0:
                self.zehir_tik = RAPTOR_ZEHIR_TIK
                if self.can > 0:
                    self.can -= RAPTOR_ZEHIR_HASAR

        # Hareket
        if self.tip in ['drone', 'sniper', 'gorunmez']:
            yon = 1 if oyuncu_x > self.x + self.w/2 else -1
            self.hiz_x = yon * abs(self.hiz_x)
            hiz_carpani = 2.0 if (self.tip == 'gorunmez' and self.gizli) else 1.0
            self.x += self.hiz_x * hiz_carpani * yavas_carpan
            self.y += math.sin(zaman / 400 + self.x * 0.01) * 1.2

        elif self.tip == 'hayalet':
            if self.hayalet_mod:
                kacis_yon = -1 if oyuncu_x > self.x + self.w/2 else 1
                self.hiz_x = kacis_yon * 2.4
            else:
                yon = 1 if oyuncu_x > self.x + self.w/2 else -1
                self.hiz_x = yon * abs(self.hiz_x)
            self.x += self.hiz_x * yavas_carpan
            self.y += math.sin(zaman / 400 + self.x * 0.01) * 1.2

        elif self.tip == 'suicide':
            yon = 1 if oyuncu_x > self.x + self.w/2 else -1
            self.hiz_x = yon * self.taban_hiz
            self.x += self.hiz_x * yavas_carpan
            self.hiz_y += 0.5
            self.y += self.hiz_y
            if self.y >= ZEMIN_Y - self.h:
                self.y = ZEMIN_Y - self.h
                self.hiz_y = 0
                self.yerde = True
            mesafe = math.hypot(oyuncu_x - (self.x + self.w/2), oyuncu_y - (self.y + self.h/2))
            if mesafe < PATLAMA_YARICAP + 15:
                self.fitil += 1
                if self.fitil >= FITIL_SURESI:
                    self.patlayacak = True
            else:
                self.fitil = 0

        elif self.tip == 'mizrakli':
            # Sabit yönde hızlı koşar, oyuncuyu takip etmez / durmaz — grup halinde geçer
            self.x += self.hiz_x * yavas_carpan
            self.hedef_havada = (ZEMIN_Y - oyuncu_y) > MIZRAKLI_HAVADA_ESIK

        elif self.tip == 'finalboss':
            self.boss_faz_timer -= 1
            if self.boss_faz_timer <= 0:
                if self.boss_faz == 'saldiri':
                    self.boss_faz = 'yorgun'
                    self.kalkanli = False
                    self.boss_faz_timer = 150
                    self.atis_timer = 9999
                else:
                    self.boss_faz = 'saldiri'
                    self.kalkanli = True
                    self.boss_faz_timer = 260
                    self.desen_idx = (self.desen_idx + 1) % 3
                    self.atis_timer = 30
            if self.can < self.max_can * 0.5 and self.faz == 1:
                self.faz = 2
            if self.can < self.max_can * 0.2 and self.faz == 2:
                self.faz = 3

        else:
            yon = 1 if oyuncu_x > self.x + self.w/2 else -1
            self.hiz_x = yon * abs(self.hiz_x)
            self.hiz_y += 0.4
            self.x += self.hiz_x * yavas_carpan
            self.y += self.hiz_y
            if self.y >= ZEMIN_Y - self.h:
                self.y = ZEMIN_Y - self.h
                self.hiz_y = 0
                self.yerde = True

        # Görünmez robotun gizlenme/belirme döngüsü
        if self.tip == 'gorunmez':
            self.faz_timer -= 1
            if self.faz_timer <= 0:
                self.gizli = not self.gizli
                if self.gizli:
                    self.faz_timer = random.randint(90, 150)
                    self.atis_timer = 9999
                else:
                    self.faz_timer = 55
                    self.atis_timer = 12

        # Hayaletin somutlaşma/hayalet olma döngüsü
        if self.tip == 'hayalet':
            if not self.hayalet_mod and self.hayalet_cooldown <= 0 and self.can < self.max_can * 0.4:
                # Canı azaldığında hemen hayalet moduna geçip iyileşsin (bekleme dolmuşsa)
                self.hayalet_mod = True
                self.can = min(self.max_can, self.can + self.can * 0.30)
                self.faz_timer = 80
            else:
                if not self.hayalet_mod and self.hayalet_cooldown > 0:
                    self.hayalet_cooldown -= 1
                self.faz_timer -= 1
                if self.faz_timer <= 0:
                    self.hayalet_mod = not self.hayalet_mod
                    if self.hayalet_mod:
                        self.can = min(self.max_can, self.can + self.can * 0.30)
                        self.faz_timer = 80
                    else:
                        self.faz_timer = random.randint(150, 220)
                        self.atis_timer = 20
                        self.hayalet_cooldown = 100

        # Sınır (kaydırmalı kamera modlarında düşmanlar ekran dışına çıkabilsin diye kapatılabilir)
        if not self.sinirsiz:
            if self.x < 10:
                self.x = 10
                self.hiz_x = abs(self.hiz_x)
            if self.x > GENISLIK - self.w - 10:
                self.x = GENISLIK - self.w - 10
                self.hiz_x = -abs(self.hiz_x)

        # Uçan/havada süzülen düşmanlar haritanın dışına (yukarı/aşağı) çıkmasın
        if self.tip in ['drone', 'sniper', 'gorunmez', 'hayalet']:
            if self.y < 44:
                self.y = 44
            if self.y > ZEMIN_Y - self.h:
                self.y = ZEMIN_Y - self.h

        # Animasyon
        self.anim_zamani += 1
        if self.anim_zamani >= 10:
            self.anim_zamani = 0
            self.anim_frame = (self.anim_frame + 1) % 2

        if self.atis_timer > 0:
            self.atis_timer -= 1

    def atis_yapabilir(self):
        if self.tip == 'mizrakli':
            ortada_mi = GENISLIK*0.2 < self.x < GENISLIK*0.8
            return self.hedef_havada and ortada_mi and not self.mizrak_atildi and self.atis_timer <= 0
        if self.tip in ['melee', 'shield', 'suicide']:
            return False
        if getattr(self, 'gizli', False) or getattr(self, 'hayalet_mod', False):
            return False
        return self.atis_timer <= 0

    def atis_sifirla(self):
        hizlar = {'ranged':70,'drone':65,'sniper':35,'tank':110,'boss':35,'finalboss':20,'gorunmez':55,'hayalet':65,'mizrakli':75}
        self.atis_timer = hizlar.get(self.tip, 60) + random.randint(0,20)

    def mermi_olustur(self, oyuncu_x, oyuncu_y):
        ex, ey = self.x + self.w/2, self.y + self.h/2
        dx = oyuncu_x - ex
        dy = oyuncu_y - ey
        uzunluk = math.sqrt(dx*dx + dy*dy) or 1
        aci = math.atan2(dy, dx)
        mermiler = []

        if self.tip == 'sniper':
            sp = 14
            for k in range(3):
                mermiler.append(Mermi(ex, ey,
                    math.cos(aci)*sp, math.sin(aci)*sp,
                    (255,0,0), 18, False))
        elif self.tip == 'mizrakli':
            self.mizrak_atildi = True
            sp = 12
            mz = Mermi(ex, ey, math.cos(aci)*sp, math.sin(aci)*sp, (200,200,80), 14, False)
            mz.mizrak_mermisi = True
            mermiler.append(mz)
        elif self.tip == 'tank':
            sp = 5
            mermiler.append(Mermi(ex, ey-10,
                dx/uzunluk*sp, dy/uzunluk*sp - 3,
                (255,136,0), 22, False))
        elif self.tip == 'boss':
            sp = 5
            for k in range(3):
                a = aci + (k-1)*0.28
                mermiler.append(Mermi(ex, ey,
                    math.cos(a)*sp, math.sin(a)*sp,
                    (255,68,0), 18, False))
        elif self.tip == 'finalboss':
            faz = getattr(self, 'faz', 1)
            desen = getattr(self, 'desen_idx', 0)
            sp = 4 + faz*1.5
            renk = (255,0,102)
            hasar = 20 + faz*5
            if desen == 0:
                # Yelpaze deseni
                n = 3 if faz==1 else (5 if faz==2 else 8)
                for k in range(n):
                    a = aci + (k-(n-1)/2)*(0.3 if faz==1 else 0.2)
                    mermiler.append(Mermi(ex, ey+self.h*0.3,
                        math.cos(a)*sp, math.sin(a)*sp, renk, hasar, False))
            elif desen == 1:
                # Duvar barajı
                n = 5 if faz>=2 else 4
                for k in range(n):
                    yofs = (k-(n-1)/2) * 22
                    mermiler.append(Mermi(ex, ey+self.h*0.3+yofs,
                        math.cos(aci)*sp*0.9, math.sin(aci)*sp*0.9,
                        renk, hasar, False))
            else:
                # Hedefli seri atış
                n = 2 if faz==1 else 3
                for k in range(n):
                    mermiler.append(Mermi(ex, ey+self.h*0.3,
                        dx/uzunluk*(sp+3), dy/uzunluk*(sp+3), renk, hasar+5, False))
        elif self.tip == 'gorunmez':
            sp = 4.5
            mermiler.append(Mermi(ex, ey,
                dx/uzunluk*sp, dy/uzunluk*sp,
                (180,0,255), 12, False))
        elif self.tip == 'hayalet':
            sp = 3.2
            mermiler.append(Mermi(ex, ey,
                dx/uzunluk*sp, dy/uzunluk*sp,
                (190,255,255), 9, False))
        else:
            sp = 3.5
            mermiler.append(Mermi(ex, ey,
                dx/uzunluk*sp, dy/uzunluk*sp,
                (255,51,102), 8, False))
        return mermiler

    def ciz(self, ekran, zaman):
        if self.tip == 'gorunmez' and self.gizli:
            return  # tamamen görünmez

        px, py = int(self.x), int(self.y)
        hp_oran = self.can / self.max_can

        if self.tip == 'finalboss':
            boss_bar_y = YUKSEKLIK - 40
            boss_bar_rect = pygame.Rect(10, boss_bar_y, GENISLIK-20, 14)
            bos_renk = (30,30,30)
            pygame.draw.rect(ekran, bos_renk, boss_bar_rect)
            renk = YESIL if hp_oran > 0.5 else (TURUNCU if hp_oran > 0.2 else KIRMIZI)
            pygame.draw.rect(ekran, renk, (10, boss_bar_y, int((GENISLIK-20)*hp_oran), 14))
            pygame.draw.rect(ekran, (255,0,102), boss_bar_rect, 2)
            can_sayisi_ciz(ekran, boss_bar_rect, self.can, self.max_can, renk, bos_renk, fnt_kk)
            isim = fnt_mini.render("OMEGA-9", True, BEYAZ)
            ekran.blit(isim, (14, boss_bar_y - 12))
        else:
            dusman_bar_rect = pygame.Rect(px, py-8, self.w, 4)
            bos_renk = (40,40,40)
            pygame.draw.rect(ekran, bos_renk, dusman_bar_rect)
            renk = YESIL if hp_oran > 0.5 else KIRMIZI
            pygame.draw.rect(ekran, renk, (px, py-8, int(self.w*hp_oran), 4))
            can_sayisi_ciz(ekran, dusman_bar_rect, self.can, self.max_can, renk, bos_renk, fnt_mini)

        if self.tip == 'melee':
            pygame.draw.rect(ekran, (204,34,51), (px+2, py, self.w-4, self.h))
            pygame.draw.rect(ekran, (238,51,68), (px+3, py+2, self.w-6, 16))
            pygame.draw.rect(ekran, SARI, (px+6, py+6, 4, 4))
            pygame.draw.rect(ekran, SARI, (px+self.w-10, py+6, 4, 4))
            lf = 4 if self.anim_frame == 0 else 0
            pygame.draw.rect(ekran, (136,17,34), (px+2, py+self.h-14, 10, 14+lf))
            pygame.draw.rect(ekran, (136,17,34), (px+self.w-12, py+self.h-14, 10, 14-lf))
            pygame.draw.rect(ekran, (200,200,200), (px-12, py+self.h//3, 12, 4))

        elif self.tip == 'ranged':
            pygame.draw.rect(ekran, (26,68,204), (px+2, py, self.w-4, self.h))
            pygame.draw.rect(ekran, (34,85,238), (px+3, py+2, self.w-6, 16))
            pygame.draw.rect(ekran, CYAN, (px+5, py+6, self.w-10, 4))
            lf = 4 if self.anim_frame == 0 else 0
            pygame.draw.rect(ekran, (13,46,136), (px+2, py+self.h-14, 10, 14+lf))
            pygame.draw.rect(ekran, (13,46,136), (px+self.w-12, py+self.h-14, 10, 14-lf))
            pygame.draw.rect(ekran, (68,170,255), (px+self.w, py+self.h//3, 10, 4))

        elif self.tip == 'drone':
            pygame.draw.polygon(ekran, (26,34,153), [
                (px+self.w//2, py), (px+self.w, py+self.h//2),
                (px+self.w//2, py+self.h), (px, py+self.h//2)])
            pygame.draw.rect(ekran, (68,102,255), (px-10, py+self.h//2-2, 10, 4))
            pygame.draw.rect(ekran, (68,102,255), (px+self.w, py+self.h//2-2, 10, 4))
            pygame.draw.rect(ekran, (255,34,68), (px+self.w//2-3, py+self.h//2-3, 6, 6))

        elif self.tip == 'sniper':
            pygame.draw.polygon(ekran, (68,0,0), [
                (px+self.w//2, py), (px+self.w, py+self.h//2),
                (px+self.w//2, py+self.h), (px, py+self.h//2)])
            pygame.draw.rect(ekran, (255,0,0), (px+self.w//2-3, py+self.h//2-3, 6, 6))

        elif self.tip == 'shield':
            pygame.draw.rect(ekran, (34,68,136), (px+2, py, self.w-4, self.h))
            pygame.draw.rect(ekran, (51,85,170), (px+3, py+2, self.w-6, 16))
            pygame.draw.rect(ekran, CYAN, (px+5, py+6, self.w-10, 4))
            yon = -1 if self.hiz_x < 0 else 1
            kx = px-10 if yon < 0 else px+self.w
            pygame.draw.rect(ekran, CYAN, (kx, py+4, 8, self.h-8))

        elif self.tip == 'tank':
            pygame.draw.rect(ekran, (85,68,0), (px, py+10, self.w, self.h-10))
            pygame.draw.rect(ekran, (136,119,34), (px+6, py, self.w-12, 24))
            pygame.draw.rect(ekran, (50,50,50), (px, py+self.h-10, self.w, 10))
            yon = 1 if self.hiz_x > 0 else -1
            top_x = px+self.w//2 if yon > 0 else px+self.w//2-22
            pygame.draw.rect(ekran, (170,170,170), (top_x, py+10, 22, 8))

        elif self.tip == 'suicide':
            fitil_aktif = self.fitil > 0
            yaniyor = fitil_aktif and (self.fitil // 3) % 2 == 0
            gov_renk = (255,255,0) if yaniyor else (204,68,0)
            pygame.draw.rect(ekran, gov_renk, (px+2, py, self.w-4, self.h))
            pygame.draw.rect(ekran, (255,136,0), (px+3, py+2, self.w-6, 14))
            pygame.draw.rect(ekran, KIRMIZI, (px+self.w//2-3, py+self.h//2-3, 6, 6))
            lf = 4 if self.anim_frame == 0 else 0
            pygame.draw.rect(ekran, (136,34,0), (px+2, py+self.h-12, 10, 12+lf))
            pygame.draw.rect(ekran, (136,34,0), (px+self.w-12, py+self.h-12, 10, 12-lf))
            if fitil_aktif:
                yaricap = int(PATLAMA_YARICAP * (self.fitil / FITIL_SURESI))
                pygame.draw.circle(ekran, KIRMIZI, (px+self.w//2, py+self.h//2), yaricap, 1)
                font2 = pygame.font.SysFont("couriernew", 8, bold=True)
                s2 = font2.render("!!!", True, KIRMIZI)
                ekran.blit(s2, (px+self.w//2 - s2.get_width()//2, py-16))

        elif self.tip == 'gorunmez':
            belirme = 1.0 - min(1.0, self.faz_timer / 55)
            pygame.draw.polygon(ekran, (120,0,200), [
                (px+self.w//2, py), (px+self.w, py+self.h//3),
                (px+self.w, py+self.h), (px, py+self.h),
                (px, py+self.h//3)])
            pygame.draw.rect(ekran, (200,120,255), (px+self.w//2-3, py+self.h//2-3, 6, 6))
            if belirme < 1.0:
                pygame.draw.rect(ekran, (200,120,255), (px-4, py-4, self.w+8, self.h+8), 1)

        elif self.tip == 'hayalet':
            renk = (190,255,255)
            if self.hayalet_mod:
                yuzey = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
                pygame.draw.rect(yuzey, (*renk, 110), (0, 0, self.w, self.h))
                pygame.draw.rect(yuzey, (*renk, 160), (0, 0, self.w, self.h), 1)
                ekran.blit(yuzey, (px, py))
            else:
                pygame.draw.rect(ekran, (60,140,140), (px+2, py, self.w-4, self.h))
                pygame.draw.rect(ekran, renk, (px+4, py+4, self.w-8, self.h-8), 1)
                pygame.draw.rect(ekran, renk, (px+self.w//2-3, py+6, 6, 6))

        elif self.tip == 'mizrakli':
            yon = 1 if self.hiz_x >= 0 else -1
            pygame.draw.rect(ekran, (90,95,105), (px+2, py, self.w-4, self.h))
            pygame.draw.rect(ekran, (130,135,145), (px+3, py+2, self.w-6, 14))
            goz_renk = (255,60,60) if getattr(self, 'hedef_havada', False) else (255,190,60)
            pygame.draw.rect(ekran, goz_renk, (px+self.w//2-3, py+6, 6, 6))
            lf = 5 if self.anim_frame == 0 else 0
            pygame.draw.rect(ekran, (60,64,72), (px+2, py+self.h-14, 9, 14+lf))
            pygame.draw.rect(ekran, (60,64,72), (px+self.w-11, py+self.h-14, 9, 14-lf))
            if not self.mizrak_atildi:
                mizrak_ucu_x = px + (self.w+26 if yon > 0 else -26)
                mizrak_y = py + self.h//2 - 6
                pygame.draw.line(ekran, (200,200,210), (px+self.w//2, mizrak_y), (mizrak_ucu_x, mizrak_y), 3)
                uc = [(mizrak_ucu_x, mizrak_y-5), (mizrak_ucu_x + 9*yon, mizrak_y), (mizrak_ucu_x, mizrak_y+5)]
                pygame.draw.polygon(ekran, (230,230,235), uc)

        elif self.tip == 'boss':
            pygame.draw.rect(ekran, (102,0,17), (px, py, self.w, self.h))
            pygame.draw.rect(ekran, (153,0,34), (px+4, py+4, self.w-8, 22))
            pygame.draw.rect(ekran, (255,0,0), (px+8, py+10, 8, 8))
            pygame.draw.rect(ekran, (255,0,0), (px+self.w-16, py+10, 8, 8))
            pygame.draw.rect(ekran, (204,0,0), (px+4, py+self.h-18, 12, 18))
            pygame.draw.rect(ekran, (204,0,0), (px+self.w-16, py+self.h-18, 12, 18))

        elif self.tip == 'finalboss':
            faz = getattr(self, 'faz', 1)
            kalkanli = getattr(self, 'kalkanli', True)
            boss_faz = getattr(self, 'boss_faz', 'saldiri')
            pc = (204,0,68) if faz==1 else ((255,0,102) if faz==2 else (255,0,0))
            flash = (zaman // 200) % 2 == 0

            # Arkadaki kontrol ekranı/panel
            panel_x, panel_y = px - 40, py - 30
            panel_w, panel_h = self.w + 80, self.h + 55
            pygame.draw.rect(ekran, (8,8,16), (panel_x, panel_y, panel_w, panel_h))
            pygame.draw.rect(ekran, (40,40,60), (panel_x, panel_y, panel_w, panel_h), 2)
            for gx in range(panel_x+16, panel_x+panel_w, 24):
                pygame.draw.line(ekran, (20,20,34), (gx, panel_y), (gx, panel_y+panel_h))
            for gy in range(panel_y+16, panel_y+panel_h, 24):
                pygame.draw.line(ekran, (20,20,34), (panel_x, gy), (panel_x+panel_w, gy))

            pygame.draw.rect(ekran, (26,0,17), (px+8, py, self.w-16, self.h))
            pygame.draw.rect(ekran, (68,0,34), (px+14, py+8, self.w-28, 50))
            core = pc if flash else (136,0,51)
            pygame.draw.rect(ekran, core, (px+self.w//2-10, py+30, 20, 20))
            pygame.draw.rect(ekran, (255,0,0), (px+self.w//2-18, py+14, 10, 10))
            pygame.draw.rect(ekran, (255,0,0), (px+self.w//2+8, py+14, 10, 10))
            pygame.draw.rect(ekran, (51,0,17), (px-16, py+18, 16, 10))
            pygame.draw.rect(ekran, (51,0,17), (px+self.w, py+18, 16, 10))
            pygame.draw.rect(ekran, (136,0,0), (px-22, py+20, 8, 6))
            pygame.draw.rect(ekran, (136,0,0), (px+self.w+14, py+20, 8, 6))
            pygame.draw.rect(ekran, (34,0,8), (px+10, py+self.h-30, 22, 30))
            pygame.draw.rect(ekran, (34,0,8), (px+self.w-32, py+self.h-30, 22, 30))

            if kalkanli:
                nabiz = 6 + int(4 * math.sin(zaman / 120))
                kalkan_yuzey = pygame.Surface((self.w+40, self.h+40), pygame.SRCALPHA)
                pygame.draw.ellipse(kalkan_yuzey, (0,255,247,55), (0, 0, self.w+40, self.h+40))
                pygame.draw.ellipse(kalkan_yuzey, (0,255,247,160), (0, 0, self.w+40, self.h+40), 3+nabiz//3)
                ekran.blit(kalkan_yuzey, (px-20, py-20))

            font2 = pygame.font.SysFont("couriernew", 9, bold=True)
            durum = "KALKANLI" if kalkanli else "ZAYIF - VUR!"
            durum_renk = CYAN if kalkanli else YESIL
            s2 = font2.render(f"OMEGA-9  FAZ {faz}  [{durum}]", True, pc if kalkanli else durum_renk)
            ekran.blit(s2, (px + self.w//2 - s2.get_width()//2, py-18))

        if self.zehir_kare > 0:
            # RAPTOR zehiri — düşman yeşilimsi bir tint ile kaplanır
            zehir_yuzey = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            zehir_yuzey.fill((60, 220, 90, 90))
            ekran.blit(zehir_yuzey, (px, py))

        if self.dondu_kare > 0:
            # RONIN golge ustaligi — dusman buz mavisi bir tint ile donar
            don_yuzey = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            don_yuzey.fill((150, 220, 255, 130))
            ekran.blit(don_yuzey, (px, py))

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


# ══════════════════════════════════════════
#  İSKELET (REAPER müttefiği)
# ══════════════════════════════════════════
class Iskelet:
    def __init__(self, x, y, guclu=False, okcu=False):
        self.x = float(x)
        self.y = float(y)
        self.w, self.h = 22, 34
        self.hiz_y = 0.0
        self.can = REAPER_ISKELET_CAN
        self.max_can = REAPER_ISKELET_CAN
        self.hasar = REAPER_ISKELET_HASAR
        self.hiz = REAPER_ISKELET_HIZ
        self.guclu = guclu           # True: ultiyle çağrıldı (su yeşili)
        self.okcu = okcu             # True: ulti ustalığı — mavi, uzaktan vurur
        self.guc_suresi = 0          # E ile geçici güçlenme
        self.atis_bekleme = 0
        self.ziplama_bekleme = 0
        self.yerde = False
        self.anim_zamani = 0
        self.anim_frame = 0

    def guncelle(self, dusman_listesi, aktif_platformlar=()):
        onceki_ayak_y = self.y + self.h
        self.hiz_y += 0.6
        self.y += self.hiz_y
        self.yerde = False
        if self.y >= ZEMIN_Y - self.h:
            self.y = ZEMIN_Y - self.h
            self.hiz_y = 0
            self.yerde = True
        elif self.hiz_y >= 0:
            yeni_ayak_y = self.y + self.h
            for p in aktif_platformlar:
                if self.x + self.w > p['x'] and self.x < p['x'] + p['w']:
                    if onceki_ayak_y <= p['y'] + 2 and yeni_ayak_y >= p['y']:
                        self.y = p['y'] - self.h
                        self.hiz_y = 0
                        self.yerde = True
                        break

        if self.guc_suresi > 0:
            self.guc_suresi -= 1
        if self.atis_bekleme > 0:
            self.atis_bekleme -= 1
        if self.ziplama_bekleme > 0:
            self.ziplama_bekleme -= 1

        hedef = None
        en_yakin = None
        merkez_x = self.x + self.w/2
        for d in dusman_listesi:
            if d.tip == 'hayalet' and d.hayalet_mod:
                continue
            mesafe = math.hypot((d.x + d.w/2) - merkez_x, (d.y + d.h/2) - (self.y + self.h/2))
            if en_yakin is None or mesafe < en_yakin:
                en_yakin = mesafe
                hedef = d

        if hedef is not None:
            hedef_merkez_x = hedef.x + hedef.w/2
            mesafe_x = abs(hedef_merkez_x - merkez_x)
            if mesafe_x > REAPER_ISKELET_MENZIL:
                yon = 1 if hedef_merkez_x > merkez_x else -1
                carpan = REAPER_GUC_CARPAN if self.guc_suresi > 0 else 1
                self.x += self.hiz * carpan * yon

            # Uçan düşman/platform: oyuncunun standart zıplama yüksekliğiyle ulaşmayı dener
            if self.yerde and self.ziplama_bekleme <= 0 and (hedef.y + hedef.h) < self.y - 20:
                self.hiz_y = -14
                self.yerde = False
                self.ziplama_bekleme = 40

        self.x = max(0, min(GENISLIK - self.w, self.x))

        self.anim_zamani += 1
        if self.anim_zamani >= 10:
            self.anim_zamani = 0
            self.anim_frame = (self.anim_frame + 1) % 2

    def guclendir(self):
        self.can = self.max_can
        self.guc_suresi = REAPER_GUC_SURESI

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def ciz(self, ekran):
        px, py = int(self.x), int(self.y)
        if self.guc_suresi > 0:
            # E ile guclendirilip "delirmis" hali — kapkara, gozleri kizil parlar
            renk = (10, 10, 12)
            bacak_renk = (5, 5, 6)
            goz_renk = (255, 40, 25)
            parlak = (255, 70, 40)
        elif self.okcu:
            renk = (40, 70, 160)
            bacak_renk = (25, 45, 110)
            goz_renk = (150, 210, 255)
            parlak = (70, 120, 220)
        elif self.guclu:
            renk = REAPER_ULTI_ISKELET_RENK
            bacak_renk = (65,18,22)
            goz_renk = (255,45,40)
            parlak = (110,25,28)
        else:
            renk = (225,220,205)
            bacak_renk = (120,115,105)
            goz_renk = (20,20,20)
            parlak = renk
        lf = 3 if self.anim_frame == 0 else 0
        pygame.draw.rect(ekran, bacak_renk, (px+3, py+self.h-10, 6, 10+lf))
        pygame.draw.rect(ekran, bacak_renk, (px+self.w-9, py+self.h-10, 6, 10-lf))
        pygame.draw.rect(ekran, renk, (px+4, py+10, self.w-8, self.h-20))
        pygame.draw.rect(ekran, parlak, (px+6, py, self.w-12, 12))
        pygame.draw.rect(ekran, goz_renk, (px+8, py+3, 3, 3))
        pygame.draw.rect(ekran, goz_renk, (px+self.w-11, py+3, 3, 3))
        if self.guclu:
            zaman = pygame.time.get_ticks()
            for k in range(3):
                a = zaman/220 + k*(2*math.pi/3)
                hx = px + self.w/2 + math.cos(a)*11
                hy = py + self.h/2 + math.sin(a)*15
                pygame.draw.circle(ekran, (210,25,30), (int(hx), int(hy)), 2)
        can_oran = self.can / self.max_can
        pygame.draw.rect(ekran, (30,30,30), (px, py-8, self.w, 4))
        pygame.draw.rect(ekran, YESIL if can_oran > 0.4 else KIRMIZI, (px, py-8, int(self.w*can_oran), 4))



# ══════════════════════════════════════════
#  XP (HAYATTA KAL modu)
# ══════════════════════════════════════════
class Xp:
    def __init__(self, x, y, deger=1):
        self.x = float(x)
        self.y = float(y)
        self.hiz_y = -3.5
        self.hiz_x = random.uniform(-1.5, 1.5)
        self.deger = deger
        self.omur = 260

    def guncelle(self):
        self.hiz_y += 0.4
        self.x += self.hiz_x
        self.y += self.hiz_y
        if self.y >= ZEMIN_Y - 8:
            self.y = ZEMIN_Y - 8
            self.hiz_y = 0
        self.omur -= 1

    def ciz(self, ekran):
        cx, cy = int(self.x), int(self.y)
        pygame.draw.polygon(ekran, (60,220,140), [(cx, cy-5), (cx+5, cy), (cx, cy+5), (cx-5, cy)])
        pygame.draw.polygon(ekran, (180,255,220), [(cx, cy-5), (cx+5, cy), (cx, cy+5), (cx-5, cy)], 1)

    def rect(self):
        return pygame.Rect(self.x-10, self.y-10, 20, 20)


# ══════════════════════════════════════════
#  CAN TOPU (HAYATTA KAL modu — bazı düşmanlardan düşer)
# ══════════════════════════════════════════
class CanTopu:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.hiz_y = -3.5
        self.hiz_x = random.uniform(-1.5, 1.5)
        self.omur = 320

    def guncelle(self):
        self.hiz_y += 0.4
        self.x += self.hiz_x
        self.y += self.hiz_y
        if self.y >= ZEMIN_Y - 8:
            self.y = ZEMIN_Y - 8
            self.hiz_y = 0
        self.omur -= 1

    def ciz(self, ekran):
        cx, cy = int(self.x), int(self.y)
        zaman = pygame.time.get_ticks()
        nabiz = 1 + int(1 * math.sin(zaman / 120))
        pygame.draw.circle(ekran, (120,10,20), (cx, cy), 8+nabiz)
        pygame.draw.circle(ekran, (255,60,90), (cx, cy), 7+nabiz)
        pygame.draw.rect(ekran, BEYAZ, (cx-1, cy-4, 2, 8))
        pygame.draw.rect(ekran, BEYAZ, (cx-4, cy-1, 8, 2))

    def rect(self):
        return pygame.Rect(self.x-11, self.y-11, 22, 22)


# ══════════════════════════════════════════
#  ENKAZ YAĞMURU
# ══════════════════════════════════════════
class Enkaz:
    def __init__(self, x, buyuk=False):
        self.x = float(x)
        self.y = 0.0
        self.hiz_y = 6.0 if not buyuk else 5.0
        self.buyuk = buyuk
        self.boyut = 34 if buyuk else 20
        self.hasar = 30 if buyuk else 18
        self.uyari_kare = 40
        self.dusuyor = False

    def guncelle(self):
        if not self.dusuyor:
            self.uyari_kare -= 1
            if self.uyari_kare <= 0:
                self.dusuyor = True
        else:
            self.y += self.hiz_y

    def bitti_mi(self):
        return self.dusuyor and self.y > ZEMIN_Y + 20

    def ciz(self, ekran):
        if not self.dusuyor:
            genislik = 6 if self.buyuk else 4
            if (self.uyari_kare // 4) % 2 == 0:
                pygame.draw.rect(ekran, KIRMIZI, (int(self.x)-genislik//2, 0, genislik, ZEMIN_Y), 0)
        else:
            s = self.boyut
            pygame.draw.rect(ekran, (90,60,50), (int(self.x)-s//2, int(self.y)-s*0.8, s, s*0.8))
            pygame.draw.rect(ekran, (140,90,70), (int(self.x)-s//2, int(self.y)-s*0.8, s, s*0.8), 1)

    def rect(self):
        s = self.boyut
        return pygame.Rect(self.x-s//2, self.y-s*0.8, s, s*0.8)


# ══════════════════════════════════════════
#  SOLUCAN (yerden çıkan, yönü kesen tuzak)
# ══════════════════════════════════════════
class Solucan:
    def __init__(self, x):
        self.x = float(x)
        self.w = 30
        self.yukseklik = 0.0
        self.faz = 'yukseliyor'   # yukseliyor -> tehlikeli -> iniyor -> bitti  |  can biterse -> oldu -> bitti
        self.tehlike_kare = SOLUCAN_TEHLIKE_SURESI
        self.hasar = SOLUCAN_HASAR
        self.can = SOLUCAN_CAN
        self.max_can = SOLUCAN_CAN
        self.para = 40
        self.anim = 0

    @property
    def can(self):
        return self._can

    @can.setter
    def can(self, deger):
        global TOPLAM_OLDURULEN
        onceki = getattr(self, '_can', deger)
        if deger < onceki:
            KAHRAMAN_HASAR[secili_kahraman] = KAHRAMAN_HASAR.get(secili_kahraman, 0.0) + (onceki - deger)
            ustalik_kademe_kontrol(secili_kahraman)
            if onceki > 0 and deger <= 0:
                TOPLAM_OLDURULEN += 1
            elif deger > 0:
                snd_vurus()
        self._can = deger

    def vurulabilir_mi(self):
        return self.faz in ('yukseliyor', 'tehlikeli', 'iniyor') and self.yukseklik > 10

    def guncelle(self):
        self.anim += 1
        if self.can <= 0 and self.faz not in ('oldu', 'bitti'):
            self.faz = 'oldu'
        if self.faz == 'yukseliyor':
            self.yukseklik += 14
            if self.yukseklik >= SOLUCAN_YUKSEKLIK:
                self.yukseklik = SOLUCAN_YUKSEKLIK
                self.faz = 'tehlikeli'
        elif self.faz == 'tehlikeli':
            self.tehlike_kare -= 1
            if self.tehlike_kare <= 0:
                self.faz = 'iniyor'
        elif self.faz == 'iniyor':
            self.yukseklik -= 14
            if self.yukseklik <= 0:
                self.yukseklik = 0
                self.faz = 'bitti'
        elif self.faz == 'oldu':
            self.yukseklik -= 20
            if self.yukseklik <= 0:
                self.yukseklik = 0
                self.faz = 'bitti'

    def bitti_mi(self):
        return self.faz == 'bitti'

    def tehlikeli_mi(self):
        return self.faz in ('yukseliyor', 'tehlikeli') and self.yukseklik > 14

    def rect(self):
        ust = ZEMIN_Y - self.yukseklik
        return pygame.Rect(int(self.x - self.w/2), int(ust), self.w, int(self.yukseklik) + 12)

    def ciz(self, ekran):
        segment = 20
        adet = max(1, int(self.yukseklik // segment) + 1)
        zaman = self.anim
        for i in range(adet):
            sy = ZEMIN_Y - i*segment
            koyu = i % 2 == 1
            genislik = self.w - (5 if koyu else 0)
            gov_renk = (55,60,68) if koyu else (95,100,110)
            pygame.draw.rect(ekran, gov_renk, (int(self.x-genislik/2), int(sy-segment), genislik, segment+4))
            pygame.draw.rect(ekran, (20,22,26), (int(self.x-genislik/2), int(sy-segment), genislik, segment+4), 1)
            # eklem bandı (metalik vida çizgisi)
            pygame.draw.line(ekran, (140,145,155), (int(self.x-genislik/2)+2, int(sy-2)), (int(self.x+genislik/2)-2, int(sy-2)), 1)
            # yanıp sönen sensör ışığı
            if (zaman // 6 + i) % 4 == 0:
                pygame.draw.circle(ekran, (255,60,60) if self.faz == 'tehlikeli' else (60,180,255),
                                    (int(self.x + (genislik/2 - 5) * (1 if i % 2 == 0 else -1)), int(sy-segment/2)), 2)

        if self.yukseklik > 10:
            bas_y = int(ZEMIN_Y - self.yukseklik)
            renk_goz = (255,30,30) if self.faz == 'tehlikeli' else (255,160,30)
            pygame.draw.rect(ekran, (40,42,48), (int(self.x-13), bas_y-14, 26, 18))
            pygame.draw.rect(ekran, (15,16,20), (int(self.x-13), bas_y-14, 26, 18), 1)
            pygame.draw.circle(ekran, renk_goz, (int(self.x), bas_y-6), 5)
            pygame.draw.circle(ekran, (255,255,255), (int(self.x), bas_y-6), 5, 1)
            # matkap ucu gibi sivri metal dişler
            for k in range(3):
                dx = -9 + k*9
                pygame.draw.polygon(ekran, (180,185,195), [
                    (self.x+dx, bas_y-4), (self.x+dx+5, bas_y-4), (self.x+dx+2.5, bas_y+6)])

            can_oran = max(0.0, self.can / self.max_can)
            bar_w = 60
            bar_h = 13
            bar_y = bas_y - 32
            bar_rect = pygame.Rect(int(self.x-bar_w/2), bar_y, bar_w, bar_h)
            pygame.draw.rect(ekran, (25,25,25), bar_rect)
            renk_can = YESIL if can_oran > 0.5 else (TURUNCU if can_oran > 0.25 else KIRMIZI)
            pygame.draw.rect(ekran, renk_can, (bar_rect.x, bar_rect.y, int(bar_w*can_oran), bar_h))
            pygame.draw.rect(ekran, (200,200,200), bar_rect, 1)
            can_sayisi_ciz(ekran, bar_rect, max(0, self.can), self.max_can, renk_can, (25,25,25), fnt_kk)


# ══════════════════════════════════════════
#  PARÇACIK
# ══════════════════════════════════════════
class Parca:
    def __init__(self, x, y, renk):
        self.x = float(x)
        self.y = float(y)
        self.hiz_x = random.uniform(-4, 4)
        self.hiz_y = random.uniform(-4, 4)
        self.renk = renk
        self.omur = random.randint(15, 28)
        self.boyut = random.randint(2, 5)

    def guncelle(self):
        self.x += self.hiz_x
        self.y += self.hiz_y
        self.hiz_y += 0.2
        self.omur -= 1

    def ciz(self, ekran):
        alfa = max(0, self.omur / 28)
        pygame.draw.rect(ekran, self.renk,
            (int(self.x)-self.boyut//2, int(self.y)-self.boyut//2,
             self.boyut, self.boyut))

def patlama(x, y, renk=(245,166,35), sayi=12):
    return [Parca(x, y, renk) for _ in range(sayi)]


# ══════════════════════════════════════════
#  HASAR YAZISI
# ══════════════════════════════════════════
class HasarYazisi:
    def __init__(self, x, y, deger, renk, yon_x=0.0, yon_y=-1.0, art=False):
        self.x = float(x)
        self.y = float(y)
        self.deger = int(deger)
        self.renk = renk
        self.art = art  # True: can kazanımı gibi "+" önekiyle gösterilir
        uzunluk = math.hypot(yon_x, yon_y) or 1
        self.hiz_x = (yon_x / uzunluk) * 1.6
        self.hiz_y = (yon_y / uzunluk) * 1.6 - 0.4
        self.omur = 34
        self.omur_max = 34

    def guncelle(self):
        self.x += self.hiz_x
        self.y += self.hiz_y
        self.hiz_x *= 0.96
        self.hiz_y *= 0.96
        self.omur -= 1

    def ciz(self, ekran):
        metin = f"+{self.deger}" if self.art else str(self.deger)
        font = fnt_or if self.deger > 50 else fnt_kk
        yuzey = font.render(metin, True, self.renk)
        alfa = max(0, min(255, int(255 * (self.omur / self.omur_max))))
        yuzey.set_alpha(alfa)
        ekran.blit(yuzey, (int(self.x), int(self.y)))


# ══════════════════════════════════════════
#  FON
# ══════════════════════════════════════════
random.seed(42)
binalar = [{'x': i*60-100, 'w': 30+random.randint(0,40),
            'h': 60+random.randint(0,220), 'layer': random.randint(0,1)}
           for i in range(40)]
yildizlar = [(random.randint(0, GENISLIK), random.randint(0, YUKSEKLIK-140),
              random.randint(1,2)) for _ in range(80)]

# Derin uzaydaki gezegen (720,95 r=70) ile harabedeki parçalanmış hali aynı
# gezegen — harabe, o gezegenin çöküşünden sonraki enkazı temsil ediyor.
GEZEGEN_MERKEZ_X, GEZEGEN_MERKEZ_Y, GEZEGEN_YARICAP = 720, 95, 70
_gezegen_parcalari = []
for _i in range(7):
    _a0 = (2*math.pi/7) * _i + random.uniform(-0.15, 0.15)
    _a1 = _a0 + (2*math.pi/7) * random.uniform(0.55, 0.8)
    _ic_r = GEZEGEN_YARICAP * random.uniform(0.15, 0.35)
    _dis_r = GEZEGEN_YARICAP * random.uniform(0.85, 1.05)
    _surukleme = random.uniform(12, 36)
    _orta_aci = (_a0 + _a1) / 2
    _pts = []
    for _t in (0.0, 0.5, 1.0):
        _aa = _a0 + (_a1 - _a0) * _t
        _pts.append((math.cos(_aa) * _dis_r, math.sin(_aa) * _dis_r))
    for _t in (1.0, 0.5, 0.0):
        _aa = _a0 + (_a1 - _a0) * _t
        _pts.append((math.cos(_aa) * _ic_r, math.sin(_aa) * _ic_r))
    _gezegen_parcalari.append({
        'pts': _pts,
        'dx': math.cos(_orta_aci) * _surukleme,
        'dy': math.sin(_orta_aci) * _surukleme,
    })
random.seed()

PLATFORM_SEHIR = [
    {'x': 120, 'y': 370, 'w': 150, 'h': 14},
    {'x': 420, 'y': 300, 'w': 150, 'h': 14},
    {'x': 650, 'y': 370, 'w': 150, 'h': 14},
]
PLATFORM_ISTASYON = [
    {'x': 120, 'baslangic_x': 120, 'y': 370, 'w': 140, 'h': 14, 'hiz': 1.2, 'sol': 80,  'sag': 280},
    {'x': 420, 'baslangic_x': 420, 'y': 300, 'w': 140, 'h': 14, 'hiz': -1.0, 'sol': 350, 'sag': 600},
    {'x': 650, 'baslangic_x': 650, 'y': 370, 'w': 140, 'h': 14, 'hiz': 1.4, 'sol': 600, 'sag': 830},
]

def platform_ciz(ekran, p, renk):
    pygame.draw.rect(ekran, renk, (p['x'], p['y'], p['w'], p['h']))
    pygame.draw.rect(ekran, CYAN, (p['x'], p['y'], p['w'], p['h']), 1)

def fon_ciz(ekran, kaydirma=0, bolum=1):
    if bolum <= 10:
        # Şehir
        bg, yildiz_renk = KOYU, (180,180,180)
        bina0, bina1_dolgu, bina1_kenar = (6,6,20), (10,10,30), (0,30,40)
        zemin_c, zemin_cizgi = ZEMIN_C, CYAN
    elif bolum <= 20:
        # Uzay İstasyonu
        bg, yildiz_renk = (8,4,20), (200,180,230)
        bina0, bina1_dolgu, bina1_kenar = (14,6,30), (22,10,45), (70,20,90)
        zemin_c, zemin_cizgi = (18,8,35), MOR
    else:
        # Harabe (OMEGA-9'a yaklaşım)
        bg, yildiz_renk = (20,4,4), (220,160,140)
        bina0, bina1_dolgu, bina1_kenar = (28,8,6), (45,14,10), (100,25,10)
        zemin_c, zemin_cizgi = (35,10,8), KIRMIZI

    harabe = bolum > 20

    def bina_ciz(dolgu, kenar, bx, top, w, h):
        if not harabe:
            pygame.draw.rect(ekran, dolgu, (bx, top, w, h))
            if kenar is not None:
                pygame.draw.rect(ekran, kenar, (bx, top, w, h), 1)
            return
        taban = YUKSEKLIK - 80
        kink1 = top + (w % 5) * 3 + 4
        kink2 = top + (h % 4) * 4 + 8
        yikik = [
            (bx, taban),
            (bx, kink1),
            (bx + w*0.4, top),
            (bx + w*0.7, kink2),
            (bx + w, top + (w % 3) * 5),
            (bx + w, taban),
        ]
        pygame.draw.polygon(ekran, dolgu, yikik)
        if kenar is not None:
            pygame.draw.polygon(ekran, kenar, yikik, 1)
        # Taban molozu
        pygame.draw.rect(ekran, dolgu, (bx-4, taban-6, w*0.35, 6))
        pygame.draw.rect(ekran, dolgu, (bx+w*0.5, taban-10, w*0.4, 10))

    ekran.fill(bg)
    for sx, sy, sr in yildizlar:
        pygame.draw.rect(ekran, yildiz_renk, (sx, sy, sr, sr))
    if 10 < bolum <= 20:
        pygame.draw.circle(ekran, (40,20,65), (GEZEGEN_MERKEZ_X, GEZEGEN_MERKEZ_Y), GEZEGEN_YARICAP)
        pygame.draw.circle(ekran, (70,35,100), (GEZEGEN_MERKEZ_X, GEZEGEN_MERKEZ_Y), GEZEGEN_YARICAP, 2)
    elif harabe:
        # Aynı gezegen — artık parçalanmış, harabelere düşen enkazı (kızıla dönmüş)
        for parca in _gezegen_parcalari:
            noktalar = [(GEZEGEN_MERKEZ_X + parca['dx'] + px, GEZEGEN_MERKEZ_Y + parca['dy'] + py)
                        for px, py in parca['pts']]
            pygame.draw.polygon(ekran, (60,14,10), noktalar)
            pygame.draw.polygon(ekran, (150,35,20), noktalar, 2)
    for b in binalar:
        if b['layer'] == 0:
            bx = int((b['x'] - kaydirma*0.2) % (GENISLIK+200)) - 100
            bina_ciz(bina0, None, bx, YUKSEKLIK-80-b['h'], b['w'], b['h'])
    for b in binalar:
        if b['layer'] == 1:
            bx = int((b['x'] - kaydirma*0.5) % (GENISLIK+200)) - 100
            bina_ciz(bina1_dolgu, bina1_kenar, bx, YUKSEKLIK-80-b['h'], b['w'], b['h'])
    pygame.draw.rect(ekran, zemin_c, (0, ZEMIN_Y, GENISLIK, 80))
    for x in range(0, GENISLIK, 6):
        pygame.draw.rect(ekran, zemin_cizgi, (x, ZEMIN_Y, 4, 2))


# ══════════════════════════════════════════
#  FONTLAR
# ══════════════════════════════════════════
fnt_kk = pygame.font.SysFont("couriernew", 13, bold=True)
fnt_or = pygame.font.SysFont("couriernew", 20, bold=True)
fnt_by = pygame.font.SysFont("couriernew", 32, bold=True)
fnt_mini = pygame.font.SysFont("couriernew", 9, bold=True)


# ══════════════════════════════════════════
#  BUTON
# ══════════════════════════════════════════
def nisangah_ciz(ekran, fare_x, fare_y):
    renk = NISANGAH_RENKLERI[AYAR_NISANGAH_RENK_IDX][1]
    sekil = NISANGAH_SEKILLERI[AYAR_NISANGAH_SEKIL_IDX]
    if sekil == 'daire':
        pygame.draw.circle(ekran, renk, (fare_x, fare_y), 10, 2)
        pygame.draw.circle(ekran, renk, (fare_x, fare_y), 2)
    elif sekil == 'nokta':
        pygame.draw.circle(ekran, renk, (fare_x, fare_y), 3)
    elif sekil == 'kare':
        pygame.draw.rect(ekran, renk, (fare_x-9, fare_y-9, 18, 18), 2)
        pygame.draw.rect(ekran, renk, (fare_x-1, fare_y-1, 2, 2))
    else:  # 'arti'
        pygame.draw.rect(ekran, renk, (fare_x-12, fare_y-1, 8, 2))
        pygame.draw.rect(ekran, renk, (fare_x+4,  fare_y-1, 8, 2))
        pygame.draw.rect(ekran, renk, (fare_x-1, fare_y-12, 2, 8))
        pygame.draw.rect(ekran, renk, (fare_x-1, fare_y+4,  2, 8))
        pygame.draw.rect(ekran, renk, (fare_x-4, fare_y-4, 8, 8), 1)


# ══════════════════════════════════════════
#  MOBİL / DOKUNMATİK KONTROLLER
# ══════════════════════════════════════════
class _SanalTuslar:
    # Gerçek klavye durumuyla sanal joystick yönünü birleştiren sarmalayıcı —
    # tuslar[pygame.K_x] okuyan tüm mevcut kod hiç değişmeden çalışır.
    def __init__(self, gercek, sol, sag, yukari, asagi):
        self.gercek = gercek
        self.sol, self.sag, self.yukari, self.asagi = sol, sag, yukari, asagi

    def __getitem__(self, tus):
        if tus in (pygame.K_LEFT, pygame.K_a):
            return self.gercek[tus] or self.sol
        if tus in (pygame.K_RIGHT, pygame.K_d):
            return self.gercek[tus] or self.sag
        if tus in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
            return self.gercek[tus] or self.yukari
        if tus in (pygame.K_DOWN, pygame.K_s):
            return self.gercek[tus] or self.asagi
        return self.gercek[tus]


class MobilKontrol:
    # Sol altta hareket için, sağ altta ATEŞ/nişan için — İKİ sanal joystick.
    # Sağdaki sürüklendiği yöne doğru sürekli ateş eder (twin-stick shooter gibi).
    # ÖZEL/E/Q ayrı küçük dokunmatik butonlar. Gerçek dokunmada (FINGER*) her
    # parmak ayrı takip edilir (joystick'i basılı tutarken başka butona da
    # basılabilir) — mouse ile tek imleçle de (sırayla) kullanılabilir.
    def __init__(self):
        self.joy_merkez = (AYAR_MOBIL_JOY_POS[0], AYAR_MOBIL_JOY_POS[1])
        self.joy_yaricap = 60
        self.joy_parmak_id = None
        self.joy_dx = 0.0
        self.joy_dy = 0.0

        self.ates_merkez = (AYAR_MOBIL_ATES_POS[0], AYAR_MOBIL_ATES_POS[1])
        self.ates_yaricap = 60
        self.ates_parmak_id = None
        self.ates_dx = 0.0
        self.ates_dy = 0.0
        self.ates_basili = False

        ax, ay = self.ates_merkez
        self.buton_ozel = pygame.Rect(int(ax-129), int(ay+3), 58, 58)
        self.buton_e = pygame.Rect(int(ax-129), int(ay-83), 50, 50)
        self.buton_q = pygame.Rect(int(ax-193), int(ay-45), 50, 50)
        self.aim_parmak_id = None
        self.aim_konum = None

    def _joy_icinde_mi(self, merkez, yaricap, x, y):
        return math.hypot(x-merkez[0], y-merkez[1]) <= yaricap*1.7

    def _joy_yon(self, merkez, yaricap, x, y):
        dx, dy = x-merkez[0], y-merkez[1]
        mesafe = math.hypot(dx, dy) or 1
        oran = min(1.0, mesafe/yaricap)
        return (dx/mesafe)*oran, (dy/mesafe)*oran

    def _mouse_hedef_mi(self, x, y):
        return (self._joy_icinde_mi(self.joy_merkez, self.joy_yaricap, x, y)
                or self._joy_icinde_mi(self.ates_merkez, self.ates_yaricap, x, y)
                or any(b.collidepoint(x, y) for b in (self.buton_ozel, self.buton_e, self.buton_q)))

    def _dokunma_basladi(self, pid, x, y):
        if self._joy_icinde_mi(self.joy_merkez, self.joy_yaricap, x, y):
            self.joy_parmak_id = pid
            self.joy_dx, self.joy_dy = self._joy_yon(self.joy_merkez, self.joy_yaricap, x, y)
            return
        if self.buton_ozel.collidepoint(x, y):
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=(x, y)))
            return
        if self.buton_e.collidepoint(x, y):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
            return
        if self.buton_q.collidepoint(x, y):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q))
            return
        if self._joy_icinde_mi(self.ates_merkez, self.ates_yaricap, x, y):
            self.ates_parmak_id = pid
            self.ates_basili = True
            self.ates_dx, self.ates_dy = self._joy_yon(self.ates_merkez, self.ates_yaricap, x, y)
            return
        # Oyun alanına dokunuş: nişan almak için o parmağı takip et
        if self.aim_parmak_id is None:
            self.aim_parmak_id = pid
        if pid == self.aim_parmak_id:
            self.aim_konum = (x, y)

    def _dokunma_tasindi(self, pid, x, y):
        if pid == self.joy_parmak_id:
            self.joy_dx, self.joy_dy = self._joy_yon(self.joy_merkez, self.joy_yaricap, x, y)
        elif pid == self.ates_parmak_id:
            self.ates_dx, self.ates_dy = self._joy_yon(self.ates_merkez, self.ates_yaricap, x, y)
        elif pid == self.aim_parmak_id:
            self.aim_konum = (x, y)

    def _dokunma_bitti(self, pid):
        if pid == self.joy_parmak_id:
            self.joy_parmak_id = None
            self.joy_dx = 0.0
            self.joy_dy = 0.0
        if pid == self.ates_parmak_id:
            self.ates_parmak_id = None
            self.ates_basili = False
            self.ates_dx = 0.0
            self.ates_dy = 0.0
        if pid == self.aim_parmak_id:
            self.aim_parmak_id = None

    def olay_isle(self, olay):
        # Gerçek dokunmatik ekran: FINGERDOWN/MOTION/UP (finger_id ile çoklu dokunuş)
        if olay.type == pygame.FINGERDOWN:
            self._dokunma_basladi(olay.finger_id, olay.x*GENISLIK, olay.y*YUKSEKLIK)
        elif olay.type == pygame.FINGERMOTION:
            self._dokunma_tasindi(olay.finger_id, olay.x*GENISLIK, olay.y*YUKSEKLIK)
        elif olay.type == pygame.FINGERUP:
            self._dokunma_bitti(olay.finger_id)
        # Fare (tek imleç) ile de kullanılabilsin diye aynı akışı mouse'a bağla
        elif olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1:
            mx, my = olay.pos
            if self._mouse_hedef_mi(mx, my):
                self._dokunma_basladi('mouse', mx, my)
        elif olay.type == pygame.MOUSEMOTION:
            if self.joy_parmak_id == 'mouse':
                self.joy_dx, self.joy_dy = self._joy_yon(self.joy_merkez, self.joy_yaricap, *olay.pos)
            elif self.ates_parmak_id == 'mouse':
                self.ates_dx, self.ates_dy = self._joy_yon(self.ates_merkez, self.ates_yaricap, *olay.pos)
        elif olay.type == pygame.MOUSEBUTTONUP and olay.button == 1:
            self._dokunma_bitti('mouse')

    def tuslar_sarmala(self, gercek_tuslar):
        sol = self.joy_dx < -0.35
        sag = self.joy_dx > 0.35
        yukari = self.joy_dy < -0.4
        asagi = self.joy_dy > 0.55
        return _SanalTuslar(gercek_tuslar, sol, sag, yukari, asagi)

    def nisan_konumu(self, varsayilan_x, varsayilan_y, oyuncu_cx=None, oyuncu_cy=None):
        if self.ates_parmak_id is not None and oyuncu_cx is not None:
            return (oyuncu_cx + self.ates_dx*400, oyuncu_cy + self.ates_dy*400)
        if self.aim_konum is not None:
            return self.aim_konum
        return (varsayilan_x, varsayilan_y)

    def ciz(self, ekran):
        for merkez, yaricap, dx, dy, renk in ((self.joy_merkez, self.joy_yaricap, self.joy_dx, self.joy_dy, CYAN),
                                               (self.ates_merkez, self.ates_yaricap, self.ates_dx, self.ates_dy, SARI)):
            halka = pygame.Surface((yaricap*2+8, yaricap*2+8), pygame.SRCALPHA)
            pygame.draw.circle(halka, (255,255,255,70), (yaricap+4, yaricap+4), yaricap, 3)
            ekran.blit(halka, (merkez[0]-yaricap-4, merkez[1]-yaricap-4))
            kx, ky = merkez[0] + dx*yaricap, merkez[1] + dy*yaricap
            pygame.draw.circle(ekran, renk, (int(kx), int(ky)), 24)
            koyu_renk = tuple(max(0, c-120) for c in renk)
            pygame.draw.circle(ekran, koyu_renk, (int(kx), int(ky)), 24, 2)

        for rect, etiket, renk in ((self.buton_ozel, "OZEL", TURUNCU),
                                    (self.buton_e, "E", (120,220,255)), (self.buton_q, "Q", (255,120,220))):
            buton_yuzey = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.ellipse(buton_yuzey, (20,20,30,140), (0, 0, rect.w, rect.h))
            ekran.blit(buton_yuzey, rect.topleft)
            pygame.draw.ellipse(ekran, renk, rect, 2)
            t = fnt_kk.render(etiket, True, renk)
            ekran.blit(t, (rect.centerx-t.get_width()//2, rect.centery-t.get_height()//2))


def buton_ciz(ekran, rect, etiket, fare_pos, font=None):
    f = font or fnt_or
    uzerinde = rect.collidepoint(fare_pos)
    if uzerinde:
        renk, cerceve, zemin = (0,255,200), (0,255,200), (20,45,40)
    else:
        renk, cerceve, zemin = TURUNCU, TURUNCU, (0,0,0)
    pygame.draw.rect(ekran, zemin, rect)
    pygame.draw.rect(ekran, cerceve, rect, 2)
    y = f.render(etiket, True, renk)
    ekran.blit(y, (rect.centerx - y.get_width()//2, rect.centery - y.get_height()//2))
    return uzerinde


# Menü alt-ekranlarında (BOLUMLER/KAHRAMANLAR/AYARLAR/KONTROLLER) tutarlı, dokunmatikte
# de kolay bulunan sabit bir sol-üst GERİ butonu — her ekran kendi olay döngüsünde bu
# rect'e tıklamayı ESC ile aynı şekilde işler.
GERI_BUTON_RECT = pygame.Rect(10, 10, 92, 32)

def geri_butonu_ciz(ekran, fare_pos):
    buton_ciz(ekran, GERI_BUTON_RECT, t('geri'), fare_pos, fnt_kk)


def can_sayisi_ciz(ekran, bar_rect, can, max_can, dolu_renk, bos_renk, font):
    oran = max(0, min(1, can / max_can)) if max_can else 0
    dolu_genislik = int(bar_rect.w * oran)
    metin = str(int(can))
    yazi_dolu_uzerinde = font.render(metin, True, bos_renk)
    yazi_bos_uzerinde = font.render(metin, True, dolu_renk)
    mx = bar_rect.centerx - yazi_dolu_uzerinde.get_width() // 2
    my = bar_rect.centery - yazi_dolu_uzerinde.get_height() // 2
    eski_clip = ekran.get_clip()
    ekran.set_clip(pygame.Rect(bar_rect.x, bar_rect.y, dolu_genislik, bar_rect.h))
    ekran.blit(yazi_dolu_uzerinde, (mx, my))
    ekran.set_clip(pygame.Rect(bar_rect.x + dolu_genislik, bar_rect.y, bar_rect.w - dolu_genislik, bar_rect.h))
    ekran.blit(yazi_bos_uzerinde, (mx, my))
    ekran.set_clip(eski_clip)


# ══════════════════════════════════════════
#  HUD
# ══════════════════════════════════════════
def basarim_bildirim_guncelle_ciz(ekran):
    # Bir ustalik yetenegi yeni acilinca ekranin sol altinda kisa bir bildirim gosterir
    global BASARIM_AKTIF
    if BASARIM_AKTIF is None and BASARIM_KUYRUGU:
        baslik, alt_yazi = BASARIM_KUYRUGU.pop(0)
        BASARIM_AKTIF = [baslik, alt_yazi, BASARIM_SURESI]
        snd_kahraman_acildi()
    if BASARIM_AKTIF is None:
        return
    BASARIM_AKTIF[2] -= 1
    baslik, alt_yazi, kalan = BASARIM_AKTIF
    if kalan <= 0:
        BASARIM_AKTIF = None
        return
    genislik_p, yukseklik_p = 300, 62
    kayma = 0
    if kalan > BASARIM_SURESI - 18:
        oran = (BASARIM_SURESI - kalan) / 18
        kayma = int((1-oran) * (genislik_p+24))
    elif kalan < 18:
        oran = kalan / 18
        kayma = int((1-oran) * (genislik_p+24))
    taban_x, taban_y = 16 - kayma, YUKSEKLIK - yukseklik_p - 16
    panel = pygame.Surface((genislik_p, yukseklik_p), pygame.SRCALPHA)
    panel.fill((10,10,18,225))
    ekran.blit(panel, (taban_x, taban_y))
    pygame.draw.rect(ekran, SARI, (taban_x, taban_y, genislik_p, yukseklik_p), 2)
    im_x, im_y = taban_x+30, taban_y+yukseklik_p//2
    pygame.draw.circle(ekran, SARI, (im_x, im_y), 17)
    pygame.draw.circle(ekran, (130,95,0), (im_x, im_y), 17, 2)
    for kk in range(5):
        aci_y = -math.pi/2 + kk*(2*math.pi/5)
        px = im_x + math.cos(aci_y)*8
        py = im_y + math.sin(aci_y)*8
        pygame.draw.circle(ekran, (60,40,0), (int(px), int(py)), 2)
    t1 = fnt_kk.render(alt_yazi, True, SARI)
    ekran.blit(t1, (taban_x+58, taban_y+12))
    t2 = fnt_kk.render(baslik, True, BEYAZ)
    ekran.blit(t2, (taban_x+58, taban_y+32))


def hud_ciz(ekran, oyuncu, skor, para, bolum, dusmanlar_kaldi, aegis_modu=False, hex_modu=False, raptor_modu=False, wraith_modu=False, reaper_modu=False, overdrive_modu=False, ronin_modu=False):
    pygame.draw.rect(ekran, SIYAH, (0, 0, GENISLIK, 42))
    pygame.draw.rect(ekran, CYAN, (0, 0, GENISLIK, 42), 2)

    # Can
    pygame.draw.rect(ekran, (30,30,30), (10, 11, 120, 14))
    can_bar_rect = pygame.Rect(10, 11, 120, 14)
    oran = oyuncu.can / oyuncu.max_can
    rc = YESIL if oran > 0.5 else (TURUNCU if oran > 0.25 else KIRMIZI)
    pygame.draw.rect(ekran, rc, (10, 11, int(120*oran), 14))
    pygame.draw.rect(ekran, CYAN, (10, 11, 120, 14), 1)
    can_sayisi_ciz(ekran, can_bar_rect, oyuncu.can, oyuncu.max_can, rc, (30,30,30), fnt_kk)
    ekran.blit(fnt_kk.render(t('can'), True, CYAN), (136, 13))

    # Kılıç atma cooldown / HEX kitap göstergesi (canın altında)
    if aegis_modu:
        cdx, cdy, cdw, cdh = 10, 27, 120, 8
        pygame.draw.rect(ekran, (30,30,30), (cdx, cdy, cdw, cdh))
        if oyuncu.kilic_atma_bekleme > 0:
            oran_c = 1 - oyuncu.kilic_atma_bekleme / KILIC_ATMA_BEKLEME
            pygame.draw.rect(ekran, TURUNCU, (cdx, cdy, int(cdw*oran_c), cdh))
        else:
            pygame.draw.rect(ekran, CYAN, (cdx, cdy, cdw, cdh))
        pygame.draw.rect(ekran, CYAN, (cdx, cdy, cdw, cdh), 1)
    elif hex_modu:
        kitap_metni = fnt_kk.render(f"KITAP: {oyuncu.hex_kitap_sayisi}/{oyuncu.hex_kitap_max_ozel}", True, MOR)
        ekran.blit(kitap_metni, (10, 27))
    elif raptor_modu:
        cdx, cdy, cdw, cdh = 10, 27, 120, 8
        pygame.draw.rect(ekran, (30,30,30), (cdx, cdy, cdw, cdh))
        if oyuncu.raptor_dash_bekleme > 0:
            oran_c = 1 - oyuncu.raptor_dash_bekleme / RAPTOR_DASH_BEKLEME
            pygame.draw.rect(ekran, TURUNCU, (cdx, cdy, int(cdw*oran_c), cdh))
        else:
            pygame.draw.rect(ekran, YESIL, (cdx, cdy, cdw, cdh))
        pygame.draw.rect(ekran, YESIL, (cdx, cdy, cdw, cdh), 1)
    elif wraith_modu:
        ruh_metni = fnt_kk.render(f"RUH: {int(oyuncu.wraith_ruh)}/{WRAITH_RUH_MAX}", True, (150,230,220))
        ekran.blit(ruh_metni, (10, 27))
    elif reaper_modu:
        bx0 = 10
        for i in range(REAPER_RUH_BOLME_MAX):
            dolu = i < oyuncu.reaper_ruh_bolme
            bw = 11
            pygame.draw.rect(ekran, (205,45,40) if dolu else (30,30,30), (bx0 + i*(bw+1), 27, bw, 8))
            pygame.draw.rect(ekran, (205,45,40), (bx0 + i*(bw+1), 27, bw, 8), 1)
    elif overdrive_modu:
        cdx, cdy, cdw, cdh = 10, 27, 120, 8
        pygame.draw.rect(ekran, (30,30,30), (cdx, cdy, cdw, cdh))
        if oyuncu.kanca_bekleme > 0:
            oran_c = 1 - oyuncu.kanca_bekleme / OVERDRIVE_KANCA_BEKLEME
            pygame.draw.rect(ekran, (110,90,0), (cdx, cdy, int(cdw*oran_c), cdh))
        else:
            pygame.draw.rect(ekran, SARI, (cdx, cdy, cdw, cdh))
        pygame.draw.rect(ekran, SARI, (cdx, cdy, cdw, cdh), 1)
    elif ronin_modu:
        cdx, cdy, cdw, cdh = 10, 27, 120, 8
        pygame.draw.rect(ekran, (30,30,30), (cdx, cdy, cdw, cdh))
        if oyuncu.ronin_firlat_bekleme > 0:
            oran_c = 1 - oyuncu.ronin_firlat_bekleme / RONIN_FIRLAT_BEKLEME
            pygame.draw.rect(ekran, (90,60,140), (cdx, cdy, int(cdw*oran_c), cdh))
        else:
            pygame.draw.rect(ekran, (170,120,255), (cdx, cdy, cdw, cdh))
        pygame.draw.rect(ekran, (170,120,255), (cdx, cdy, cdw, cdh), 1)

    # Kalkan göstergesi (AEGIS) / Heal göstergesi (HEX) / Kaçış göstergesi (RAPTOR) / Hayalet Geçişi (WRAITH)
    kx, ky, kw, kh = 175, 11, 80, 14
    pygame.draw.rect(ekran, (30,30,30), (kx, ky, kw, kh))
    if reaper_modu:
        if oyuncu.reaper_e_bekleme > 0:
            oran_r = 1 - oyuncu.reaper_e_bekleme / REAPER_E_BEKLEME
            pygame.draw.rect(ekran, (90,90,90), (kx, ky, int(kw*oran_r), kh))
        else:
            pygame.draw.rect(ekran, (205,45,40), (kx, ky, kw, kh))
        pygame.draw.rect(ekran, (205,45,40), (kx, ky, kw, kh), 1)
        ekran.blit(fnt_kk.render("E:GUCLENDIR", True, (205,45,40)), (kx+kw+6, 13))
    elif wraith_modu:
        oran_h = min(1.0, oyuncu.wraith_ruh / WRAITH_HAYALET_MALIYET)
        renk_h = (150,230,220) if oyuncu.wraith_ruh >= WRAITH_HAYALET_MALIYET else (90,90,90)
        pygame.draw.rect(ekran, renk_h, (kx, ky, int(kw*oran_h), kh))
        pygame.draw.rect(ekran, (150,230,220), (kx, ky, kw, kh), 1)
        ekran.blit(fnt_kk.render("SAG:HAYALET  E:IYILES", True, (150,230,220)), (kx+kw+6, 13))
    elif raptor_modu:
        if oyuncu.raptor_kacis_aktif:
            pygame.draw.rect(ekran, BEYAZ, (kx, ky, kw, kh))
        elif oyuncu.raptor_kacis_bekleme > 0:
            oran_k = 1 - oyuncu.raptor_kacis_bekleme / RAPTOR_KACIS_BEKLEME
            pygame.draw.rect(ekran, (90,90,90), (kx, ky, int(kw*oran_k), kh))
        else:
            pygame.draw.rect(ekran, BEYAZ, (kx, ky, kw, kh))
        pygame.draw.rect(ekran, YESIL, (kx, ky, kw, kh), 1)
        ekran.blit(fnt_kk.render("E:KACIS", True, YESIL), (kx+kw+6, 13))
    elif hex_modu:
        if oyuncu.hex_heal_aktif:
            oran_k = 1 - oyuncu.hex_heal_suresi / HEX_HEAL_SURESI
            pygame.draw.rect(ekran, YESIL, (kx, ky, int(kw*oran_k), kh))
        elif oyuncu.hex_heal_bekleme > 0:
            oran_k = 1 - oyuncu.hex_heal_bekleme / HEX_HEAL_BEKLEME
            pygame.draw.rect(ekran, (90,90,90), (kx, ky, int(kw*oran_k), kh))
        else:
            pygame.draw.rect(ekran, YESIL, (kx, ky, kw, kh))
        pygame.draw.rect(ekran, CYAN, (kx, ky, kw, kh), 1)
        ekran.blit(fnt_kk.render("E:IYILESTIR", True, CYAN), (kx+kw+6, 13))
    elif overdrive_modu:
        if oyuncu.overdrive_e_bekleme > 0:
            oran_e = 1 - oyuncu.overdrive_e_bekleme / OVERDRIVE_E_BEKLEME
            pygame.draw.rect(ekran, (90,90,90), (kx, ky, int(kw*oran_e), kh))
        else:
            pygame.draw.rect(ekran, SARI, (kx, ky, kw, kh))
        pygame.draw.rect(ekran, SARI, (kx, ky, kw, kh), 1)
        ekran.blit(fnt_kk.render("E:PATLAT", True, SARI), (kx+kw+6, 13))
    elif ronin_modu:
        if oyuncu.ronin_e_bekleme > 0:
            oran_e = 1 - oyuncu.ronin_e_bekleme / RONIN_E_BEKLEME
            pygame.draw.rect(ekran, (90,90,90), (kx, ky, int(kw*oran_e), kh))
        else:
            pygame.draw.rect(ekran, (170,120,255), (kx, ky, kw, kh))
        pygame.draw.rect(ekran, (170,120,255), (kx, ky, kw, kh), 1)
        ekran.blit(fnt_kk.render("E:GIZLEN", True, (170,120,255)), (kx+kw+6, 13))
    else:
        if oyuncu.kalkan_aktif:
            oran_k = oyuncu.kalkan_kapasite / KALKAN_KAPASITE
            pygame.draw.rect(ekran, CYAN, (kx, ky, int(kw*oran_k), kh))
        elif oyuncu.kalkan_bekleme > 0:
            oran_k = 1 - oyuncu.kalkan_bekleme / KALKAN_BEKLEME
            pygame.draw.rect(ekran, (90,90,90), (kx, ky, int(kw*oran_k), kh))
        pygame.draw.rect(ekran, CYAN, (kx, ky, kw, kh), 1)
        ekran.blit(fnt_kk.render("E:KALKAN", True, CYAN), (kx+kw+6, 13))

    # Ulti göstergesi
    ux, uy, uw, uh = 560, 11, 60, 14
    pygame.draw.rect(ekran, (30,30,30), (ux, uy, uw, uh))
    if reaper_modu:
        oran_u = oyuncu.reaper_ruh_bolme / REAPER_RUH_BOLME_MAX
        pygame.draw.rect(ekran, (205,45,40), (ux, uy, int(uw*oran_u), uh))
        pygame.draw.rect(ekran, (205,45,40), (ux, uy, uw, uh), 1)
        ekran.blit(fnt_kk.render("Q:ISKELET CAGIR", True, (205,45,40)), (ux+uw+6, 13))
    else:
        if oyuncu.ulti_aktif or oyuncu.raptor_ulti_aktif or oyuncu.wraith_ulti_aktif:
            pygame.draw.rect(ekran, (255,215,0), (ux, uy, uw, uh))
        else:
            oran_u = oyuncu.ulti_dolu / ULTI_MAX
            pygame.draw.rect(ekran, SARI, (ux, uy, int(uw*oran_u), uh))
        pygame.draw.rect(ekran, SARI, (ux, uy, uw, uh), 1)
        ekran.blit(fnt_kk.render("Q:ULTI", True, SARI), (ux+uw+6, 13))

    # Bölüm ve düşman
    b = fnt_kk.render(f"{t('bolum')} {bolum}/30   {t('dusman')}:{dusmanlar_kaldi}", True, TURUNCU)
    ekran.blit(b, (GENISLIK//2 - b.get_width()//2, 13))

    # Skor
    ekran.blit(fnt_kk.render(f"SKOR:{skor}", True, BEYAZ), (GENISLIK-220, 13))

    # Silah/kılıç ipucu (ekranın sol altında — karakterin üstünde artık metin yok)
    px, py = int(oyuncu.x), int(oyuncu.y)
    if aegis_modu:
        sw = fnt_kk.render("KILIC - AEGIS", True, CYAN)
        ekran.blit(sw, (10, YUKSEKLIK - 22))
    elif hex_modu:
        sw = fnt_kk.render("SOL:BUYU  SAG:ISIN - HEX", True, MOR)
        ekran.blit(sw, (10, YUKSEKLIK - 22))
    elif raptor_modu:
        sw = fnt_kk.render("SOL:PENCE  SAG:HAMLE - RAPTOR", True, YESIL)
        ekran.blit(sw, (10, YUKSEKLIK - 22))
    elif reaper_modu:
        sw = fnt_kk.render("SOL:ALAN VURUSU  SAG:ATIS - REAPER", True, (205,45,40))
        ekran.blit(sw, (10, YUKSEKLIK - 22))
    elif wraith_modu:
        sw = fnt_kk.render("SOL:RUH CISMI  SAG:HAYALET - WRAITH", True, (150,230,220))
        ekran.blit(sw, (10, YUKSEKLIK - 22))
    elif overdrive_modu:
        sw = fnt_kk.render("SOL:ATES  SAG:KANCA  E:PATLAT - OVERDRIVE", True, SARI)
        ekran.blit(sw, (10, YUKSEKLIK - 22))
    elif ronin_modu:
        sw = fnt_kk.render("SOL:ITIS  SAG:FIRLAT  E:GIZLEN - RONIN", True, (170,120,255))
        ekran.blit(sw, (10, YUKSEKLIK - 22))
    else:
        s = oyuncu.silah()
        if oyuncu.doluyor:
            prog = 1 - oyuncu.dolum_timer / s['dolum']
            pygame.draw.rect(ekran, (40,40,40), (px-20, py-28, 44, 6))
            pygame.draw.rect(ekran, TURUNCU, (px-20, py-28, int(44*prog), 6))

        # Silah adı
        sw = fnt_kk.render(f"{s['ikon']} {s['isim']}", True, s['renk'])
        ekran.blit(sw, (10, YUKSEKLIK - 22))


# ══════════════════════════════════════════
#  HİKAYE
# ══════════════════════════════════════════
async def hikaye_ekrani(ekran):
    sayfalar = [
        [
            "INSANLIK KENDINI YOK ETTI.",
            "",
            "Savaslar, salginlar ve nihayet yapay zekaya",
            "birakilan kontrol... Dunya artik robotlarin.",
            "",
            "Enkazin uzerinde yeni bir duzen kuruldu.",
        ],
        [
            "OMEGA-9 GELDI.",
            "",
            "Once bir kurtarici gibi gorundu. Sonra robotlari",
            "birbirine dusurdu, bir ic savas baslatti.",
            "",
            "Ona karsi duranlarin cogu yok edildi.",
        ],
        [
            "SADECE 7 TANESI KALDI.",
            "",
            "Her birinin kendine ozgu, farkli bir gucu var.",
            "Son umut onlar.",
            "",
            "Bolumleri gecip OMEGA-9'a ulasmalilar... ve onu yok etmeliler.",
        ],
    ]

    sayfa_idx = 0
    kayan_x = 0.0

    while True:
        saat.tick(FPS)
        kayan_x += 0.3
        fon_ciz(ekran, kayan_x)
        pygame.draw.rect(ekran, CYAN, (0, 0, GENISLIK, YUKSEKLIK), 3)

        baslik = fnt_by.render("HIKAYE", True, CYAN)
        ekran.blit(baslik, (GENISLIK//2 - baslik.get_width()//2, 40))

        satirlar = sayfalar[sayfa_idx]
        satir_y = 150
        for satir in satirlar:
            if satir:
                y = fnt_or.render(satir, True, BEYAZ)
                ekran.blit(y, (GENISLIK//2 - y.get_width()//2, satir_y))
            satir_y += 34

        sayfa_g = fnt_kk.render(f"{sayfa_idx+1}/{len(sayfalar)}", True, TURUNCU)
        ekran.blit(sayfa_g, (GENISLIK//2 - sayfa_g.get_width()//2, YUKSEKLIK-60))

        ipucu = fnt_kk.render("SPACE/ENTER Devam   ESC Atla", True, (90,90,90))
        ekran.blit(ipucu, (GENISLIK//2 - ipucu.get_width()//2, YUKSEKLIK-30))

        pygame.display.flip()
        await asyncio.sleep(0)

        for olay in pygame.event.get():
            if olay.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if olay.type == pygame.KEYDOWN:
                if olay.key == pygame.K_ESCAPE:
                    return
                if olay.key in (pygame.K_SPACE, pygame.K_RETURN):
                    sayfa_idx += 1
                    if sayfa_idx >= len(sayfalar):
                        return


# ══════════════════════════════════════════
#  KONTROLLER
# ══════════════════════════════════════════
async def kontroller_ekrani(ekran):
    kayan_x = 0.0

    while True:
        saat.tick(FPS)
        kayan_x += 0.3
        fon_ciz(ekran, kayan_x)
        pygame.draw.rect(ekran, CYAN, (0, 0, GENISLIK, YUKSEKLIK), 3)

        baslik = fnt_by.render(t('kontroller_baslik'), True, CYAN)
        ekran.blit(baslik, (GENISLIK//2 - baslik.get_width()//2, 60))

        satirlar = [t('kontrol_1'), t('kontrol_2'), t('kontrol_3'), t('kontrol_4'),
                    t('kontrol_5'), t('kontrol_6'), t('kontrol_7')]
        yy = 170
        for satir in satirlar:
            y = fnt_or.render(satir, True, BEYAZ)
            ekran.blit(y, (GENISLIK//2 - y.get_width()//2, yy))
            yy += 40

        ipucu = fnt_kk.render(t('geri_enter'), True, (90,90,90))
        ekran.blit(ipucu, (GENISLIK//2 - ipucu.get_width()//2, YUKSEKLIK-30))
        geri_butonu_ciz(ekran, pygame.mouse.get_pos())
        pygame.display.flip()
        await asyncio.sleep(0)

        for olay in pygame.event.get():
            if olay.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if olay.type == pygame.KEYDOWN:
                if olay.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    return
            if olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1:
                return


# ══════════════════════════════════════════
#  KREDİLER
# ══════════════════════════════════════════
async def kredi_ekrani(ekran):
    kayan_x = 0.0

    while True:
        saat.tick(FPS)
        kayan_x += 0.3
        fon_ciz(ekran, kayan_x)
        pygame.draw.rect(ekran, CYAN, (0, 0, GENISLIK, YUKSEKLIK), 3)

        baslik = fnt_by.render(t('krediler_baslik'), True, CYAN)
        ekran.blit(baslik, (GENISLIK//2 - baslik.get_width()//2, 44))

        alt_baslik = fnt_kk.render(t('krediler_alt'), True, (150,150,150))
        ekran.blit(alt_baslik, (GENISLIK//2 - alt_baslik.get_width()//2, 88))

        yy = 128
        for isim, sanatci, lisans in KREDI_LISTESI:
            lis = fnt_kk.render(lisans, True, (0,255,170))
            lis_x = GENISLIK - 60 - lis.get_width()
            ekran.blit(lis, (lis_x, yy))
            satir = fnt_kk.render(f"{isim} — {sanatci}", True, BEYAZ)
            if satir.get_width() > lis_x - 60 - 16:
                # Uzun isim + sanatçı satırı lisans etiketine değmesin diye sığana kadar kısaltılır.
                kisa = f"{isim} — {sanatci}"
                while satir.get_width() > lis_x - 60 - 16 and len(kisa) > 4:
                    kisa = kisa[:-2] + "…"
                    satir = fnt_kk.render(kisa, True, BEYAZ)
            ekran.blit(satir, (60, yy))
            yy += 34

        kaynak = fnt_kk.render("freesound.org", True, (90,90,90))
        ekran.blit(kaynak, (GENISLIK//2 - kaynak.get_width()//2, yy+10))

        ipucu = fnt_kk.render(t('geri_enter'), True, (90,90,90))
        ekran.blit(ipucu, (GENISLIK//2 - ipucu.get_width()//2, YUKSEKLIK-30))
        geri_butonu_ciz(ekran, pygame.mouse.get_pos())
        pygame.display.flip()
        await asyncio.sleep(0)

        for olay in pygame.event.get():
            if olay.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if olay.type == pygame.KEYDOWN:
                if olay.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    return
            if olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1:
                return


# ══════════════════════════════════════════
#  AYARLAR
# ══════════════════════════════════════════
async def ayarlar_ekrani(ekran):
    global AYAR_SES_SEVIYESI, AYAR_MUZIK_SEVIYESI, AYAR_NISANGAH_RENK_IDX, AYAR_NISANGAH_SEKIL_IDX, AYAR_IMLEC_GIZLI, AYAR_MOBIL_KONTROL, AYAR_DIL

    ses_eksi_rect = pygame.Rect(560, 96, 34, 30)
    ses_arti_rect = pygame.Rect(690, 96, 34, 30)
    muzik_eksi_rect = pygame.Rect(560, 150, 34, 30)
    muzik_arti_rect = pygame.Rect(690, 150, 34, 30)

    renk_rectleri = [pygame.Rect(150 + i*76, 260, 62, 36) for i in range(len(NISANGAH_RENKLERI))]
    sekil_etiketleri = {'arti': 'ARTI', 'daire': 'DAIRE', 'nokta': 'NOKTA', 'kare': 'KARE'}
    sekil_rectleri = [pygame.Rect(150 + i*140, 340, 124, 38) for i in range(len(NISANGAH_SEKILLERI))]

    dil_rectleri = [pygame.Rect(150 + i*72, 388, 64, 28) for i in range(len(DILLER))]
    imlec_rect = pygame.Rect(150, 424, 460, 30)
    mobil_rect = pygame.Rect(150, 460, 460, 30)
    geri_rect = pygame.Rect(GENISLIK//2 - 100, YUKSEKLIK - 54, 200, 40)

    mobil_onizleme_rect = pygame.Rect(560, 96, 260, 159)
    mobil_olcek = mobil_onizleme_rect.w / GENISLIK
    mobil_surukleme = None  # None | 'joy' | 'ates'

    kaydet_gerek = False

    while True:
        saat.tick(FPS)
        fon_ciz(ekran, 0, en_yuksek_bolum if en_yuksek_bolum <= 10 else (11 if en_yuksek_bolum <= 20 else 21))
        ortu = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)
        ortu.fill((0, 0, 0, 165))
        ekran.blit(ortu, (0, 0))

        fare_x, fare_y = pygame.mouse.get_pos()

        baslik = fnt_by.render(t('ayarlar_baslik'), True, CYAN)
        ekran.blit(baslik, (GENISLIK//2 - baslik.get_width()//2, 30))

        # Ses efekti seviyesi
        t1 = fnt_or.render(f"{t('ses_efekti')}: {int(AYAR_SES_SEVIYESI*100)}%", True, BEYAZ)
        ekran.blit(t1, (150, 100))
        buton_ciz(ekran, ses_eksi_rect, "-", (fare_x, fare_y))
        buton_ciz(ekran, ses_arti_rect, "+", (fare_x, fare_y))

        # Müzik seviyesi
        t2 = fnt_or.render(f"{t('muzik')}: {int(AYAR_MUZIK_SEVIYESI*100)}%", True, BEYAZ)
        ekran.blit(t2, (150, 154))
        buton_ciz(ekran, muzik_eksi_rect, "-", (fare_x, fare_y))
        buton_ciz(ekran, muzik_arti_rect, "+", (fare_x, fare_y))

        # Nişangah rengi
        t3 = fnt_or.render(t('nisangah_rengi'), True, BEYAZ)
        ekran.blit(t3, (150, 226))
        for i, (renk_isim, renk_deger) in enumerate(NISANGAH_RENKLERI):
            r = renk_rectleri[i]
            secili = i == AYAR_NISANGAH_RENK_IDX
            pygame.draw.rect(ekran, renk_deger, r)
            pygame.draw.rect(ekran, BEYAZ if secili else (60,60,60), r, 3 if secili else 1)

        # Nişangah şekli
        t4 = fnt_or.render(t('nisangah_sekli'), True, BEYAZ)
        ekran.blit(t4, (150, 306))
        for i, sekil in enumerate(NISANGAH_SEKILLERI):
            r = sekil_rectleri[i]
            secili = i == AYAR_NISANGAH_SEKIL_IDX
            zemin = (20,45,40) if secili else (18,18,28)
            cerceve = (0,255,200) if secili else (70,70,80)
            pygame.draw.rect(ekran, zemin, r)
            pygame.draw.rect(ekran, cerceve, r, 2)
            et = fnt_kk.render(t(sekil_etiketleri[sekil]), True, BEYAZ if secili else (150,150,150))
            ekran.blit(et, (r.centerx - et.get_width()//2, r.centery - et.get_height()//2))

        # Nişangah önizleme
        onizleme_x, onizleme_y = 780, 358
        pygame.draw.rect(ekran, (10,10,18), (onizleme_x-40, onizleme_y-40, 80, 80))
        pygame.draw.rect(ekran, (70,70,80), (onizleme_x-40, onizleme_y-40, 80, 80), 1)
        nisangah_ciz(ekran, onizleme_x, onizleme_y)

        # Dil
        dl = fnt_kk.render(t('dil_label'), True, BEYAZ)
        ekran.blit(dl, (150, 368))
        for i, kod in enumerate(DILLER):
            r = dil_rectleri[i]
            secili = kod == AYAR_DIL
            zemin = (20,45,40) if secili else (18,18,28)
            cerceve = (0,255,200) if secili else (70,70,80)
            pygame.draw.rect(ekran, zemin, r)
            pygame.draw.rect(ekran, cerceve, r, 2)
            et = fnt_mini.render(DIL_ISIMLERI[kod], True, BEYAZ if secili else (150,150,150))
            ekran.blit(et, (r.centerx - et.get_width()//2, r.centery - et.get_height()//2))

        # İmleç gizleme
        buton_ciz(ekran, imlec_rect, f"{t('imlec_gizle')}: {t('acik') if AYAR_IMLEC_GIZLI else t('kapali')}", (fare_x, fare_y), fnt_kk)

        # Mobil / dokunmatik kontroller
        buton_ciz(ekran, mobil_rect, f"{t('mobil_kontroller')}: {t('acik') if AYAR_MOBIL_KONTROL else t('kapali')}", (fare_x, fare_y), fnt_kk)

        if AYAR_MOBIL_KONTROL:
            t5 = fnt_kk.render(t('mobil_duzen'), True, BEYAZ)
            ekran.blit(t5, (mobil_onizleme_rect.x, mobil_onizleme_rect.y - 20))
            pygame.draw.rect(ekran, (10,10,18), mobil_onizleme_rect)
            pygame.draw.rect(ekran, (70,70,80), mobil_onizleme_rect, 1)
            joy_prev_x = mobil_onizleme_rect.x + AYAR_MOBIL_JOY_POS[0]*mobil_olcek
            joy_prev_y = mobil_onizleme_rect.y + AYAR_MOBIL_JOY_POS[1]*mobil_olcek
            ates_prev_x = mobil_onizleme_rect.x + AYAR_MOBIL_ATES_POS[0]*mobil_olcek
            ates_prev_y = mobil_onizleme_rect.y + AYAR_MOBIL_ATES_POS[1]*mobil_olcek
            pygame.draw.circle(ekran, CYAN, (int(joy_prev_x), int(joy_prev_y)), 14, 2)
            hj = fnt_mini.render(t('hareket_label'), True, CYAN)
            ekran.blit(hj, (joy_prev_x-hj.get_width()//2, joy_prev_y+15))
            pygame.draw.circle(ekran, SARI, (int(ates_prev_x), int(ates_prev_y)), 14, 2)
            ha = fnt_mini.render(t('ates_label'), True, SARI)
            ekran.blit(ha, (ates_prev_x-ha.get_width()//2, ates_prev_y+15))

        buton_ciz(ekran, geri_rect, t('geri'), (fare_x, fare_y))
        geri_butonu_ciz(ekran, (fare_x, fare_y))

        pygame.display.flip()
        await asyncio.sleep(0)

        for olay in pygame.event.get():
            if olay.type == pygame.QUIT:
                if kaydet_gerek:
                    kayit_kaydet()
                pygame.quit()
                sys.exit()
            if olay.type == pygame.KEYDOWN and olay.key == pygame.K_ESCAPE:
                if kaydet_gerek:
                    kayit_kaydet()
                return
            if olay.type == pygame.MOUSEMOTION and mobil_surukleme is not None:
                mx, my = olay.pos
                yeni_x = max(0, min(GENISLIK, (mx - mobil_onizleme_rect.x) / mobil_olcek))
                yeni_y = max(0, min(YUKSEKLIK, (my - mobil_onizleme_rect.y) / mobil_olcek))
                if mobil_surukleme == 'joy':
                    AYAR_MOBIL_JOY_POS[0], AYAR_MOBIL_JOY_POS[1] = yeni_x, yeni_y
                else:
                    AYAR_MOBIL_ATES_POS[0], AYAR_MOBIL_ATES_POS[1] = yeni_x, yeni_y
                kaydet_gerek = True
            if olay.type == pygame.MOUSEBUTTONUP and olay.button == 1:
                mobil_surukleme = None
            if olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1:
                mx, my = olay.pos
                if AYAR_MOBIL_KONTROL and math.hypot(mx - (mobil_onizleme_rect.x + AYAR_MOBIL_JOY_POS[0]*mobil_olcek),
                                                      my - (mobil_onizleme_rect.y + AYAR_MOBIL_JOY_POS[1]*mobil_olcek)) <= 16:
                    mobil_surukleme = 'joy'
                elif AYAR_MOBIL_KONTROL and math.hypot(mx - (mobil_onizleme_rect.x + AYAR_MOBIL_ATES_POS[0]*mobil_olcek),
                                                        my - (mobil_onizleme_rect.y + AYAR_MOBIL_ATES_POS[1]*mobil_olcek)) <= 16:
                    mobil_surukleme = 'ates'
                elif ses_eksi_rect.collidepoint(mx, my):
                    AYAR_SES_SEVIYESI = max(0.0, round(AYAR_SES_SEVIYESI - 0.1, 2))
                    kaydet_gerek = True
                    snd_para()
                elif ses_arti_rect.collidepoint(mx, my):
                    AYAR_SES_SEVIYESI = min(1.0, round(AYAR_SES_SEVIYESI + 0.1, 2))
                    kaydet_gerek = True
                    snd_para()
                elif muzik_eksi_rect.collidepoint(mx, my):
                    AYAR_MUZIK_SEVIYESI = max(0.0, round(AYAR_MUZIK_SEVIYESI - 0.1, 2))
                    kaydet_gerek = True
                    muzik_ses_guncelle()
                elif muzik_arti_rect.collidepoint(mx, my):
                    AYAR_MUZIK_SEVIYESI = min(1.0, round(AYAR_MUZIK_SEVIYESI + 0.1, 2))
                    kaydet_gerek = True
                    muzik_ses_guncelle()
                elif imlec_rect.collidepoint(mx, my):
                    AYAR_IMLEC_GIZLI = not AYAR_IMLEC_GIZLI
                    kaydet_gerek = True
                elif mobil_rect.collidepoint(mx, my):
                    AYAR_MOBIL_KONTROL = not AYAR_MOBIL_KONTROL
                    kaydet_gerek = True
                elif geri_rect.collidepoint(mx, my) or GERI_BUTON_RECT.collidepoint(mx, my):
                    if kaydet_gerek:
                        kayit_kaydet()
                    return
                else:
                    for i, r in enumerate(dil_rectleri):
                        if r.collidepoint(mx, my):
                            AYAR_DIL = DILLER[i]
                            kaydet_gerek = True
                    for i, r in enumerate(renk_rectleri):
                        if r.collidepoint(mx, my):
                            AYAR_NISANGAH_RENK_IDX = i
                            kaydet_gerek = True
                    for i, r in enumerate(sekil_rectleri):
                        if r.collidepoint(mx, my):
                            AYAR_NISANGAH_SEKIL_IDX = i
                            kaydet_gerek = True


# ══════════════════════════════════════════
#  ANA MENÜ
# ══════════════════════════════════════════
async def ana_menu():
    pygame.mouse.set_visible(True)
    secim = 0
    kayan_x = 0.0

    async def sec_uygula(i):
        if i == 0:
            return 1  # Bölüm 1'den başla
        elif i == 1:
            await hayatta_kal_modu(ekran)
        elif i == 2:
            await kahraman_sec(ekran)
        elif i == 3:
            b = await bolum_sec()
            if b:
                return b
        elif i == 4:
            await kontroller_ekrani(ekran)
        elif i == 5:
            await ayarlar_ekrani(ekran)
        elif i == 6:
            pygame.quit()
            sys.exit()
        return None

    kredi_rect = pygame.Rect(GENISLIK - 118, YUKSEKLIK - 26, 108, 20)

    while True:
        saat.tick(FPS)
        kayan_x += 0.3
        menuler = [t('menu_oyna'), t('menu_hayatta_kal'), t('menu_kahramanlar'), t('menu_bolumler'),
                   t('menu_kontroller'), t('menu_ayarlar'), t('menu_cikis')]

        # Menü, oyuncunun şu ana kadar ilerlediği en uzak bölgenin temasını yansıtır
        if en_yuksek_bolum <= 10:
            menu_tema = 1
            muzik_calistir(SES_METROPOL_MUZIK)
        elif en_yuksek_bolum <= 20:
            menu_tema = 11
            muzik_calistir(SES_DERIN_UZAY_MUZIK)
        else:
            menu_tema = 21
            muzik_calistir(SES_HARABE_MUZIK)
        fon_ciz(ekran, kayan_x, menu_tema)

        # Başlık
        if REVOLT_LOGO_GORSELI:
            ekran.blit(REVOLT_LOGO_GORSELI, (GENISLIK//2 - REVOLT_LOGO_GORSELI.get_width()//2, 15))
        else:
            baslik = fnt_by.render("REVOLT", True, CYAN)
            ekran.blit(baslik, (GENISLIK//2 - baslik.get_width()//2, 60))

        # Menü butonları
        fare_x, fare_y = pygame.mouse.get_pos()
        for i, m in enumerate(menuler):
            bx = GENISLIK//2 - 120
            by = 165 + i * 52
            uzerinde = bx <= fare_x <= bx+240 and by <= fare_y <= by+44
            if uzerinde:
                secim = i

            aktif = i == secim
            renk = (0,255,200) if uzerinde else (TURUNCU if aktif else (80,80,80))
            cerceve = (0,255,200) if uzerinde else (TURUNCU if aktif else (40,40,40))
            zemin = (20,45,40) if uzerinde else (0,0,0)
            pygame.draw.rect(ekran, zemin, (bx, by, 240, 44))
            pygame.draw.rect(ekran, cerceve, (bx, by, 240, 44), 2)
            y = fnt_or.render(("► " if aktif else "  ") + m, True, renk)
            ekran.blit(y, (bx + 120 - y.get_width()//2, by + 11))

        hint = fnt_kk.render(t('menu_ipucu'), True, (60,60,60))
        ekran.blit(hint, (GENISLIK//2 - hint.get_width()//2, YUKSEKLIK-30))

        kredi_uzerinde = kredi_rect.collidepoint(fare_x, fare_y)
        kredi_y = fnt_kk.render(t('menu_krediler'), True, (0,255,170) if kredi_uzerinde else (70,70,70))
        ekran.blit(kredi_y, (kredi_rect.right - kredi_y.get_width(), kredi_rect.y))

        pygame.display.flip()
        await asyncio.sleep(0)

        for olay in pygame.event.get():
            if olay.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if olay.type == pygame.KEYDOWN:
                if olay.key == pygame.K_UP:
                    secim = (secim - 1) % len(menuler)
                if olay.key == pygame.K_DOWN:
                    secim = (secim + 1) % len(menuler)
                if olay.key == pygame.K_RETURN:
                    sonuc = await sec_uygula(secim)
                    if sonuc:
                        return sonuc
            if olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1:
                mx, my = pygame.mouse.get_pos()
                if kredi_rect.collidepoint(mx, my):
                    await kredi_ekrani(ekran)
                    continue
                for i in range(len(menuler)):
                    bx = GENISLIK//2 - 120
                    by = 165 + i * 52
                    if bx <= mx <= bx+240 and by <= my <= by+44:
                        secim = i
                        sonuc = await sec_uygula(i)
                        kayit_kaydet()
                        if sonuc:
                            return sonuc


async def bolum_sec():
    TEMA_RENK = [(70,170,255), (170,90,255), (255,80,60)]  # mavi / mor / kirmizi-turuncu
    TEMA_ADI = ["METROPOL", "DERIN UZAY", "HARABE"]

    # Gorsel yok — butonlari kendimiz ciziyoruz, boylece konumlari tam bilinir.
    buton_w, buton_h = 62, 56
    satir_bosluk = 96
    ust_satir_y = YUKSEKLIK // 2 - satir_bosluk // 2
    alt_satir_y = YUKSEKLIK // 2 + satir_bosluk // 2
    alt_bosluk = 40

    def kutulari_al(sayfa_no):
        kutular = []
        spacing = GENISLIK / 5
        for sutun in range(10):
            i = sayfa_no*10 + sutun
            sutun_satirda = sutun % 5
            cy = ust_satir_y if sutun < 5 else alt_satir_y
            cx = spacing * (sutun_satirda + 0.5)
            ucgen_mi = (sutun == 4) or (sutun == 8)   # 5/15/25 ve 9/19/29 = KAOS BOLUM
            kutular.append((pygame.Rect(int(cx-buton_w/2), int(cy-buton_h/2), buton_w, buton_h), i+1, ucgen_mi, TEMA_RENK[sayfa_no]))
        return kutular

    def buton_ciz(rect, bolum_no, ucgen_mi, renk, acik, uzerinde):
        cx, cy = rect.center
        if uzerinde:
            zemin = (renk[0]//5, renk[1]//5, renk[2]//5)
            cerceve = renk
            yazi_renk = BEYAZ
            kalinlik = 4
        else:
            zemin = (16,16,24)
            cerceve = renk if acik else (55,55,65)
            yazi_renk = BEYAZ if acik else (95,95,95)
            kalinlik = 2
        if ucgen_mi:
            uc = [(cx, rect.top), (rect.right, rect.bottom), (rect.left, rect.bottom)]
            pygame.draw.polygon(ekran, zemin, uc)
            pygame.draw.polygon(ekran, cerceve, uc, kalinlik)
        else:
            pygame.draw.rect(ekran, zemin, rect, border_radius=8)
            pygame.draw.rect(ekran, cerceve, rect, kalinlik, border_radius=8)
        if not acik:
            karart = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            karart.fill((0,0,0,150))
            ekran.blit(karart, rect.topleft)
        t = fnt_or.render(str(bolum_no), True, yazi_renk)
        ekran.blit(t, (cx - t.get_width()//2, cy - t.get_height()//2))


    sayfa = 0
    ok_sol_rect = pygame.Rect(6, YUKSEKLIK//2-30, 40, 60)
    ok_sag_rect = pygame.Rect(GENISLIK-46, YUKSEKLIK//2-30, 40, 60)

    while True:
        saat.tick(FPS)
        fare_x, fare_y = pygame.mouse.get_pos()
        ekran.fill(KOYU)
        pygame.draw.rect(ekran, CYAN, (0,0,GENISLIK,YUKSEKLIK), 3)
        b = fnt_by.render("BOLUM SEC", True, CYAN)
        ekran.blit(b, (GENISLIK//2 - b.get_width()//2, 14))
        say = fnt_kk.render(f"{TEMA_ADI[sayfa]}   ({sayfa+1} / 3)", True, TEMA_RENK[sayfa])
        ekran.blit(say, (GENISLIK//2 - say.get_width()//2, 44))

        kutular = kutulari_al(sayfa)
        for rect, bolum_no, ucgen_mi, renk in kutular:
            acik = TEST_MODU or bolum_no <= en_yuksek_bolum
            uzerinde = acik and rect.collidepoint(fare_x, fare_y)
            buton_ciz(rect, bolum_no, ucgen_mi, renk, acik, uzerinde)
            # O bolumde acilan bir kahraman varsa, hangi bolumun "onun" oldugu gorulsun
            for k_etiket in KAHRAMANLAR:
                if k_etiket['acilis_bolum'] == bolum_no and k_etiket['acilis_bolum'] > 1:
                    et = fnt_mini.render(k_etiket['isim'], True, k_etiket['renk'])
                    ekran.blit(et, (rect.centerx - et.get_width()//2, rect.top - 13))

        for i in range(3):
            renk_n = TEMA_RENK[i] if i == sayfa else (70,70,80)
            pygame.draw.circle(ekran, renk_n, (GENISLIK//2 - 16 + i*16, YUKSEKLIK-alt_bosluk+10), 4)

        ok_sol_aktif = ok_sol_rect.collidepoint(fare_x, fare_y)
        ok_sag_aktif = ok_sag_rect.collidepoint(fare_x, fare_y)
        renk_ok_sol = TEMA_RENK[(sayfa-1)%3] if ok_sol_aktif else (110,110,120)
        renk_ok_sag = TEMA_RENK[(sayfa+1)%3] if ok_sag_aktif else (110,110,120)
        pygame.draw.polygon(ekran, renk_ok_sol, [(ok_sol_rect.right-8, ok_sol_rect.top), (ok_sol_rect.left+8, ok_sol_rect.centery), (ok_sol_rect.right-8, ok_sol_rect.bottom)], 0 if ok_sol_aktif else 3)
        pygame.draw.polygon(ekran, renk_ok_sag, [(ok_sag_rect.left+8, ok_sag_rect.top), (ok_sag_rect.right-8, ok_sag_rect.centery), (ok_sag_rect.left+8, ok_sag_rect.bottom)], 0 if ok_sag_aktif else 3)

        g = fnt_kk.render("Oklara tikla ya da fare tekerlegini kaydir   ESC Geri", True, (90,90,90))
        ekran.blit(g, (GENISLIK//2 - g.get_width()//2, YUKSEKLIK-16))
        geri_butonu_ciz(ekran, (fare_x, fare_y))
        pygame.display.flip()
        await asyncio.sleep(0)

        for olay in pygame.event.get():
            if olay.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if olay.type == pygame.KEYDOWN:
                if olay.key == pygame.K_ESCAPE:
                    return None
            if olay.type == pygame.MOUSEWHEEL:
                if olay.y < 0:
                    sayfa = (sayfa + 1) % 3
                elif olay.y > 0:
                    sayfa = (sayfa - 1) % 3
            if olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1:
                if GERI_BUTON_RECT.collidepoint(olay.pos):
                    return None
                elif ok_sol_rect.collidepoint(olay.pos):
                    sayfa = (sayfa - 1) % 3
                elif ok_sag_rect.collidepoint(olay.pos):
                    sayfa = (sayfa + 1) % 3
                else:
                    for rect, bolum_no, ucgen_mi, renk in kutular:
                        if (TEST_MODU or bolum_no <= en_yuksek_bolum) and rect.collidepoint(olay.pos):
                            return bolum_no


# ══════════════════════════════════════════
#  KAHRAMAN SEÇİM EKRANI
# ══════════════════════════════════════════
async def kahraman_sec(ekran):
    global secili_kahraman
    panel_acik = False
    panel_sekme = 'kahraman'
    yukselt_buton_rect = pygame.Rect(GENISLIK - 150, 6, 130, 28)

    while True:
        saat.tick(FPS)
        fare_pos = pygame.mouse.get_pos()
        ekran.fill((0, 0, 10))
        pygame.draw.rect(ekran, CYAN, (0, 0, GENISLIK, YUKSEKLIK), 3)

        baslik = fnt_by.render("KAHRAMANLAR", True, CYAN)
        ekran.blit(baslik, (GENISLIK//2 - baslik.get_width()//2, 8))

        # Tam ekran ekip afişi: kahramanlar bu görselin üzerinden, üstüne
        # tıklanarak seçilir. Afiş görselleri (ekip_1..5.jpg) zaten kimin
        # renkli kimin gölge olduğunu kendi içinde barındırıyor — üstüne
        # ayrıca bir siyah katman eklemiyoruz. En yüksek basamaktaki afişi
        # seçiyoruz ama SADECE o afişte renkli olan herkes gerçekten açıksa
        # (aksi halde henüz açılmamış biri yanlışlıkla renkli görünür).
        acik_kume = {k['id'] for k in KAHRAMANLAR if TEST_MODU or en_yuksek_bolum >= k['acilis_bolum']}
        afis_idx = 0
        for i, kume in enumerate(EKIP_AFIS_ACIK_KUMELERI):
            if kume <= acik_kume:
                afis_idx = i
            else:
                break
        afis_gorseli = EKIP_AFIS_GORSELLERI[afis_idx] if EKIP_AFIS_GORSELLERI[afis_idx] else None

        afis_alan = pygame.Rect(6, 42, GENISLIK-12, YUKSEKLIK-42-26)
        kartlar = []
        EKIP_AFIS_SIRA = [0, 1, 6, 7, 8, 5, 9]
        EKIP_AFIS_FRACS = [0.09, 0.22, 0.35, 0.49, 0.62, 0.75, 0.88]
        if afis_gorseli:
            oran_a = min(afis_alan.w / afis_gorseli.get_width(), afis_alan.h / afis_gorseli.get_height())
            aw, ah = int(afis_gorseli.get_width()*oran_a), int(afis_gorseli.get_height()*oran_a)
            ax, ay = afis_alan.centerx - aw//2, afis_alan.centery - ah//2
            olcekli_a = pygame.transform.smoothscale(afis_gorseli, (aw, ah))
            ekran.blit(olcekli_a, (ax, ay))

            for kid, frac in zip(EKIP_AFIS_SIRA, EKIP_AFIS_FRACS):
                k = next(kk for kk in KAHRAMANLAR if kk['id'] == kid)
                acik = TEST_MODU or en_yuksek_bolum >= k['acilis_bolum']
                cx = ax + int(aw*frac)
                rw, rh = int(aw*0.125), int(ah*0.66)
                rect = pygame.Rect(cx-rw//2, ay+int(ah*0.22), rw, rh)
                secildi = acik and secili_kahraman == k['id']
                uzerinde = acik and rect.collidepoint(fare_pos)
                # Karakterin tam siluetini tutturmaya çalışmak yerine, altında
                # konumu bağışlayıcı bir gösterge çubuğu — üstüne gelince yanar,
                # seçilince yeşile döner.
                cubuk_rect = pygame.Rect(rect.left, rect.bottom-6, rect.w, 6)
                if secildi:
                    pygame.draw.rect(ekran, (0,255,136), cubuk_rect)
                elif uzerinde:
                    pygame.draw.rect(ekran, CYAN, cubuk_rect)
                elif acik:
                    pygame.draw.rect(ekran, (70,70,80), cubuk_rect)
                isim_r = fnt_kk.render(k['isim'] if acik else "?????",
                                        True, (0,255,136) if secildi else (BEYAZ if acik else (90,90,90)))
                ekran.blit(isim_r, (rect.centerx - isim_r.get_width()//2, rect.bottom-24))
                kartlar.append((rect, k, acik))
        else:
            for i, k in enumerate(KAHRAMANLAR):
                acik = TEST_MODU or en_yuksek_bolum >= k['acilis_bolum']
                rect = pygame.Rect(20 + i*120, 200, 100, 100)
                pygame.draw.rect(ekran, k['renk'] if acik else (40,40,40), rect, 2)
                isim_r = fnt_kk.render(k['isim'], True, BEYAZ if acik else (90,90,90))
                ekran.blit(isim_r, (rect.centerx - isim_r.get_width()//2, rect.bottom+4))
                kartlar.append((rect, k, acik))

        ipucu = fnt_kk.render("Mouse ile sec   ESC/D Geri", True, (90,90,90))
        ekran.blit(ipucu, (GENISLIK//2 - ipucu.get_width()//2, YUKSEKLIK-16))
        buton_ciz(ekran, yukselt_buton_rect, "YUKSELT", fare_pos, fnt_kk)

        panel_rect = pygame.Rect(90, 60, GENISLIK-180, YUKSEKLIK-120)
        kapat_buton_rect = pygame.Rect(panel_rect.right-90, panel_rect.bottom-42, 74, 30)
        sekme_kahraman_rect = pygame.Rect(panel_rect.left+20, panel_rect.top+12, 150, 30)
        sekme_genel_rect = pygame.Rect(panel_rect.left+178, panel_rect.top+12, 150, 30)
        if panel_acik:
            gomlek = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)
            gomlek.fill((0,0,0,190))
            ekran.blit(gomlek, (0,0))
            pygame.draw.rect(ekran, (10,10,20), panel_rect)
            pygame.draw.rect(ekran, CYAN, panel_rect, 2)

            for sekme_rect, sekme_ad, sekme_deger in ((sekme_kahraman_rect, "KAHRAMANLAR", 'kahraman'), (sekme_genel_rect, "GENEL", 'genel')):
                aktif_sekme = panel_sekme == sekme_deger
                pygame.draw.rect(ekran, (0,60,50) if aktif_sekme else (18,18,28), sekme_rect)
                pygame.draw.rect(ekran, (0,255,170) if aktif_sekme else (70,70,80), sekme_rect, 2)
                st = fnt_kk.render(sekme_ad, True, BEYAZ if aktif_sekme else (130,130,130))
                ekran.blit(st, (sekme_rect.centerx - st.get_width()//2, sekme_rect.centery - st.get_height()//2))

            icerik_ust = panel_rect.top + 56

            secim_kutulari = []
            yetenek_kutulari = []
            if panel_sekme == 'kahraman':
                secilebilir = [k for k in KAHRAMANLAR if k['id'] in KAHRAMAN_YUKSELTMELERI and (TEST_MODU or en_yuksek_bolum >= k['acilis_bolum'])]
                pil_w = (panel_rect.w - 40) / max(1, len(secilebilir))
                for i, k in enumerate(secilebilir):
                    pil_rect = pygame.Rect(int(panel_rect.left+20+i*pil_w), icerik_ust, int(pil_w)-6, 26)
                    secili_mi = k['id'] == secili_kahraman
                    pygame.draw.rect(ekran, (0,60,50) if secili_mi else (18,18,28), pil_rect)
                    pygame.draw.rect(ekran, k['renk'] if secili_mi else (70,70,80), pil_rect, 2)
                    pt = fnt_kk.render(k['isim'], True, BEYAZ if secili_mi else (140,140,140))
                    ekran.blit(pt, (pil_rect.centerx - pt.get_width()//2, pil_rect.centery - pt.get_height()//2))
                    secim_kutulari.append((pil_rect, k['id']))
                icerik_ust += 38

                k_aktif = next((k for k in KAHRAMANLAR if k['id'] == secili_kahraman), None)
                tierler = KAHRAMAN_YUKSELTMELERI.get(secili_kahraman)
                if k_aktif and tierler:
                    pb = fnt_or.render(f"{k_aktif['isim']} USTALASMASI", True, k_aktif['renk'])
                    ekran.blit(pb, (panel_rect.centerx - pb.get_width()//2, icerik_ust))

                    hasar_toplam = KAHRAMAN_HASAR.get(secili_kahraman, 0.0)
                    kademe_p = ustalik_kademesi(secili_kahraman)
                    esikler_p = ustalik_esikleri(secili_kahraman)
                    bar_rect = pygame.Rect(panel_rect.left+30, icerik_ust+34, panel_rect.w-60, 16)
                    sonraki_esik = esikler_p[kademe_p] if kademe_p < len(esikler_p) else esikler_p[-1]
                    onceki_esik = esikler_p[kademe_p-1] if kademe_p > 0 else 0
                    oran_p = 1.0 if kademe_p >= len(esikler_p) else max(0.0, min(1.0, (hasar_toplam-onceki_esik)/(sonraki_esik-onceki_esik)))
                    pygame.draw.rect(ekran, (30,30,40), bar_rect)
                    pygame.draw.rect(ekran, k_aktif['renk'], (bar_rect.x, bar_rect.y, int(bar_rect.w*oran_p), bar_rect.h))
                    pygame.draw.rect(ekran, (90,90,100), bar_rect, 1)
                    etiket = f"{int(hasar_toplam)} / {sonraki_esik} HASAR" if kademe_p < len(esikler_p) else f"{int(hasar_toplam)} HASAR — TAM USTA"
                    et = fnt_kk.render(etiket, True, BEYAZ)
                    ekran.blit(et, (bar_rect.centerx - et.get_width()//2, bar_rect.bottom+4))

                    for i, (t_isim, t_aciklama, _) in enumerate(tierler):
                        ty = icerik_ust + 92 + i*54
                        yet_rect = pygame.Rect(panel_rect.left+30, ty, panel_rect.w-60, 44)
                        acik_t = i < kademe_p
                        kapali_t = (secili_kahraman, i) in KAHRAMAN_YETENEK_KAPALI
                        if acik_t:
                            renk_t = (70,70,80) if kapali_t else (0,255,136)
                            durum_i = "KAPALI (aç için tıkla)" if kapali_t else "AKTİF (kapatmak için tıkla)"
                            yetenek_kutulari.append((yet_rect, i))
                        else:
                            renk_t = (70,70,80)
                            durum_i = f"KADEME {i+1} — {esikler_p[i]} HASAR GEREKIR"
                        pygame.draw.rect(ekran, (18,18,28), yet_rect)
                        pygame.draw.rect(ekran, renk_t, yet_rect, 2)
                        ti = fnt_or.render(t_isim, True, BEYAZ if (acik_t and not kapali_t) else (140,140,140))
                        ekran.blit(ti, (panel_rect.left+44, ty+4))
                        ta = fnt_kk.render(f"{t_aciklama}   [{durum_i}]", True, renk_t)
                        ekran.blit(ta, (panel_rect.left+44, ty+24))

                    if secili_kahraman == 5:
                        sy = icerik_ust + 92 + len(tierler)*54
                        acik_s = hasar_toplam >= OVERDRIVE_SALLANMA_ESIGI
                        renk_s = (0,255,136) if acik_s else (70,70,80)
                        pygame.draw.rect(ekran, (18,18,28), (panel_rect.left+30, sy, panel_rect.w-60, 44))
                        pygame.draw.rect(ekran, renk_s, (panel_rect.left+30, sy, panel_rect.w-60, 44), 2)
                        durum_s = "ACIK" if acik_s else f"{int(hasar_toplam)} / {OVERDRIVE_SALLANMA_ESIGI} HASAR GEREKIR"
                        ts = fnt_or.render("SALINIM SISTEMI", True, BEYAZ if acik_s else (140,140,140))
                        ekran.blit(ts, (panel_rect.left+44, sy+4))
                        tas = fnt_kk.render(f"Kanca ile sallanma + pompalama   [{durum_s}]", True, renk_s)
                        ekran.blit(tas, (panel_rect.left+44, sy+24))
                else:
                    uyari = fnt_kk.render("Once bir kahraman sec", True, (150,150,150))
                    ekran.blit(uyari, (panel_rect.centerx - uyari.get_width()//2, panel_rect.centery))
            else:
                pg = fnt_or.render("GENEL YUKSELTMELER — TUM KAHRAMANLARA UYGULANIR", True, CYAN)
                ekran.blit(pg, (panel_rect.centerx - pg.get_width()//2, icerik_ust))
                for i, (gid, g_isim, g_aciklama, kontrol_fn, _) in enumerate(GENEL_GOREVLER):
                    ty = icerik_ust + 34 + i*44
                    acik_g = kontrol_fn()
                    renk_g = (0,255,136) if acik_g else (70,70,80)
                    pygame.draw.rect(ekran, (18,18,28), (panel_rect.left+30, ty, panel_rect.w-60, 38))
                    pygame.draw.rect(ekran, renk_g, (panel_rect.left+30, ty, panel_rect.w-60, 38), 2)
                    durum_g = "TAMAMLANDI" if acik_g else "AÇIK DEĞİL"
                    tg = fnt_kk.render(f"{g_isim}: {g_aciklama}", True, BEYAZ if acik_g else (140,140,140))
                    ekran.blit(tg, (panel_rect.left+42, ty+5))
                    dg = fnt_kk.render(f"[{durum_g}]", True, renk_g)
                    ekran.blit(dg, (panel_rect.right - 42 - dg.get_width(), ty+5))

            buton_ciz(ekran, kapat_buton_rect, "KAPAT", fare_pos, fnt_kk)
        else:
            geri_butonu_ciz(ekran, fare_pos)

        pygame.display.flip()
        await asyncio.sleep(0)

        for olay in pygame.event.get():
            if olay.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if olay.type == pygame.KEYDOWN:
                if olay.key in (pygame.K_ESCAPE, pygame.K_d):
                    if panel_acik:
                        panel_acik = False
                    else:
                        return
            if olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1:
                mx, my = pygame.mouse.get_pos()
                if not panel_acik and GERI_BUTON_RECT.collidepoint(mx, my):
                    return
                if panel_acik:
                    if kapat_buton_rect.collidepoint(mx, my) or yukselt_buton_rect.collidepoint(mx, my):
                        panel_acik = False
                    elif sekme_kahraman_rect.collidepoint(mx, my):
                        panel_sekme = 'kahraman'
                    elif sekme_genel_rect.collidepoint(mx, my):
                        panel_sekme = 'genel'
                    else:
                        for pil_rect, kid in secim_kutulari:
                            if pil_rect.collidepoint(mx, my):
                                secili_kahraman = kid
                        for yet_rect, idx in yetenek_kutulari:
                            if yet_rect.collidepoint(mx, my):
                                anahtar_y = (secili_kahraman, idx)
                                if anahtar_y in KAHRAMAN_YETENEK_KAPALI:
                                    KAHRAMAN_YETENEK_KAPALI.discard(anahtar_y)
                                else:
                                    KAHRAMAN_YETENEK_KAPALI.add(anahtar_y)
                    continue
                if yukselt_buton_rect.collidepoint(mx, my):
                    panel_acik = True
                    continue
                for rect, k, acik in kartlar:
                    if acik and rect.collidepoint(mx, my):
                        secili_kahraman = k['id']


# ══════════════════════════════════════════
#  ANA OYUN DÖNGÜSÜ
# ══════════════════════════════════════════
async def oyun(baslangic_bolum=1, baslangic_para=0, sahip_silahlar=None, secili_silah=0):
    global en_yuksek_bolum
    muzik_calistir(None)  # savaş sırasında müzik çalmasın — oyuncu odaklansın
    pygame.mouse.set_visible(not AYAR_IMLEC_GIZLI)
    mobil_kontrol = MobilKontrol()
    if sahip_silahlar is None:
        sahip_silahlar = [0]

    aegis_modu = (secili_kahraman == 0)
    hex_modu = (secili_kahraman == 6)
    raptor_modu = (secili_kahraman == 1)
    wraith_modu = (secili_kahraman == 7)
    reaper_modu = (secili_kahraman == 8)
    overdrive_modu = (secili_kahraman == 5)
    ronin_modu = (secili_kahraman == 9)

    oyuncu = Oyuncu()
    oyuncu.silah_idx = secili_silah
    oyuncu.sarjor = SILAHLAR[secili_silah]['sarjor']
    if hex_modu:
        oyuncu.max_can = HEX_MAX_CAN
        oyuncu.can = HEX_MAX_CAN
        oyuncu.daima_ucar = True
    if raptor_modu:
        oyuncu.raptor_hizli = True
    if wraith_modu:
        oyuncu.max_can = WRAITH_MAX_CAN
        oyuncu.can = WRAITH_MAX_CAN
        oyuncu.daima_ucar = True
        oyuncu.wraith_yavas = True
    if reaper_modu:
        oyuncu.max_can = REAPER_MAX_CAN
        oyuncu.can = REAPER_MAX_CAN
        oyuncu.w, oyuncu.h = REAPER_W, REAPER_H
        oyuncu.reaper_agir = True
    if overdrive_modu:
        oyuncu.max_can = OVERDRIVE_MAX_CAN
        oyuncu.can = OVERDRIVE_MAX_CAN
        oyuncu.overdrive_sinirsiz_mermi = True
        oyuncu.overdrive_sallanma_acik = KAHRAMAN_HASAR.get(5, 0.0) >= OVERDRIVE_SALLANMA_ESIGI
    if ronin_modu:
        oyuncu.max_can = RONIN_MAX_CAN
        oyuncu.can = RONIN_MAX_CAN
    ustalik_uygula(oyuncu, secili_kahraman)
    genel_yukseltme_uygula(oyuncu)

    def ronin_itis():
        nonlocal skor
        merkez_x = oyuncu.x + oyuncu.w/2
        merkez_y = oyuncu.y + oyuncu.h/2
        hedef_aci = math.atan2(fare_y-merkez_y, fare_x-merkez_x)
        carpan = oyuncu.ronin_hasar_carpani()
        for d in dusman_listesi[:]:
            if d.tip == 'hayalet' and d.hayalet_mod:
                continue
            dm_x, dm_y = d.x+d.w/2, d.y+d.h/2
            dx, dy = dm_x-merkez_x, dm_y-merkez_y
            if math.hypot(dx, dy) > RONIN_ITIS_MENZIL * oyuncu.ronin_menzil_carpan:
                continue
            fark = (math.atan2(dy, dx) - hedef_aci + math.pi) % (2*math.pi) - math.pi
            if abs(fark) > RONIN_ITIS_ACI:
                continue
            if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                parca_listesi.extend(patlama(dm_x, dm_y, CYAN, 5))
                continue
            hasar = RONIN_ITIS_HASAR * carpan
            d.can -= hasar
            if oyuncu.ronin_gizli_aktif and oyuncu.ronin_gizli_sersem_acik:
                d.dondu_kare = 300
            hasar_yazisi_listesi.append(HasarYazisi(dm_x, dm_y, hasar, (220,220,220), dx, dy))
            parca_listesi.extend(patlama(dm_x, dm_y, (170,120,255), 7))
            if d.can <= 0:
                parca_listesi.extend(patlama(dm_x, dm_y, (245,166,35), 14))
                skor += d.para
                oyuncu.ulti_sarj_ekle()
                oyuncu.reaper_ruh_ekle()
                snd_olum()
                dusman_listesi.remove(d)
        for sl in solucan_listesi[:]:
            if not sl.vurulabilir_mi():
                continue
            dx, dy = sl.x-merkez_x, (ZEMIN_Y-sl.yukseklik/2)-merkez_y
            if math.hypot(dx, dy) > RONIN_ITIS_MENZIL * oyuncu.ronin_menzil_carpan:
                continue
            fark = (math.atan2(dy, dx) - hedef_aci + math.pi) % (2*math.pi) - math.pi
            if abs(fark) > RONIN_ITIS_ACI:
                continue
            solucan_hasar_uygula(sl, RONIN_ITIS_HASAR * carpan, dx, dy)

    def ronin_firlat():
        nonlocal skor
        oyuncu.ronin_firlat_bekleme = RONIN_FIRLAT_BEKLEME
        oyuncu.ronin_firlat_goster = 10
        snd_mizrak()
        ex, ey = oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2
        dx, dy = fare_x-ex, fare_y-ey
        uzunluk = math.hypot(dx, dy) or 1
        ux, uy = dx/uzunluk, dy/uzunluk
        carpan = oyuncu.ronin_hasar_carpani()
        vurulanlar = []
        mesafe = 0
        son_x, son_y = ex, ey
        while mesafe < RONIN_FIRLAT_MENZIL * oyuncu.ronin_menzil_carpan:
            mesafe += 14
            nx, ny = ex+ux*mesafe, ey+uy*mesafe
            if nx < -20 or nx > GENISLIK+20:
                break
            son_x, son_y = nx, ny
            for d in dusman_listesi[:]:
                if d in vurulanlar or (d.tip == 'hayalet' and d.hayalet_mod):
                    continue
                if d.rect().collidepoint(nx, ny):
                    vurulanlar.append(d)
                    if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                        parca_listesi.extend(patlama(nx, ny, CYAN, 5))
                        continue
                    hasar = RONIN_FIRLAT_HASAR * carpan
                    d.can -= hasar
                    if oyuncu.ronin_gizli_aktif and oyuncu.ronin_gizli_sersem_acik:
                        d.dondu_kare = 300
                    hasar_yazisi_listesi.append(HasarYazisi(nx, ny, hasar, (220,220,220), ux, uy))
                    parca_listesi.extend(patlama(nx, ny, (170,120,255), 6))
                    if d.can <= 0:
                        parca_listesi.extend(patlama(nx, ny, (245,166,35), 14))
                        skor += d.para
                        oyuncu.ulti_sarj_ekle()
                        oyuncu.reaper_ruh_ekle()
                        snd_olum()
                        dusman_listesi.remove(d)
            for sl in solucan_listesi[:]:
                if sl not in vurulanlar and sl.vurulabilir_mi() and sl.rect().collidepoint(nx, ny):
                    vurulanlar.append(sl)
                    solucan_hasar_uygula(sl, RONIN_FIRLAT_HASAR * carpan, ux, uy)
        oyuncu.x = max(0, min(GENISLIK-oyuncu.w, son_x - oyuncu.w/2))
        oyuncu.y = max(46, min(ZEMIN_Y-oyuncu.h, son_y - oyuncu.h/2))
        oyuncu.hiz_x = 0
        oyuncu.hiz_y = 0
        parca_listesi.extend(patlama(son_x, son_y, (170,120,255), 10))
        snd_zipla()

    def overdrive_kanca_baglan(hx, hy):
        ex2, ey2 = oyuncu.x + oyuncu.w/2, oyuncu.y + oyuncu.h/2
        oyuncu.kanca_x, oyuncu.kanca_y = hx, hy
        oyuncu.kanca_ip_uzunlugu = max(30, math.hypot(ex2-hx, ey2-hy))
        oyuncu.kanca_aci = math.atan2(ey2-hy, ex2-hx)
        oyuncu.kanca_acisal_hiz = 0.0
        oyuncu.kanca_durum = 'sallaniyor'
        oyuncu.kanca_bekleme = OVERDRIVE_KANCA_BEKLEME
        snd_zipla()

    def overdrive_kanca_direk_git(hx, hy):
        # Salınım açık değilken: sallanmadan, normal hızda hedefe doğru uçarak gider (eskisi gibi)
        oyuncu.kanca_x, oyuncu.kanca_y = hx, hy
        oyuncu.kanca_ucus_hedef_x = max(0, min(GENISLIK - oyuncu.w, hx - oyuncu.w/2))
        oyuncu.kanca_ucus_hedef_y = max(46, min(ZEMIN_Y - oyuncu.h, hy - oyuncu.h))
        oyuncu.kanca_durum = 'ucuyor'
        oyuncu.kanca_bekleme = OVERDRIVE_KANCA_BEKLEME
        snd_zipla()

    def overdrive_kanca_at(hedef_x, hedef_y):
        if oyuncu.overdrive_kanca_heal_acik:
            can_once_ok = oyuncu.can
            oyuncu.can = min(oyuncu.max_can, oyuncu.can + 10)
            kazanc_ok = oyuncu.can - can_once_ok
            if kazanc_ok > 0:
                hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, kazanc_ok, YESIL, 0, -1, art=True))
        ex, ey = oyuncu.x + oyuncu.w/2, oyuncu.y + oyuncu.h/2
        dx, dy = hedef_x - ex, hedef_y - ey
        uzunluk = math.hypot(dx, dy) or 1
        ux, uy = dx/uzunluk, dy/uzunluk
        mesafe = 0
        while mesafe < OVERDRIVE_KANCA_MENZIL:
            mesafe += 12
            nx, ny = ex + ux*mesafe, ey + uy*mesafe
            for d in dusman_listesi:
                if d.rect().collidepoint(nx, ny):
                    d.cekim_kare = 24
                    d.cekim_hedef_x = ex + ux*40
                    d.cekim_hedef_y = ey + uy*40
                    parca_listesi.extend(patlama(nx, ny, SARI, 8))
                    oyuncu.kanca_bekleme = OVERDRIVE_KANCA_BEKLEME
                    snd_zipla()
                    return
            for p in aktif_platformlar:
                if pygame.Rect(p['x'], p['y'], p['w'], p['h']).collidepoint(nx, ny):
                    if oyuncu.overdrive_sallanma_acik:
                        overdrive_kanca_baglan(nx, ny)
                    else:
                        overdrive_kanca_direk_git(nx, ny)
                    return
            if nx <= 0 or nx >= GENISLIK:
                # Arenanın sol/sağ duvarı
                hx = max(4, min(GENISLIK-4, nx))
                if oyuncu.overdrive_sallanma_acik:
                    overdrive_kanca_baglan(hx, ny)
                else:
                    overdrive_kanca_direk_git(hx, ny)
                return
            if ny <= 66:
                # Tavan — HUD (0-42) alanina girmesin diye biraz asagida durur
                if oyuncu.overdrive_sallanma_acik:
                    overdrive_kanca_baglan(nx, 70)
                else:
                    overdrive_kanca_direk_git(nx, 70)
                return
            if ny >= ZEMIN_Y - 2:
                overdrive_kanca_direk_git(nx, ZEMIN_Y - 10)
                return
        oyuncu.kanca_bekleme = OVERDRIVE_KANCA_BEKLEME  # boşluğa attı — işe yaramadı, geri çekildi

    bolum = baslangic_bolum
    para = baslangic_para
    skor = 0

    def solucan_hasar_uygula(sl, hasar, hy_x=0, hy_y=-1):
        nonlocal skor
        sl.can -= hasar
        tepe_y = ZEMIN_Y - sl.yukseklik
        hasar_yazisi_listesi.append(HasarYazisi(sl.x, tepe_y, hasar, (220,220,220), hy_x, hy_y))
        parca_listesi.extend(patlama(sl.x, tepe_y, (150,150,160), 8))
        if sl.can <= 0:
            parca_listesi.extend(patlama(sl.x, ZEMIN_Y-30, (245,166,35), 16))
            skor += sl.para
            oyuncu.ulti_sarj_ekle()
            oyuncu.reaper_ruh_ekle()
            snd_olum()

    while bolum <= 30:
        en_yuksek_bolum = max(en_yuksek_bolum, bolum)
        if TEST_MODU:
            oyuncu.ulti_dolu = ULTI_MAX  # TEST: her bölüm başında ulti hazır olsun
        # ── BÖLÜM HAZIRLIK ──
        if TEST_MODU:
            tema_bolum = {1: 1, 2: 11, 3: 21}.get(bolum, 21)  # TEST: her temayı hızlıca görelim
        else:
            tema_bolum = bolum
        ayar = bolum_ayar(bolum)
        spawn_listesi = []
        for tip, sayi in [('melee',ayar['melee']),('ranged',ayar['ranged']),
                           ('drone',ayar['drone']),('sniper',ayar.get('sniper',0)),
                           ('shield',ayar.get('shield',0)),('tank',ayar.get('tank',0)),
                           ('suicide',ayar.get('suicide',0)),('gorunmez',ayar.get('gorunmez',0)),
                           ('hayalet',ayar.get('hayalet',0))]:
            spawn_listesi.extend([tip]*sayi)
        if ayar.get('boss'):
            spawn_listesi.append('boss')
        # Final boss savaşında normal düşmanlar spawn_sira yerine ayrı,
        # sürekli bir mekanizmayla gelir (aşağıdaki "Spawn" bloğuna bak).

        random.shuffle(spawn_listesi)
        spawn_sira = list(spawn_listesi)
        spawn_idx = 0
        spawn_timer = 60

        dusman_listesi = []
        mermi_listesi = []
        parca_listesi = []
        hasar_yazisi_listesi = []
        enkaz_listesi = []
        enkaz_timer = random.randint(90, 150)
        iskelet_listesi = []
        solucan_listesi = []
        solucan_timer = random.randint(SOLUCAN_ARALIK_MIN, SOLUCAN_ARALIK_MAX)
        solucan_can_kalan = SOLUCAN_CAN
        solucan_olduruldu = False
        son_hareket_yonu = 1

        mizrakli_aktif = ayar.get('mizrakli', 0) > 0
        mizrakli_timer = random.randint(180, 260)
        mizrakli_sonraki_yon = random.choice([1, -1])

        if tema_bolum <= 10:
            aktif_platformlar = PLATFORM_SEHIR
        elif tema_bolum <= 20:
            aktif_platformlar = PLATFORM_ISTASYON
            for p in aktif_platformlar:
                p['x'] = p['baslangic_x']
        else:
            aktif_platformlar = []

        oyuncu.x = 150
        oyuncu.y = ZEMIN_Y - oyuncu.h
        oyuncu.can = oyuncu.max_can
        oyuncu.hasar_timer = 80
        oyuncu.kilic_durum = 'beklemede'
        oyuncu.hex_kitap_sayisi = 0
        oyuncu.hex_kitap_timer = HEX_KITAP_SURESI
        oyuncu.hex_heal_aktif = False
        oyuncu.hex_heal_bekleme = 0
        oyuncu.hex_buyu_bekleme = 0
        oyuncu.raptor_zip_tutuluyor = False
        oyuncu.raptor_pence_bekleme = 0
        oyuncu.raptor_dash_aktif = False
        oyuncu.raptor_dash_bekleme = 0
        oyuncu.raptor_kacis_aktif = False
        oyuncu.raptor_kacis_bekleme = 0
        oyuncu.wraith_ruh = 0
        oyuncu.wraith_ruh_bekleme = 0
        oyuncu.wraith_hayalet_aktif = False
        oyuncu.wraith_heal_bekleme = 0
        oyuncu.wraith_ulti_aktif = False
        oyuncu.reaper_ruh_bolme = 0
        oyuncu.reaper_vurus_bekleme = 0
        oyuncu.reaper_atis_bekleme = 0
        oyuncu.reaper_e_bekleme = 0

        bolum_bitti = False
        zaman = 0
        fare_basili = False
        geri_buton_rect = pygame.Rect(GENISLIK//2 - 210, 145, 200, 42)
        devam_buton_rect = pygame.Rect(GENISLIK//2 + 10, 145, 200, 42)

        durduruldu = False
        duraklama_goruntusu = None
        durdur_buton_rect = pygame.Rect(GENISLIK - 34, 8, 26, 26)
        pause_devam_rect = pygame.Rect(GENISLIK//2 - 110, YUKSEKLIK//2 - 10, 220, 46)
        pause_menu_rect = pygame.Rect(GENISLIK//2 - 110, YUKSEKLIK//2 + 50, 220, 46)

        # Final boss özel spawn
        if ayar.get('final'):
            dusman_listesi.append(Dusman(GENISLIK//2, 'finalboss', bolum))

        # ── OYUN DÖNGÜSÜ ──
        while True:
            saat.tick(FPS)
            zaman = pygame.time.get_ticks()
            sonraki_bolume_gec = False

            for olay in pygame.event.get():
                if AYAR_MOBIL_KONTROL:
                    mobil_kontrol.olay_isle(olay)
                if olay.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if olay.type == pygame.KEYDOWN:
                    if olay.key == pygame.K_ESCAPE and not bolum_bitti:
                        if not durduruldu:
                            duraklama_goruntusu = ekran.copy()
                        durduruldu = not durduruldu
                    if olay.key == pygame.K_r and not aegis_modu and not hex_modu and not raptor_modu and not wraith_modu and not reaper_modu:
                        oyuncu.reload_baslat()
                    if olay.key == pygame.K_e:
                        if hex_modu:
                            oyuncu.hex_heal_baslat()
                        elif raptor_modu:
                            mx_e, my_e = pygame.mouse.get_pos()
                            yon_e = 1 if mx_e > oyuncu.x + oyuncu.w/2 else -1
                            if oyuncu.raptor_kacis_baslat(yon_e) and oyuncu.raptor_zehir_patlama_acik:
                                merkez_zx, merkez_zy = oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2
                                for dz in dusman_listesi:
                                    if math.hypot(dz.x+dz.w/2-merkez_zx, dz.y+dz.h/2-merkez_zy) <= RAPTOR_ZEHIR_PATLAMA_YARICAP:
                                        dz.zehir_kare = RAPTOR_ZEHIR_DUSMAN_SURESI
                                        dz.zehir_tik = RAPTOR_ZEHIR_TIK
                                parca_listesi.extend(patlama(merkez_zx, merkez_zy, (60,220,90), 16))
                        elif wraith_modu:
                            can_once = oyuncu.can
                            oyuncu.wraith_heal_baslat()
                            kazanilan = oyuncu.can - can_once
                            if kazanilan > 0:
                                hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, kazanilan, YESIL, 0, -1, art=True))
                        elif reaper_modu:
                            e_kullanilabilir = (oyuncu.reaper_e_bekleme <= 0 and oyuncu.can > REAPER_E_CAN_MALIYET
                                                 and (iskelet_listesi or oyuncu.reaper_e_ek_iskelet_acik))
                            if e_kullanilabilir:
                                oyuncu.can -= REAPER_E_CAN_MALIYET
                                for isk in iskelet_listesi:
                                    isk.guclendir()
                                if oyuncu.reaper_e_ek_iskelet_acik:
                                    for _ in range(3):
                                        yeni_isk = Iskelet(oyuncu.x + oyuncu.w/2 - 11 + random.randint(-30, 30), ZEMIN_Y - 34, guclu=True)
                                        yeni_isk.guclendir()
                                        iskelet_listesi.append(yeni_isk)
                                oyuncu.reaper_e_bekleme = REAPER_E_BEKLEME
                        elif overdrive_modu:
                            if oyuncu.overdrive_e_bekleme <= 0:
                                oyuncu.overdrive_e_bekleme = OVERDRIVE_E_BEKLEME
                                oyuncu.overdrive_e_goster = 10
                                snd_overdrive_patlat()
                                can_once_od = oyuncu.can
                                oyuncu.can = min(oyuncu.max_can, oyuncu.can + OVERDRIVE_E_CAN_YENILEME)
                                kazanilan_od = oyuncu.can - can_once_od
                                if kazanilan_od > 0:
                                    hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, kazanilan_od, YESIL, 0, -1, art=True))
                                merkez_x, merkez_y = oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2
                                for d in dusman_listesi[:]:
                                    if d.tip == 'hayalet' and d.hayalet_mod:
                                        continue
                                    dm_x, dm_y = d.x+d.w/2, d.y+d.h/2
                                    if math.hypot(dm_x-merkez_x, dm_y-merkez_y) > OVERDRIVE_E_MENZIL:
                                        continue
                                    if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                                        parca_listesi.extend(patlama(dm_x, dm_y, CYAN, 5))
                                        continue
                                    d.can -= OVERDRIVE_E_HASAR
                                    hasar_yazisi_listesi.append(HasarYazisi(dm_x, dm_y, OVERDRIVE_E_HASAR, (220,220,220), dm_x-merkez_x, dm_y-merkez_y))
                                    parca_listesi.extend(patlama(dm_x, dm_y, SARI, 8))
                                    if d.can <= 0:
                                        parca_listesi.extend(patlama(dm_x, dm_y, (245,166,35), 14))
                                        skor += d.para
                                        oyuncu.ulti_sarj_ekle()
                                        oyuncu.reaper_ruh_ekle()
                                        if oyuncu.overdrive_ulti_aktif:
                                            oyuncu.can = min(oyuncu.max_can, oyuncu.can + OVERDRIVE_ULTI_CAN_KAZANC)
                                        snd_olum()
                                        dusman_listesi.remove(d)
                                for sl in solucan_listesi[:]:
                                    if not sl.vurulabilir_mi():
                                        continue
                                    if math.hypot(sl.x-merkez_x, (ZEMIN_Y-sl.yukseklik/2)-merkez_y) > OVERDRIVE_E_MENZIL:
                                        continue
                                    solucan_hasar_uygula(sl, OVERDRIVE_E_HASAR, sl.x-merkez_x, -1)
                        elif ronin_modu:
                            if oyuncu.ronin_e_bekleme <= 0:
                                oyuncu.ronin_e_bekleme = RONIN_E_BEKLEME
                                oyuncu.ronin_gizli_aktif = True
                                oyuncu.ronin_gizli_suresi = RONIN_E_SURESI
                                oyuncu.ronin_kritik_hazir = True
                        else:
                            oyuncu.kalkan_baslat()
                    if olay.key == pygame.K_q:
                        if hex_modu:
                            if oyuncu.ulti_dolu >= ULTI_MAX:
                                oyuncu.ulti_dolu = 0
                                snd_hex_ulti()
                                hex_ulti_hasar_g = 99999 if oyuncu.hex_ulti_ekran_temizle_acik else HEX_ULTI_HASAR
                                for d in dusman_listesi[:]:
                                    d.can -= hex_ulti_hasar_g
                                    d.yavaslatildi = HEX_ULTI_YAVAS_SURESI
                                    hasar_yazisi_listesi.append(HasarYazisi(d.x+d.w/2, d.y+d.h/2, min(hex_ulti_hasar_g, int(d.max_can)), (220,220,220), 0, -1))
                                    if d.can <= 0:
                                        parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (245,166,35), 14))
                                        skor += d.para
                                        oyuncu.ulti_sarj_ekle()
                                        oyuncu.reaper_ruh_ekle()
                                        snd_olum()
                                        dusman_listesi.remove(d)
                                for sl in solucan_listesi[:]:
                                    if not sl.vurulabilir_mi():
                                        continue
                                    sl.can -= hex_ulti_hasar_g
                                    hasar_yazisi_listesi.append(HasarYazisi(sl.x, ZEMIN_Y-sl.yukseklik, min(hex_ulti_hasar_g, int(sl.max_can)), (220,220,220), 0, -1))
                                    if sl.can <= 0:
                                        parca_listesi.extend(patlama(sl.x, ZEMIN_Y-30, (245,166,35), 16))
                                        skor += sl.para
                                        oyuncu.ulti_sarj_ekle()
                                        oyuncu.reaper_ruh_ekle()
                                        snd_olum()
                        elif raptor_modu:
                            if oyuncu.ulti_dolu >= ULTI_MAX and not oyuncu.raptor_ulti_aktif:
                                oyuncu.ulti_dolu = 0
                                oyuncu.raptor_ulti_aktif = True
                                oyuncu.raptor_ulti_suresi = RAPTOR_ULTI_SURESI
                                snd_raptor_ulti()
                        elif wraith_modu:
                            if oyuncu.ulti_dolu >= ULTI_MAX and not oyuncu.wraith_ulti_aktif:
                                oyuncu.ulti_dolu = 0
                                oyuncu.wraith_ulti_aktif = True
                                oyuncu.wraith_ulti_suresi = WRAITH_ULTI_SURESI
                                snd_wraith_ulti()
                        elif reaper_modu:
                            if oyuncu.reaper_ruh_bolme > 0:
                                adet = oyuncu.reaper_ruh_bolme
                                for i in range(adet):
                                    offset = (i - (adet-1)/2) * 32
                                    sx = max(0, min(GENISLIK-22, oyuncu.x + oyuncu.w/2 + offset - 11))
                                    iskelet_listesi.append(Iskelet(sx, ZEMIN_Y - 34, guclu=True, okcu=oyuncu.reaper_ulti_okcu_acik))
                                oyuncu.reaper_ruh_bolme = 0
                                snd_reaper_ulti()
                        elif overdrive_modu:
                            if oyuncu.ulti_dolu >= ULTI_MAX and not oyuncu.overdrive_ulti_aktif:
                                oyuncu.ulti_dolu = 0
                                oyuncu.overdrive_ulti_aktif = True
                                oyuncu.overdrive_ulti_suresi = OVERDRIVE_ULTI_SURESI
                                for d in dusman_listesi:
                                    d.yavaslatildi = OVERDRIVE_ULTI_SURESI
                                for m in mermi_listesi:
                                    if not m.oyuncu_mermisi:
                                        m.hiz_x *= OVERDRIVE_ULTI_YAVAS_CARPAN
                                        m.hiz_y *= OVERDRIVE_ULTI_YAVAS_CARPAN
                                if oyuncu.overdrive_ulti_olumsuz_acik:
                                    oyuncu.overdrive_olumsuzluk_kalan = OVERDRIVE_ULTI_SURESI + 180
                                snd_overdrive_ulti()
                        elif ronin_modu:
                            if oyuncu.ulti_dolu >= ULTI_MAX and not oyuncu.ronin_ulti_aktif:
                                oyuncu.ulti_dolu = 0
                                oyuncu.ronin_ulti_aktif = True
                                oyuncu.ronin_ulti_suresi = RONIN_ULTI_SURESI
                                if oyuncu.ronin_ulti_gelismis_acik:
                                    can_once_ro = oyuncu.can
                                    oyuncu.can = min(oyuncu.max_can, oyuncu.can + 50)
                                    kazanc_ro = oyuncu.can - can_once_ro
                                    if kazanc_ro > 0:
                                        hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, kazanc_ro, YESIL, 0, -1, art=True))
                                snd_ronin_ulti()
                        else:
                            ulti_oncesi = oyuncu.ulti_aktif
                            can_once = oyuncu.can
                            oyuncu.ulti_kullan()
                            kazanilan = oyuncu.can - can_once
                            if kazanilan > 0:
                                hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, kazanilan, YESIL, 0, -1, art=True))
                            if oyuncu.ulti_aktif and not ulti_oncesi:
                                snd_aegis_ulti()
                    # Silah değiştir (1-0 tuşları)
                    if not aegis_modu and not hex_modu and not raptor_modu and not wraith_modu and not reaper_modu:
                        for i in range(len(SILAHLAR)):
                            k = getattr(pygame, f'K_{i+1}' if i < 9 else 'K_0', None)
                            if k and olay.key == k and i in sahip_silahlar:
                                oyuncu.silah_idx = i
                                oyuncu.sarjor = SILAHLAR[i]['sarjor']
                                oyuncu.doluyor = False
                if olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1:
                    if durduruldu:
                        if pause_devam_rect.collidepoint(olay.pos):
                            durduruldu = False
                        elif pause_menu_rect.collidepoint(olay.pos):
                            return None  # Ana menüye
                    elif bolum_bitti:
                        if geri_buton_rect.collidepoint(olay.pos):
                            return None  # Ana menüye
                        elif devam_buton_rect.collidepoint(olay.pos):
                            bolum += 1
                            bolum_bitti = False
                            sonraki_bolume_gec = True
                    elif durdur_buton_rect.collidepoint(olay.pos):
                        duraklama_goruntusu = ekran.copy()
                        durduruldu = True
                    else:
                        fare_basili = True
                if olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 3:
                    if not bolum_bitti and aegis_modu:
                        # Sağ tık: kılıcı fırlat / geri çağır
                        if oyuncu.kilic_durum == 'beklemede':
                            oyuncu.kilic_firlat(*olay.pos)
                        else:
                            oyuncu.kilic_geri_cagir()
                    elif not bolum_bitti and hex_modu:
                        # Sağ tık: kitap sayısına göre ölçeklenen anlık ışın
                        if oyuncu.hex_kitap_sayisi >= 1:
                            ex, ey = oyuncu.kilic_el_konumu()
                            dx, dy = olay.pos[0] - ex, olay.pos[1] - ey
                            uzunluk = math.hypot(dx, dy) or 1
                            yon_x, yon_y = dx/uzunluk, dy/uzunluk
                            hasar_isin = HEX_ISIN_BIRIM_HASAR * oyuncu.hex_kitap_sayisi
                            isin_vurulanlar = []
                            isin_solucan_vuruldu = []
                            mesafe = 0
                            while mesafe < HEX_ISIN_MENZIL:
                                mesafe += 14
                                nx, ny = ex + yon_x*mesafe, ey + yon_y*mesafe
                                for d in dusman_listesi[:]:
                                    if d in isin_vurulanlar:
                                        continue
                                    if d.tip == 'hayalet' and d.hayalet_mod:
                                        continue
                                    if d.rect().collidepoint(nx, ny):
                                        isin_vurulanlar.append(d)
                                        if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                                            parca_listesi.extend(patlama(nx, ny, CYAN, 5))
                                            continue
                                        d.can -= hasar_isin
                                        hasar_yazisi_listesi.append(HasarYazisi(d.x+d.w/2, d.y+d.h/2, hasar_isin, (220,220,220), yon_x, yon_y))
                                        parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, MOR, 8))
                                        if d.can <= 0:
                                            parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (245,166,35), 14))
                                            skor += d.para
                                            oyuncu.ulti_sarj_ekle()
                                            oyuncu.reaper_ruh_ekle()
                                            snd_olum()
                                            dusman_listesi.remove(d)
                                for sl in solucan_listesi[:]:
                                    if sl in isin_solucan_vuruldu or not sl.vurulabilir_mi():
                                        continue
                                    if sl.rect().collidepoint(nx, ny):
                                        isin_solucan_vuruldu.append(sl)
                                        solucan_hasar_uygula(sl, hasar_isin, yon_x, yon_y)
                            oyuncu.hex_isin_bitis = (ex + yon_x*HEX_ISIN_MENZIL, ey + yon_y*HEX_ISIN_MENZIL)
                            oyuncu.hex_isin_goster = 8
                            oyuncu.hex_isin_kitap_sayisi = oyuncu.hex_kitap_sayisi
                            oyuncu.hex_kitap_sayisi = 0
                            snd_buyu()
                    elif not bolum_bitti and raptor_modu:
                        # Sağ tık: hasar veren hamle (dash)
                        if oyuncu.raptor_dash_bekleme <= 0 and not oyuncu.raptor_dash_aktif:
                            yon_dash = 1 if oyuncu.hiz_x >= 0 else -1
                            if oyuncu.hiz_x == 0:
                                yon_dash = 1 if olay.pos[0] > oyuncu.x + oyuncu.w/2 else -1
                            oyuncu.raptor_dash_aktif = True
                            oyuncu.raptor_dash_suresi = RAPTOR_DASH_SURESI
                            oyuncu.raptor_dash_yon = yon_dash
                            oyuncu.raptor_dash_bekleme = 0 if oyuncu.raptor_dash_sinirsiz_acik else RAPTOR_DASH_BEKLEME
                            oyuncu.raptor_dash_vurulanlar = []
                            if oyuncu.raptor_ofke_acik:
                                oyuncu.raptor_ofke_aktif = True
                                oyuncu.raptor_ofke_suresi = RAPTOR_OFKE_SURESI
                            snd_zipla()
                    elif not bolum_bitti and wraith_modu:
                        # Sağ tık: Hayalet Geçişi — dokunulmazlık, ruh enerjisi harcar
                        oyuncu.wraith_hayalet_baslat()
                    elif not bolum_bitti and reaper_modu:
                        # Sağ tık: baktığı yöne daha büyük ve güçlü koni — öldürdüğü düşman iskelete dönüşür
                        if oyuncu.reaper_atis_bekleme <= 0:
                            oyuncu.reaper_atis_bekleme = REAPER_ATIS_BEKLEME
                            oyuncu.reaper_atis_goster = 8
                            snd_koni()
                            merkez_x = oyuncu.x + oyuncu.w/2
                            merkez_y = oyuncu.y + oyuncu.h/2
                            hedef_aci = math.atan2(olay.pos[1]-merkez_y, olay.pos[0]-merkez_x)
                            for d in dusman_listesi[:]:
                                if d.tip == 'hayalet' and d.hayalet_mod:
                                    continue
                                dm_x, dm_y = d.x+d.w/2, d.y+d.h/2
                                dx, dy = dm_x-merkez_x, dm_y-merkez_y
                                if math.hypot(dx, dy) > REAPER_ATIS_MENZIL:
                                    continue
                                fark = (math.atan2(dy, dx) - hedef_aci + math.pi) % (2*math.pi) - math.pi
                                if abs(fark) > REAPER_ATIS_ACI:
                                    continue
                                if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                                    parca_listesi.extend(patlama(dm_x, dm_y, CYAN, 5))
                                    continue
                                d.can -= REAPER_ATIS_HASAR
                                hasar_yazisi_listesi.append(HasarYazisi(dm_x, dm_y, REAPER_ATIS_HASAR, (220,220,220), dx, dy))
                                parca_listesi.extend(patlama(dm_x, dm_y, (255,35,35), 7))
                                parca_listesi.extend(patlama(dm_x, dm_y, (12,7,8), 6))
                                if d.can <= 0:
                                    olum_x, olum_y = dm_x, dm_y
                                    parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                                    skor += d.para
                                    oyuncu.ulti_sarj_ekle()
                                    oyuncu.reaper_ruh_ekle()
                                    snd_olum()
                                    dusman_listesi.remove(d)
                                    iskelet_listesi.append(Iskelet(olum_x - 11, olum_y - 17, guclu=False))
                            for sl in solucan_listesi[:]:
                                if not sl.vurulabilir_mi():
                                    continue
                                dx, dy = sl.x-merkez_x, (ZEMIN_Y-sl.yukseklik/2)-merkez_y
                                if math.hypot(dx, dy) > REAPER_ATIS_MENZIL:
                                    continue
                                fark = (math.atan2(dy, dx) - hedef_aci + math.pi) % (2*math.pi) - math.pi
                                if abs(fark) > REAPER_ATIS_ACI:
                                    continue
                                olduruldu_mu = sl.can <= REAPER_ATIS_HASAR
                                solucan_hasar_uygula(sl, REAPER_ATIS_HASAR, dx, dy)
                                if olduruldu_mu:
                                    iskelet_listesi.append(Iskelet(sl.x - 11, ZEMIN_Y - 51, guclu=False))
                    elif not bolum_bitti and overdrive_modu:
                        # Sağ tık: kanca — duvara/zemine atarsa oraya çekilir, düşmana atarsa onu kendine çeker
                        if oyuncu.kanca_bekleme <= 0 and oyuncu.kanca_durum == 'yok':
                            overdrive_kanca_at(*olay.pos)
                    elif not bolum_bitti and ronin_modu:
                        # Sağ tık: mızrağı fırlat — çizgide delip geçer, sonra düştüğü noktaya ışınlanır
                        if oyuncu.ronin_firlat_bekleme <= 0:
                            ronin_firlat()
                if olay.type == pygame.MOUSEBUTTONUP and olay.button == 1:
                    fare_basili = False
                if olay.type == pygame.MOUSEBUTTONUP and olay.button == 3:
                    if overdrive_modu and oyuncu.kanca_durum in ('sallaniyor', 'ucuyor'):
                        oyuncu.overdrive_sallan(*olay.pos)

            if sonraki_bolume_gec:
                break  # Bir sonraki bölümün düşmanlarını hazırlamak için dış döngüye dön

            fare_x, fare_y = pygame.mouse.get_pos()
            if AYAR_MOBIL_KONTROL:
                fare_x, fare_y = mobil_kontrol.nisan_konumu(fare_x, fare_y, oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2)
                fare_basili = fare_basili or mobil_kontrol.ates_basili

            if durduruldu:
                ekran.blit(duraklama_goruntusu, (0, 0))
                ortu = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)
                ortu.fill((0, 0, 0, 150))
                ekran.blit(ortu, (0, 0))
                baslik_p = fnt_by.render(t('pause_baslik'), True, CYAN)
                ekran.blit(baslik_p, (GENISLIK//2 - baslik_p.get_width()//2, YUKSEKLIK//2 - 90))
                buton_ciz(ekran, pause_devam_rect, t('devam_et'), (fare_x, fare_y))
                buton_ciz(ekran, pause_menu_rect, t('ana_menuye_don'), (fare_x, fare_y))
                nisangah_ciz(ekran, fare_x, fare_y)
                pygame.display.flip()
                await asyncio.sleep(0)
                continue

            tuslar = pygame.key.get_pressed()
            if AYAR_MOBIL_KONTROL:
                tuslar = mobil_kontrol.tuslar_sarmala(tuslar)

            if fare_basili and not bolum_bitti:
                if aegis_modu:
                    # Sol tık (basılı tut): savurma (kılıç eldeyken kısa menzilli darbe)
                    if oyuncu.kilic_durum == 'beklemede' and oyuncu.kilic_savurma_bekleme <= 0:
                        savur_rect = oyuncu.kilic_savur_rect(fare_x, fare_y)
                        oyuncu.kilic_savurma_bekleme = KILIC_SAVURMA_BEKLEME
                        oyuncu.kilic_savurma_goster = 8
                        snd_kilic()
                        for d in dusman_listesi[:]:
                            if d.tip == 'hayalet' and d.hayalet_mod:
                                continue
                            if d.rect().colliderect(savur_rect):
                                if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                                    parca_listesi.extend(patlama(savur_rect.centerx, savur_rect.centery, CYAN, 5))
                                    continue
                                d.can -= KILIC_HASAR
                                hasar_yazisi_listesi.append(HasarYazisi(d.x+d.w/2, d.y+d.h/2, KILIC_HASAR, (220,220,220), d.x-oyuncu.x, d.y-oyuncu.y))
                                parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (0,200,200), 8))
                                if d.can <= 0:
                                    parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (245,166,35), 14))
                                    skor += d.para
                                    oyuncu.ulti_sarj_ekle()
                                    oyuncu.reaper_ruh_ekle()
                                    snd_olum()
                                    dusman_listesi.remove(d)
                        for sl in solucan_listesi[:]:
                            if sl.vurulabilir_mi() and sl.rect().colliderect(savur_rect):
                                solucan_hasar_uygula(sl, KILIC_HASAR, sl.x-oyuncu.x, -1)
                elif hex_modu:
                    # Sol tık (basılı tut): yavaş ama güçlü mor büyü mermisi
                    if oyuncu.hex_buyu_bekleme <= 0:
                        oyuncu.hex_buyu_bekleme = HEX_BUYU_BEKLEME
                        ex, ey = oyuncu.kilic_el_konumu()
                        dx, dy = fare_x - ex, fare_y - ey
                        uzunluk = math.hypot(dx, dy) or 1
                        mermi_listesi.append(Mermi(ex, ey, dx/uzunluk*HEX_BUYU_HIZI, dy/uzunluk*HEX_BUYU_HIZI,
                                                    MOR, HEX_BUYU_HASAR, True))
                        snd_buyu()
                elif raptor_modu:
                    # Sol tık (basılı tut): hızlı pençe darbesi
                    if oyuncu.raptor_pence_bekleme <= 0:
                        pence_hasar = int(RAPTOR_PENCE_HASAR * (RAPTOR_ULTI_PENCE_CARPAN if oyuncu.raptor_ulti_aktif else 1) * (RAPTOR_OFKE_CARPAN if oyuncu.raptor_ofke_aktif else 1))
                        pence_rect = oyuncu.kilic_savur_rect(fare_x, fare_y)
                        oyuncu.raptor_pence_bekleme = RAPTOR_PENCE_BEKLEME
                        oyuncu.raptor_pence_goster = 6
                        snd_pence()
                        for d in dusman_listesi[:]:
                            if d.tip == 'hayalet' and d.hayalet_mod:
                                continue
                            if d.rect().colliderect(pence_rect):
                                if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                                    parca_listesi.extend(patlama(pence_rect.centerx, pence_rect.centery, CYAN, 5))
                                    continue
                                d.can -= pence_hasar
                                if oyuncu.raptor_zehir_aktif:
                                    d.zehir_kare = RAPTOR_ZEHIR_DUSMAN_SURESI
                                    d.zehir_tik = RAPTOR_ZEHIR_TIK
                                yasam_kazanc = pence_hasar * RAPTOR_PENCE_YASAM_CALMA
                                oyuncu.can = min(oyuncu.max_can, oyuncu.can + yasam_kazanc)
                                hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, yasam_kazanc, YESIL, 0, -1, art=True))
                                hasar_yazisi_listesi.append(HasarYazisi(d.x+d.w/2, d.y+d.h/2, pence_hasar, (220,220,220), d.x-oyuncu.x, d.y-oyuncu.y))
                                parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, YESIL, 8))
                                if d.can <= 0:
                                    parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (245,166,35), 14))
                                    skor += d.para
                                    oyuncu.ulti_sarj_ekle()
                                    oyuncu.reaper_ruh_ekle()
                                    snd_olum()
                                    dusman_listesi.remove(d)
                        for sl in solucan_listesi[:]:
                            if sl.vurulabilir_mi() and sl.rect().colliderect(pence_rect):
                                yasam_kazanc2 = pence_hasar * RAPTOR_PENCE_YASAM_CALMA
                                oyuncu.can = min(oyuncu.max_can, oyuncu.can + yasam_kazanc2)
                                hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, yasam_kazanc2, YESIL, 0, -1, art=True))
                                solucan_hasar_uygula(sl, pence_hasar, sl.x-oyuncu.x, -1)
                elif wraith_modu:
                    # Sol tık (basılı tut): yavaş giden ruh cismi — hasar + yaşam çalma + ruh şarjı
                    if oyuncu.wraith_ruh_bekleme <= 0:
                        oyuncu.wraith_ruh_bekleme = WRAITH_RUH_BEKLEME
                        ex, ey = oyuncu.kilic_el_konumu()
                        dx, dy = fare_x - ex, fare_y - ey
                        uzunluk = math.hypot(dx, dy) or 1
                        ruh_hasar = WRAITH_RUH_HASAR * ((WRAITH_HAYALET_HASAR_ARTIS_CARPAN if oyuncu.wraith_hayalet_hasar_artis_acik else WRAITH_HAYALET_YARI_CARPAN) if oyuncu.wraith_hayalet_aktif else 1)
                        m = Mermi(ex, ey, dx/uzunluk*WRAITH_RUH_HIZI, dy/uzunluk*WRAITH_RUH_HIZI,
                                  (150,220,210), ruh_hasar, True)
                        m.wraith_mermisi = True
                        mermi_listesi.append(m)
                        snd_ruh()
                elif reaper_modu:
                    # Sol tık (basılı tut): baktığı yöne doğru uzun, saçılan (koni) alan hasarı
                    if oyuncu.reaper_vurus_bekleme <= 0:
                        oyuncu.reaper_vurus_bekleme = REAPER_VURUS_BEKLEME
                        oyuncu.reaper_vurus_goster = 8
                        snd_koni()
                        merkez_x = oyuncu.x + oyuncu.w/2
                        merkez_y = oyuncu.y + oyuncu.h/2
                        hedef_aci = math.atan2(fare_y-merkez_y, fare_x-merkez_x)
                        for d in dusman_listesi[:]:
                            if d.tip == 'hayalet' and d.hayalet_mod:
                                continue
                            dm_x, dm_y = d.x+d.w/2, d.y+d.h/2
                            dx, dy = dm_x-merkez_x, dm_y-merkez_y
                            if math.hypot(dx, dy) > REAPER_VURUS_MENZIL:
                                continue
                            fark = (math.atan2(dy, dx) - hedef_aci + math.pi) % (2*math.pi) - math.pi
                            if abs(fark) > REAPER_VURUS_ACI:
                                continue
                            if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                                parca_listesi.extend(patlama(dm_x, dm_y, CYAN, 5))
                                continue
                            d.can -= REAPER_VURUS_HASAR
                            hasar_yazisi_listesi.append(HasarYazisi(dm_x, dm_y, REAPER_VURUS_HASAR, (220,220,220), dx, dy))
                            parca_listesi.extend(patlama(dm_x, dm_y, (200,25,30), 6))
                            parca_listesi.extend(patlama(dm_x, dm_y, (15,10,10), 4))
                            if d.can <= 0:
                                parca_listesi.extend(patlama(dm_x, dm_y, (245,166,35), 14))
                                skor += d.para
                                oyuncu.ulti_sarj_ekle()
                                oyuncu.reaper_ruh_ekle()
                                snd_olum()
                                dusman_listesi.remove(d)
                                if oyuncu.reaper_atis_iskelet_acik:
                                    iskelet_listesi.append(Iskelet(dm_x - 11, ZEMIN_Y - 34, guclu=False))
                        for sl in solucan_listesi[:]:
                            if not sl.vurulabilir_mi():
                                continue
                            dx, dy = sl.x-merkez_x, (ZEMIN_Y-sl.yukseklik/2)-merkez_y
                            if math.hypot(dx, dy) > REAPER_VURUS_MENZIL:
                                continue
                            fark = (math.atan2(dy, dx) - hedef_aci + math.pi) % (2*math.pi) - math.pi
                            if abs(fark) > REAPER_VURUS_ACI:
                                continue
                            solucan_hasar_uygula(sl, REAPER_VURUS_HASAR, dx, dy)
                elif ronin_modu:
                    if oyuncu.ronin_itis_bekleme <= 0:
                        oyuncu.ronin_itis_bekleme = RONIN_ITIS_BEKLEME
                        oyuncu.ronin_itis_goster = 8
                        oyuncu.ronin_itis_zirh = 14
                        snd_mizrak()
                        ronin_itis()
                else:
                    oyuncu.ates_et(fare_x, fare_y, mermi_listesi)

            onceki_ayak_y = oyuncu.y + oyuncu.h
            if overdrive_modu:
                oyuncu.overdrive_guncelle(tuslar)
            if ronin_modu:
                oyuncu.ronin_guncelle()
                if oyuncu.ronin_ulti_aktif and oyuncu.ronin_ulti_suresi % 6 == 0:
                    ronin_ulti_r = RONIN_ULTI_YARICAP * (2.0 if oyuncu.ronin_ulti_gelismis_acik else 1.0)
                    merkez_x, merkez_y = oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2
                    for d in dusman_listesi[:]:
                        if d.tip == 'hayalet' and d.hayalet_mod:
                            continue
                        if math.hypot((d.x+d.w/2)-merkez_x, (d.y+d.h/2)-merkez_y) > ronin_ulti_r:
                            continue
                        if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                            continue
                        d.can -= RONIN_ULTI_HASAR
                        parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (170,120,255), 4))
                        if d.can <= 0:
                            parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (245,166,35), 14))
                            skor += d.para
                            oyuncu.ulti_sarj_ekle()
                            oyuncu.reaper_ruh_ekle()
                            snd_olum()
                            dusman_listesi.remove(d)
                    for sl in solucan_listesi[:]:
                        if sl.vurulabilir_mi() and math.hypot(sl.x-merkez_x, (ZEMIN_Y-sl.yukseklik/2)-merkez_y) <= ronin_ulti_r:
                            solucan_hasar_uygula(sl, RONIN_ULTI_HASAR, sl.x-merkez_x, -1)
            if not (overdrive_modu and oyuncu.kanca_durum != 'yok'):
                oyuncu.hareket_et(tuslar, (fare_x, fare_y))
            oyuncu.kilic_guncelle()
            oyuncu.hex_kitap_guncelle()
            oyuncu.raptor_guncelle()
            oyuncu.wraith_guncelle()
            oyuncu.reaper_guncelle()

            # Platformlar (hareket + tek yönlü çarpışma)
            for p in aktif_platformlar:
                if 'hiz' in p:
                    p['x'] += p['hiz']
                    if p['x'] <= p['sol'] or p['x'] + p['w'] >= p['sag']:
                        p['hiz'] *= -1
                        p['x'] = max(p['sol'], min(p['sag'] - p['w'], p['x']))
            s_basili = tuslar[pygame.K_s] or tuslar[pygame.K_DOWN]
            if not s_basili and oyuncu.hiz_y >= 0:
                yeni_ayak_y = oyuncu.y + oyuncu.h
                for p in aktif_platformlar:
                    if oyuncu.x + oyuncu.w > p['x'] and oyuncu.x < p['x'] + p['w']:
                        if onceki_ayak_y <= p['y'] + 2 and yeni_ayak_y >= p['y']:
                            oyuncu.y = p['y'] - oyuncu.h
                            oyuncu.hiz_y = 0
                            oyuncu.yerde = True
                            break

            # Spawn
            if ayar.get('final'):
                # Boss savaşı boyunca normal düşmanlar sürekli gelsin
                if any(d.tip == 'finalboss' for d in dusman_listesi):
                    spawn_timer -= 1
                    destek_sayisi = sum(1 for d in dusman_listesi if d.tip != 'finalboss')
                    if spawn_timer <= 0 and destek_sayisi < 6:
                        tip = random.choice(['melee', 'ranged', 'drone', 'sniper'])
                        sx = GENISLIK + 50 if random.random() > 0.5 else -50
                        dusman_listesi.append(Dusman(sx, tip, bolum))
                        spawn_timer = max(70, 150 - bolum*2)
            elif spawn_idx < len(spawn_sira):
                spawn_timer -= 1
                if spawn_timer <= 0:
                    tip = spawn_sira[spawn_idx]
                    sx = GENISLIK + 50 if random.random() > 0.5 else -50
                    dusman_listesi.append(Dusman(sx, tip, bolum))
                    spawn_idx += 1
                    spawn_timer = max(40, 100 - bolum*2)

            # Mızraklı robot grubu — o levelde varsa, oluyor bitene kadar sırayla
            # bir sağdan bir soldan gelmeye devam eder (kalıcı, tekrar eden dalga)
            if mizrakli_aktif:
                if not any(d.tip == 'mizrakli' for d in dusman_listesi):
                    mizrakli_timer -= 1
                    if mizrakli_timer <= 0:
                        grup_yon = mizrakli_sonraki_yon
                        mizrakli_sonraki_yon *= -1
                        grup_sayisi = random.randint(MIZRAKLI_GRUP_MIN, MIZRAKLI_GRUP_MAX)
                        sx_baslangic = -60 if grup_yon == 1 else GENISLIK + 60
                        for k in range(grup_sayisi):
                            yd = Dusman(sx_baslangic - grup_yon * k * 46, 'mizrakli', bolum)
                            yd.hiz_x = grup_yon * MIZRAKLI_HIZ
                            yd.sinirsiz = True
                            dusman_listesi.append(yd)
                        mizrakli_timer = random.randint(260, 380)

            # Düşmanlar
            for d in dusman_listesi[:]:
                d.guncelle(oyuncu.x + oyuncu.w/2, oyuncu.y + oyuncu.h/2, zaman)

                # Mızraklı robot ekranın diğer ucundan çıkıp gitti — öldürülmeden sessizce temizlenir
                if d.tip == 'mizrakli' and (d.x < -400 or d.x > GENISLIK + 400):
                    dusman_listesi.remove(d)
                    continue

                # Zehir gibi vurus-disi (pasif) hasarlarla can bitmis olabilir — bir
                # oyuncu vurusuyla eslesmezse fark edilmeden "hayalet" kalmasin diye.
                if d.can <= 0:
                    parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (245,166,35), 14))
                    skor += d.para
                    oyuncu.ulti_sarj_ekle()
                    oyuncu.reaper_ruh_ekle()
                    dusman_listesi.remove(d)
                    continue

                dokunulmaz = (d.tip == 'hayalet' and d.hayalet_mod)

                # Melee temas
                if not dokunulmaz and d.tip in ['melee','shield'] and d.rect().colliderect(oyuncu.rect()) and oyuncu.hasar_timer <= 0:
                    yon_x = (oyuncu.x+oyuncu.w/2) - (d.x+d.w/2)
                    yon_y = (oyuncu.y+oyuncu.h/2) - (d.y+d.h/2)
                    kaybedilen = oyuncu.hasar_al(15)
                    if kaybedilen > 0:
                        hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2, kaybedilen, KIRMIZI, yon_x, yon_y))
                    oyuncu.hasar_timer = 55
                    snd_hasar()

                # Temas hasarı (diğerleri)
                if not dokunulmaz and d.tip not in ['melee','shield','suicide'] and d.rect().colliderect(oyuncu.rect()) and oyuncu.hasar_timer <= 0:
                    yon_x = (oyuncu.x+oyuncu.w/2) - (d.x+d.w/2)
                    yon_y = (oyuncu.y+oyuncu.h/2) - (d.y+d.h/2)
                    kaybedilen = oyuncu.hasar_al(10)
                    if kaybedilen > 0:
                        hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2, kaybedilen, KIRMIZI, yon_x, yon_y))
                    oyuncu.hasar_timer = 50
                    snd_hasar()

                # İntihar robotu patlaması
                if d.tip == 'suicide' and getattr(d, 'patlayacak', False):
                    merkez_x, merkez_y = d.x + d.w/2, d.y + d.h/2
                    oyuncu_merkez_x, oyuncu_merkez_y = oyuncu.x + oyuncu.w/2, oyuncu.y + oyuncu.h/2
                    if math.hypot(oyuncu_merkez_x - merkez_x, oyuncu_merkez_y - merkez_y) < PATLAMA_YARICAP and oyuncu.hasar_timer <= 0:
                        kaybedilen = oyuncu.hasar_al(28)
                        if kaybedilen > 0:
                            hasar_yazisi_listesi.append(HasarYazisi(oyuncu_merkez_x, oyuncu_merkez_y, kaybedilen, KIRMIZI, oyuncu_merkez_x-merkez_x, oyuncu_merkez_y-merkez_y))
                        oyuncu.hasar_timer = 55
                        snd_hasar()
                    parca_listesi.extend(patlama(merkez_x, merkez_y, TURUNCU, 20))
                    skor += d.para
                    oyuncu.ulti_sarj_ekle()
                    oyuncu.reaper_ruh_ekle()
                    snd_olum()
                    if d in dusman_listesi:
                        dusman_listesi.remove(d)
                    continue

                # Ateş et
                if d.atis_yapabilir():
                    yeni = d.mermi_olustur(oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2)
                    if wraith_modu and oyuncu.wraith_ulti_aktif:
                        # WRAITH ultisi: her mermi/büyü mavi bir ruha dönüşüp atanı takip eder
                        for m in yeni:
                            m.oyuncu_mermisi = True
                            m.renk = WRAITH_ULTI_RUH_RENGI
                            m.wraith_mermisi = True
                            m.homing = True
                            m.hedef_dusman = d
                    mermi_listesi.extend(yeni)
                    d.atis_sifirla()

            # Mermiler
            for m in mermi_listesi[:]:
                m.guncelle()
                if m.omur <= 0 or m.x < -20 or m.x > GENISLIK+20 or m.y < -20 or m.y > YUKSEKLIK+20:
                    mermi_listesi.remove(m)
                    continue

                if m.oyuncu_mermisi:
                    for d in dusman_listesi[:]:
                        if d.tip == 'hayalet' and d.hayalet_mod:
                            continue
                        if d.rect().colliderect(m.rect()):
                            if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                                parca_listesi.extend(patlama(m.x, m.y, CYAN, 5))
                                if m in mermi_listesi:
                                    mermi_listesi.remove(m)
                                break
                            d.can -= m.hasar
                            hasar_yazisi_listesi.append(HasarYazisi(m.x, m.y, m.hasar, (220,220,220), m.hiz_x, m.hiz_y))
                            parca_listesi.extend(patlama(m.x, m.y, (0,200,200), 6))
                            if getattr(m, 'wraith_mermisi', False):
                                yasam_kazanc3 = m.hasar * WRAITH_YASAM_CALMA_ORAN
                                oyuncu.can = min(oyuncu.max_can, oyuncu.can + yasam_kazanc3)
                                hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, yasam_kazanc3, YESIL, 0, -1, art=True))
                                oyuncu.wraith_ruh_ekle(WRAITH_RUH_SARJ_VURUS)
                            if m in mermi_listesi:
                                mermi_listesi.remove(m)
                            if d.can <= 0:
                                olum_x, olum_y = d.x+d.w/2, d.y+d.h/2
                                parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                                skor += d.para
                                oyuncu.ulti_sarj_ekle()
                                oyuncu.reaper_ruh_ekle()
                                if getattr(m, 'wraith_mermisi', False):
                                    oyuncu.wraith_ruh_ekle(WRAITH_RUH_SARJ_OLUM)
                                if overdrive_modu and oyuncu.overdrive_ulti_aktif:
                                    oyuncu.can = min(oyuncu.max_can, oyuncu.can + OVERDRIVE_ULTI_CAN_KAZANC)
                                snd_olum()
                                dusman_listesi.remove(d)
                            break
                    if m in mermi_listesi:
                        for sl in solucan_listesi[:]:
                            if not sl.vurulabilir_mi():
                                continue
                            if sl.rect().colliderect(m.rect()):
                                sl.can -= m.hasar
                                hasar_yazisi_listesi.append(HasarYazisi(m.x, m.y, m.hasar, (220,220,220), m.hiz_x, m.hiz_y))
                                parca_listesi.extend(patlama(m.x, m.y, (150,150,160), 6))
                                if getattr(m, 'wraith_mermisi', False):
                                    yasam_kazanc4 = m.hasar * WRAITH_YASAM_CALMA_ORAN
                                    oyuncu.can = min(oyuncu.max_can, oyuncu.can + yasam_kazanc4)
                                    hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, yasam_kazanc4, YESIL, 0, -1, art=True))
                                    oyuncu.wraith_ruh_ekle(WRAITH_RUH_SARJ_VURUS)
                                if m in mermi_listesi:
                                    mermi_listesi.remove(m)
                                if sl.can <= 0:
                                    parca_listesi.extend(patlama(sl.x, ZEMIN_Y-30, (245,166,35), 16))
                                    skor += sl.para
                                    oyuncu.ulti_sarj_ekle()
                                    oyuncu.reaper_ruh_ekle()
                                    if overdrive_modu and oyuncu.overdrive_ulti_aktif:
                                        oyuncu.can = min(oyuncu.max_can, oyuncu.can + OVERDRIVE_ULTI_CAN_KAZANC)
                                    snd_olum()
                                break
                else:
                    if m.rect().colliderect(oyuncu.rect()) and oyuncu.hasar_timer <= 0:
                        kaybedilen = oyuncu.hasar_al(m.hasar)
                        oyuncu.hasar_timer = 45
                        parca_listesi.extend(patlama(oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2, KIRMIZI, 8))
                        snd_hasar()
                        if kaybedilen > 0:
                            hasar_yazisi_listesi.append(HasarYazisi(m.x, m.y, kaybedilen, KIRMIZI, m.hiz_x, m.hiz_y))
                        if m in mermi_listesi:
                            mermi_listesi.remove(m)

            # İskeletler (REAPER müttefikleri)
            if reaper_modu:
                for isk in iskelet_listesi[:]:
                    isk.guncelle(dusman_listesi, aktif_platformlar)

                    for d in dusman_listesi[:]:
                        if d.tip == 'hayalet' and d.hayalet_mod:
                            continue
                        if isk.okcu:
                            mesafe_isk = math.hypot((d.x+d.w/2)-(isk.x+isk.w/2), (d.y+d.h/2)-(isk.y+isk.h/2))
                            if mesafe_isk > REAPER_ISKELET_OKCU_MENZIL:
                                continue
                        elif not d.rect().colliderect(isk.rect()):
                            continue
                        isk_hasar = isk.hasar * (REAPER_GUC_CARPAN if isk.guc_suresi > 0 else 1)
                        if isk.atis_bekleme <= 0:
                            isk.atis_bekleme = REAPER_ISKELET_ATIS_BEKLEME
                            if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                                parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, CYAN, 5))
                            else:
                                d.can -= isk_hasar
                                hasar_yazisi_listesi.append(HasarYazisi(d.x+d.w/2, d.y+d.h/2, isk_hasar, (220,220,220), d.x-isk.x, d.y-isk.y))
                                parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (70,120,220) if isk.okcu else (205,45,40), 6))
                                if d.can <= 0:
                                    parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (245,166,35), 14))
                                    skor += d.para
                                    oyuncu.ulti_sarj_ekle()
                                    oyuncu.reaper_ruh_ekle()
                                    snd_olum()
                                    dusman_listesi.remove(d)
                        if not isk.okcu:
                            isk.can -= 1  # düşman temasında sürekli hafif hasar (okçu temas etmez)
                            if d.tip != 'suicide':
                                snd_hasar()

                    if isk.can <= 0:
                        can_once_isk = oyuncu.can
                        oyuncu.can = min(oyuncu.max_can, oyuncu.can + 10)
                        kazanc_isk = oyuncu.can - can_once_isk
                        if kazanc_isk > 0:
                            hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, kazanc_isk, YESIL, 0, -1, art=True))
                        iskelet_listesi.remove(isk)

            # Kılıç (AEGIS)
            if oyuncu.kilic_durum in ('giden', 'donuyor'):
                kilic_r = oyuncu.kilic_rect()
                for d in dusman_listesi[:]:
                    if d in oyuncu.kilic_vurulanlar:
                        continue
                    if d.tip == 'hayalet' and d.hayalet_mod:
                        continue
                    if d.rect().colliderect(kilic_r):
                        oyuncu.kilic_vurulanlar.append(d)
                        if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                            parca_listesi.extend(patlama(oyuncu.kilic_x, oyuncu.kilic_y, CYAN, 5))
                            continue
                        d.can -= KILIC_HASAR
                        hasar_yazisi_listesi.append(HasarYazisi(oyuncu.kilic_x, oyuncu.kilic_y, KILIC_HASAR, (220,220,220), oyuncu.kilic_hiz_x, oyuncu.kilic_hiz_y))
                        parca_listesi.extend(patlama(oyuncu.kilic_x, oyuncu.kilic_y, (0,200,200), 8))
                        if d.can <= 0:
                            parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (245,166,35), 14))
                            skor += d.para
                            oyuncu.ulti_sarj_ekle()
                            oyuncu.reaper_ruh_ekle()
                            snd_olum()
                            dusman_listesi.remove(d)
                for sl in solucan_listesi[:]:
                    if sl in oyuncu.kilic_vurulanlar or not sl.vurulabilir_mi():
                        continue
                    if sl.rect().colliderect(kilic_r):
                        oyuncu.kilic_vurulanlar.append(sl)
                        solucan_hasar_uygula(sl, KILIC_HASAR, oyuncu.kilic_hiz_x, oyuncu.kilic_hiz_y)

            # SEKEN KILIÇ: kılıç saplandığı yerden, uzaklık fark etmeden 5 düşmana kadar aninda seker
            if (oyuncu.kilic_durum == 'sapli' and oyuncu.aegis_kilic_sekme_acik
                    and not oyuncu.kilic_sekme_yapildi):
                oyuncu.kilic_sekme_yapildi = True
                sekme_hedefler = [d for d in dusman_listesi
                                   if not (d.tip == 'hayalet' and d.hayalet_mod)][:AEGIS_KILIC_SEKME_MAKS]
                for d in sekme_hedefler:
                    dm_x, dm_y = d.x+d.w/2, d.y+d.h/2
                    parca_listesi.extend(patlama(oyuncu.kilic_x, oyuncu.kilic_y, (0,200,200), 4))
                    parca_listesi.extend(patlama(dm_x, dm_y, (0,200,200), 8))
                    if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                        continue
                    d.can -= KILIC_HASAR
                    hasar_yazisi_listesi.append(HasarYazisi(dm_x, dm_y, KILIC_HASAR, (220,220,220), dm_x-oyuncu.kilic_x, dm_y-oyuncu.kilic_y))
                    if d.can <= 0:
                        parca_listesi.extend(patlama(dm_x, dm_y, (245,166,35), 14))
                        skor += d.para
                        oyuncu.ulti_sarj_ekle()
                        oyuncu.reaper_ruh_ekle()
                        snd_olum()
                        dusman_listesi.remove(d)
                if sekme_hedefler:
                    snd_kilic()
                oyuncu.kilic_durum = 'donuyor'
                oyuncu.kilic_vurulanlar = []

            # Hamle (RAPTOR dash) çarpışmaları
            if oyuncu.raptor_dash_aktif:
                for d in dusman_listesi[:]:
                    if d in oyuncu.raptor_dash_vurulanlar:
                        continue
                    if d.tip == 'hayalet' and d.hayalet_mod:
                        continue
                    if d.rect().colliderect(oyuncu.rect()):
                        oyuncu.raptor_dash_vurulanlar.append(d)
                        if d.tip == 'finalboss' and getattr(d, 'kalkanli', False):
                            parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, CYAN, 5))
                            continue
                        dash_hasar = RAPTOR_DASH_HASAR * (RAPTOR_OFKE_CARPAN if oyuncu.raptor_ofke_aktif else 1)
                        d.can -= dash_hasar
                        if oyuncu.raptor_zehir_aktif:
                            d.zehir_kare = RAPTOR_ZEHIR_DUSMAN_SURESI
                            d.zehir_tik = RAPTOR_ZEHIR_TIK
                        hasar_yazisi_listesi.append(HasarYazisi(d.x+d.w/2, d.y+d.h/2, dash_hasar, (220,220,220), oyuncu.raptor_dash_yon, 0))
                        parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, YESIL, 10))
                        if d.can <= 0:
                            parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (245,166,35), 14))
                            skor += d.para
                            oyuncu.ulti_sarj_ekle()
                            oyuncu.reaper_ruh_ekle()
                            snd_olum()
                            dusman_listesi.remove(d)
                for sl in solucan_listesi[:]:
                    if sl in oyuncu.raptor_dash_vurulanlar or not sl.vurulabilir_mi():
                        continue
                    if sl.rect().colliderect(oyuncu.rect()):
                        oyuncu.raptor_dash_vurulanlar.append(sl)
                        solucan_hasar_uygula(sl, RAPTOR_DASH_HASAR, oyuncu.raptor_dash_yon, 0)

            # Enkaz Yağmuru (Uzay İstasyonu + Harabe)
            if tema_bolum > 10:
                enkaz_timer -= 1
                if enkaz_timer <= 0:
                    enkaz_listesi.append(Enkaz(random.randint(30, GENISLIK-30), buyuk=(tema_bolum > 20)))
                    enkaz_timer = random.randint(150, 250)
            for ek in enkaz_listesi[:]:
                ek.guncelle()
                if ek.bitti_mi():
                    enkaz_listesi.remove(ek)
                    continue
                if ek.dusuyor and ek.rect().colliderect(oyuncu.rect()) and oyuncu.hasar_timer <= 0:
                    kaybedilen = oyuncu.hasar_al(ek.hasar)
                    oyuncu.hasar_timer = 45
                    parca_listesi.extend(patlama(ek.x, ek.y, (140,90,70), 10))
                    snd_hasar()
                    if kaybedilen > 0:
                        hasar_yazisi_listesi.append(HasarYazisi(ek.x, ek.y, kaybedilen, KIRMIZI, 0, -1))
                    enkaz_listesi.remove(ek)

            # Solucan (yerden çıkıp oyuncunun gittiği yönü kesen tuzak — öldürülene kadar can'ı kalıcı, tekrar tekrar çıkar)
            if oyuncu.hiz_x != 0:
                son_hareket_yonu = 1 if oyuncu.hiz_x > 0 else -1
            if not solucan_olduruldu:
                solucan_timer -= 1
                if solucan_timer <= 0 and not solucan_listesi:
                    hedef_x = oyuncu.x + oyuncu.w/2 + son_hareket_yonu * SOLUCAN_ONDEN_MESAFE
                    hedef_x = max(40, min(GENISLIK-40, hedef_x))
                    yeni_solucan = Solucan(hedef_x)
                    yeni_solucan.can = solucan_can_kalan
                    yeni_solucan.max_can = SOLUCAN_CAN
                    solucan_listesi.append(yeni_solucan)
                    solucan_timer = random.randint(SOLUCAN_ARALIK_MIN, SOLUCAN_ARALIK_MAX)
            for sl in solucan_listesi[:]:
                sl.guncelle()
                if sl.bitti_mi():
                    solucan_can_kalan = sl.can
                    if sl.can <= 0:
                        solucan_olduruldu = True
                    solucan_listesi.remove(sl)
                    continue
                if sl.tehlikeli_mi() and sl.rect().colliderect(oyuncu.rect()) and oyuncu.hasar_timer <= 0:
                    kaybedilen = oyuncu.hasar_al(sl.hasar)
                    oyuncu.hasar_timer = 55
                    parca_listesi.extend(patlama(sl.x, ZEMIN_Y-20, (95,72,42), 12))
                    snd_hasar()
                    if kaybedilen > 0:
                        hasar_yazisi_listesi.append(HasarYazisi(sl.x, ZEMIN_Y-40, kaybedilen, KIRMIZI, 0, -1))

            # Parçacık
            for pc in parca_listesi[:]:
                pc.guncelle()
                if pc.omur <= 0:
                    parca_listesi.remove(pc)

            # Hasar yazısı
            for hy in hasar_yazisi_listesi[:]:
                hy.guncelle()
                if hy.omur <= 0:
                    hasar_yazisi_listesi.remove(hy)

            # Ölüm
            oyuncu.can = max(0, min(oyuncu.max_can, oyuncu.can))
            if overdrive_modu and oyuncu.overdrive_olumsuzluk_kalan > 0 and oyuncu.can <= 0:
                oyuncu.can = 1  # OVERDRIVE ustalığı: ulti + 3 sn ölümsüzlük
            if TEST_MODU:
                if oyuncu.can <= 0:
                    oyuncu.can = 1  # TEST: hasar alalım ama ölmeyelim
            elif oyuncu.can <= 0:
                snd_karakter_olum()
                return ('kaybettin', skor, para)  # Öldün ekranı gösterilsin

            # Bölüm bitti mi?  (solucan öldürülmeden bölüm bitmez)
            # Mizrakli robotlar surekli gidip gelen ayri bir tehlike — sayima dahil
            # edilmezler, yoksa "kalan dusman" ekrana girip cikislarina gore titrer.
            kalan = len([d for d in dusman_listesi if d.tip != 'mizrakli']) + (len(spawn_sira) - spawn_idx)
            if ayar.get('final'):
                if not bolum_bitti and not any(d.tip == 'finalboss' for d in dusman_listesi) and solucan_olduruldu:
                    bolum_bitti = True
                    snd_bolum_tamam()
                    if any(k['acilis_bolum'] == bolum and k['acilis_bolum'] > 1 for k in KAHRAMANLAR):
                        snd_kahraman_acildi()
            elif kalan <= 0 and not bolum_bitti and solucan_olduruldu:
                bolum_bitti = True
                snd_bolum_tamam()
                if any(k['acilis_bolum'] == bolum and k['acilis_bolum'] > 1 for k in KAHRAMANLAR):
                    snd_kahraman_acildi()

            # ── ÇİZİM ──
            fon_ciz(ekran, oyuncu.x, tema_bolum)
            platform_renk = (60,60,80) if tema_bolum <= 10 else (40,25,70)
            for p in aktif_platformlar:
                platform_ciz(ekran, p, platform_renk)
            hud_ciz(ekran, oyuncu, skor, para, bolum, kalan, aegis_modu, hex_modu, raptor_modu, wraith_modu, reaper_modu, overdrive_modu, ronin_modu)
            if not bolum_bitti:
                durdur_uzerinde = durdur_buton_rect.collidepoint(fare_x, fare_y)
                pygame.draw.rect(ekran, (20,45,40) if durdur_uzerinde else (10,10,18), durdur_buton_rect)
                pygame.draw.rect(ekran, (0,255,200) if durdur_uzerinde else CYAN, durdur_buton_rect, 2)
                pygame.draw.rect(ekran, BEYAZ, (durdur_buton_rect.x+7, durdur_buton_rect.y+6, 4, 14))
                pygame.draw.rect(ekran, BEYAZ, (durdur_buton_rect.x+15, durdur_buton_rect.y+6, 4, 14))

            for ek in enkaz_listesi:
                ek.ciz(ekran)
            for sl in solucan_listesi:
                sl.ciz(ekran)
            for pc in parca_listesi:
                pc.ciz(ekran)
            for isk in iskelet_listesi:
                isk.ciz(ekran)
            for d in dusman_listesi:
                d.ciz(ekran, zaman)
            for m in mermi_listesi:
                m.ciz(ekran)
            oyuncu.ciz(ekran, fare_x, fare_y, aegis_modu, hex_modu, raptor_modu, wraith_modu, reaper_modu, overdrive_modu, ronin_modu)
            for hy in hasar_yazisi_listesi:
                hy.ciz(ekran)

            # Nişan
            nisangah_ciz(ekran, fare_x, fare_y)

            # Bölüm bitti paneli
            if bolum_bitti:
                panel = pygame.Surface((500, 140), pygame.SRCALPHA)
                panel.fill((0,0,0,200))
                ekran.blit(panel, (GENISLIK//2-250, 60))
                pygame.draw.rect(ekran, CYAN, (GENISLIK//2-250, 60, 500, 140), 2)
                bt = fnt_or.render(t('bolum_tamam', bolum=bolum), True, TURUNCU)
                ekran.blit(bt, (GENISLIK//2 - bt.get_width()//2, 78))
                bt3 = fnt_kk.render(t('para_skor', para=para, skor=skor), True, BEYAZ)
                ekran.blit(bt3, (GENISLIK//2 - bt3.get_width()//2, 118))
                buton_ciz(ekran, geri_buton_rect, t('geri'), (fare_x, fare_y))
                buton_ciz(ekran, devam_buton_rect, t('devam_et'), (fare_x, fare_y))

                yeni_kahraman = next((k for k in KAHRAMANLAR if k['acilis_bolum'] == bolum and k['acilis_bolum'] > 1), None)
                if yeni_kahraman:
                    ak_w, ak_h = 460, 160
                    ak_x, ak_y = GENISLIK//2 - ak_w//2, 210
                    ak_panel = pygame.Surface((ak_w, ak_h), pygame.SRCALPHA)
                    ak_panel.fill((0,0,0,225))
                    ekran.blit(ak_panel, (ak_x, ak_y))
                    pygame.draw.rect(ekran, yeni_kahraman['renk'], (ak_x, ak_y, ak_w, ak_h), 3)
                    gorsel_k = KAHRAMAN_KART_GORSELLERI.get(yeni_kahraman['id'])
                    if gorsel_k:
                        kucuk = pygame.transform.smoothscale(gorsel_k, (120, 120))
                        ekran.blit(kucuk, (ak_x+16, ak_y+ak_h//2-60))
                    ak_baslik = fnt_or.render(t('yeni_kahraman_acildi'), True, yeni_kahraman['renk'])
                    ekran.blit(ak_baslik, (ak_x+156, ak_y+28))
                    ak_isim = fnt_by.render(yeni_kahraman['isim'], True, BEYAZ)
                    ekran.blit(ak_isim, (ak_x+156, ak_y+60))
                    ak_alt = fnt_kk.render(t('kahraman_secilebilir'), True, (180,180,180))
                    ekran.blit(ak_alt, (ak_x+156, ak_y+112))

            if AYAR_MOBIL_KONTROL:
                mobil_kontrol.ciz(ekran)
            basarim_bildirim_guncelle_ciz(ekran)

            pygame.display.flip()
            await asyncio.sleep(0)

            if bolum > 30:
                return ('kazandin', skor, para)

    return ('kazandin', skor, para)


# ══════════════════════════════════════════
#  HAYATTA KAL (SURVIVOR) MODU — tüm kahramanlar oynanabilir
#  (kahramana özel güçler henüz yok, ortak kılıç-savurma saldırısı kullanılıyor)
# ══════════════════════════════════════════
YUKSELTME_HAVUZU = [
    ('hasar',   '+%20 HASAR',    'Saldırı hasarı artar',     (255,90,60)),
    ('hiz',     '+%15 HIZ',      'Hareket hızı artar',       (0,255,200)),
    ('can',     '+25 CAN',       'Maksimum can artar',       (0,255,100)),
    ('saldiri', '-%15 BEKLEME',  'Saldırı hızı artar',       SARI),
    ('regen',   'CAN YENILEME',  'Sürekli can yeniler',      (150,230,220)),
]

# Kahramana özel HAYATTA KAL kartları — genel havuza eklenir, karaktere göre farklılaşır
KAHRAMAN_KART_HAVUZU = {
    0: [('aegis_kalkan',  'KORUYUCU KALKAN', '5 sn hasarsız kalınca kalkan biriktirirsin',      (120,220,255)),
        ('aegis_menzil',  'UZUN KILIÇ',      'Kılıç savurma menzili +%35 artar',                (0,200,200))],
    1: [('raptor_zehir',  'ZEHIRLI PENCE',   'Vurduğun her düşman kalıcı olarak zehirlenir',    (60,220,90)),
        ('raptor_hamle',  'SINIRSIZ HAMLE',  'Hamle (dash) bekleme süresi kalkar',              (150,255,170))],
    6: [('hex_kitap',     'USTA KITAPLIK',   'Azami kitap sayısı artar, ışın kalınlaşır',       MOR),
        ('hex_can',       'BUYULU OZDIRENC', '+50 Can',                                          (200,120,255))],
    7: [('wraith_hasar',  'HAYALET AVCISI',  'Hayaletken hasar penaltısı kalkar, +%30 hasar',   (150,220,210)),
        ('wraith_ruhbagi','RUH BAGI',        'Kazandığın her ruh anında can da verir',          (100,230,220))],
    8: [('reaper_zirh',   'KARANLIK ZIRH',   '+30 Can',                                          (210,200,180)),
        ('reaper_emici',  'RUH EMICI',       'Vurduğun düşmanlardan can çalarsın',              (150,25,28))],
}

def kart_zaten_acik(oyuncu, kod):
    if kod == 'raptor_zehir':
        return oyuncu.raptor_zehir_aktif
    if kod == 'raptor_hamle':
        return oyuncu.raptor_dash_sinirsiz_acik
    if kod == 'hex_kitap':
        return oyuncu.hex_kitap_max_ozel >= HEX_KITAP_MAX_USTA
    if kod == 'wraith_hasar':
        return oyuncu.wraith_hayalet_hasar_artis_acik
    if kod == 'wraith_ruhbagi':
        return oyuncu.wraith_ruh_heal_acik
    if kod == 'aegis_kalkan':
        return oyuncu.aegis_pasif_kalkan_acik
    if kod == 'reaper_emici':
        return oyuncu.reaper_emici_acik
    return False


async def hayatta_kal_modu(ekran):
    muzik_calistir(None)  # savaş sırasında müzik çalmasın — oyuncu odaklansın
    pygame.mouse.set_visible(not AYAR_IMLEC_GIZLI)
    mobil_kontrol = MobilKontrol()
    DUNYA_GENISLIK = 2700  # harita ekranın 3 katı genişliğinde, sınırlı (sonsuz değil)

    aegis_modu = (secili_kahraman == 0)
    hex_modu = (secili_kahraman == 6)
    raptor_modu = (secili_kahraman == 1)
    wraith_modu = (secili_kahraman == 7)
    reaper_modu = (secili_kahraman == 8)
    overdrive_modu = (secili_kahraman == 5)
    ronin_modu = (secili_kahraman == 9)

    oyuncu = Oyuncu()
    oyuncu.x = GENISLIK / 2
    oyuncu.y = ZEMIN_Y - oyuncu.h
    if hex_modu:
        oyuncu.max_can = HEX_MAX_CAN
        oyuncu.can = HEX_MAX_CAN
        oyuncu.daima_ucar = True
    if raptor_modu:
        oyuncu.raptor_hizli = True
    if wraith_modu:
        oyuncu.max_can = WRAITH_MAX_CAN
        oyuncu.can = WRAITH_MAX_CAN
        oyuncu.daima_ucar = True
        oyuncu.wraith_yavas = True
    if reaper_modu:
        oyuncu.max_can = REAPER_MAX_CAN
        oyuncu.can = REAPER_MAX_CAN
        oyuncu.w, oyuncu.h = REAPER_W, REAPER_H
        oyuncu.reaper_agir = True
    if overdrive_modu:
        oyuncu.max_can = OVERDRIVE_MAX_CAN
        oyuncu.can = OVERDRIVE_MAX_CAN
        oyuncu.overdrive_sinirsiz_mermi = True
        oyuncu.overdrive_sallanma_acik = KAHRAMAN_HASAR.get(5, 0.0) >= OVERDRIVE_SALLANMA_ESIGI
    if ronin_modu:
        oyuncu.max_can = RONIN_MAX_CAN
        oyuncu.can = RONIN_MAX_CAN
    ustalik_uygula(oyuncu, secili_kahraman)
    genel_yukseltme_uygula(oyuncu)
    dunya_x = DUNYA_GENISLIK / 2
    kamera_x = max(0, min(DUNYA_GENISLIK - GENISLIK, dunya_x - GENISLIK/2))
    toplam_mesafe = dunya_x

    dusman_listesi = []
    mermi_listesi = []
    parca_listesi = []
    hasar_yazisi_listesi = []
    xp_listesi = []
    mizrakli_sonraki_yon = random.choice([1, -1])
    can_topu_listesi = []
    iskelet_listesi = []
    oldurulen_onceki = 0

    oyuncu_hasar_carpan = 1.0
    oyuncu_saldiri_carpan = 1.0

    seviye = 1
    xp_dolu = 0
    xp_gerekli = SURVIVOR_XP_BASE
    oldurulen = 0
    gecen_kare = 0
    spawn_timer = 60

    # Her 10 sanal bölümde bir mini-boss ('boss' tipi) çıkar.
    # TEST_MODU'da hızlı test edebilmek için eşik küçültülür (ilk bölümde hemen dener).
    minibos_esik_kare = 300 if TEST_MODU else SURVIVOR_ZORLUK_ARALIK * 10
    sonraki_minibos_kare = minibos_esik_kare

    kart_bekleniyor = False
    kart_secenekleri = []
    kart_rectleri = []
    fare_basili = False

    durduruldu = False
    duraklama_goruntusu = None
    durdur_buton_rect = pygame.Rect(GENISLIK - 34, 8, 26, 26)
    pause_devam_rect = pygame.Rect(GENISLIK//2 - 110, YUKSEKLIK//2 - 10, 220, 46)
    pause_menu_rect = pygame.Rect(GENISLIK//2 - 110, YUKSEKLIK//2 + 50, 220, 46)

    def ronin_itis():
        nonlocal oldurulen
        merkez_x = oyuncu.x + oyuncu.w/2
        merkez_y = oyuncu.y + oyuncu.h/2
        hedef_aci = math.atan2(fare_y-merkez_y, fare_x-merkez_x)
        carpan = oyuncu.ronin_hasar_carpani() * oyuncu_hasar_carpan
        for d in dusman_listesi[:]:
            if d.tip == 'hayalet' and d.hayalet_mod:
                continue
            dm_x, dm_y = d.x+d.w/2, d.y+d.h/2
            dx, dy = dm_x-merkez_x, dm_y-merkez_y
            if math.hypot(dx, dy) > RONIN_ITIS_MENZIL * oyuncu.ronin_menzil_carpan:
                continue
            fark_a = (math.atan2(dy, dx) - hedef_aci + math.pi) % (2*math.pi) - math.pi
            if abs(fark_a) > RONIN_ITIS_ACI:
                continue
            hasar = RONIN_ITIS_HASAR * carpan
            d.can -= hasar
            if oyuncu.ronin_gizli_aktif and oyuncu.ronin_gizli_sersem_acik:
                d.dondu_kare = 300
            hasar_yazisi_listesi.append(HasarYazisi(dm_x, dm_y, hasar, (220,220,220), dx, dy))
            parca_listesi.extend(patlama(dm_x, dm_y, (170,120,255), 7))
            if d.can <= 0:
                olum_x, olum_y = dm_x, dm_y
                parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                for _ in range(random.randint(1, 3)):
                    xp_listesi.append(Xp(olum_x, olum_y))
                if random.random() < 0.12:
                    can_topu_listesi.append(CanTopu(olum_x, olum_y))
                oldurulen += 1
                snd_olum()
                dusman_listesi.remove(d)

    def ronin_firlat():
        nonlocal oldurulen, dunya_x
        oyuncu.ronin_firlat_bekleme = max(6, int(RONIN_FIRLAT_BEKLEME * oyuncu_saldiri_carpan))
        oyuncu.ronin_firlat_goster = 10
        snd_mizrak()
        ex, ey = oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2
        dx, dy = fare_x-ex, fare_y-ey
        uzunluk = math.hypot(dx, dy) or 1
        ux, uy = dx/uzunluk, dy/uzunluk
        carpan = oyuncu.ronin_hasar_carpani() * oyuncu_hasar_carpan
        vurulanlar = []
        mesafe = 0
        son_x, son_y = ex, ey
        while mesafe < RONIN_FIRLAT_MENZIL * oyuncu.ronin_menzil_carpan:
            mesafe += 14
            nx, ny = ex+ux*mesafe, ey+uy*mesafe
            if nx < -20 or nx > GENISLIK+20:
                break
            son_x, son_y = nx, ny
            for d in dusman_listesi[:]:
                if d in vurulanlar or (d.tip == 'hayalet' and d.hayalet_mod):
                    continue
                if d.rect().collidepoint(nx, ny):
                    vurulanlar.append(d)
                    hasar = RONIN_FIRLAT_HASAR * carpan
                    d.can -= hasar
                    if oyuncu.ronin_gizli_aktif and oyuncu.ronin_gizli_sersem_acik:
                        d.dondu_kare = 300
                    hasar_yazisi_listesi.append(HasarYazisi(nx, ny, hasar, (220,220,220), ux, uy))
                    parca_listesi.extend(patlama(nx, ny, (170,120,255), 6))
                    if d.can <= 0:
                        parca_listesi.extend(patlama(nx, ny, (245,166,35), 14))
                        for _ in range(random.randint(1, 3)):
                            xp_listesi.append(Xp(nx, ny))
                        if random.random() < 0.12:
                            can_topu_listesi.append(CanTopu(nx, ny))
                        oldurulen += 1
                        snd_olum()
                        dusman_listesi.remove(d)
        # Ekran hep ortalı kalsın diye: oyuncu.x'i degistirmek yerine, ilerledigi
        # mesafeyi dunya_x'e ekleyip kamerayi kaydiriyoruz — bir sonraki karede
        # tum sahne (dusmanlar dahil) oyuncuyu tekrar merkeze alacak sekilde kayar.
        dunya_x = max(0, min(DUNYA_GENISLIK, dunya_x + (son_x - ex)))
        oyuncu.y = max(46, min(ZEMIN_Y-oyuncu.h, son_y - oyuncu.h/2))
        oyuncu.hiz_x = 0
        oyuncu.hiz_y = 0
        parca_listesi.extend(patlama(son_x, son_y, (170,120,255), 10))
        snd_zipla()

    def overdrive_kanca_baglan(hx, hy):
        ex2, ey2 = oyuncu.x + oyuncu.w/2, oyuncu.y + oyuncu.h/2
        oyuncu.kanca_x, oyuncu.kanca_y = hx, hy
        oyuncu.kanca_ip_uzunlugu = max(30, math.hypot(ex2-hx, ey2-hy))
        oyuncu.kanca_aci = math.atan2(ey2-hy, ex2-hx)
        oyuncu.kanca_acisal_hiz = 0.0
        oyuncu.kanca_durum = 'sallaniyor'
        oyuncu.kanca_bekleme = OVERDRIVE_KANCA_BEKLEME
        snd_zipla()

    def overdrive_kanca_direk_git(hx, hy):
        oyuncu.kanca_x, oyuncu.kanca_y = hx, hy
        oyuncu.kanca_ucus_hedef_x = max(0, min(GENISLIK - oyuncu.w, hx - oyuncu.w/2))
        oyuncu.kanca_ucus_hedef_y = max(46, min(ZEMIN_Y - oyuncu.h, hy - oyuncu.h))
        oyuncu.kanca_durum = 'ucuyor'
        oyuncu.kanca_bekleme = OVERDRIVE_KANCA_BEKLEME
        snd_zipla()

    def overdrive_kanca_at(hedef_x, hedef_y):
        if oyuncu.overdrive_kanca_heal_acik:
            can_once_ok = oyuncu.can
            oyuncu.can = min(oyuncu.max_can, oyuncu.can + 10)
            kazanc_ok = oyuncu.can - can_once_ok
            if kazanc_ok > 0:
                hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, kazanc_ok, YESIL, 0, -1, art=True))
        ex, ey = oyuncu.x + oyuncu.w/2, oyuncu.y + oyuncu.h/2
        dx, dy = hedef_x - ex, hedef_y - ey
        uzunluk = math.hypot(dx, dy) or 1
        ux, uy = dx/uzunluk, dy/uzunluk
        mesafe = 0
        while mesafe < OVERDRIVE_KANCA_MENZIL:
            mesafe += 12
            nx, ny = ex + ux*mesafe, ey + uy*mesafe
            for d in dusman_listesi:
                if d.rect().collidepoint(nx, ny):
                    d.cekim_kare = 24
                    d.cekim_hedef_x = ex + ux*40
                    d.cekim_hedef_y = ey + uy*40
                    parca_listesi.extend(patlama(nx, ny, SARI, 8))
                    oyuncu.kanca_bekleme = OVERDRIVE_KANCA_BEKLEME
                    snd_zipla()
                    return
            if nx <= 0 or nx >= GENISLIK:
                hx = max(4, min(GENISLIK-4, nx))
                if oyuncu.overdrive_sallanma_acik:
                    overdrive_kanca_baglan(hx, ny)
                else:
                    overdrive_kanca_direk_git(hx, ny)
                return
            if ny <= 66:
                if oyuncu.overdrive_sallanma_acik:
                    overdrive_kanca_baglan(nx, 70)
                else:
                    overdrive_kanca_direk_git(nx, 70)
                return
            if ny >= ZEMIN_Y - 2:
                overdrive_kanca_direk_git(nx, ZEMIN_Y - 10)
                return
        oyuncu.kanca_bekleme = OVERDRIVE_KANCA_BEKLEME  # boşluğa attı — işe yaramadı, geri çekildi

    while True:
        saat.tick(FPS)
        zaman = pygame.time.get_ticks()

        for olay in pygame.event.get():
            if AYAR_MOBIL_KONTROL:
                mobil_kontrol.olay_isle(olay)
            if olay.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if olay.type == pygame.KEYDOWN:
                if olay.key == pygame.K_ESCAPE and not kart_bekleniyor:
                    if not durduruldu:
                        duraklama_goruntusu = ekran.copy()
                    durduruldu = not durduruldu
                if not kart_bekleniyor and not durduruldu:
                    if olay.key == pygame.K_e:
                        if hex_modu:
                            oyuncu.hex_heal_baslat()
                        elif raptor_modu:
                            mx_e, my_e = pygame.mouse.get_pos()
                            yon_e = 1 if mx_e > oyuncu.x + oyuncu.w/2 else -1
                            if oyuncu.raptor_kacis_baslat(yon_e) and oyuncu.raptor_zehir_patlama_acik:
                                merkez_zx, merkez_zy = oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2
                                for dz in dusman_listesi:
                                    if math.hypot(dz.x+dz.w/2-merkez_zx, dz.y+dz.h/2-merkez_zy) <= RAPTOR_ZEHIR_PATLAMA_YARICAP:
                                        dz.zehir_kare = RAPTOR_ZEHIR_DUSMAN_SURESI
                                        dz.zehir_tik = RAPTOR_ZEHIR_TIK
                                parca_listesi.extend(patlama(merkez_zx, merkez_zy, (60,220,90), 16))
                        elif wraith_modu:
                            can_once = oyuncu.can
                            oyuncu.wraith_heal_baslat()
                            kazanilan = oyuncu.can - can_once
                            if kazanilan > 0:
                                hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, kazanilan, YESIL, 0, -1, art=True))
                        elif reaper_modu:
                            e_kullanilabilir = (oyuncu.reaper_e_bekleme <= 0 and oyuncu.can > REAPER_E_CAN_MALIYET
                                                 and (iskelet_listesi or oyuncu.reaper_e_ek_iskelet_acik))
                            if e_kullanilabilir:
                                oyuncu.can -= REAPER_E_CAN_MALIYET
                                for isk in iskelet_listesi:
                                    isk.guclendir()
                                if oyuncu.reaper_e_ek_iskelet_acik:
                                    for _ in range(3):
                                        yeni_isk = Iskelet(oyuncu.x + oyuncu.w/2 - 11 + random.randint(-30, 30), ZEMIN_Y - 34, guclu=True)
                                        yeni_isk.guclendir()
                                        iskelet_listesi.append(yeni_isk)
                                oyuncu.reaper_e_bekleme = REAPER_E_BEKLEME
                        elif overdrive_modu:
                            if oyuncu.overdrive_e_bekleme <= 0:
                                oyuncu.overdrive_e_bekleme = OVERDRIVE_E_BEKLEME
                                oyuncu.overdrive_e_goster = 10
                                snd_overdrive_patlat()
                                can_once_od = oyuncu.can
                                oyuncu.can = min(oyuncu.max_can, oyuncu.can + OVERDRIVE_E_CAN_YENILEME)
                                kazanilan_od = oyuncu.can - can_once_od
                                if kazanilan_od > 0:
                                    hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, kazanilan_od, YESIL, 0, -1, art=True))
                                merkez_x, merkez_y = oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2
                                for d in dusman_listesi[:]:
                                    if d.tip == 'hayalet' and d.hayalet_mod:
                                        continue
                                    dm_x, dm_y = d.x+d.w/2, d.y+d.h/2
                                    if math.hypot(dm_x-merkez_x, dm_y-merkez_y) > OVERDRIVE_E_MENZIL:
                                        continue
                                    d.can -= OVERDRIVE_E_HASAR
                                    hasar_yazisi_listesi.append(HasarYazisi(dm_x, dm_y, OVERDRIVE_E_HASAR, (220,220,220), dm_x-merkez_x, dm_y-merkez_y))
                                    parca_listesi.extend(patlama(dm_x, dm_y, SARI, 8))
                                    if d.can <= 0:
                                        parca_listesi.extend(patlama(dm_x, dm_y, (245,166,35), 14))
                                        for _ in range(random.randint(1, 3)):
                                            xp_listesi.append(Xp(dm_x, dm_y))
                                        if random.random() < 0.12:
                                            can_topu_listesi.append(CanTopu(dm_x, dm_y))
                                        oldurulen += 1
                                        if oyuncu.overdrive_ulti_aktif:
                                            oyuncu.can = min(oyuncu.max_can, oyuncu.can + OVERDRIVE_ULTI_CAN_KAZANC)
                                        snd_olum()
                                        dusman_listesi.remove(d)
                        elif ronin_modu:
                            if oyuncu.ronin_e_bekleme <= 0:
                                oyuncu.ronin_e_bekleme = RONIN_E_BEKLEME
                                oyuncu.ronin_gizli_aktif = True
                                oyuncu.ronin_gizli_suresi = RONIN_E_SURESI
                                oyuncu.ronin_kritik_hazir = True
                        else:
                            oyuncu.kalkan_baslat()
                    if olay.key == pygame.K_q:
                        if hex_modu:
                            if oyuncu.ulti_dolu >= ULTI_MAX:
                                oyuncu.ulti_dolu = 0
                                snd_hex_ulti()
                                hex_ulti_hasar_g = 99999 if oyuncu.hex_ulti_ekran_temizle_acik else HEX_ULTI_HASAR
                                for d in dusman_listesi[:]:
                                    d.can -= hex_ulti_hasar_g
                                    d.yavaslatildi = HEX_ULTI_YAVAS_SURESI
                                    hasar_yazisi_listesi.append(HasarYazisi(d.x+d.w/2, d.y+d.h/2, min(hex_ulti_hasar_g, int(d.max_can)), (220,220,220), 0, -1))
                                    if d.can <= 0:
                                        parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (245,166,35), 14))
                                        for _ in range(random.randint(1, 3)):
                                            xp_listesi.append(Xp(d.x+d.w/2, d.y))
                                        if random.random() < 0.12:
                                            can_topu_listesi.append(CanTopu(d.x+d.w/2, d.y))
                                        oldurulen += 1
                                        snd_olum()
                                        dusman_listesi.remove(d)
                        elif raptor_modu:
                            if oyuncu.ulti_dolu >= ULTI_MAX and not oyuncu.raptor_ulti_aktif:
                                oyuncu.ulti_dolu = 0
                                oyuncu.raptor_ulti_aktif = True
                                oyuncu.raptor_ulti_suresi = RAPTOR_ULTI_SURESI
                                snd_raptor_ulti()
                        elif wraith_modu:
                            if oyuncu.ulti_dolu >= ULTI_MAX and not oyuncu.wraith_ulti_aktif:
                                oyuncu.ulti_dolu = 0
                                oyuncu.wraith_ulti_aktif = True
                                oyuncu.wraith_ulti_suresi = WRAITH_ULTI_SURESI
                                snd_wraith_ulti()
                        elif reaper_modu:
                            if oyuncu.reaper_ruh_bolme > 0:
                                adet = oyuncu.reaper_ruh_bolme
                                for i in range(adet):
                                    offset = (i - (adet-1)/2) * 32
                                    sx = max(0, min(GENISLIK-22, oyuncu.x + oyuncu.w/2 + offset - 11))
                                    iskelet_listesi.append(Iskelet(sx, ZEMIN_Y - 34, guclu=True, okcu=oyuncu.reaper_ulti_okcu_acik))
                                oyuncu.reaper_ruh_bolme = 0
                                snd_reaper_ulti()
                        elif overdrive_modu:
                            if oyuncu.ulti_dolu >= ULTI_MAX and not oyuncu.overdrive_ulti_aktif:
                                oyuncu.ulti_dolu = 0
                                oyuncu.overdrive_ulti_aktif = True
                                oyuncu.overdrive_ulti_suresi = OVERDRIVE_ULTI_SURESI
                                for d in dusman_listesi:
                                    d.yavaslatildi = OVERDRIVE_ULTI_SURESI
                                for m in mermi_listesi:
                                    if not m.oyuncu_mermisi:
                                        m.hiz_x *= OVERDRIVE_ULTI_YAVAS_CARPAN
                                        m.hiz_y *= OVERDRIVE_ULTI_YAVAS_CARPAN
                                if oyuncu.overdrive_ulti_olumsuz_acik:
                                    oyuncu.overdrive_olumsuzluk_kalan = OVERDRIVE_ULTI_SURESI + 180
                                snd_overdrive_ulti()
                        elif ronin_modu:
                            if oyuncu.ulti_dolu >= ULTI_MAX and not oyuncu.ronin_ulti_aktif:
                                oyuncu.ulti_dolu = 0
                                oyuncu.ronin_ulti_aktif = True
                                oyuncu.ronin_ulti_suresi = RONIN_ULTI_SURESI
                                if oyuncu.ronin_ulti_gelismis_acik:
                                    can_once_ro = oyuncu.can
                                    oyuncu.can = min(oyuncu.max_can, oyuncu.can + 50)
                                    kazanc_ro = oyuncu.can - can_once_ro
                                    if kazanc_ro > 0:
                                        hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, kazanc_ro, YESIL, 0, -1, art=True))
                                snd_ronin_ulti()
                        else:
                            ulti_oncesi = oyuncu.ulti_aktif
                            can_once = oyuncu.can
                            oyuncu.ulti_kullan()
                            kazanilan = oyuncu.can - can_once
                            if kazanilan > 0:
                                hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, kazanilan, YESIL, 0, -1, art=True))
                            if oyuncu.ulti_aktif and not ulti_oncesi:
                                snd_aegis_ulti()
            if olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1 and durduruldu:
                if pause_devam_rect.collidepoint(olay.pos):
                    durduruldu = False
                elif pause_menu_rect.collidepoint(olay.pos):
                    return
            elif olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1 and not durduruldu:
                if not kart_bekleniyor and durdur_buton_rect.collidepoint(olay.pos):
                    duraklama_goruntusu = ekran.copy()
                    durduruldu = True
                elif kart_bekleniyor:
                    for i, r in enumerate(kart_rectleri):
                        if r.collidepoint(olay.pos):
                            kod = kart_secenekleri[i][0]
                            if kod == 'hasar':
                                oyuncu_hasar_carpan *= 1.2
                            elif kod == 'hiz':
                                oyuncu.survivor_hiz_carpan *= 1.15
                            elif kod == 'can':
                                oyuncu.max_can += 25
                                oyuncu.can += 25
                            elif kod == 'saldiri':
                                oyuncu_saldiri_carpan = max(0.35, oyuncu_saldiri_carpan * 0.85)
                            elif kod == 'regen':
                                oyuncu.survivor_can_yenileme += 0.03
                            elif kod == 'aegis_kalkan':
                                oyuncu.aegis_pasif_kalkan_acik = True
                            elif kod == 'aegis_menzil':
                                oyuncu.aegis_kilic_menzil_carpan *= 1.35
                            elif kod == 'raptor_zehir':
                                oyuncu.raptor_zehir_aktif = True
                                oyuncu.raptor_zehir_suresi = 999999
                            elif kod == 'raptor_hamle':
                                oyuncu.raptor_dash_sinirsiz_acik = True
                            elif kod == 'hex_kitap':
                                oyuncu.hex_kitap_max_ozel = HEX_KITAP_MAX_USTA
                            elif kod == 'hex_can':
                                oyuncu.max_can += 50
                                oyuncu.can += 50
                            elif kod == 'wraith_hasar':
                                oyuncu.wraith_hayalet_hasar_artis_acik = True
                            elif kod == 'wraith_ruhbagi':
                                oyuncu.wraith_ruh_heal_acik = True
                            elif kod == 'reaper_zirh':
                                oyuncu.max_can += 30
                                oyuncu.can += 30
                            elif kod == 'reaper_emici':
                                oyuncu.reaper_emici_acik = True
                            kart_bekleniyor = False
                            snd_seviye()
                else:
                    fare_basili = True
            if olay.type == pygame.MOUSEBUTTONUP and olay.button == 1:
                fare_basili = False
            if olay.type == pygame.MOUSEBUTTONUP and olay.button == 3:
                if overdrive_modu and oyuncu.kanca_durum in ('sallaniyor', 'ucuyor'):
                    oyuncu.overdrive_sallan(*olay.pos)
            if olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 3 and not kart_bekleniyor:
                if hex_modu:
                    if oyuncu.hex_kitap_sayisi >= 1:
                        ex, ey = oyuncu.kilic_el_konumu()
                        dx, dy = olay.pos[0] - ex, olay.pos[1] - ey
                        uzunluk = math.hypot(dx, dy) or 1
                        yon_x, yon_y = dx/uzunluk, dy/uzunluk
                        hasar_isin = HEX_ISIN_BIRIM_HASAR * oyuncu.hex_kitap_sayisi * oyuncu_hasar_carpan
                        isin_vurulanlar = []
                        mesafe = 0
                        while mesafe < HEX_ISIN_MENZIL:
                            mesafe += 14
                            nx, ny = ex + yon_x*mesafe, ey + yon_y*mesafe
                            for d in dusman_listesi[:]:
                                if d in isin_vurulanlar:
                                    continue
                                if d.tip == 'hayalet' and d.hayalet_mod:
                                    continue
                                if d.rect().collidepoint(nx, ny):
                                    isin_vurulanlar.append(d)
                                    d.can -= hasar_isin
                                    hasar_yazisi_listesi.append(HasarYazisi(d.x+d.w/2, d.y+d.h/2, hasar_isin, (220,220,220), yon_x, yon_y))
                                    parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, MOR, 8))
                                    if d.can <= 0:
                                        olum_x, olum_y = d.x+d.w/2, d.y+d.h/2
                                        parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                                        for _ in range(random.randint(1, 3)):
                                            xp_listesi.append(Xp(olum_x, d.y))
                                        if random.random() < 0.12:
                                            can_topu_listesi.append(CanTopu(olum_x, d.y))
                                        oldurulen += 1
                                        snd_olum()
                                        dusman_listesi.remove(d)
                        oyuncu.hex_isin_bitis = (ex + yon_x*HEX_ISIN_MENZIL, ey + yon_y*HEX_ISIN_MENZIL)
                        oyuncu.hex_isin_goster = 8
                        oyuncu.hex_isin_kitap_sayisi = oyuncu.hex_kitap_sayisi
                        oyuncu.hex_kitap_sayisi = 0
                        snd_buyu()
                elif raptor_modu:
                    if oyuncu.raptor_dash_bekleme <= 0 and not oyuncu.raptor_dash_aktif:
                        yon_dash = 1 if oyuncu.hiz_x >= 0 else -1
                        if oyuncu.hiz_x == 0:
                            yon_dash = 1 if olay.pos[0] > oyuncu.x + oyuncu.w/2 else -1
                        oyuncu.raptor_dash_aktif = True
                        oyuncu.raptor_dash_suresi = RAPTOR_DASH_SURESI
                        oyuncu.raptor_dash_yon = yon_dash
                        oyuncu.raptor_dash_bekleme = 0 if oyuncu.raptor_dash_sinirsiz_acik else RAPTOR_DASH_BEKLEME
                        oyuncu.raptor_dash_vurulanlar = []
                        if oyuncu.raptor_ofke_acik:
                            oyuncu.raptor_ofke_aktif = True
                            oyuncu.raptor_ofke_suresi = RAPTOR_OFKE_SURESI
                        snd_zipla()
                elif wraith_modu:
                    oyuncu.wraith_hayalet_baslat()
                elif reaper_modu:
                    if oyuncu.reaper_atis_bekleme <= 0:
                        oyuncu.reaper_atis_bekleme = REAPER_ATIS_BEKLEME
                        oyuncu.reaper_atis_goster = 8
                        snd_koni()
                        merkez_x = oyuncu.x + oyuncu.w/2
                        merkez_y = oyuncu.y + oyuncu.h/2
                        hedef_aci = math.atan2(olay.pos[1]-merkez_y, olay.pos[0]-merkez_x)
                        for d in dusman_listesi[:]:
                            if d.tip == 'hayalet' and d.hayalet_mod:
                                continue
                            dm_x, dm_y = d.x+d.w/2, d.y+d.h/2
                            dx, dy = dm_x-merkez_x, dm_y-merkez_y
                            if math.hypot(dx, dy) > REAPER_ATIS_MENZIL:
                                continue
                            fark_aci2 = (math.atan2(dy, dx) - hedef_aci + math.pi) % (2*math.pi) - math.pi
                            if abs(fark_aci2) > REAPER_ATIS_ACI:
                                continue
                            hasar_r2 = REAPER_ATIS_HASAR * oyuncu_hasar_carpan
                            d.can -= hasar_r2
                            if oyuncu.reaper_emici_acik:
                                oyuncu.can = min(oyuncu.max_can, oyuncu.can + hasar_r2 * REAPER_EMICI_ORAN)
                            hasar_yazisi_listesi.append(HasarYazisi(dm_x, dm_y, hasar_r2, (220,220,220), dx, dy))
                            parca_listesi.extend(patlama(dm_x, dm_y, (255,35,35), 7))
                            if d.can <= 0:
                                olum_x, olum_y = dm_x, dm_y
                                parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                                for _ in range(random.randint(1, 3)):
                                    xp_listesi.append(Xp(olum_x, olum_y))
                                if random.random() < 0.12:
                                    can_topu_listesi.append(CanTopu(olum_x, olum_y))
                                oldurulen += 1
                                snd_olum()
                                dusman_listesi.remove(d)
                elif overdrive_modu:
                    if oyuncu.kanca_bekleme <= 0 and oyuncu.kanca_durum == 'yok':
                        overdrive_kanca_at(*olay.pos)
                elif ronin_modu:
                    if oyuncu.ronin_firlat_bekleme <= 0:
                        ronin_firlat()
                elif aegis_modu:
                    if oyuncu.kilic_durum == 'beklemede':
                        oyuncu.kilic_firlat(*olay.pos)
                    else:
                        oyuncu.kilic_geri_cagir()

        fare_x, fare_y = pygame.mouse.get_pos()
        if AYAR_MOBIL_KONTROL:
            fare_x, fare_y = mobil_kontrol.nisan_konumu(fare_x, fare_y, oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2)
            fare_basili = fare_basili or mobil_kontrol.ates_basili

        if durduruldu:
            ekran.blit(duraklama_goruntusu, (0, 0))
            ortu = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)
            ortu.fill((0, 0, 0, 150))
            ekran.blit(ortu, (0, 0))
            baslik_p = fnt_by.render(t('pause_baslik'), True, CYAN)
            ekran.blit(baslik_p, (GENISLIK//2 - baslik_p.get_width()//2, YUKSEKLIK//2 - 90))
            buton_ciz(ekran, pause_devam_rect, t('devam_et'), (fare_x, fare_y))
            buton_ciz(ekran, pause_menu_rect, t('ana_menuye_don'), (fare_x, fare_y))
            nisangah_ciz(ekran, fare_x, fare_y)
            pygame.display.flip()
            await asyncio.sleep(0)
            continue

        if not kart_bekleniyor:
            tuslar = pygame.key.get_pressed()
            if AYAR_MOBIL_KONTROL:
                tuslar = mobil_kontrol.tuslar_sarmala(tuslar)
            if not (overdrive_modu and oyuncu.kanca_durum != 'yok'):
                oyuncu.hareket_et(tuslar, (fare_x, fare_y))

            # Kamera: oyuncunun dünya konumunu takip eder, harita kenarlarında durur
            # (DUNYA_GENISLIK ile sınırlı — sonsuz kaymaz).
            dunya_x += oyuncu.hiz_x
            dunya_x = max(0, min(DUNYA_GENISLIK, dunya_x))
            toplam_mesafe = dunya_x
            yeni_kamera_x = max(0, min(DUNYA_GENISLIK - GENISLIK, dunya_x - GENISLIK/2))
            fark = kamera_x - yeni_kamera_x
            kamera_x = yeni_kamera_x
            if fark != 0.0:
                oyuncu.x += fark
                oyuncu.kilic_x += fark
                oyuncu.kanca_x += fark
                oyuncu.kanca_ucus_hedef_x += fark
                for grup in (dusman_listesi, mermi_listesi, xp_listesi, can_topu_listesi,
                             parca_listesi, hasar_yazisi_listesi, iskelet_listesi):
                    for e in grup:
                        e.x += fark

            # Öldürme sayısı arttıkça ulti barı ve REAPER'ın ruh biriktirmesi de
            # dolsun diye — her tek öldürme noktasına ayrı ayrı eklemek yerine
            # oldurulen sayacındaki artışı burada tek yerden yakalıyoruz.
            if oldurulen > oldurulen_onceki:
                yeni_oldurme = oldurulen - oldurulen_onceki
                oyuncu.ulti_sarj_ekle(ULTI_SARJ_OLUM * yeni_oldurme)
                for _ in range(yeni_oldurme):
                    oyuncu.reaper_ruh_ekle()
                oldurulen_onceki = oldurulen

            oyuncu.kilic_guncelle()
            oyuncu.hex_kitap_guncelle()
            if raptor_modu and oyuncu.raptor_dash_aktif:
                # Ekran hep ortalı kalsın diye: dash'in oyuncu.x'i kaydırmasını
                # geri alıp aynı miktarı dünya konumuna (kameraya) ekliyoruz.
                dash_hareket = RAPTOR_DASH_HIZI * oyuncu.raptor_dash_yon
                oyuncu.raptor_guncelle()
                oyuncu.x -= dash_hareket
                dunya_x = max(0, min(DUNYA_GENISLIK, dunya_x + dash_hareket))
            else:
                oyuncu.raptor_guncelle()
            oyuncu.wraith_guncelle()
            oyuncu.reaper_guncelle()
            if overdrive_modu:
                oyuncu.overdrive_guncelle(tuslar)
            if ronin_modu:
                oyuncu.ronin_guncelle()
                if oyuncu.ronin_ulti_aktif and oyuncu.ronin_ulti_suresi % 6 == 0:
                    ronin_ulti_r = RONIN_ULTI_YARICAP * (2.0 if oyuncu.ronin_ulti_gelismis_acik else 1.0)
                    merkez_x, merkez_y = oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2
                    for d in dusman_listesi[:]:
                        if d.tip == 'hayalet' and d.hayalet_mod:
                            continue
                        if math.hypot((d.x+d.w/2)-merkez_x, (d.y+d.h/2)-merkez_y) > ronin_ulti_r:
                            continue
                        d.can -= RONIN_ULTI_HASAR
                        parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (170,120,255), 4))
                        if d.can <= 0:
                            olum_x, olum_y = d.x+d.w/2, d.y+d.h/2
                            parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                            for _ in range(random.randint(1, 3)):
                                xp_listesi.append(Xp(olum_x, olum_y))
                            if random.random() < 0.12:
                                can_topu_listesi.append(CanTopu(olum_x, olum_y))
                            oldurulen += 1
                            snd_olum()
                            dusman_listesi.remove(d)

            if reaper_modu:
                for isk in iskelet_listesi[:]:
                    isk.guncelle(dusman_listesi)
                    for d in dusman_listesi[:]:
                        if d.tip == 'hayalet' and d.hayalet_mod:
                            continue
                        if isk.okcu:
                            mesafe_isk = math.hypot((d.x+d.w/2)-(isk.x+isk.w/2), (d.y+d.h/2)-(isk.y+isk.h/2))
                            if mesafe_isk > REAPER_ISKELET_OKCU_MENZIL:
                                continue
                        elif not d.rect().colliderect(isk.rect()):
                            continue
                        isk_hasar = isk.hasar * (REAPER_GUC_CARPAN if isk.guc_suresi > 0 else 1)
                        if isk.atis_bekleme <= 0:
                            isk.atis_bekleme = REAPER_ISKELET_ATIS_BEKLEME
                            d.can -= isk_hasar
                            hasar_yazisi_listesi.append(HasarYazisi(d.x+d.w/2, d.y+d.h/2, isk_hasar, (220,220,220), d.x-isk.x, d.y-isk.y))
                            parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (70,120,220) if isk.okcu else (205,45,40), 6))
                            if d.can <= 0:
                                olum_x, olum_y = d.x+d.w/2, d.y+d.h/2
                                parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                                for _ in range(random.randint(1, 3)):
                                    xp_listesi.append(Xp(olum_x, olum_y))
                                if random.random() < 0.12:
                                    can_topu_listesi.append(CanTopu(olum_x, olum_y))
                                oldurulen += 1
                                snd_olum()
                                dusman_listesi.remove(d)
                        if not isk.okcu:
                            isk.can -= 1
                            if d.tip != 'suicide':
                                snd_hasar()
                    if isk.can <= 0:
                        can_once_isk = oyuncu.can
                        oyuncu.can = min(oyuncu.max_can, oyuncu.can + 10)
                        kazanc_isk = oyuncu.can - can_once_isk
                        if kazanc_isk > 0:
                            hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, kazanc_isk, YESIL, 0, -1, art=True))
                        iskelet_listesi.remove(isk)

            if fare_basili and aegis_modu and oyuncu.kilic_durum == 'beklemede' and oyuncu.kilic_savurma_bekleme <= 0:
                savur_rect = oyuncu.kilic_savur_rect(fare_x, fare_y)
                oyuncu.kilic_savurma_bekleme = max(4, int(KILIC_SAVURMA_BEKLEME * oyuncu_saldiri_carpan))
                oyuncu.kilic_savurma_goster = 8
                snd_kilic()
                hasar = KILIC_HASAR * oyuncu_hasar_carpan
                for d in dusman_listesi[:]:
                    if d.tip == 'hayalet' and d.hayalet_mod:
                        continue
                    if d.rect().colliderect(savur_rect):
                        d.can -= hasar
                        hasar_yazisi_listesi.append(HasarYazisi(d.x+d.w/2, d.y+d.h/2, hasar, (220,220,220), d.x-oyuncu.x, d.y-oyuncu.y))
                        parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, (0,200,200), 8))
                        if d.can <= 0:
                            olum_x, olum_y = d.x+d.w/2, d.y+d.h/2
                            parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                            for _ in range(random.randint(1, 3)):
                                xp_listesi.append(Xp(olum_x, d.y))
                            if random.random() < 0.12:
                                can_topu_listesi.append(CanTopu(olum_x, d.y))
                            oldurulen += 1
                            snd_olum()
                            dusman_listesi.remove(d)
            elif fare_basili and hex_modu and oyuncu.hex_buyu_bekleme <= 0:
                oyuncu.hex_buyu_bekleme = max(6, int(HEX_BUYU_BEKLEME * oyuncu_saldiri_carpan))
                ex, ey = oyuncu.kilic_el_konumu()
                dx, dy = fare_x - ex, fare_y - ey
                uzunluk = math.hypot(dx, dy) or 1
                mermi_listesi.append(Mermi(ex, ey, dx/uzunluk*HEX_BUYU_HIZI, dy/uzunluk*HEX_BUYU_HIZI,
                                            MOR, HEX_BUYU_HASAR * oyuncu_hasar_carpan, True))
                snd_buyu()
            elif fare_basili and raptor_modu and oyuncu.raptor_pence_bekleme <= 0:
                pence_hasar = RAPTOR_PENCE_HASAR * (RAPTOR_ULTI_PENCE_CARPAN if oyuncu.raptor_ulti_aktif else 1) * (RAPTOR_OFKE_CARPAN if oyuncu.raptor_ofke_aktif else 1) * oyuncu_hasar_carpan
                pence_rect = oyuncu.kilic_savur_rect(fare_x, fare_y)
                oyuncu.raptor_pence_bekleme = max(4, int(RAPTOR_PENCE_BEKLEME * oyuncu_saldiri_carpan))
                oyuncu.raptor_pence_goster = 6
                snd_pence()
                for d in dusman_listesi[:]:
                    if d.tip == 'hayalet' and d.hayalet_mod:
                        continue
                    if d.rect().colliderect(pence_rect):
                        d.can -= pence_hasar
                        if oyuncu.raptor_zehir_aktif:
                            d.zehir_kare = RAPTOR_ZEHIR_DUSMAN_SURESI
                            d.zehir_tik = RAPTOR_ZEHIR_TIK
                        yasam_k = pence_hasar * RAPTOR_PENCE_YASAM_CALMA
                        oyuncu.can = min(oyuncu.max_can, oyuncu.can + yasam_k)
                        hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, yasam_k, YESIL, 0, -1, art=True))
                        hasar_yazisi_listesi.append(HasarYazisi(d.x+d.w/2, d.y+d.h/2, pence_hasar, (220,220,220), d.x-oyuncu.x, d.y-oyuncu.y))
                        parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, YESIL, 8))
                        if d.can <= 0:
                            olum_x, olum_y = d.x+d.w/2, d.y+d.h/2
                            parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                            for _ in range(random.randint(1, 3)):
                                xp_listesi.append(Xp(olum_x, d.y))
                            if random.random() < 0.12:
                                can_topu_listesi.append(CanTopu(olum_x, d.y))
                            oldurulen += 1
                            snd_olum()
                            dusman_listesi.remove(d)
            elif fare_basili and wraith_modu and oyuncu.wraith_ruh_bekleme <= 0:
                oyuncu.wraith_ruh_bekleme = max(6, int(WRAITH_RUH_BEKLEME * oyuncu_saldiri_carpan))
                ex, ey = oyuncu.kilic_el_konumu()
                dx, dy = fare_x - ex, fare_y - ey
                uzunluk = math.hypot(dx, dy) or 1
                ruh_hasar = WRAITH_RUH_HASAR * ((WRAITH_HAYALET_HASAR_ARTIS_CARPAN if oyuncu.wraith_hayalet_hasar_artis_acik else WRAITH_HAYALET_YARI_CARPAN) if oyuncu.wraith_hayalet_aktif else 1) * oyuncu_hasar_carpan
                m = Mermi(ex, ey, dx/uzunluk*WRAITH_RUH_HIZI, dy/uzunluk*WRAITH_RUH_HIZI, (150,220,210), ruh_hasar, True)
                m.wraith_mermisi = True
                mermi_listesi.append(m)
                snd_ruh()
            elif fare_basili and reaper_modu and oyuncu.reaper_vurus_bekleme <= 0:
                oyuncu.reaper_vurus_bekleme = max(4, int(REAPER_VURUS_BEKLEME * oyuncu_saldiri_carpan))
                oyuncu.reaper_vurus_goster = 8
                snd_koni()
                merkez_x = oyuncu.x + oyuncu.w/2
                merkez_y = oyuncu.y + oyuncu.h/2
                hedef_aci = math.atan2(fare_y-merkez_y, fare_x-merkez_x)
                for d in dusman_listesi[:]:
                    if d.tip == 'hayalet' and d.hayalet_mod:
                        continue
                    dm_x, dm_y = d.x+d.w/2, d.y+d.h/2
                    dx, dy = dm_x-merkez_x, dm_y-merkez_y
                    if math.hypot(dx, dy) > REAPER_VURUS_MENZIL:
                        continue
                    fark_aci = (math.atan2(dy, dx) - hedef_aci + math.pi) % (2*math.pi) - math.pi
                    if abs(fark_aci) > REAPER_VURUS_ACI:
                        continue
                    hasar_r = REAPER_VURUS_HASAR * oyuncu_hasar_carpan
                    d.can -= hasar_r
                    if oyuncu.reaper_emici_acik:
                        oyuncu.can = min(oyuncu.max_can, oyuncu.can + hasar_r * REAPER_EMICI_ORAN)
                    hasar_yazisi_listesi.append(HasarYazisi(dm_x, dm_y, hasar_r, (220,220,220), dx, dy))
                    parca_listesi.extend(patlama(dm_x, dm_y, (200,25,30), 6))
                    if d.can <= 0:
                        olum_x, olum_y = dm_x, dm_y
                        parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                        for _ in range(random.randint(1, 3)):
                            xp_listesi.append(Xp(olum_x, olum_y))
                        if random.random() < 0.12:
                            can_topu_listesi.append(CanTopu(olum_x, olum_y))
                        oldurulen += 1
                        snd_olum()
                        dusman_listesi.remove(d)
            elif fare_basili and overdrive_modu:
                mermi_once_sayisi = len(mermi_listesi)
                oyuncu.ates_et(fare_x, fare_y, mermi_listesi)
                for m in mermi_listesi[mermi_once_sayisi:]:
                    m.hasar *= oyuncu_hasar_carpan
            elif fare_basili and ronin_modu and oyuncu.ronin_itis_bekleme <= 0:
                oyuncu.ronin_itis_bekleme = max(4, int(RONIN_ITIS_BEKLEME * oyuncu_saldiri_carpan))
                oyuncu.ronin_itis_goster = 8
                oyuncu.ronin_itis_zirh = 14
                snd_mizrak()
                ronin_itis()

            gecen_kare += 1
            sanal_bolum = min(29, 1 + gecen_kare // SURVIVOR_ZORLUK_ARALIK)
            if sanal_bolum == 5:
                sanal_bolum = 6

            spawn_timer -= 1
            if spawn_timer <= 0:
                ayar = bolum_ayar(sanal_bolum)
                havuz = [(t, ayar.get(t, 0)) for t in
                         ['melee', 'ranged', 'drone', 'sniper', 'shield', 'tank', 'suicide', 'gorunmez', 'hayalet', 'mizrakli']]
                havuz = [(t, a) for t, a in havuz if a > 0]
                if havuz:
                    tipler, agirliklar = zip(*havuz)
                    tip = random.choices(tipler, weights=agirliklar, k=1)[0]
                    if tip == 'mizrakli':
                        grup_yon = mizrakli_sonraki_yon
                        mizrakli_sonraki_yon *= -1
                        grup_sayisi = random.randint(MIZRAKLI_GRUP_MIN, MIZRAKLI_GRUP_MAX)
                        sx_baslangic = -60 if grup_yon == 1 else GENISLIK + 60
                        for k in range(grup_sayisi):
                            yd = Dusman(sx_baslangic - grup_yon * k * 46, 'mizrakli', sanal_bolum)
                            yd.hiz_x = grup_yon * MIZRAKLI_HIZ
                            yd.sinirsiz = True
                            dusman_listesi.append(yd)
                    else:
                        sx = GENISLIK + 50 if random.random() > 0.5 else -50
                        yeni_dusman = Dusman(sx, tip, sanal_bolum)
                        yeni_dusman.sinirsiz = True
                        dusman_listesi.append(yeni_dusman)
                spawn_timer = max(25, 70 - sanal_bolum * 2)

            if gecen_kare >= sonraki_minibos_kare:
                sx_boss = GENISLIK + 50 if random.random() > 0.5 else -50
                mini_boss = Dusman(sx_boss, 'boss', sanal_bolum)
                mini_boss.sinirsiz = True
                dusman_listesi.append(mini_boss)
                sonraki_minibos_kare += minibos_esik_kare

            # Düşmanlar
            for d in dusman_listesi[:]:
                d.guncelle(oyuncu.x + oyuncu.w/2, oyuncu.y + oyuncu.h/2, zaman)

                # Zehir gibi vurus-disi (pasif) hasarlarla can bitmis olabilir — bir
                # oyuncu vurusuyla eslesmezse fark edilmeden "hayalet" kalmasin diye.
                if d.can <= 0:
                    olum_x, olum_y = d.x+d.w/2, d.y+d.h/2
                    parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                    for _ in range(random.randint(1, 3)):
                        xp_listesi.append(Xp(olum_x, d.y))
                    if random.random() < 0.12:
                        can_topu_listesi.append(CanTopu(olum_x, d.y))
                    oldurulen += 1
                    dusman_listesi.remove(d)
                    continue

                # Harita sonsuz kaydığı için: oyuncu sürekli tek yöne kaçarsa yavaş
                # düşmanlar asla yetişemez ve arkada birikirdi. 400px'den uzaktakiler
                # mesafeyle orantılı "yetişme" hızı alır, tamamen kopmalarını engeller.
                mesafe_d = d.x - oyuncu.x
                if d.tip != 'mizrakli' and abs(mesafe_d) > 400:
                    fazlalik = mesafe_d - (400 if mesafe_d > 0 else -400)
                    d.x -= fazlalik * 0.03

                # Yine de aşırı uzakta kalan (örn. ekran dışı doğan, hiç yaklaşamayan) silinir
                if abs(d.x - oyuncu.x) > 1300:
                    dusman_listesi.remove(d)
                    continue

                dokunulmaz = (d.tip == 'hayalet' and d.hayalet_mod)

                # Sadece yakın dövüşçüler (melee/shield) temasla hasar verir, ve sadece
                # DOKUNMA ANINDA bir kez — üstünde durmak art arda hasar vermez, tekrar
                # hasar almak için önce ayrılıp yeniden değmek gerekir. Uzaktan vuran
                # düşmanlar (ranged/sniper/drone/tank/gorunmez/hayalet/boss) SADECE
                # kendi mermileriyle hasar verir, temasla değil.
                temas_ediyor = d.rect().colliderect(oyuncu.rect())
                if not dokunulmaz and d.tip in ['melee', 'shield', 'mizrakli']:
                    if temas_ediyor and not getattr(d, 'dokundu', False):
                        d.dokundu = True
                        yon_x = (oyuncu.x+oyuncu.w/2) - (d.x+d.w/2)
                        yon_y = (oyuncu.y+oyuncu.h/2) - (d.y+d.h/2)
                        kaybedilen = oyuncu.hasar_al(15)
                        if kaybedilen > 0:
                            hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2, kaybedilen, KIRMIZI, yon_x, yon_y))
                        oyuncu.hasar_timer = 10
                        snd_hasar()
                    elif not temas_ediyor:
                        d.dokundu = False

                if d.tip == 'suicide' and getattr(d, 'patlayacak', False):
                    merkez_x, merkez_y = d.x + d.w/2, d.y + d.h/2
                    oyuncu_merkez_x, oyuncu_merkez_y = oyuncu.x + oyuncu.w/2, oyuncu.y + oyuncu.h/2
                    if math.hypot(oyuncu_merkez_x-merkez_x, oyuncu_merkez_y-merkez_y) < PATLAMA_YARICAP and oyuncu.hasar_timer <= 0:
                        kaybedilen = oyuncu.hasar_al(28)
                        if kaybedilen > 0:
                            hasar_yazisi_listesi.append(HasarYazisi(oyuncu_merkez_x, oyuncu_merkez_y, kaybedilen, KIRMIZI, oyuncu_merkez_x-merkez_x, oyuncu_merkez_y-merkez_y))
                        oyuncu.hasar_timer = 10
                        snd_hasar()
                    parca_listesi.extend(patlama(merkez_x, merkez_y, TURUNCU, 20))
                    for _ in range(random.randint(1, 3)):
                        xp_listesi.append(Xp(merkez_x, merkez_y))
                    if random.random() < 0.12:
                        can_topu_listesi.append(CanTopu(merkez_x, merkez_y))
                    oldurulen += 1
                    snd_olum()
                    if d in dusman_listesi:
                        dusman_listesi.remove(d)
                    continue

                if d.atis_yapabilir():
                    mermi_listesi.extend(d.mermi_olustur(oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2))
                    d.atis_sifirla()

            # Mermiler
            for m in mermi_listesi[:]:
                m.guncelle()
                if m.omur <= 0 or m.x < -20 or m.x > GENISLIK+20 or m.y < -20 or m.y > YUKSEKLIK+20:
                    mermi_listesi.remove(m)
                    continue
                if m.oyuncu_mermisi:
                    for d in dusman_listesi[:]:
                        if d.tip == 'hayalet' and d.hayalet_mod:
                            continue
                        if d.rect().colliderect(m.rect()):
                            d.can -= m.hasar
                            hasar_yazisi_listesi.append(HasarYazisi(m.x, m.y, m.hasar, (220,220,220), m.hiz_x, m.hiz_y))
                            parca_listesi.extend(patlama(m.x, m.y, (0,200,200), 6))
                            if getattr(m, 'wraith_mermisi', False):
                                yasam_k2 = m.hasar * WRAITH_YASAM_CALMA_ORAN
                                oyuncu.can = min(oyuncu.max_can, oyuncu.can + yasam_k2)
                                hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, yasam_k2, YESIL, 0, -1, art=True))
                                oyuncu.wraith_ruh_ekle(WRAITH_RUH_SARJ_VURUS)
                            if m in mermi_listesi:
                                mermi_listesi.remove(m)
                            if d.can <= 0:
                                olum_x, olum_y = d.x+d.w/2, d.y+d.h/2
                                parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                                for _ in range(random.randint(1, 3)):
                                    xp_listesi.append(Xp(olum_x, d.y))
                                if random.random() < 0.12:
                                    can_topu_listesi.append(CanTopu(olum_x, d.y))
                                if getattr(m, 'wraith_mermisi', False):
                                    oyuncu.wraith_ruh_ekle(WRAITH_RUH_SARJ_OLUM)
                                oldurulen += 1
                                snd_olum()
                                dusman_listesi.remove(d)
                            break
                elif m.rect().colliderect(oyuncu.rect()) and oyuncu.hasar_timer <= 0:
                    kaybedilen = oyuncu.hasar_al(m.hasar)
                    oyuncu.hasar_timer = 10
                    parca_listesi.extend(patlama(oyuncu.x+oyuncu.w/2, oyuncu.y+oyuncu.h/2, KIRMIZI, 8))
                    snd_hasar()
                    if kaybedilen > 0:
                        hasar_yazisi_listesi.append(HasarYazisi(m.x, m.y, kaybedilen, KIRMIZI, m.hiz_x, m.hiz_y))
                    if m in mermi_listesi:
                        mermi_listesi.remove(m)

            # Fırlatılan/dönen kılıç çarpışması
            if oyuncu.kilic_durum in ('giden', 'donuyor'):
                kilic_r = oyuncu.kilic_rect()
                hasar_k = KILIC_HASAR * oyuncu_hasar_carpan
                for d in dusman_listesi[:]:
                    if d in oyuncu.kilic_vurulanlar:
                        continue
                    if d.tip == 'hayalet' and d.hayalet_mod:
                        continue
                    if d.rect().colliderect(kilic_r):
                        oyuncu.kilic_vurulanlar.append(d)
                        d.can -= hasar_k
                        hasar_yazisi_listesi.append(HasarYazisi(oyuncu.kilic_x, oyuncu.kilic_y, hasar_k, (220,220,220), oyuncu.kilic_hiz_x, oyuncu.kilic_hiz_y))
                        parca_listesi.extend(patlama(oyuncu.kilic_x, oyuncu.kilic_y, (0,200,200), 8))
                        if d.can <= 0:
                            olum_x, olum_y = d.x+d.w/2, d.y+d.h/2
                            parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                            for _ in range(random.randint(1, 3)):
                                xp_listesi.append(Xp(olum_x, d.y))
                            if random.random() < 0.12:
                                can_topu_listesi.append(CanTopu(olum_x, d.y))
                            oldurulen += 1
                            snd_olum()
                            dusman_listesi.remove(d)

            # Hamle (RAPTOR dash) çarpışmaları
            if oyuncu.raptor_dash_aktif:
                for d in dusman_listesi[:]:
                    if d in oyuncu.raptor_dash_vurulanlar:
                        continue
                    if d.tip == 'hayalet' and d.hayalet_mod:
                        continue
                    if d.rect().colliderect(oyuncu.rect()):
                        oyuncu.raptor_dash_vurulanlar.append(d)
                        hasar_d = RAPTOR_DASH_HASAR * (RAPTOR_OFKE_CARPAN if oyuncu.raptor_ofke_aktif else 1) * oyuncu_hasar_carpan
                        d.can -= hasar_d
                        if oyuncu.raptor_zehir_aktif:
                            d.zehir_kare = RAPTOR_ZEHIR_DUSMAN_SURESI
                            d.zehir_tik = RAPTOR_ZEHIR_TIK
                        hasar_yazisi_listesi.append(HasarYazisi(d.x+d.w/2, d.y+d.h/2, hasar_d, (220,220,220), oyuncu.raptor_dash_yon, 0))
                        parca_listesi.extend(patlama(d.x+d.w/2, d.y+d.h/2, YESIL, 10))
                        if d.can <= 0:
                            olum_x, olum_y = d.x+d.w/2, d.y+d.h/2
                            parca_listesi.extend(patlama(olum_x, olum_y, (245,166,35), 14))
                            for _ in range(random.randint(1, 3)):
                                xp_listesi.append(Xp(olum_x, d.y))
                            if random.random() < 0.12:
                                can_topu_listesi.append(CanTopu(olum_x, d.y))
                            oldurulen += 1
                            snd_olum()
                            dusman_listesi.remove(d)

            # XP toplama
            for xp in xp_listesi[:]:
                xp.guncelle()
                if xp.omur <= 0:
                    xp_listesi.remove(xp)
                    continue
                if oyuncu.rect().inflate(24, 24).colliderect(xp.rect()):
                    xp_dolu += xp.deger
                    snd_para()
                    xp_listesi.remove(xp)

            # Can topu toplama (alınca can tam dolar)
            for ct in can_topu_listesi[:]:
                ct.guncelle()
                if ct.omur <= 0:
                    can_topu_listesi.remove(ct)
                    continue
                if oyuncu.rect().inflate(24, 24).colliderect(ct.rect()):
                    can_once_ct = oyuncu.can
                    oyuncu.can = oyuncu.max_can
                    kazanc_ct = oyuncu.can - can_once_ct
                    if kazanc_ct > 0:
                        hasar_yazisi_listesi.append(HasarYazisi(oyuncu.x+oyuncu.w/2, oyuncu.y, kazanc_ct, YESIL, 0, -1, art=True))
                    snd_can()
                    can_topu_listesi.remove(ct)

            for pc in parca_listesi[:]:
                pc.guncelle()
                if pc.omur <= 0:
                    parca_listesi.remove(pc)
            for hy in hasar_yazisi_listesi[:]:
                hy.guncelle()
                if hy.omur <= 0:
                    hasar_yazisi_listesi.remove(hy)

            oyuncu.can = max(0, min(oyuncu.max_can, oyuncu.can))
            if TEST_MODU:
                if oyuncu.can <= 0:
                    oyuncu.can = 1  # TEST: hasar alalım ama ölmeyelim
            elif oyuncu.can <= 0:
                snd_karakter_olum()
                break

            if xp_dolu >= xp_gerekli:
                xp_dolu -= xp_gerekli
                seviye += 1
                xp_gerekli = int(SURVIVOR_XP_BASE * SURVIVOR_XP_ARTIS ** (seviye-1))
                havuz_kart = YUKSELTME_HAVUZU + [k for k in KAHRAMAN_KART_HAVUZU.get(secili_kahraman, [])
                                                  if not kart_zaten_acik(oyuncu, k[0])]
                kart_secenekleri = random.sample(havuz_kart, min(3, len(havuz_kart)))
                kart_w, kart_h = 220, 260
                toplam_w = kart_w*3 + 40*2
                bas_x = GENISLIK//2 - toplam_w//2
                kart_y = YUKSEKLIK//2 - kart_h//2
                kart_rectleri = [pygame.Rect(bas_x + i*(kart_w+40), kart_y, kart_w, kart_h) for i in range(3)]
                kart_bekleniyor = True

        # ── ÇİZİM ──
        fon_ciz(ekran, toplam_mesafe, 1)
        for xp in xp_listesi:
            xp.ciz(ekran)
        for ct in can_topu_listesi:
            ct.ciz(ekran)
        for pc in parca_listesi:
            pc.ciz(ekran)
        for isk in iskelet_listesi:
            isk.ciz(ekran)
        for d in dusman_listesi:
            d.ciz(ekran, zaman)
        for m in mermi_listesi:
            m.ciz(ekran)
        oyuncu.ciz(ekran, fare_x, fare_y, aegis_modu, hex_modu, raptor_modu, wraith_modu, reaper_modu, overdrive_modu, ronin_modu)
        for hy in hasar_yazisi_listesi:
            hy.ciz(ekran)

        # HUD
        pygame.draw.rect(ekran, SIYAH, (0, 0, GENISLIK, 42))
        pygame.draw.rect(ekran, CYAN, (0, 0, GENISLIK, 42), 2)
        can_bar_rect = pygame.Rect(10, 11, 120, 14)
        pygame.draw.rect(ekran, (30,30,30), can_bar_rect)
        oran_c = oyuncu.can / oyuncu.max_can
        rc = YESIL if oran_c > 0.5 else (TURUNCU if oran_c > 0.25 else KIRMIZI)
        pygame.draw.rect(ekran, rc, (10, 11, int(120*oran_c), 14))
        pygame.draw.rect(ekran, CYAN, can_bar_rect, 1)
        can_sayisi_ciz(ekran, can_bar_rect, oyuncu.can, oyuncu.max_can, rc, (30,30,30), fnt_kk)
        ekran.blit(fnt_kk.render(t('can'), True, CYAN), (136, 13))

        xp_bar_rect = pygame.Rect(175, 11, 160, 14)
        pygame.draw.rect(ekran, (30,30,30), xp_bar_rect)
        oran_x = xp_dolu / xp_gerekli if xp_gerekli else 0
        pygame.draw.rect(ekran, (150,230,220), (175, 11, int(160*oran_x), 14))
        pygame.draw.rect(ekran, (150,230,220), xp_bar_rect, 1)
        ekran.blit(fnt_kk.render(f"{t('seviye')} {seviye}", True, (150,230,220)), (345, 13))

        sure_sn = gecen_kare // FPS
        b = fnt_kk.render(f"{t('sure')} {sure_sn//60:02d}:{sure_sn%60:02d}   {t('oldurulen')}:{oldurulen}", True, TURUNCU)
        ekran.blit(b, (GENISLIK//2 - b.get_width()//2, 27))

        if not kart_bekleniyor:
            durdur_uzerinde = durdur_buton_rect.collidepoint(fare_x, fare_y)
            pygame.draw.rect(ekran, (20,45,40) if durdur_uzerinde else (10,10,18), durdur_buton_rect)
            pygame.draw.rect(ekran, (0,255,200) if durdur_uzerinde else CYAN, durdur_buton_rect, 2)
            pygame.draw.rect(ekran, BEYAZ, (durdur_buton_rect.x+7, durdur_buton_rect.y+6, 4, 14))
            pygame.draw.rect(ekran, BEYAZ, (durdur_buton_rect.x+15, durdur_buton_rect.y+6, 4, 14))

        # Nişan
        nisangah_ciz(ekran, fare_x, fare_y)

        # Seviye atlama kart ekranı
        if kart_bekleniyor:
            ortu = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)
            ortu.fill((0, 0, 0, 170))
            ekran.blit(ortu, (0, 0))
            baslik = fnt_by.render("SEVIYE ATLADIN!", True, (150,230,220))
            ekran.blit(baslik, (GENISLIK//2 - baslik.get_width()//2, YUKSEKLIK//2 - 160))
            for i, rect in enumerate(kart_rectleri):
                kod, ad, aciklama, renk = kart_secenekleri[i]
                uzerinde = rect.collidepoint(fare_x, fare_y)
                zemin = (20,45,40) if uzerinde else (10,10,18)
                pygame.draw.rect(ekran, zemin, rect)
                pygame.draw.rect(ekran, renk, rect, 3 if uzerinde else 2)
                ad_y = fnt_or.render(ad, True, renk)
                ekran.blit(ad_y, (rect.centerx - ad_y.get_width()//2, rect.y + 90))
                acik_y = fnt_kk.render(aciklama, True, BEYAZ)
                ekran.blit(acik_y, (rect.centerx - acik_y.get_width()//2, rect.y + 130))

        if AYAR_MOBIL_KONTROL and not kart_bekleniyor:
            mobil_kontrol.ciz(ekran)
        if not kart_bekleniyor:
            basarim_bildirim_guncelle_ciz(ekran)

        pygame.display.flip()
        await asyncio.sleep(0)

    # ── ÖZET EKRANI ──
    global EN_UZUN_HAYATTA_KALMA
    EN_UZUN_HAYATTA_KALMA = max(EN_UZUN_HAYATTA_KALMA, gecen_kare / FPS)
    devam_buton_rect = pygame.Rect(GENISLIK//2 - 110, YUKSEKLIK//2 + 60, 220, 46)
    while True:
        saat.tick(FPS)
        fon_ciz(ekran, oyuncu.x, 1)
        panel = pygame.Surface((460, 240), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 200))
        ekran.blit(panel, (GENISLIK//2-230, YUKSEKLIK//2-140))
        pygame.draw.rect(ekran, CYAN, (GENISLIK//2-230, YUKSEKLIK//2-140, 460, 240), 2)
        bt = fnt_by.render(t('hayatta_kalma_bitti'), True, TURUNCU)
        ekran.blit(bt, (GENISLIK//2 - bt.get_width()//2, YUKSEKLIK//2-120))
        sure_sn = gecen_kare // FPS
        bt2 = fnt_or.render(f"{t('sure')}: {sure_sn//60:02d}:{sure_sn%60:02d}   {t('seviye')}: {seviye}", True, BEYAZ)
        ekran.blit(bt2, (GENISLIK//2 - bt2.get_width()//2, YUKSEKLIK//2-60))
        bt3 = fnt_or.render(f"{t('oldurulen')} {t('dusman')}: {oldurulen}", True, BEYAZ)
        ekran.blit(bt3, (GENISLIK//2 - bt3.get_width()//2, YUKSEKLIK//2-20))
        fare_x, fare_y = pygame.mouse.get_pos()
        buton_ciz(ekran, devam_buton_rect, t('ana_menuye_don'), (fare_x, fare_y))
        pygame.display.flip()
        await asyncio.sleep(0)

        for olay in pygame.event.get():
            if olay.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if olay.type == pygame.KEYDOWN and olay.key == pygame.K_ESCAPE:
                return
            if olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1:
                if devam_buton_rect.collidepoint(olay.pos):
                    return


# ══════════════════════════════════════════
#  BAŞLAT
# ══════════════════════════════════════════
async def main():
    ilk_acilis = True

    while True:
        if ilk_acilis:
            await hikaye_ekrani(ekran)
            ilk_acilis = False

        baslangic = await ana_menu()
        if baslangic is None:
            continue

        sahip_silahlar = [0]
        secili = 0
        toplam_para = 0

        sonuc = await oyun(baslangic, toplam_para, sahip_silahlar, secili)

        if sonuc is None:
            continue

        durum, skor, para = sonuc

        # Sonuç ekranı
        tekrar_rect = pygame.Rect(GENISLIK//2 - 230, 400, 210, 50)
        menu_rect = pygame.Rect(GENISLIK//2 + 20, 400, 210, 50)
        canlan_rect = pygame.Rect(GENISLIK//2 - 140, 470, 280, 50)
        while True:
            saat.tick(FPS)
            ekran.fill(KOYU)
            pygame.draw.rect(ekran, CYAN, (0,0,GENISLIK,YUKSEKLIK), 3)

            if durum == 'kazandin':
                b = fnt_by.render(t('tebrikler_kazandin'), True, TURUNCU)
                ekran.blit(b, (GENISLIK//2 - b.get_width()//2, 180))
            else:
                b = fnt_by.render(t('game_over'), True, KIRMIZI)
                ekran.blit(b, (GENISLIK//2 - b.get_width()//2, 180))

            s1 = fnt_or.render(t('skor_para', skor=skor, para=para), True, BEYAZ)
            ekran.blit(s1, (GENISLIK//2 - s1.get_width()//2, 250))
            s2 = fnt_kk.render(t('enter_tekrar'), True, (110,140,150))
            ekran.blit(s2, (GENISLIK//2 - s2.get_width()//2, 340))

            fare_x, fare_y = pygame.mouse.get_pos()
            buton_ciz(ekran, tekrar_rect, t('tekrar_oyna'), (fare_x, fare_y))
            buton_ciz(ekran, menu_rect, t('ana_menuye_don'), (fare_x, fare_y))

            canli_kaldi = False
            if durum == 'kaybettin':
                uzerinde = canlan_rect.collidepoint(fare_x, fare_y)
                renk = (0,255,200) if uzerinde else (255,210,0)
                zemin = (20,45,40) if uzerinde else (40,32,0)
                pygame.draw.rect(ekran, zemin, canlan_rect)
                pygame.draw.rect(ekran, renk, canlan_rect, 2)
                # küçük "reklam" simgesi: TV çerçevesi + play üçgeni
                ikon_rect = pygame.Rect(canlan_rect.left + 12, canlan_rect.centery - 12, 34, 24)
                pygame.draw.rect(ekran, renk, ikon_rect, 2)
                uc = [(ikon_rect.left+11, ikon_rect.top+5), (ikon_rect.left+11, ikon_rect.bottom-5), (ikon_rect.right-8, ikon_rect.centery)]
                pygame.draw.polygon(ekran, renk, uc)
                yz = fnt_or.render(t('canlan'), True, renk)
                ekran.blit(yz, (ikon_rect.right + 14, canlan_rect.centery - yz.get_height()//2))

            pygame.display.flip()
            await asyncio.sleep(0)

            cik = False
            canlan_tiklandi = False
            for olay in pygame.event.get():
                if olay.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if olay.type == pygame.KEYDOWN:
                    if olay.key == pygame.K_RETURN:
                        cik = True
                    if olay.key == pygame.K_ESCAPE:
                        cik = True
                if olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1:
                    if tekrar_rect.collidepoint(olay.pos) or menu_rect.collidepoint(olay.pos):
                        cik = True
                    elif durum == 'kaybettin' and canlan_rect.collidepoint(olay.pos):
                        canlan_tiklandi = True
            if canlan_tiklandi:
                # "Reklam izle" yerine (henüz gerçek reklam SDK'sı yok) doğrudan aynı bölümden canlan
                sonuc = await oyun(baslangic, toplam_para, sahip_silahlar, secili)
                if sonuc is None:
                    break
                durum, skor, para = sonuc
                continue
            if cik:
                break


asyncio.run(main())
