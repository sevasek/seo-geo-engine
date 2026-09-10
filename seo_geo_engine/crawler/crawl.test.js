// Unit tests for crawl.js's pure/injectable helpers. Uses Node's built-in
// test runner (node --test) — no extra dependency, since this directory
// isn't part of the Python package's pytest suite. Run with:
//   node --test seo_geo_engine/crawler/crawl.test.js
'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const {
  parseArgs,
  hasNoindexMeta,
  resolveRedirectTarget,
  computeNoJsWordCount,
  crawlAllPages,
  runWithBrowser,
} = require('./crawl.js');

test('parseArgs: --origin/--sitemap-url/--ua/--out are all recognized', () => {
  const args = parseArgs(['--origin', 'https://example.com', '--sitemap-url', 'https://example.com/s.xml', '--ua', 'MyBot', '--out', 'out.json']);
  assert.equal(args.origin, 'https://example.com');
  assert.equal(args.sitemapUrl, 'https://example.com/s.xml');
  assert.equal(args.ua, 'MyBot');
  assert.equal(args.out, 'out.json');
});

test('parseArgs: --out defaults to site-crawl.json, --ua defaults to a generic UA', () => {
  const args = parseArgs(['--origin', 'https://example.com']);
  assert.equal(args.out, 'site-crawl.json');
  assert.ok(args.ua.includes('seo-geo-engine-crawler'));
});

test('parseArgs: a bare positional argument is treated as the output path (back-compat)', () => {
  const args = parseArgs(['my-output.json']);
  assert.equal(args.out, 'my-output.json');
});

test('hasNoindexMeta: matches name before content (the common order)', () => {
  assert.equal(hasNoindexMeta('<html><head><meta name="robots" content="noindex,follow"></head></html>'), true);
});

test('hasNoindexMeta: matches content before name — valid HTML either order', () => {
  assert.equal(hasNoindexMeta('<html><head><meta content="noindex,follow" name="robots"></head></html>'), true);
});

test('hasNoindexMeta: false when there is no robots meta tag at all', () => {
  assert.equal(hasNoindexMeta('<html><head><meta name="description" content="hi"></head></html>'), false);
});

test('hasNoindexMeta: false when a robots meta tag exists but does not say noindex', () => {
  assert.equal(hasNoindexMeta('<meta name="robots" content="index,follow">'), false);
});

test('hasNoindexMeta: false when "noindex" appears elsewhere on the page, not in a robots meta tag', () => {
  assert.equal(hasNoindexMeta('<body>Please noindex this reference to the word.</body>'), false);
});

test('resolveRedirectTarget: null when the Location header is missing', () => {
  assert.equal(resolveRedirectTarget(undefined, 'https://example.com/a'), null);
  assert.equal(resolveRedirectTarget('', 'https://example.com/a'), null);
});

test('resolveRedirectTarget: resolves a relative Location against the request URL', () => {
  assert.equal(resolveRedirectTarget('/b', 'https://example.com/a'), 'https://example.com/b');
});

test('resolveRedirectTarget: passes through an absolute Location', () => {
  assert.equal(resolveRedirectTarget('https://other.example.com/x', 'https://example.com/a'), 'https://other.example.com/x');
});

test('computeNoJsWordCount: strips script/style/comments before counting', () => {
  const html = '<html><body><script>var x=1;var y=2;</script><style>.a{color:red}</style><!-- hi --><p>Real content here</p></body></html>';
  assert.equal(computeNoJsWordCount(html), 3);
});

test('crawlAllPages: one URL failing extraction does not lose pages already crawled', async () => {
  const urls = ['https://example.com/a', 'https://example.com/broken', 'https://example.com/c'];
  const extractFn = async (url) => {
    if (url.includes('broken')) throw new Error('navigation timeout of 30000ms exceeded');
    return { url, internalHrefs: [] };
  };
  const fetchImpl = async () => ({ arrayBuffer: async () => Buffer.from('hello world') });

  const pages = await crawlAllPages(urls, extractFn, fetchImpl, 'test-ua');

  assert.equal(pages.length, 3, 'all three URLs must be represented, none dropped');
  assert.equal(pages[0].url, 'https://example.com/a');
  assert.equal(pages[1].url, 'https://example.com/broken');
  assert.ok(pages[1].extractError, 'the failed page should carry an extractError instead of aborting the crawl');
  assert.equal(pages[2].url, 'https://example.com/c');
});

test('crawlAllPages: a byte-size fetch failure does not lose the already-extracted page data', async () => {
  const urls = ['https://example.com/a'];
  const extractFn = async (url) => ({ url, internalHrefs: [], title: 'A' });
  const fetchImpl = async () => {
    throw new Error('network error');
  };

  const pages = await crawlAllPages(urls, extractFn, fetchImpl, 'test-ua');

  assert.equal(pages.length, 1);
  assert.equal(pages[0].title, 'A');
  assert.equal(pages[0].bytes, null);
  assert.equal(pages[0].noJsWordCount, null);
});

test('runWithBrowser: closes the browser even when the crawl function throws', async () => {
  let closed = false;
  const fakeBrowser = {
    close: async () => {
      closed = true;
    },
  };

  await assert.rejects(
    () =>
      runWithBrowser(fakeBrowser, async () => {
        throw new Error('boom');
      }),
    /boom/
  );
  assert.equal(closed, true, 'browser.close() must run even though the crawl function threw');
});

test('runWithBrowser: closes the browser and returns the result on success', async () => {
  let closed = false;
  const fakeBrowser = {
    close: async () => {
      closed = true;
    },
  };

  const result = await runWithBrowser(fakeBrowser, async () => 'done');

  assert.equal(result, 'done');
  assert.equal(closed, true);
});
