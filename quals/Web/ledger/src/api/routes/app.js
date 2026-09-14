const data = require('../db')
const password = require('../password')
const sessions = require('../sessions')

const PAGE_SIZE = 10
const MIN_PASSWORD = 8

const csvCell = value => {
  const text = String(value ?? '')
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}

const publicUser = user => ({ id: user.id, username: user.username, name: user.full_name, role: user.role })

module.exports = async function (app) {
  app.addHook('preHandler', async (request, reply) => {
    const session = sessions.read(request.cookies[sessions.COOKIE])
    request.user = session ? data.userById(session.userId) : null

    if (request.routeOptions.url === '/api/login' || request.user) return
    reply.code(401).send({ error: 'Sign in to continue.' })
  })

  app.post('/api/login', async (request, reply) => {
    const { username, password: given } = request.body || {}
    const user = data.userByUsername(String(username || ''))

    if (!user || !password.verify(String(given || ''), user.password_hash)) {
      return reply.code(401).send({ error: 'That username and password do not match.' })
    }

    reply.setCookie(sessions.COOKIE, sessions.open(user), { path: '/', httpOnly: true, sameSite: 'lax' })
    return publicUser(user)
  })

  app.post('/api/logout', async (request, reply) => {
    sessions.close(request.cookies[sessions.COOKIE])
    reply.clearCookie(sessions.COOKIE, { path: '/' })
    return { ok: true }
  })

  app.get('/api/me', async request => publicUser(request.user))

  app.get('/api/vendors', async () => ({ vendors: data.vendors() }))

  app.get('/api/invoices', async request => {
    const { status, vendor_id: vendorId, from, to, page } = request.query
    const current = Math.max(1, Number(page) || 1)

    const { invoices, total } = data.invoicesForUser(request.user.id, {
      status,
      vendorId: vendorId ? Number(vendorId) : undefined,
      from,
      to,
    }, current, PAGE_SIZE)

    return { invoices, total, page: current, pages: Math.max(1, Math.ceil(total / PAGE_SIZE)) }
  })

  app.get('/api/invoices.csv', async (request, reply) => {
    const rows = data.allInvoicesForUser(request.user.id)
    const header = ['Number', 'Vendor', 'Description', 'Status', 'Amount', 'Submitted']

    const lines = rows.map(row =>
      [row.number, row.vendor, row.description, row.status, row.amount, row.created_at.slice(0, 10)]
        .map(csvCell).join(','))

    reply.header('content-type', 'text/csv; charset=utf-8')
    reply.header('content-disposition', 'attachment; filename="invoices.csv"')
    return [header.join(','), ...lines].join('\n')
  })

  app.get('/api/vendors/:id', async (request, reply) => {
    const vendor = data.vendorById(Number(request.params.id))
    if (!vendor) return reply.code(404).send({ error: 'Vendor not found.' })

    return { vendor, invoices: data.vendorInvoicesForUser(vendor.id, request.user.id) }
  })

  app.get('/api/invoices/:id', async (request, reply) => {
    const invoice = data.invoiceForUser(Number(request.params.id), request.user.id)
    if (!invoice) return reply.code(404).send({ error: 'Invoice not found.' })

    delete invoice.internal_note
    return { invoice, items: data.lineItems(invoice.id), history: data.history(invoice.id) }
  })

  app.post('/api/invoices', async (request, reply) => {
    const { vendor_id: vendorId, description, items } = request.body || {}

    if (!data.vendors().some(vendor => vendor.id === Number(vendorId))) {
      return reply.code(400).send({ error: 'Choose a vendor.' })
    }

    const lines = Array.isArray(items) ? items.filter(item => item.description && item.qty > 0 && item.unit_price > 0) : []
    if (!lines.length) return reply.code(400).send({ error: 'Add at least one line item.' })
    if (!String(description || '').trim()) return reply.code(400).send({ error: 'Describe what this invoice covers.' })

    const id = data.createInvoice(request.user.id, Number(vendorId), String(description).trim(), lines.map(item => ({
      description: String(item.description).trim(),
      qty: Number(item.qty),
      unit_price: Number(item.unit_price),
    })))

    return { id }
  })

  app.get('/api/approvals', async (request, reply) => {
    if (request.user.role !== 'finance') return reply.code(403).send({ error: 'Finance only.' })
    return { invoices: data.submittedQueue() }
  })

  app.get('/api/approvals/decided', async (request, reply) => {
    if (request.user.role !== 'finance') return reply.code(403).send({ error: 'Finance only.' })
    return { invoices: data.decidedInvoices() }
  })

  app.post('/api/profile/password', async (request, reply) => {
    const { current, replacement } = request.body || {}
    const stored = data.userByUsername(request.user.username)

    if (!password.verify(String(current || ''), stored.password_hash)) {
      return reply.code(400).send({ error: 'Your current password is wrong.' })
    }

    if (String(replacement || '').length < MIN_PASSWORD) {
      return reply.code(400).send({ error: `Choose a password of at least ${MIN_PASSWORD} characters.` })
    }

    data.setPassword(request.user.id, password.hash(String(replacement)))
    return { ok: true }
  })

  app.post('/api/approvals/:id', async (request, reply) => {
    if (request.user.role !== 'finance') return reply.code(403).send({ error: 'Finance only.' })

    const invoice = data.invoiceById(Number(request.params.id))
    if (!invoice || invoice.status !== 'submitted') return reply.code(404).send({ error: 'Invoice not found.' })

    const { action, note } = request.body || {}
    if (action !== 'approved' && action !== 'rejected') return reply.code(400).send({ error: 'Action must be approved or rejected.' })

    data.decide(invoice.id, request.user.id, action, note)
    return { ok: true }
  })
}
