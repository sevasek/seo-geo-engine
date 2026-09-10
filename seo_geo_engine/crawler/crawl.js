// Website-agnostic crawler: real browser (not static fetch), strip
// script/style/noscript/template before taking bodyText, capture full
// internalHrefs + anchorTexts, resolve internal link redirects, and check
// /robots.txt separately. Reads the page list from a sitemap.xml (fetched
// from the target origin, or an explicit URL) or an explicit newline-
// delimited page list — never a hardcoded URL list.
//
// Usage:
//   node crawl.js --origin https://example.com [--sitemap-url URL] [--pages-file path.txt]
//                 [--ua "Mozilla/5.0 ..."] [--out site-crawl.json]
//
// --origin is required unless --pages-file is given with fully-qualified
// URLs (in which case the origin is derived from the first page URL).
// Without --sitemap-url, the sitemap is fetched from `${origin}/sitemap.xml`.
// --pages-file, if given, is used INSTEAD of fetching a sitemap — one URL
// per line, blank lines ignored — for a site with no sitemap.xml (e.g. a
// local-serve target during development, see local_serve.py).
//
// Requires: npm install (playwright + a downloaded chromium — see this
// directory's package.json). First run: npx playwright install chromium.
//
// A crawl's `externalPresence` (Crunchbase/Wikidata/press mentions) isn't
// gathered here — it needs a WebSearch, not a page fetch — a profile fills
// it in separately, or the checks that read it see an empty default.
//
// Required lazily inside the require.main guard below, not at module load —
// so a test can `require('./crawl.js')` for its pure/injectable helpers
// without needing playwright's (heavy, browser-download-requiring) package
// installed.
const fs = require('fs');
const https = require('https');
const http = require('http');

const DEFAULT_UA = 'Mozilla/5.0 (compatible; seo-geo-engine-crawler/1.0)';

function parseArgs(argv) {
  const args = { out: 'site-crawl.json', ua: DEFAULT_UA };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--origin') args.origin = argv[++i];
    else if (a === '--sitemap-url') args.sitemapUrl = argv[++i];
    else if (a === '--pages-file') args.pagesFile = argv[++i];
    else if (a === '--ua') args.ua = argv[++i];
    else if (a === '--out') args.out = argv[++i];
    else if (!a.startsWith('--') && !args._legacyOut) args._legacyOut = a; // back-compat: bare positional = output path
  }
  if (args._legacyOut && args.out === 'site-crawl.json') args.out = args._legacyOut;
  return args;
}

function fetchText(url, ua) {
  // Some sites' WAF/CDN returns an error page (or blocks outright) to a
  // request with no User-Agent header — a browser-like UA is enough to
  // pass, and is harmless to send unconditionally, so this crawler always
  // sends one rather than treating it as a per-site special case.
  const client = url.startsWith('https:') ? https : http;
  return new Promise((resolve, reject) => {
    client
      .get(url, { headers: { 'User-Agent': ua } }, (res) => {
        let data = '';
        res.on('data', (c) => (data += c));
        res.on('end', () => resolve(data));
      })
      .on('error', reject);
  });
}

async function extractPage(page, url) {
  const resp = await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
  const status = resp ? resp.status() : null;

  const data = await page.evaluate(() => {
    function text(sel) {
      const el = document.querySelector(sel);
      return el ? el.getAttribute('content') : null;
    }
    const title = document.title || '';
    const metaDesc = text('meta[name="description"]') || '';
    const canonical = document.querySelector('link[rel="canonical"]')?.href || null;
    // OG-001 needs to name which specific tag(s) are duplicated, not just
    // whether any duplicate exists.
    const ogTags = Array.from(document.querySelectorAll('meta[property^="og:"]'));
    const ogNames = ogTags.map((t) => t.getAttribute('property'));
    const ogNameCounts = {};
    for (const n of ogNames) ogNameCounts[n] = (ogNameCounts[n] || 0) + 1;
    const dupOgTags = Object.keys(ogNameCounts).filter((n) => ogNameCounts[n] > 1);
    const ogDescription = text('meta[property="og:description"]') || '';
    const viewport = text('meta[name="viewport"]') || '';
    const generator = text('meta[name="generator"]') || '';

    const jsonLdScripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
    let jsonLdTypes = [];
    let organizationNode = null;
    let dateModified = null;
    for (const s of jsonLdScripts) {
      try {
        const parsed = JSON.parse(s.textContent);
        const nodes = Array.isArray(parsed) ? parsed : parsed['@graph'] || [parsed];
        for (const node of nodes) {
          if (node['@type']) {
            const types = Array.isArray(node['@type']) ? node['@type'] : [node['@type']];
            jsonLdTypes.push(...types);
            if (types.includes('Organization') && !organizationNode) organizationNode = node;
          }
          if (node.dateModified && !dateModified) dateModified = node.dateModified;
        }
      } catch (e) {
        /* ignore malformed JSON-LD */
      }
    }

    const h1s = Array.from(document.querySelectorAll('h1')).map((h) => h.textContent.trim());
    const h2Count = document.querySelectorAll('h2').length;
    const h3Count = document.querySelectorAll('h3').length;
    // Heading levels in DOM order — lets a check tell "h1 then h2 then h3"
    // (fine) apart from "h1 then h3" (a skipped level), which raw counts
    // per level can't distinguish.
    const headingSequence = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6')).map((h) =>
      h.tagName.toLowerCase()
    );

    // GA4/GTM signature in the raw HTML — script src or an inline gtag()
    // call. Doesn't try to detect every analytics vendor, just the most
    // common Google-family ones this check is scoped to.
    const htmlSource = document.documentElement.outerHTML;
    const hasAnalytics = /googletagmanager\.com|gtag\(|google-analytics\.com\/analytics\.js/.test(htmlSource);

    const images = Array.from(document.querySelectorAll('img'));
    const imageCount = images.length;
    const imagesMissingAlt = images.filter(
      (img) => !img.getAttribute('alt') || img.getAttribute('alt').trim() === ''
    ).length;

    // Many page builders lazy-load iframe embeds (maps, calendars) via
    // IntersectionObserver: the real URL sits in
    // data-lazy-src/data-src/data-original until the element scrolls into
    // view, at which point `src` gets swapped in. A plain page.goto() with
    // no scrolling never triggers that for anything below the fold, so
    // `src` alone can silently under-count embeds — falling back to the
    // common lazy-load attribute names when `src` is empty catches the
    // pre-trigger case without needing to script a scroll. This is common
    // enough across page builders that it's unconditional default
    // behavior, not a per-site special case.
    const iframes = Array.from(document.querySelectorAll('iframe'))
      .map(
        (f) =>
          f.getAttribute('src') ||
          f.getAttribute('data-lazy-src') ||
          f.getAttribute('data-src') ||
          f.getAttribute('data-original')
      )
      .filter(Boolean);

    // Strip script/style/noscript/template before computing bodyText/wordCount
    const clone = document.body.cloneNode(true);
    clone.querySelectorAll('script,style,noscript,template').forEach((el) => el.remove());
    const bodyText = (clone.textContent || '').replace(/\s+/g, ' ').trim();
    const wordCount = bodyText ? bodyText.split(' ').filter(Boolean).length : 0;

    // Words specifically inside real <p> elements — content extractors key
    // off <p> to tell real prose from chrome; text sitting in a styled
    // <div> instead doesn't count to them even though it's visible to a
    // human.
    const pText = Array.from(clone.querySelectorAll('p'))
      .map((el) => el.textContent)
      .join(' ')
      .replace(/\s+/g, ' ')
      .trim();
    const pTagWordCount = pText ? pText.split(' ').filter(Boolean).length : 0;

    const origin = location.origin;
    const anchors = Array.from(document.querySelectorAll('a[href]'));
    const internalHrefsSet = new Set();
    const anchorTexts = [];
    for (const a of anchors) {
      let href;
      try {
        href = new URL(a.getAttribute('href'), location.href).href;
      } catch (e) {
        continue;
      }
      if (href.startsWith(origin)) {
        internalHrefsSet.add(href);
        const t = a.textContent.trim();
        if (t) anchorTexts.push(t);
      }
    }

    // Internal links found outside <nav>/<header>/<footer> — i.e. body
    // content, not nav/chrome. Needed because internalHrefs is a
    // deduplicated per-page set: a page linking to /x from both nav and
    // body content looks identical to one linking to it from nav only, so
    // a frequency-based "is this a nav link" guess can't tell a genuine
    // in-content link apart from one that just happens to also be a nav
    // item — this captures it directly instead of inferring it. Excludes
    // by ANCESTOR landmark rather than requiring a <main> wrapper, since
    // not every site's builder emits one.
    const contentInternalHrefsSet = new Set();
    for (const a of anchors) {
      if (a.closest('nav, header, footer')) continue;
      let href;
      try {
        href = new URL(a.getAttribute('href'), location.href).href;
      } catch (e) {
        continue;
      }
      if (href.startsWith(origin)) contentInternalHrefsSet.add(href);
    }

    return {
      title,
      titleLen: title.length,
      metaDesc,
      metaDescLen: metaDesc.length,
      canonical,
      dupOgTags,
      ogDescription,
      jsonLdTypes: [...new Set(jsonLdTypes)],
      organizationNode,
      dateModified,
      h1Count: h1s.length,
      h1s,
      h2Count,
      h3Count,
      headingSequence,
      imageCount,
      imagesMissingAlt,
      wordCount,
      pTagWordCount,
      bodyText,
      viewport,
      generator,
      hasAnalytics,
      internalHrefs: Array.from(internalHrefsSet),
      contentInternalHrefs: Array.from(contentInternalHrefsSet),
      anchorTexts,
      iframes,
    };
  });

  return { url, status, bytes: null, ...data };
}

const MAX_REDIRECT_HOPS = 10;

// Lookaheads instead of a fixed name-then-content order, since valid HTML
// doesn't guarantee attribute order.
const NOINDEX_META_RE = /<meta\b(?=[^>]*\bname=["']robots["'])(?=[^>]*\bcontent=["'][^"']*noindex)[^>]*>/i;

function hasNoindexMeta(html) {
  return NOINDEX_META_RE.test(html);
}

// Returns null (rather than throwing, or silently coercing to the literal
// string ".../undefined") when a 3xx response has no Location header — a
// malformed redirect the crawler must flag, not one it can chase.
function resolveRedirectTarget(locationHeader, baseUrl) {
  if (!locationHeader) return null;
  return new URL(locationHeader, baseUrl).href;
}

async function resolveUrl(url, ua, hopCount = 0) {
  if (hopCount >= MAX_REDIRECT_HOPS) {
    // A genuine redirect loop would otherwise recurse forever — every
    // await in the crawl is sequential, so one bad URL would hang the
    // whole run. Report what we know rather than guessing.
    return { url, status: null, redirected: true, finalUrl: null, noindex: false, redirectStatus: null, redirectHops: hopCount };
  }
  const client = url.startsWith('https:') ? https : http;
  return new Promise((resolve) => {
    const req = client.request(url, { method: 'GET', headers: { 'User-Agent': ua } }, (res) => {
      const status = res.statusCode;
      const redirected = status >= 300 && status < 400;
      if (redirected) {
        const finalUrl = resolveRedirectTarget(res.headers.location, url);
        res.resume();
        if (finalUrl === null) {
          resolve({ url, status, redirected: true, finalUrl: null, noindex: false, redirectStatus: status, redirectHops: 0 });
          return;
        }
        resolveUrl(finalUrl, ua, hopCount + 1).then((inner) =>
          resolve({
            url,
            status: inner.status,
            redirected: true,
            finalUrl: inner.finalUrl,
            noindex: inner.noindex,
            // First hop's own status code (301 vs 302); total hop count
            // accumulates from the innermost (non-redirect) call outward.
            redirectStatus: hopCount === 0 ? status : inner.redirectStatus,
            redirectHops: inner.redirectHops + 1,
          })
        );
        return;
      }
      let body = '';
      res.on('data', (c) => (body += c));
      res.on('end', () => {
        const noindex = hasNoindexMeta(body);
        resolve({ url, status, redirected: false, finalUrl: url, noindex, redirectStatus: null, redirectHops: 0 });
      });
    });
    req.on('error', () =>
      resolve({ url, status: null, redirected: false, finalUrl: url, noindex: false, redirectStatus: null, redirectHops: 0 })
    );
    req.end();
  });
}

// Word count from raw HTML with no JS execution — so CRAWL-006 can compare
// it against the JS-rendered wordCount every other check uses. Crude
// script/style strip via regex (not a real DOM), good enough to answer "is
// there real text here at all without running JS."
function computeNoJsWordCount(html) {
  const stripped = html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&[a-z]+;|&#\d+;/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return stripped ? stripped.split(' ').filter(Boolean).length : 0;
}

// extractFn/fetchImpl are injected (rather than closing over the real
// Playwright `page` and global `fetch`) so this loop's control flow — one
// URL's extraction failing must not lose every page already crawled — is
// unit-testable without a real browser or network.
async function crawlAllPages(urls, extractFn, fetchImpl, ua) {
  const pages = [];
  for (const url of urls) {
    console.error(`Fetching ${url} ...`);
    let p;
    try {
      p = await extractFn(url);
    } catch (e) {
      console.error(`  FAILED to extract ${url}: ${e.message}`);
      pages.push({ url, status: null, bytes: null, noJsWordCount: null, extractError: e.message });
      continue;
    }
    // One plain-fetch request (page.goto doesn't expose raw body size or
    // text) supplies both the byte size and the no-JS word count.
    try {
      const r = await fetchImpl(url, { headers: { 'User-Agent': ua } });
      const buf = await r.arrayBuffer();
      p.bytes = buf.byteLength;
      p.noJsWordCount = computeNoJsWordCount(Buffer.from(buf).toString('utf-8'));
    } catch (e) {
      p.bytes = null;
      p.noJsWordCount = null;
    }
    pages.push(p);
  }
  return pages;
}

// `browser` and `fn` are both injected so the "close always runs, even
// when fn throws" contract is unit-testable with a fake browser stub,
// without launching a real Chromium process.
async function runWithBrowser(browser, fn) {
  try {
    return await fn(browser);
  } finally {
    await browser.close();
  }
}

async function runCrawl(browser, args) {
  const ua = args.ua;
  const context = await browser.newContext({ userAgent: ua });
  const page = await context.newPage();

  let pageUrls;
  let origin = args.origin;
  let robotsTxt = '';

  if (args.pagesFile) {
    pageUrls = fs
      .readFileSync(args.pagesFile, 'utf-8')
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean);
    if (!origin && pageUrls.length) origin = new URL(pageUrls[0]).origin;
  } else {
    if (!origin) throw new Error('--origin is required unless --pages-file is given');
    const sitemapUrl = args.sitemapUrl || `${origin}/sitemap.xml`;
    const sitemapXml = await fetchText(sitemapUrl, ua);
    pageUrls = [...sitemapXml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1].trim());
    if (pageUrls.length === 0) {
      throw new Error(`no <loc> entries found in ${sitemapUrl} — aborting`);
    }
  }

  try {
    robotsTxt = await fetchText(`${origin}/robots.txt`, ua);
  } catch (e) {
    robotsTxt = '';
  }

  const pages = await crawlAllPages(pageUrls, (url) => extractPage(page, url), fetch, ua);

  // Discover internal hrefs not in the sitemap/page list (strip #fragments
  // — a same-page anchor isn't a distinct URL, so it can't be a coverage gap).
  const allInternalHrefs = new Set();
  for (const p of pages) for (const h of p.internalHrefs || []) allInternalHrefs.add(h);
  const knownSet = new Set(pageUrls.map((u) => u.replace(/\/$/, '')));
  const candidates = [...new Set([...allInternalHrefs].map((h) => h.split('#')[0]).filter(Boolean))].filter(
    (h) => !knownSet.has(h.replace(/\/$/, ''))
  );

  // Every candidate is also a (fragment-stripped) member of allInternalHrefs,
  // so resolving both independently would fetch the same URL twice — cache
  // by the fragment-stripped form and reuse it for both.
  const resolutionCache = new Map();
  function resolveCached(rawUrl) {
    const key = rawUrl.split('#')[0];
    if (!resolutionCache.has(key)) resolutionCache.set(key, resolveUrl(key, ua));
    return resolutionCache.get(key);
  }

  const discoveredNonSitemapPages = await Promise.all(candidates.map((c) => resolveCached(c)));

  const linkResolutions = await Promise.all(
    [...allInternalHrefs].map(async (h) => ({ ...(await resolveCached(h)), url: h }))
  );

  const site = {
    sitemapUrls: pageUrls,
    robotsTxt,
    pages,
    discoveredNonSitemapPages,
    linkResolutions,
    externalPresence: null, // filled in separately via WebSearch, not by the crawler
  };

  fs.writeFileSync(args.out, JSON.stringify(site, null, 2));
  console.error(`Wrote ${args.out} (${pages.length} pages).`);
}

// Guarded so `require('./crawl.js')` from a test can reach the exports
// below without launching a browser or hitting a live site.
if (require.main === module) {
  const args = parseArgs(process.argv.slice(2));
  const { chromium } = require('playwright');
  (async () => {
    const browser = await chromium.launch();
    await runWithBrowser(browser, (b) => runCrawl(b, args));
  })().catch((e) => {
    console.error(`ERROR: crawl failed: ${e.message}`);
    process.exit(1);
  });
}

module.exports = {
  parseArgs,
  hasNoindexMeta,
  resolveRedirectTarget,
  computeNoJsWordCount,
  resolveUrl,
  crawlAllPages,
  runWithBrowser,
  runCrawl,
};
