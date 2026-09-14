const { randomBytes, scryptSync, timingSafeEqual } = require('crypto')

const hash = plain => {
  const salt = randomBytes(16)
  return `${salt.toString('hex')}:${scryptSync(plain, salt, 64).toString('hex')}`
}

const verify = (plain, stored) => {
  const [salt, digest] = String(stored).split(':')
  if (!salt || !digest) return false
  const expected = Buffer.from(digest, 'hex')
  const actual = scryptSync(plain, Buffer.from(salt, 'hex'), expected.length)
  return timingSafeEqual(expected, actual)
}

module.exports = { hash, verify }
