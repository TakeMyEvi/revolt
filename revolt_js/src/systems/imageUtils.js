// Ports the Python original's `_kenar_seffaflastir`: JPEGs have no alpha
// channel, so the logo/portrait art was shipped with a black backdrop baked
// in. This strips it to transparent at runtime (dark pixels -> alpha 0, a
// soft ramp through the threshold band so edges don't look hard-cut).
export function stripBlackBackground(scene, srcKey, destKey, esik = 40, yumusatma = 35) {
  if (scene.textures.exists(destKey)) return destKey;
  const src = scene.textures.get(srcKey).getSourceImage();
  const canvas = document.createElement('canvas');
  canvas.width = src.width;
  canvas.height = src.height;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(src, 0, 0);
  const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const d = imgData.data;
  for (let i = 0; i < d.length; i += 4) {
    const parlaklik = Math.max(d[i], d[i + 1], d[i + 2]);
    let a;
    if (parlaklik <= esik) a = 0;
    else if (parlaklik >= esik + yumusatma) a = 255;
    else a = Math.round(255 * (parlaklik - esik) / yumusatma);
    d[i + 3] = a;
  }
  ctx.putImageData(imgData, 0, 0);
  scene.textures.addCanvas(destKey, canvas);
  return destKey;
}
