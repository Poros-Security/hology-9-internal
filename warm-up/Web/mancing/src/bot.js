// bot.js - CTF Challenge Bot
const puppeteer = require('puppeteer');
require('dotenv').config();

const FLAG = process.env.GZCTF_FLAG || process.env.APPFLAG || 'HOLOGY9{1nTro_2_w3Bh0ok_s4Ng_7uK4n6_m4nC1nG_local}';
const BASE_URL = process.env.BASE_URL || 'http://localhost:7777';

async function reviewLetter(letterId) {
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage'
    ]
  });

  try {
    const page = await browser.newPage();
    
    // Set custom header untuk autentikasi bot
    const BOT_SECRET = process.env.BOT_SECRET || 'b0T_53Cr3t_14377ec1';
    await page.setExtraHTTPHeaders({
      'X-Bot-Secret': BOT_SECRET
    });
    
    // Extract domain dari BASE_URL untuk cookie
    const url = new URL(BASE_URL);
    const cookieDomain = url.hostname;
    
    // Set cookie dengan flag
    await page.setCookie({
      name: 'flag',
      value: FLAG,
      domain: cookieDomain,
      httpOnly: false // Vulnerable: flag bisa diakses via JavaScript
    });

    // Bot mengunjungi halaman review surat
    await page.goto(`${BASE_URL}/review/${letterId}`, {
      waitUntil: 'networkidle0',
      timeout: 10000
    });

    // Tunggu sebentar untuk XSS payload ter-execute
    await page.waitForTimeout(3000);

    // Bot selalu reject surat
    const rejectButton = await page.$('#reject-button');
    if (rejectButton) {
      await rejectButton.click();
      await page.waitForTimeout(1000);
    }

    console.log(`[BOT] Reviewed letter ${letterId} - REJECTED`);
  } catch (error) {
    console.error(`[BOT] Error reviewing letter: ${error.message}`);
  } finally {
    await browser.close();
  }
}

module.exports = { reviewLetter };
