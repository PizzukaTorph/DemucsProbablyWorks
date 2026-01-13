const path = require('path');

function runDemucs(filename, model = 'htdemucs_6s') {
  // Il demucs worker (container demucs) guarda la cartella uploads e processa i file.
  // Qui ritorniamo il percorso in cui il worker genererà i file una volta completato.
  const nameNoExt = path.parse(filename).name;
  const outputDir = path.join('output', model, nameNoExt);
  return Promise.resolve(outputDir);
}

module.exports = { runDemucs };