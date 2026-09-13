const { randomUUID } = require('crypto')

const store = new Map()

const open = user => {
  const id = randomUUID()
  store.set(id, { userId: user.id, role: user.role })
  return id
}

const read = id => (id ? store.get(id) : undefined)

const close = id => store.delete(id)

const parseCookies = header =>
  Object.fromEntries((header || '').split(';').map(part => {
    const [name, ...rest] = part.trim().split('=')
    return [name, rest.join('=')]
  }))

module.exports = { open, read, close, parseCookies, COOKIE: 'ledger_sid' }
