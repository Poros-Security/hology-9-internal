// server.js - Main Application
const express = require('express');
const bodyParser = require('body-parser');
const session = require('express-session');
const morgan = require('morgan');
const { reviewLetter } = require('./bot');
const { initDB, userOps, letterOps } = require('./database');
const app = express();
const PORT = 7777;
const USER_SECRET = process.env.USER_SECRET || 'u53R_S3cR37_0e115794';
const BOT_SECRET = process.env.BOT_SECRET || 'b0T_53Cr3t_14377ec1';

// Initialize database
initDB();

// HTTP request logging
app.use(morgan('combined'));

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(express.static('public'));
app.set('view engine', 'ejs');

// Session untuk tracking user
app.use(session({
  secret: USER_SECRET,
  resave: false,
  saveUninitialized: true,
  cookie: { secure: false }
}));

// Middleware untuk check login
function requireLogin(req, res, next) {
  if (!req.session.username) {
    return res.redirect('/login');
  }
  next();
}

// Halaman login
app.get('/login', (req, res) => {
  if (req.session.username) {
    return res.redirect('/');
  }
  res.render('login', { error: null });
});

// Proses login
app.post('/login', (req, res) => {
  const { username, password } = req.body;
  
  const user = userOps.findByUsername(username);
  if (!user || user.password !== password) {
    return res.render('login', { error: 'Username atau password salah' });
  }
  
  req.session.username = username;
  res.redirect('/');
});

// Halaman register
app.get('/register', (req, res) => {
  if (req.session.username) {
    return res.redirect('/');
  }
  res.render('register', { error: null });
});

// Proses register
app.post('/register', (req, res) => {
  const { username, password } = req.body;
  
  if (userOps.exists(username)) {
    return res.render('register', { error: 'Username sudah digunakan' });
  }
  
  if (username.length < 3 || password.length < 4) {
    return res.render('register', { error: 'Username minimal 3 karakter, password minimal 4 karakter' });
  }
  
  try {
    userOps.create(username, password);
    req.session.username = username;
    res.redirect('/');
  } catch (error) {
    res.render('register', { error: 'Terjadi kesalahan saat registrasi' });
  }
});

// Logout
app.post('/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/login');
});

// Home page - form buat surat izin (requires login)
app.get('/', requireLogin, (req, res) => {
  const username = req.session.username;
  
  // Hanya tampilkan surat milik user ini
  const userLetters = letterOps.findByUsername(username);
  
  res.render('index', { letters: userLetters, username });
});

// Submit surat izin baru (requires login)
app.post('/submit', requireLogin, async (req, res) => {
  const { name, reason } = req.body;
  const username = req.session.username;
  
  const letterId = letterOps.create(name, reason, username);
  
  // Trigger bot review (async)
  setTimeout(() => {
    reviewLetter(letterId).then(() => {
      letterOps.updateStatus(letterId, 'Rejected');
    });
  }, 1000);
  
  res.redirect('/');
});

// Halaman review untuk bot (hanya bot yang bisa akses)
app.get('/review/:id', (req, res) => {
  // Check apakah request dari bot (via custom header)
  const botSecret = req.headers['x-bot-secret'];
  const expectedSecret = BOT_SECRET;
  
  if (botSecret !== expectedSecret) {
    return res.status(403).send('PERGI KAMU, KAMU BUKAN DOSEN !!!');
  }
  
  const letterId = parseInt(req.params.id);
  const letter = letterOps.findById(letterId);
  
  if (!letter) {
    return res.status(404).send('Letter not found');
  }
  
  res.render('review', { letter });
});

app.listen(PORT, () => {
  console.log(`[SERVER] Running on http://localhost:${PORT}`);
});
