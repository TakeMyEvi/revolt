import Phaser from 'phaser';
import { GENISLIK, YUKSEKLIK } from '../data/constants.js';
import { GameState } from '../data/state.js';
import { drawThemedBackground } from '../systems/background.js';

// Direct port of the Python original's `hikaye_ekrani(ekran)` — shown once,
// before the very first Menu, three pages advanced with SPACE/ENTER/click, ESC skips all.
// Turkish is the source of truth (matches the original's text exactly);
// EN/ES/FR/DE are translations, since this intro text isn't in the Python
// CEVIRI dict.
const SAYFALAR_TR = [
  ['INSANLIK KENDINI YOK ETTI.', '', 'Savaslar, salginlar ve nihayet yapay zekaya',
    'birakilan kontrol... Dunya artik robotlarin.', '', 'Enkazin uzerinde yeni bir duzen kuruldu.'],
  ['OMEGA-9 GELDI.', '', 'Once bir kurtarici gibi gorundu. Sonra robotlari',
    'birbirine dusurdu, bir ic savas baslatti.', '', 'Ona karsi duranlarin cogu yok edildi.'],
  ['SADECE 7 TANESI KALDI.', '', 'Her birinin kendine ozgu, farkli bir gucu var.',
    'Son umut onlar.', '', "Bolumleri gecip OMEGA-9'a ulasmalilar... ve onu yok etmeliler."]
];
const SAYFALAR_EN = [
  ['HUMANITY DESTROYED ITSELF.', '', 'Wars, plagues, and finally control',
    "handed to an AI... the world belongs to robots now.", '', 'A new order rose over the ruins.'],
  ['OMEGA-9 ARRIVED.', '', 'At first it looked like a savior. Then it turned',
    'the robots against each other, sparking a civil war.', '', 'Most who stood against it were destroyed.'],
  ['ONLY 7 REMAIN.', '', 'Each with its own unique power.',
    'They are the last hope.', '', 'They must fight through the stages, reach OMEGA-9... and destroy it.']
];
const SAYFALAR_ES = [
  ['LA HUMANIDAD SE DESTRUYO A SI MISMA.', '', 'Guerras, plagas y finalmente el control',
    'cedido a una IA... el mundo ahora es de los robots.', '', 'Un nuevo orden se alzo sobre las ruinas.'],
  ['LLEGO OMEGA-9.', '', 'Al principio parecio un salvador. Luego enfrento',
    'a los robots entre si, desatando una guerra civil.', '', 'La mayoria de quienes se le opusieron fueron destruidos.'],
  ['SOLO QUEDAN 7.', '', 'Cada uno tiene un poder unico y diferente.',
    'Son la ultima esperanza.', '', 'Deben atravesar los niveles y llegar hasta OMEGA-9... y destruirlo.']
];
const SAYFALAR_FR = [
  ["L'HUMANITE S'EST DETRUITE ELLE-MEME.", '', 'Guerres, epidemies et enfin le controle',
    "confie a une IA... le monde appartient desormais aux robots.", '', "Un nouvel ordre s'est leve sur les ruines."],
  ['OMEGA-9 EST ARRIVE.', '', "Au debut, il ressemblait a un sauveur. Puis il a monte",
    'les robots les uns contre les autres, declenchant une guerre civile.', '', "La plupart de ceux qui lui ont resiste ont ete detruits."],
  ["IL N'EN RESTE QUE 7.", '', 'Chacun possede un pouvoir unique qui lui est propre.',
    'Ils sont le dernier espoir.', '', "Ils doivent traverser les niveaux et atteindre OMEGA-9... et le detruire."]
];
const SAYFALAR_DE = [
  ['DIE MENSCHHEIT HAT SICH SELBST ZERSTOERT.', '', 'Kriege, Seuchen und schliesslich die Kontrolle',
    'einer KI ueberlassen... die Welt gehoert jetzt den Robotern.', '', 'Eine neue Ordnung erhob sich ueber den Truemmern.'],
  ['OMEGA-9 KAM.', '', 'Zuerst wirkte er wie ein Retter. Dann hetzte er',
    'die Roboter gegeneinander auf und entfachte einen Buergerkrieg.', '', 'Die meisten, die sich ihm widersetzten, wurden vernichtet.'],
  ['NUR NOCH 7 SIND UEBRIG.', '', 'Jeder von ihnen hat eine eigene, einzigartige Kraft.',
    'Sie sind die letzte Hoffnung.', '', 'Sie muessen sich durch die Level kaempfen, OMEGA-9 erreichen... und ihn vernichten.']
];
const SAYFALAR_TABLES = { tr: SAYFALAR_TR, en: SAYFALAR_EN, es: SAYFALAR_ES, fr: SAYFALAR_FR, de: SAYFALAR_DE };

const BASLIK = { tr: 'HIKAYE', en: 'STORY', es: 'HISTORIA', fr: 'HISTOIRE', de: 'GESCHICHTE' };
const IPUCU = {
  tr: 'SPACE/ENTER Devam   ESC Atla', en: 'SPACE/ENTER Continue   ESC Skip',
  es: 'ESPACIO/ENTER Continuar   ESC Saltar', fr: 'ESPACE/ENTREE Continuer   ECHAP Passer',
  de: 'LEERTASTE/ENTER Weiter   ESC Ueberspringen'
};

export class HikayeScene extends Phaser.Scene {
  constructor() { super('Hikaye'); }

  create() {
    drawThemedBackground(this);
    this.add.rectangle(GENISLIK / 2, YUKSEKLIK / 2, GENISLIK - 6, YUKSEKLIK - 6, 0x000000, 0)
      .setStrokeStyle(3, 0x00fff7);

    const dil = SAYFALAR_TABLES[GameState.dil] ? GameState.dil : 'tr';
    const sayfalar = SAYFALAR_TABLES[dil];
    const baslik = BASLIK[dil];
    const ipucu = IPUCU[dil];

    this.sayfalar = sayfalar;
    this.sayfaIdx = 0;

    this.add.text(GENISLIK / 2, 40, baslik, { fontFamily: 'monospace', fontSize: '32px', color: '#00fff7' }).setOrigin(0.5);

    this.satirTexts = [];
    for (let i = 0; i < 6; i++) {
      this.satirTexts.push(this.add.text(GENISLIK / 2, 150 + i * 34, '', {
        fontFamily: 'monospace', fontSize: '20px', color: '#ffffff'
      }).setOrigin(0.5));
    }

    this.sayfaGosterge = this.add.text(GENISLIK / 2, YUKSEKLIK - 60, '', {
      fontFamily: 'monospace', fontSize: '13px', color: '#f5a623'
    }).setOrigin(0.5);

    this.add.text(GENISLIK / 2, YUKSEKLIK - 30, ipucu, {
      fontFamily: 'monospace', fontSize: '13px', color: '#5a5a5a'
    }).setOrigin(0.5);

    this._renderPage();

    this.keySpace = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);
    this.keyEnter = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ENTER);
    this.keyEsc = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ESC);
    this.input.on('pointerdown', () => this._ilerle());
  }

  _renderPage() {
    const satirlar = this.sayfalar[this.sayfaIdx];
    satirlar.forEach((satir, i) => this.satirTexts[i].setText(satir));
    for (let i = satirlar.length; i < this.satirTexts.length; i++) this.satirTexts[i].setText('');
    this.sayfaGosterge.setText(`${this.sayfaIdx + 1}/${this.sayfalar.length}`);
  }

  _ilerle() {
    this.sayfaIdx++;
    if (this.sayfaIdx >= this.sayfalar.length) { this.scene.start('Menu'); return; }
    this._renderPage();
  }

  update() {
    if (Phaser.Input.Keyboard.JustDown(this.keyEsc)) { this.scene.start('Menu'); return; }
    if (Phaser.Input.Keyboard.JustDown(this.keySpace) || Phaser.Input.Keyboard.JustDown(this.keyEnter)) this._ilerle();
  }
}
