const path = require('path')
const Fastify = require('fastify')

const data = require('./db')
const sessions = require('./sessions')

const guardAdmin = (req, res, next) => {
  const session = sessions.read(sessions.parseCookies(req.headers.cookie)[sessions.COOKIE])

  if (session && data.userById(session.userId)?.role === 'staff') return next()

  res.statusCode = session ? 403 : 401
  res.setHeader('content-type', 'application/json; charset=utf-8')
  res.end(JSON.stringify({ error: 'Staff only.' }))
}

async function main () {
  const app = Fastify()

  await app.register(require('@fastify/middie'))
  await app.register(require('@fastify/cookie'))
  await app.register(require('@fastify/multipart'))

  app.use('/ops', guardAdmin)

  await app.register(require('./routes/app'))
  await app.register(require('./routes/admin'))

  await app.register(require('@fastify/static'), {
    root: path.join(__dirname, 'public'),
    wildcard: false,
  })

  app.setNotFoundHandler((request, reply) => {
    const route = request.url.replace(/^\/+/, '/')

    if (!route.startsWith('/api/') && !route.startsWith('/ops/')) return reply.sendFile('index.html')

    return reply.code(404).send({
      message: `Route ${request.method}:${request.url} not found`,
      error: 'Not Found',
      statusCode: 404,
    })
  })

  await app.listen({ port: Number(process.env.PORT) || 3000, host: '0.0.0.0' })
}

main()
