const express = require('express');
const { Pool } = require('pg');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

// Pool reads standard PG* env vars (PGHOST, PGUSER, PGPASSWORD, PGDATABASE, PGPORT)
const pool = new Pool({
  host: process.env.PGHOST,
  user: process.env.PGUSER,
  password: process.env.PGPASSWORD,
  database: process.env.PGDATABASE,
  port: process.env.PGPORT || 5432,
  connectionTimeoutMillis: 2000,
});

let dbReady = false;

async function initDb() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS todos (
      id SERIAL PRIMARY KEY,
      title TEXT NOT NULL,
      done BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMP DEFAULT NOW()
    );
  `);
  dbReady = true;
}

// --- LIVENESS: process is up and event loop is responsive. Never touches the DB. ---
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'alive' });
});

// --- READINESS: pod should only receive traffic if it can actually serve requests ---
app.get('/ready', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    res.status(200).json({ status: 'ready', db: 'connected' });
  } catch (err) {
    res.status(503).json({ status: 'not ready', db: 'unreachable', error: err.message });
  }
});

app.get('/todos', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM todos ORDER BY id DESC');
    res.json(result.rows);
  } catch (err) {
    console.error('DB query failed:', err.message);
    res.status(500).json({ error: 'database error', detail: err.message });
  }
});

app.post('/todos', async (req, res) => {
  const { title } = req.body;
  if (!title) return res.status(400).json({ error: 'title is required' });
  try {
    const result = await pool.query(
      'INSERT INTO todos (title) VALUES ($1) RETURNING *',
      [title]
    );
    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error('DB insert failed:', err.message);
    res.status(500).json({ error: 'database error', detail: err.message });
  }
});

app.get('/', (req, res) => {
  res.json({ service: 'devops-challenge-backend', version: '1.0.0' });
});

app.listen(PORT, () => {
  console.log(`Backend listening on port ${PORT}`);
  // Retry DB init in the background so the process still starts (liveness passes)
  // even if the DB isn't up yet — readiness will correctly report not-ready until it is.
  const tryInit = () => {
    initDb().catch((err) => {
      console.error('DB init failed, retrying in 3s:', err.message);
      setTimeout(tryInit, 3000);
    });
  };
  tryInit();
});
