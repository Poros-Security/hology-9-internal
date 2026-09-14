const { randomBytes } = require('crypto')

const data = require('./db')
const password = require('./password')

const flag = process.env.GZCTF_FLAG

if (!flag) {
  console.error('GZCTF_FLAG is not set')
  process.exit(1)
}

const daysAgo = days => {
  const when = new Date(Date.now() - days * 86400000)
  when.setUTCHours(2 + (days % 7), (days * 13) % 60, 0, 0)
  return when.toISOString()
}

const people = [
  ['rina.w', 'Rina Wijaya', 'employee', 'ledger2026'],
  ['dimas.p', 'Dimas Prakoso', 'employee', randomBytes(24).toString('hex')],
  ['budi.h', 'Budi Hartono', 'finance', randomBytes(24).toString('hex')],
  ['agung.s', 'Agung Setiawan', 'staff', randomBytes(24).toString('hex')],
]

const vendors = [
  ['PT Sinar Abadi Teknik', '01.234.567.8-051.000', '8820114477'],
  ['CV Mitra Solusi Data', '02.998.114.3-014.000', '1390025588'],
  ['PT Karya Bangun Perkasa', '31.447.902.1-092.000', '7011336699'],
  ['CV Anugerah Percetakan', '09.556.238.4-033.000', '2450118833'],
  ['PT Cipta Logistik Nusantara', '44.201.776.5-071.000', '6680042211'],
]

const invoices = [
  {
    vendor: 0, owner: 0, status: 'approved', created: 48, decided: 45,
    description: 'Perawatan genset gedung B, periode Juli',
    note: 'Kontrak tahunan, sudah dicek sama pak Agung.',
    items: [['Servis berkala genset 150 kVA', 2, 1500000], ['Filter solar dan oli', 12, 100000]],
  },
  {
    vendor: 1, owner: 0, status: 'approved', created: 31, decided: 28,
    description: 'Perpanjangan lisensi backup server, 12 bulan',
    note: flag,
    items: [['Lisensi agent per server', 18, 1250000], ['Dukungan teknis tahunan', 1, 7500000]],
  },
  {
    vendor: 3, owner: 0, status: 'rejected', created: 22, decided: 20,
    description: 'Cetak kalender dan agenda perusahaan',
    note: 'Lampiran kuitansi tidak jelas, minta kirim ulang.',
    items: [['Kalender dinding', 500, 18000], ['Agenda kulit', 120, 65000]],
  },
  {
    vendor: 2, owner: 0, status: 'submitted', created: 6, decided: null,
    description: 'Renovasi ruang arsip lantai 3',
    note: null,
    items: [['Partisi gypsum terpasang', 46, 285000], ['Rak arsip besi', 14, 1150000]],
  },
  {
    vendor: 4, owner: 0, status: 'draft', created: 2, decided: null,
    description: 'Pengiriman dokumen cabang Surabaya',
    note: null,
    items: [['Paket dokumen reguler', 31, 42000]],
  },
  {
    vendor: 1, owner: 1, status: 'submitted', created: 9, decided: null,
    description: 'Audit keamanan aplikasi internal',
    note: null,
    items: [['Pengujian aplikasi', 1, 34000000]],
  },
  {
    vendor: 0, owner: 1, status: 'approved', created: 60, decided: 57,
    description: 'Penggantian pompa air gedung A',
    note: 'Nomor rekening vendor berubah, sudah diverifikasi lewat telepon.',
    items: [['Pompa sentrifugal', 1, 8900000], ['Jasa pemasangan', 1, 1750000]],
  },
]

data.create()

const insertUser = data.db.prepare(
  'INSERT INTO users (username, full_name, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)')
const insertVendor = data.db.prepare(
  'INSERT INTO vendors (name, tax_id, bank_account) VALUES (?, ?, ?)')
const insertInvoice = data.db.prepare(
  `INSERT INTO invoices (number, user_id, vendor_id, amount, description, status, internal_note, created_at, approved_at)
   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`)
const insertItem = data.db.prepare(
  'INSERT INTO line_items (invoice_id, description, qty, unit_price) VALUES (?, ?, ?, ?)')
const insertApproval = data.db.prepare(
  'INSERT INTO approvals (invoice_id, actor_id, action, note, created_at) VALUES (?, ?, ?, ?, ?)')

data.db.transaction(() => {
  const userIds = people.map(([username, name, role, plain], index) =>
    insertUser.run(username, name, password.hash(plain), role, daysAgo(400 - index * 20)).lastInsertRowid)

  const vendorIds = vendors.map(vendor => insertVendor.run(...vendor).lastInsertRowid)

  invoices.forEach((invoice, index) => {
    const amount = invoice.items.reduce((sum, [, qty, unit]) => sum + qty * unit, 0)
    const approvedAt = invoice.decided ? daysAgo(invoice.decided) : null

    const id = insertInvoice.run(
      `INV-2026-${String(index + 101).padStart(4, '0')}`,
      userIds[invoice.owner], vendorIds[invoice.vendor], amount, invoice.description,
      invoice.status, invoice.note, daysAgo(invoice.created),
      invoice.status === 'approved' ? approvedAt : null,
    ).lastInsertRowid

    for (const [description, qty, unit] of invoice.items) insertItem.run(id, description, qty, unit)

    if (invoice.status !== 'draft') {
      insertApproval.run(id, userIds[invoice.owner], 'submitted', null, daysAgo(invoice.created))
    }

    if (invoice.status === 'approved') {
      insertApproval.run(id, userIds[2], 'approved', 'Sesuai kontrak dan anggaran.', approvedAt)
    }

    if (invoice.status === 'rejected') {
      insertApproval.run(id, userIds[2], 'rejected', 'Lampiran kurang, mohon dilengkapi.', approvedAt)
    }
  })
})()
