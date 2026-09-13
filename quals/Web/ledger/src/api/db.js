const fs = require('fs')
const path = require('path')
const Database = require('better-sqlite3')

const file = process.env.DB_PATH || '/var/lib/ledger/ledger.db'

fs.mkdirSync(path.dirname(file), { recursive: true })

const db = new Database(file)
db.pragma('journal_mode = WAL')
db.pragma('foreign_keys = ON')

const create = () => db.exec(fs.readFileSync(path.join(__dirname, 'database/schema.sql'), 'utf8'))

const userByUsername = username =>
  db.prepare('SELECT * FROM users WHERE username = ?').get(username)

const userById = id =>
  db.prepare('SELECT id, username, full_name, role FROM users WHERE id = ?').get(id)

const vendors = () =>
  db.prepare('SELECT id, name, tax_id, bank_account FROM vendors ORDER BY name').all()

const invoiceFilter = (userId, filter) => {
  const where = ['i.user_id = ?']
  const values = [userId]

  if (filter.status) { where.push('i.status = ?'); values.push(filter.status) }
  if (filter.vendorId) { where.push('i.vendor_id = ?'); values.push(filter.vendorId) }
  if (filter.from) { where.push('i.created_at >= ?'); values.push(filter.from) }
  if (filter.to) { where.push('i.created_at <= ?'); values.push(`${filter.to}T23:59:59Z`) }

  return { clause: where.join(' AND '), values }
}

const invoicesForUser = (userId, filter = {}, page = 1, pageSize = 10) => {
  const { clause, values } = invoiceFilter(userId, filter)
  const total = db.prepare(`SELECT COUNT(*) AS n FROM invoices i WHERE ${clause}`).get(...values).n

  const invoices = db.prepare(
    `SELECT i.id, i.number, i.amount, i.status, i.created_at, v.name AS vendor
     FROM invoices i JOIN vendors v ON v.id = i.vendor_id
     WHERE ${clause} ORDER BY i.created_at DESC, i.id DESC LIMIT ? OFFSET ?`
  ).all(...values, pageSize, (page - 1) * pageSize)

  return { invoices, total }
}

const allInvoicesForUser = userId =>
  db.prepare(`SELECT i.number, i.status, i.amount, i.created_at, i.description, v.name AS vendor
              FROM invoices i JOIN vendors v ON v.id = i.vendor_id
              WHERE i.user_id = ? ORDER BY i.created_at DESC, i.id DESC`).all(userId)

const vendorById = id =>
  db.prepare('SELECT id, name, tax_id, bank_account FROM vendors WHERE id = ?').get(id)

const vendorInvoicesForUser = (vendorId, userId) =>
  db.prepare(`SELECT id, number, amount, status, created_at FROM invoices
              WHERE vendor_id = ? AND user_id = ? ORDER BY created_at DESC, id DESC`).all(vendorId, userId)

const decidedInvoices = () =>
  db.prepare(`SELECT i.id, i.number, i.amount, i.status, i.approved_at, v.name AS vendor,
                     u.full_name AS submitted_by, a.note, d.full_name AS decided_by
              FROM invoices i
              JOIN vendors v ON v.id = i.vendor_id
              JOIN users u ON u.id = i.user_id
              JOIN approvals a ON a.invoice_id = i.id AND a.action IN ('approved', 'rejected')
              JOIN users d ON d.id = a.actor_id
              WHERE i.status IN ('approved', 'rejected')
              ORDER BY a.created_at DESC LIMIT 50`).all()

const setPassword = (userId, hash) =>
  db.prepare('UPDATE users SET password_hash = ? WHERE id = ?').run(hash, userId)

const invoiceForUser = (id, userId) =>
  db.prepare(`SELECT i.*, v.name AS vendor, v.tax_id, v.bank_account
              FROM invoices i JOIN vendors v ON v.id = i.vendor_id
              WHERE i.id = ? AND i.user_id = ?`).get(id, userId)

const invoiceById = id =>
  db.prepare(`SELECT i.*, v.name AS vendor, v.tax_id, v.bank_account, u.full_name AS submitted_by
              FROM invoices i
              JOIN vendors v ON v.id = i.vendor_id
              JOIN users u ON u.id = i.user_id
              WHERE i.id = ?`).get(id)

const lineItems = invoiceId =>
  db.prepare('SELECT description, qty, unit_price FROM line_items WHERE invoice_id = ? ORDER BY id').all(invoiceId)

const history = invoiceId =>
  db.prepare(`SELECT a.action, a.note, a.created_at, u.full_name AS actor
              FROM approvals a JOIN users u ON u.id = a.actor_id
              WHERE a.invoice_id = ? ORDER BY a.created_at, a.id`).all(invoiceId)

const submittedQueue = () =>
  db.prepare(`SELECT i.id, i.number, i.amount, i.created_at, v.name AS vendor, u.full_name AS submitted_by
              FROM invoices i
              JOIN vendors v ON v.id = i.vendor_id
              JOIN users u ON u.id = i.user_id
              WHERE i.status = 'submitted' ORDER BY i.created_at, i.id`).all()

const allInvoices = () =>
  db.prepare(`SELECT i.id, i.number, i.amount, i.status, i.created_at, i.internal_note,
                     v.name AS vendor, v.tax_id, v.bank_account, u.full_name AS submitted_by
              FROM invoices i
              JOIN vendors v ON v.id = i.vendor_id
              JOIN users u ON u.id = i.user_id
              ORDER BY i.created_at DESC, i.id DESC`).all()

const nextNumber = () => {
  const year = new Date().getFullYear()
  const count = db.prepare("SELECT COUNT(*) AS n FROM invoices WHERE number LIKE ?").get(`INV-${year}-%`).n
  return `INV-${year}-${String(count + 1).padStart(4, '0')}`
}

const createInvoice = db.transaction((userId, vendorId, description, items) => {
  const amount = items.reduce((sum, item) => sum + item.qty * item.unit_price, 0)
  const now = new Date().toISOString()
  const result = db.prepare(`INSERT INTO invoices (number, user_id, vendor_id, amount, description, status, created_at)
                             VALUES (?, ?, ?, ?, ?, 'submitted', ?)`)
    .run(nextNumber(), userId, vendorId, amount, description, now)

  const insertItem = db.prepare('INSERT INTO line_items (invoice_id, description, qty, unit_price) VALUES (?, ?, ?, ?)')
  for (const item of items) insertItem.run(result.lastInsertRowid, item.description, item.qty, item.unit_price)

  db.prepare('INSERT INTO approvals (invoice_id, actor_id, action, created_at) VALUES (?, ?, ?, ?)')
    .run(result.lastInsertRowid, userId, 'submitted', now)

  return result.lastInsertRowid
})

const decide = db.transaction((invoiceId, actorId, action, note) => {
  const now = new Date().toISOString()
  db.prepare('UPDATE invoices SET status = ?, approved_at = ? WHERE id = ?')
    .run(action === 'approved' ? 'approved' : 'rejected', action === 'approved' ? now : null, invoiceId)
  db.prepare('INSERT INTO approvals (invoice_id, actor_id, action, note, created_at) VALUES (?, ?, ?, ?, ?)')
    .run(invoiceId, actorId, action, note || null, now)
})

module.exports = {
  db,
  create,
  userByUsername,
  userById,
  vendors,
  vendorById,
  vendorInvoicesForUser,
  invoicesForUser,
  allInvoicesForUser,
  decidedInvoices,
  setPassword,
  invoiceForUser,
  invoiceById,
  lineItems,
  history,
  submittedQueue,
  allInvoices,
  createInvoice,
  decide,
}
