import Phaser from 'phaser';

// Mirrors the Python original's `buton_ciz`: bordered rect, TURUNCU/black
// normal state, cyan-green/dark-teal hover state.
const SECILI_MAVI = 0x2288ff;

export function makeButton(scene, x, y, w, h, label, onClick, fontSize = '16px') {
  const bg = scene.add.rectangle(x, y, w, h, 0x000000).setStrokeStyle(2, 0xf5a623).setInteractive({ useHandCursor: true });
  const text = scene.add.text(x, y, label, { fontFamily: 'monospace', fontSize, color: '#f5a623' }).setOrigin(0.5);

  const btn = { bg, text, selected: false };

  const repaint = (hover) => {
    if (btn.selected) {
      bg.setFillStyle(SECILI_MAVI);
      bg.setStrokeStyle(2, 0x66bbff);
      text.setColor('#ffffff');
    } else {
      bg.setFillStyle(hover ? 0x142d28 : 0x000000);
      bg.setStrokeStyle(2, hover ? 0x00ffc8 : 0xf5a623);
      text.setColor(hover ? '#00ffc8' : '#f5a623');
    }
  };

  bg.on('pointerover', () => repaint(true));
  bg.on('pointerout', () => repaint(false));
  bg.on('pointerdown', onClick);

  // Marks this button as the current choice in a multi-option group — fills
  // it solid blue so the selection reads clearly (see SECILI_MAVI usage
  // across Settings/HeroSelect/etc for every "which one is picked" control).
  btn.setSelected = (selected) => { btn.selected = selected; repaint(false); };

  return btn;
}
