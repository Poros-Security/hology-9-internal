import { RedisClient, type BunRequest } from 'bun'
import puppeteer, { Browser } from 'puppeteer-core';
import { randomBytes } from 'node:crypto';
import { mkdtemp, rm, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

const host = 'web';
const internalOrigin = `http://${host}:443`;
const redisUrl = Bun.env.REDIS_URL || 'redis://127.0.0.1:6379';
const secretAlphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
const secretLength = 20;
const fallbackSecret = secretAlphabet.slice(0, secretLength);
const markerType = 'image/gif';
const markerInitialBaseTtl = 26;
const markerInitialJitter = 17;
const markerRefreshBonusTtl = 14;
const allowedUploadTypes = new Set([
	'application/octet-stream',
	'application/xml',
	'application/xslt+xml',
	markerType,
	'text/plain',
	'text/xml',
	'text/xsl'
]);

const inferUploadType = (file: File) => {
	const normalizedType = file.type.toLowerCase().split(';', 1)[0].trim();
	if (normalizedType) return normalizedType;
	const name = file.name.toLowerCase();
	if (name.endsWith('.gif')) return markerType;
	if (name.endsWith('.xml')) return 'application/xml';
	if (name.endsWith('.xsl') || name.endsWith('.xslt')) return 'text/xsl';
	if (name.endsWith('.txt')) return 'text/plain';
	return 'application/octet-stream';
}

const makeSecret = () => {
	return Array.from(randomBytes(secretLength), byte => secretAlphabet[byte & 31]).join('');
}

const markerInitialTtl = (id: number) => {
	return markerInitialBaseTtl + ((id * 7 + 3) % markerInitialJitter);
}

const markerRefreshTtl = (id: number) => {
	return markerInitialTtl(id) + markerRefreshBonusTtl;
}

const escapeXml = (value: string) => {
	return value
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&apos;');
}

await mkdir('/etc/opt/chrome/policies/managed/', { recursive: true });
await writeFile('/etc/opt/chrome/policies/managed/policy.json', JSON.stringify({
	'NetworkPredictionOptions': 2,
	'URLBlocklist': ['*'],
	'URLAllowlist': [internalOrigin, `${internalOrigin}/*`]
}));

const redis = new RedisClient(redisUrl, { idleTimeout: 0, autoReconnect: true });

const visit = async (url: string) => {
	await redis.set('browser_open', 'true');

	const secret = makeSecret();

	let browser: Browser | null = null;

	const userDataDir = await mkdtemp(join(tmpdir(), 'paper-'));
	try {
		browser = await puppeteer.launch({
			executablePath: '/usr/bin/google-chrome',
			args: [
				'--no-sandbox',
				'--disable-gpu',
				'--js-flags=--noexpose_wasm,--jitless',
				`--host-rules=MAP ${host} 127.0.0.1`
			],
			headless: true,
			pipe: true,
			userDataDir
		});
		await browser.setCookie({
			name: 'secret',
			value: secret,
			url: `${internalOrigin}/`,
			httpOnly: true,
			sameSite: 'Strict'
		});

		const page = await browser.newPage();
		await redis.set('secret', secret, 'EX', 60);
		await page.goto(url);
		await Bun.sleep(61000);
	} catch(e) {
		console.log(e);
	}

	try {
		if (browser) await browser.close();
	} catch(e) {};

	await rm(userDataDir, { recursive: true, force: true })

	await redis.del('secret');
	await redis.del('browser_open');
}

const headers = (type: string) => {
	return {
		headers: {
			'Content-Type': type,
			'Content-Security-Policy': [
				"default-src 'self' 'unsafe-inline'",
				"script-src 'none'",
				"script-src-elem 'self'"
			].join('; '),
			'X-Content-Type-Options': 'nosniff'
		}
	}
}

const routes = {
	'/': new Response(`
		<form action="/upload" method="POST" enctype="multipart/form-data">
			<input type="file" name="file">
			<input type="submit" value="upload">
		</form>
	`, headers('text/html')),

	'/upload': {
		POST: async (req: BunRequest): Promise<Response> => {
			let form: FormData;
			try {
				form = await req.formData();
			} catch(e) {
				return new Response('invalid upload!', headers('text/plain'));
			}
			const file = form.get('file');
			if (!file || !(file instanceof File) || !file.size || file.size > 2 ** 16) {
				return new Response('no file upload!', headers('text/plain'));
			}
			const uploadType = inferUploadType(file);
			if (!allowedUploadTypes.has(uploadType)) {
				return new Response('unsupported file type!', headers('text/plain'));
			}
			const id = await redis.incr('current-id');
			const data = JSON.stringify([uploadType, (await file.bytes()).toBase64()]);
			const ttl = uploadType === markerType ? markerInitialTtl(id) : 10 * 60;
			await redis.set(`file|${id}`, data, 'EX', ttl);
			return Response.redirect(`/paper/${id}`);
		}
	},

	'/paper/:id': {
		GET: async (req: BunRequest<'/paper/:id'>): Promise<Response> => {
			const key = `file|${req.params.id}`;
			const res = await redis.get(key);
			if (!res) {
				return new Response('not found!', headers('text/plain'));
			}
			const [type, data] = JSON.parse(res) as [string, string];
			if (type === markerType) {
				await redis.set(key, res, 'EX', markerRefreshTtl(Number(req.params.id)));
			}
			return new Response(Buffer.from(data, 'base64'), headers(type));
		},

		HEAD: async (req: BunRequest<'/paper/:id'>): Promise<Response> => {
			const exists = await redis.exists(`file|${req.params.id}`);
			return new Response(null, {
				status: exists ? 200 : 404,
				headers: headers('application/octet-stream').headers
			});
		}
	},

	'/secret': async (req: BunRequest): Promise<Response> => {
		const secret = req.cookies.get('secret') || fallbackSecret;
		const payload = new URL(req.url, 'http://127.0.0.1').searchParams.get('payload') || '';

		return new Response(
			[
				'<?xml version="1.0" encoding="UTF-8"?>',
				`<paper alphabet="${secretAlphabet}" length="${secretLength}">`,
				`	<ink value="${escapeXml(secret)}"/>`,
				`	<note>${escapeXml(payload)}</note>`,
				'</paper>'
			].join('\n'),
			headers('application/xml')
		);
	},

	'/flag': async (req: BunRequest): Promise<Response> => {
		const guess = new URL(req.url, 'http://127.0.0.1').searchParams.get('secret');
		const secret = await redis.getdel('secret');
		if (!secret) {
			return new Response('nice try', headers('text/plain'));
		}
		if (secret !== guess) {
			return new Response('wrong', headers('text/plain'));
		}
		return new Response(
			Bun.env.GZCTF_FLAG || Bun.env.FLAG || 'HOLOGY9{p4p3rcl1p_4ud1t_b0ught_4_y0gurt_l1c3ns3_l0c4l}',
			headers('text/plain')
		);
	},

	'/visit/:id': async(req: BunRequest<'/visit/:id'>): Promise<Response> => {
		if (await redis.get('browser_open')) {
			return new Response('browser still open!');
		}

		const res = await redis.get(`file|${req.params.id}`);
		if (!res) {
			return new Response('not found!', headers('text/plain'));
		}

			visit(`${internalOrigin}/paper/${req.params.id}`)

		return new Response('visiting!', headers('text/plain'));
	}
}

Bun.serve({
	port: 443,
	maxRequestBodySize: 2 ** 16,
	development: false,
	routes,
});

console.log('Listening.');
