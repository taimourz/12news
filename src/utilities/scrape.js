import * as cheerio from 'cheerio';
import * as fs from 'fs/promises';
import puppeteer from 'puppeteer';

function resolveImageUrl($article, $) {
  const img = $article.find('img').first();
  const picture = $article.find('picture').first();

  let url;

  url = img.attr('data-src');
  if (url && !url.startsWith('data:image')) return url;

  url = img.attr('data-original');
  if (url && !url.startsWith('data:image')) return url;

  url = img.attr('srcset');
  if (url) {
    const first = url.split(',')[0].trim().split(' ')[0];
    if (!first.startsWith('data:image')) return first;
  }

  if (picture.length > 0) {
    const srcset = picture.find('source').attr('srcset');
    if (srcset) {
      const first = srcset.split(',')[0].trim().split(' ')[0];
      return first;
    }
  }

  url = img.attr('src');
  if (url && !url.startsWith('data:image')) return url;

  return undefined;
}

class DawnScraper {
  constructor() {
    this.baseUrl = 'https://www.dawn.com/newspaper';
    this.dataDir = './public/data';
    this.archiveFile = './public/data/archive.json';
    this.delay = 2000;
    this.browser = null;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async initBrowser() {
    if (!this.browser) {
      this.browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      });
    }
    return this.browser;
  }

  async closeBrowser() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  async saveArchive(dayArchive) {
    await fs.mkdir(this.dataDir, { recursive: true });
    await fs.writeFile(
      this.archiveFile,
      JSON.stringify(dayArchive, null, 2),
      'utf-8'
    );
    console.log(`Archive saved to ${this.archiveFile}`);
  }

  async fetchPage(url) {
    try {
      const browser = await this.initBrowser();
      const page = await browser.newPage();

      await page.setViewport({ width: 1920, height: 1080 });
      await page.setUserAgent(
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      );

      console.log(`  Fetching: ${url}`);
      await page.goto(url, {
        waitUntil: 'networkidle2',
        timeout: 30000
      });

      const html = await page.content();
      await page.close();

      return html;
    } catch (err) {
      console.error(`Error fetching ${url}:`, err);
      throw err;
    }
  }

  async scrapeDay(dateString) {
    const sections = ['front-page', 'back-page', 'national', 'editorial', 'business'];
    const dayArchive = {
      date: dateString,
      sections: {}
    };

    await this.initBrowser();

    for (const section of sections) {
      console.log(`Scraping ${section} for ${dateString}...`);

      try {
        const url = `${this.baseUrl}/${section}/${dateString}`;
        const html = await this.fetchPage(url);
        const articles = this.parseSection(html, section, dateString);

        if (articles.length > 0) {
          dayArchive.sections[section] = articles;
          console.log(`  Found ${articles.length} articles`);
        } else {
          console.log(` No articles found`);
          dayArchive.sections[section] = [];
        }

        await this.sleep(this.delay);
      } catch (err) {
        console.error(`Failed to scrape ${section} for ${dateString}`);
        dayArchive.sections[section] = [];
      }
    }

    await this.closeBrowser();
    await this.saveArchive(dayArchive);

    return dayArchive;
  }

  parseSection(html, section, date) {
    const $ = cheerio.load(html);
    const articles = [];

    const selectors = [
      'article.story',
      '.story',
      'article',
      '.box.story',
      '.story-list article'
    ];

    for (const selector of selectors) {
      const elements = $(selector);

      if (elements.length === 0) continue;

      elements.each((_, el) => {
        const $article = $(el);

        const $title = $article.find('h2 a, .story__title a, h3 a, .story__link').first();
        const $summary = $article.find('.story__excerpt, .story__text, p').first();

        const title = $title.text().trim();
        const url = $title.attr('href');
        const summary = $summary.text().trim();

        const rawImage = resolveImageUrl($article, $);
        let imageUrl;

        if (rawImage) {
          if (rawImage.startsWith('//')) {
            imageUrl = `https:${rawImage}`;
          } else if (rawImage.startsWith('http')) {
            imageUrl = rawImage;
          } else {
            imageUrl = `https://www.dawn.com${rawImage}`;
          }
        }

        if (title && url && !articles.some(a => a.title === title)) {
          const article = {
            title,
            url: url.startsWith('http') ? url : `https://www.dawn.com${url}`,
            summary: summary || '',
            section,
            date
          };

          if (imageUrl) article.imageUrl = imageUrl;

          articles.push(article);
        }
      });

      if (articles.length > 0) break;
    }

    return articles;
  }

  async scrapeToday() {
    const today = new Date();
    const yearsAgo = 12;

    const past = new Date(today);
    past.setFullYear(today.getFullYear() - yearsAgo);

    const dateString = past.toISOString().split('T')[0];
    console.log(`\n=== Scraping ${yearsAgo} years ago: ${dateString} ===`);

    const archive = await this.scrapeDay(dateString);

    const count = Object.values(archive.sections)
      .reduce((sum, arr) => sum + arr.length, 0);

    console.log(`\n✓ Scraping complete! Found ${count} articles for ${dateString}`);
  }

  async showArchive() {
    try {
      const raw = await fs.readFile(this.archiveFile, 'utf-8');
      const archive = JSON.parse(raw);

      console.log('\n=== Current Archive ===');
      console.log(`Date: ${archive.date}`);

      let total = 0;
      for (const [sec, items] of Object.entries(archive.sections)) {
        console.log(`  ${sec}: ${items.length} articles`);
        total += items.length;
      }

      console.log(`\nTotal Articles: ${total}`);
      console.log('======================\n');
    } catch (err) {
      console.error('No archive found or error reading file:', err);
    }
  }
}

async function main() {
  const scraper = new DawnScraper();
  const args = process.argv.slice(2);
  const cmd = args[0];

  try {
    if (cmd === 'today') {
      await scraper.scrapeToday();
    } else if (cmd === 'date') {
      const date = args[1];
      if (!date) {
        console.error("Usage: node src/index.js date YYYY-MM-DD");
        process.exit(1);
      }
      await scraper.scrapeDay(date);
    } else if (cmd === 'show') {
      await scraper.showArchive();
    } else {
      console.log(`
Dawn Archive Scraper

Commands:
  today              Scrape today's date from 12 years ago
  date <YYYY-MM-DD>  Scrape a specific date
  show               Show archive contents

Examples:
  node src/index.js today
  node src/index.js date 2013-01-02
      `);
    }
  } catch (err) {
    console.error("Fatal error:", err);
  }
}

main();
