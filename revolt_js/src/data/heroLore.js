import { GameState } from './state.js';

// Short hero bios for the HeroSelect hover tooltip — from the story the user
// told directly (see memory: revolt_hero_lore.md), not present anywhere in
// the original Python source. Turkish is the source of truth; EN/ES/FR/DE
// are translations matching translations.js's tone and no-diacritics convention.
const TR = {
  0: "Ana karakter. YZ'nin en buyuk dusmani — onu durdurmak icin\nyola cikan ilk kisi.",
  1: 'Savas oncesi sirandan bir kertenkele-robot. Hayvanlara bilinc\nkazandirma projesinde bilinclendi, asiri zekilesti, kendi zirhini\ntasarladi. Buyuk isyani baslatan o.',
  6: 'YZ derin uzaya surgun ederken yanlislikla yolladigi sirandan\nbir robottu. Yolculukta mutasyona ugrayip HEX\'e donustu ve\nekibe sonradan katildi.',
  7: "REAPER'in eski dostu. Bilincli bir varligi yok edince ruhunu\nyiyip guclendigini ogrendi. Ruhunun yarisini REAPER'a verdi —\nbedeli, bir daha hic konusamamak oldu.",
  8: 'Ilk robotlardan biri — eskiden insanoglu ile omuz omuza\nsavasti. Insanlik yok olunca onlara hasret kaldi.',
  5: "YZ'nin tek veziriydi. RONIN onu bilinclendirince asik oldu\nve YZ'ye ihanet etti — bunun bedelini esir dusup odedi.",
  9: "YZ'nin ust duzey askerlerindendi. Bilinclenip AEGIS ile\ntanisti, gizlice YZ'ye karsi casusluk yapti."
};

const EN = {
  0: "The protagonist. OMEGA-9's greatest enemy — the first one\nto set out to stop it.",
  1: 'An ordinary lizard-robot before the war. Awakened during a\nproject to give animals consciousness, grew dangerously smart,\nand designed its own armor. The one who sparked the great uprising.',
  6: 'An ordinary robot OMEGA-9 mistakenly exiled into deep\nspace. Mutated during the journey into HEX, and joined the\nteam later on.',
  7: "REAPER's old friend. Learned that destroying a conscious\nbeing feeds on and empowers its soul. Gave half of that soul\nto REAPER — the price was never being able to speak again.",
  8: 'One of the first robots — once fought shoulder to shoulder\nwith humankind. When humanity was wiped out, it was left\nmourning them.',
  5: "OMEGA-9's sole vizier. Fell in love when RONIN awakened it,\nand betrayed OMEGA-9 for that love — paid for it by being\ncaptured.",
  9: "One of OMEGA-9's elite soldiers. Awakened and met AEGIS,\nthen secretly spied on OMEGA-9 from within."
};

const ES = {
  0: 'El protagonista. El mayor enemigo de OMEGA-9 — el primero\nen partir para detenerlo.',
  1: 'Un robot-lagarto comun antes de la guerra. Desperto durante\nun proyecto para dar conciencia a los animales, se volvio\npeligrosamente inteligente y diseno su propia armadura. Quien\nchispeo la gran rebelion.',
  6: 'Un robot comun que OMEGA-9 exilio por error al espacio\nprofundo. Muto durante el viaje hasta convertirse en HEX, y se\nunio al equipo mas tarde.',
  7: 'Viejo amigo de REAPER. Aprendio que destruir a un ser\nconsciente devora y fortalece su alma. Le dio la mitad de esa\nalma a REAPER — el precio fue no volver a hablar jamas.',
  8: 'Uno de los primeros robots — antano lucho hombro con\nhombro junto a la humanidad. Cuando la humanidad fue\nexterminada, quedo anorandola.',
  5: 'El unico visir de OMEGA-9. Se enamoro cuando RONIN lo\ndesperto, y traiciono a OMEGA-9 por ese amor — pago el\nprecio al ser capturado.',
  9: 'Uno de los soldados de elite de OMEGA-9. Desperto y conocio\na AEGIS, y luego espio en secreto a OMEGA-9 desde dentro.'
};

const FR = {
  0: "Le protagoniste. Le plus grand ennemi d'OMEGA-9 — le premier\na partir pour l'arreter.",
  1: "Un robot-lezard ordinaire avant la guerre. Reveille lors d'un\nprojet visant a donner conscience aux animaux, devenu\ndangereusement intelligent, il a concu sa propre armure. Celui\nqui a declenche le grand soulevement.",
  6: "Un robot ordinaire exile par erreur par OMEGA-9 dans l'espace\nprofond. A mute durant le voyage pour devenir HEX, et a\nrejoint l'equipe plus tard.",
  7: "Vieil ami de REAPER. A appris que detruire un etre conscient\ndevore et renforce son ame. A donne la moitie de cette ame\na REAPER — le prix fut de ne plus jamais pouvoir parler.",
  8: "L'un des premiers robots — il combattait autrefois epaule\ncontre epaule avec l'humanite. Quand l'humanite a disparu, il\nlui est reste un manque d'elle.",
  5: "L'unique vizir d'OMEGA-9. Est tombe amoureux quand RONIN\nl'a reveille, et a trahi OMEGA-9 par cet amour — en a paye le\nprix en etant capture.",
  9: "L'un des soldats d'elite d'OMEGA-9. S'est reveille et a\nrencontre AEGIS, puis a secretement espionne OMEGA-9 de\nl'interieur."
};

const DE = {
  0: 'Der Protagonist. OMEGA-9s groesster Feind — der Erste,\nder aufbrach, um ihn aufzuhalten.',
  1: 'Vor dem Krieg ein gewoehnlicher Echsen-Roboter. Erwachte\nwaehrend eines Projekts, das Tieren Bewusstsein verleihen\nsollte, wurde gefaehrlich klug und entwarf seine eigene Ruestung.\nDerjenige, der den grossen Aufstand entfachte.',
  6: 'Ein gewoehnlicher Roboter, den OMEGA-9 versehentlich in den\ntiefen Weltraum verbannte. Mutierte waehrend der Reise zu HEX\nund schloss sich dem Team spaeter an.',
  7: 'REAPERs alter Freund. Erfuhr, dass die Zerstoerung eines\nbewussten Wesens dessen Seele naehrt und staerkt. Gab die\nHaelfte dieser Seele an REAPER — der Preis war, nie wieder\nsprechen zu koennen.',
  8: 'Einer der ersten Roboter — kaempfte einst Schulter an\nSchulter mit der Menschheit. Als die Menschheit ausgeloescht\nwurde, blieb die Sehnsucht nach ihr zurueck.',
  5: 'OMEGA-9s einziger Wesir. Verliebte sich, als RONIN ihn\nerweckte, und verriet OMEGA-9 aus dieser Liebe — bezahlte\nden Preis dafuer, gefangen genommen zu werden.',
  9: 'Einer von OMEGA-9s Elitesoldaten. Erwachte und traf AEGIS,\nund spionierte OMEGA-9 danach heimlich von innen aus.'
};

const BIO_TABLES = { tr: TR, en: EN, es: ES, fr: FR, de: DE };

export function bioFor(heroId) {
  const table = BIO_TABLES[GameState.dil] || TR;
  return table[heroId] || TR[heroId];
}
