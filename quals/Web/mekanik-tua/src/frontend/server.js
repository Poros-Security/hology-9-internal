const express = require('express')
const session = require('cookie-session')

const API = process.env.BACKEND_URL || 'http://localhost:8080'
const PROXIED = new Set(['list', 'get', 'create', 'vehicles', 'addVehicle'])

const badges = { antri: 'default', dikerjakan: 'info', 'tunggu-sparepart': 'warning', selesai: 'success' }

const messages = {
  'invalid username': 'Username hanya boleh huruf, angka dan garis bawah, 3 sampai 20 karakter.',
  'password too short': 'Password minimal 8 karakter.',
  'invalid phone': 'Nomor HP tidak sesuai.',
  'username taken': 'Username sudah dipakai.',
  'bad credentials': 'Username atau password salah.',
  'current password incorrect': 'Password lama salah.',
  'invalid plate': 'Plat nomor tidak sesuai. Contoh: N 1234 ABC.',
  'invalid vehicle': 'Model dan tahun motor harus diisi.',
  'complaint is required': 'Keluhan harus diisi.',
}

const message = body =>
  body.error === 'account locked'
    ? 'Akun dikunci karena terlalu banyak percobaan login. Tunggu ' + Math.ceil(body.retry_in / 60) + ' menit lagi.'
    : messages[body.error] || 'Terjadi kesalahan, coba lagi.'

const app = express()
app.set('view engine', 'ejs')
app.use(express.static('public'))
app.use(session({ name: 'sid', secret: process.env.SESSION_SECRET || 'dev', maxAge: 86400000 }))

async function api(req, action, params = {}) {
  const url = new URL(API)
  url.searchParams.set('action', action)

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) url.searchParams.set(key, value)
  }

  const headers = {}
  if (req.session.apiSid) headers.cookie = 'api_sid=' + req.session.apiSid

  const response = await fetch(url, { headers })

  return { status: response.status, body: await response.json() }
}

app.use('/api', async (req, res) => {
  const { action } = req.query

  if (!PROXIED.has(action)) return res.status(400).json({ error: 'bad action' })

  const cookies = (req.headers.cookie || '').split(';').map(c => c.trim()).filter(c => c && !c.startsWith('api_sid='))
  if (req.session.apiSid) cookies.push('api_sid=' + req.session.apiSid)

  const init = { method: req.method, headers: { cookie: cookies.join('; ') } }

  if (req.method !== 'GET' && req.method !== 'HEAD') {
    init.body = req
    init.duplex = 'half'
    if (req.headers['content-type']) init.headers['content-type'] = req.headers['content-type']
  }

  const response = await fetch(API + req.url, init)

  res.status(response.status).type('application/json').send(await response.text())
})

app.use(express.urlencoded({ extended: false }))

app.use(async (req, res, next) => {
  res.locals.user = null
  res.locals.path = req.path
  res.locals.badges = badges

  if (req.session.apiSid) {
    const { body } = await api(req, 'me')
    if (body.user) res.locals.user = body.user
    else req.session = null
  }

  next()
})

const auth = (req, res, next) => (res.locals.user ? next() : res.redirect('/login'))

app.get('/', (req, res) => res.render('index'))

app.get('/register', (req, res) => res.render('register', { error: null }))
app.post('/register', async (req, res) => {
  const { username, password, phone } = req.body
  const created = await api(req, 'register', { username, password, phone })

  if (!created.body.ok) return res.render('register', { error: message(created.body) })

  const login = await api(req, 'login', { u: username, p: password })
  req.session.apiSid = login.body.sid

  res.redirect('/jobs')
})

app.get('/login', (req, res) => res.render('login', { error: null }))
app.post('/login', async (req, res) => {
  const { body } = await api(req, 'login', { u: req.body.username, p: req.body.password })

  if (!body.ok) return res.render('login', { error: message(body) })

  if (body.role !== 'customer') {
    return res.render('login', { error: 'Akun ini tidak bisa dipakai di portal pelanggan.' })
  }

  req.session.apiSid = body.sid

  res.redirect('/jobs')
})

app.post('/logout', (req, res) => {
  req.session = null
  res.redirect('/')
})

app.get('/jobs', auth, async (req, res) => {
  const { body } = await api(req, 'list')
  res.render('jobs', { jobs: body.jobs })
})

app.get('/jobs/new', auth, async (req, res) => {
  const { body } = await api(req, 'vehicles')
  res.render('new', { vehicles: body.vehicles, error: null })
})

app.post('/jobs', auth, async (req, res) => {
  const { plate, model, year, complaint } = req.body
  let vehicleId = req.body.vehicle_id

  const back = async error => {
    const { body } = await api(req, 'vehicles')
    res.render('new', { vehicles: body.vehicles, error })
  }

  if (!vehicleId) {
    const added = await api(req, 'addVehicle', { plate, model, year })
    if (!added.body.ok) return back(message(added.body))
    vehicleId = added.body.id
  }

  const created = await api(req, 'create', { vehicle_id: vehicleId, complaint })

  if (!created.body.ok) return back(message(created.body))

  res.redirect('/jobs/' + created.body.id)
})

app.get('/jobs/:id', auth, async (req, res) => {
  const { status, body } = await api(req, 'get', { id: req.params.id })

  if (status !== 200) return res.sendStatus(404)

  res.render('job', { job: body.job, notes: body.notes })
})

app.get('/profile', auth, async (req, res) => {
  const { body } = await api(req, 'vehicles')
  res.render('profile', { vehicles: body.vehicles, msg: null })
})

app.post('/profile/password', auth, async (req, res) => {
  const changed = await api(req, 'changePassword', { current: req.body.current, password: req.body.password })
  const { body } = await api(req, 'vehicles')

  const msg = changed.body.ok
    ? { type: 'success', text: 'Password sudah diganti.' }
    : { type: 'danger', text: message(changed.body) }

  res.render('profile', { vehicles: body.vehicles, msg })
})

app.listen(3000)
