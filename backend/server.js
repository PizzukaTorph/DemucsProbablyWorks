// ...existing code...
const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { runDemucs } = require('./runDemucs');
const app = express();
const port = process.env.PORT || 3000;
const host = '0.0.0.0';

// Configure dirs (use mounted dirs in containers)
const UPLOAD_DIR = process.env.UPLOAD_DIR || '/app/uploads';
const OUTPUT_DIR = process.env.OUTPUT_DIR || '/app/output';
const STATUS_DIR = path.join(OUTPUT_DIR, 'status');

// Ensure directories exist
fs.mkdirSync(UPLOAD_DIR, { recursive: true });
fs.mkdirSync(OUTPUT_DIR, { recursive: true });
fs.mkdirSync(STATUS_DIR, { recursive: true });

// Multer storage to keep original filename (prefixed to avoid collisions)
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOAD_DIR),
  filename: (req, file, cb) => {
    const safeName = path.basename(file.originalname).replace(/\s+/g, '_');
    cb(null, `${Date.now()}-${safeName}`);
  },
});
const upload = multer({ storage });

// Simple health check
app.get('/health', (req, res) => res.json({ ok: true }));

// Serve static public files
app.use(express.static(path.join(__dirname, 'public')));

// root -> index.html from public
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Expose uploaded files and outputs for quick inspection
app.use('/uploads', express.static(UPLOAD_DIR));
app.use('/output', express.static(OUTPUT_DIR));

// Endpoint per upload + separazione
app.post('/upload', upload.single('file'), async (req, res) => {
  try {
    const file = req.file;
    const model = req.body.model || 'htdemucs_6s';

    if (!file) {
      return res.status(400).send('Nessun file caricato.');
    }

    // create initial status file
    const statusPath = path.join(STATUS_DIR, `${file.filename}.json`);
    const init = {
      status: 'queued',
      filename: file.filename,
      uploaded: `/uploads/${file.filename}`,
      model,
      progress: 0,
      logs: []
    };
    fs.writeFileSync(statusPath, JSON.stringify(init, null, 2));

    // runDemucs returns the expected output dir (relative path like output/<model>/<name>)
    const outputPath = await runDemucs(file.filename, model);

    // Return useful info to the client
    res.json({
      message: 'File caricato correttamente. Demucs worker elaborerà il file.',
      filename: file.filename,
      uploaded: `/uploads/${file.filename}`,
      expectedOutput: `/${outputPath.replace(/\\\\/g, '/')}`,
    });
  } catch (err) {
    console.error(err);
    res.status(500).send('Errore nella separazione.');
  }
});

// Status endpoint (reads JSON status file written by watcher)
app.get('/status', (req, res) => {
  const filename = req.query.file;
  if (!filename) return res.status(400).send({ error: 'file query required' });
  const statusPath = path.join(STATUS_DIR, `${filename}.json`);
  if (!fs.existsSync(statusPath)) return res.status(404).send({ error: 'status not found' });
  try {
    const raw = fs.readFileSync(statusPath, 'utf8');
    const parsed = JSON.parse(raw);
    res.type('application/json').send(parsed);
  } catch (err) {
    res.status(500).send({ error: 'cannot read status' });
  }
});

app.listen(port, host, () => {
  console.log(`Backend Node in ascolto su http://${host}:${port}`);
});