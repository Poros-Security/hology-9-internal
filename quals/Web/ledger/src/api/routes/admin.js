const fs = require('fs')
const os = require('os')
const path = require('path')
const { randomUUID } = require('crypto')

const data = require('../db')
const settings = require('../settings')
const sessions = require('../sessions')

const serialise = (rows, opts = {}) =>
  rows.map(row => opts.includeInternal ? row : {
    id: row.id,
    number: row.number,
    vendor: row.vendor,
    amount: row.amount,
    status: row.status,
    created_at: row.created_at,
  })

const viewer = request => {
  const session = sessions.read(sessions.parseCookies(request.headers.cookie)[sessions.COOKIE])
  return session ? data.userById(session.userId) : null
}

const staffOnly = (request, reply) => {
  const user = viewer(request)
  if (user?.role === 'staff') return false
  reply.code(user ? 403 : 401).send({ error: 'Staff only.' })
  return true
}

module.exports = async function (app) {
  app.get('/ops/export', async request => {
    const opts = viewer(request)?.role === 'staff' ? { includeInternal: true } : {}
    return { invoices: serialise(data.allInvoices(), opts) }
  })

  app.get('/ops/settings', async () => settings.getProperties())

  app.post('/ops/settings/import', async (request, reply) => {
    const upload = await request.file()
    if (!upload) return reply.code(400).send({ error: 'Attach a settings file.' })

    const scratch = path.join(os.tmpdir(), `settings-${randomUUID()}.json`)
    fs.writeFileSync(scratch, await upload.toBuffer())

    try {
      settings.loadFile(scratch)
    } catch (error) {
      return reply.code(400).send({ error: 'That settings file could not be read.' })
    } finally {
      fs.unlinkSync(scratch)
    }

    return { ok: true, settings: settings.getProperties() }
  })

  app.get('/ops/users', async (request, reply) => {
    if (staffOnly(request, reply)) return
    return { users: data.db.prepare('SELECT id, username, full_name, role FROM users ORDER BY id').all() }
  })

  app.post('/ops/users', async (request, reply) => {
    if (staffOnly(request, reply)) return
    return reply.code(501).send({ error: 'People are provisioned by the directory sync.' })
  })

  app.get('/ops/vendors', async (request, reply) => {
    if (staffOnly(request, reply)) return
    return { vendors: data.vendors() }
  })

  app.post('/ops/vendors', async (request, reply) => {
    if (staffOnly(request, reply)) return
    return reply.code(501).send({ error: 'Vendor records are managed in the finance system.' })
  })

  app.get('/ops/audit', async (request, reply) => {
    if (staffOnly(request, reply)) return
    return {
      entries: data.db.prepare(`SELECT a.action, a.created_at, u.full_name AS actor, i.number
                                FROM approvals a
                                JOIN users u ON u.id = a.actor_id
                                JOIN invoices i ON i.id = a.invoice_id
                                ORDER BY a.created_at DESC LIMIT 100`).all(),
    }
  })

  app.post('/ops/invoices/:id/void', async (request, reply) => {
    if (staffOnly(request, reply)) return
    return reply.code(501).send({ error: 'Voiding is closed until the fiscal year rolls over.' })
  })
}
