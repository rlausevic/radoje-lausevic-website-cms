# Website counters — first phase

## What is implemented

- Journal and gallery **detail pages** display `views` beside their existing metadata.
- Video detail pages display `page views`, not plays or YouTube views.
- Archive cards, Home and Insights show no counters.
- Project details, Bibliography download buttons (also on Resume), and shared Download CV buttons record private aggregate events. Download clicks do not prove completed downloads.
- One event per item per browser-tab session, using sessionStorage and an opaque, random per-item token. The server hashes the receipt and deduplicates retries atomically in D1. Blocked browser storage limits deduplication to the current page; different tabs/devices may count separately. This is not unique-visitor analytics.
- Title edits do not reset counts. Posts, videos and galleries use collection filenames as identity, so manual filenames changes require an intentional data migration; normal CMS title/URL edits retain counts. Projects use persistent project URLs; Bibliography uses its existing UUID; the brief CV uses one permanent key even when its file is replaced.
- Counts start on activation. No historical views are invented.
- No raw IP, email, referrer or user-agent is stored in the database. IP is used transiently for best-effort request limiting. Session receipt hashes expire after 30 days; aggregate totals remain.
- These are lightweight indicative counters, not fraud-resistant audience measurement. Requests from preview deployment hosts and obvious bots are rejected. Production pages.dev and the custom domain share counters if they use the same database binding; browser session storage is origin-specific.
- No public statistics dashboard or private-count API is exposed. Private reports are available only through the owner's Cloudflare D1 console.

## Activate in Cloudflare Pages

The code is safe to publish before setup: unavailable counters stay hidden; downloads, galleries, navigation and Contact keep working.

1. Create a dedicated D1 database named **website-metrics** in the existing Cloudflare account. Check the applicable account quota before creation; no paid upgrade is required by this code.
2. In that database's Console, execute the SQL in `migrations/0001_metrics.sql`. It only creates dedicated metrics tables/index/trigger; re-running it is safe.
3. Open **Workers & Pages → radoje-lausevic-website-cms (Pages) → Settings → Bindings**. Add a **D1 database** binding named exactly **METRICS_DB**, selecting `website-metrics`, for **Production**. Do not modify CONTACT_SERVICE or any Contact variables/secrets.
4. Redeploy the Pages production build so it receives the binding.
5. Visit `https://www.radojelausevic.com/api/metrics?status=1`: `{ "enabled": true }` means the binding and schema are ready. A 503 with `enabled:false` means the binding or schema is missing/unavailable.
6. Open one published Journal detail, video detail and gallery; check the counter appears. Refresh each in the same tab: it must stay unchanged. Test visits count from activation.

The Pages function uses its own METRICS_DB binding; it does **not** forward metrics to CONTACT_SERVICE. Thus the email Worker and its settings remain independent.

## Optional direct Worker deployment

The existing Worker also supports `/api/metrics`. If the domain is changed to serve that Worker directly, it needs the same D1 binding. Configure it in `wrangler.jsonc` with the real database ID (never an invented placeholder):

```json
"d1_databases": [{"binding":"METRICS_DB","database_name":"website-metrics","database_id":"ACTUAL_DATABASE_ID"}]
```

Do not add a dummy ID to the deployed configuration. The existing `assets.run_worker_first` already routes `/api/*` through the Worker. For stronger per-location rate limiting, a separate `METRICS_RATE_LIMITER` can be bound; do not reuse CONTACT_RATE_LIMITER. Without that optional binding, a bounded in-memory limit is applied.

## Private report (D1 Console)

```sql
SELECT kind, title, path, total, first_recorded, last_recorded
FROM metrics_totals
ORDER BY kind, total DESC;
```

`post`, `video`, `gallery` are public page totals. `project` is private project interest; `bibliography` is private document-click interest per item; `cv` is private Brief CV click interest. A row appears after its first recorded event. Titles and paths update on the next event after content is edited.

## Verification

- `node --test tests/metrics*.test.mjs tests/contact*.test.mjs` (Node 22+ with node:sqlite support)
- `python3 -m unittest test_metrics test_navigation test_media_pagination test_journal_pagination test_related_content -q`
- `python3 build.py && python3 validate.py`

The SQL trigger increments totals only when a new receipt is inserted; D1 batch transactions prevent lost updates. GET requests only read counts. Unknown IDs are rejected against the deployment-generated `dist/_metrics/catalog.json`, so arbitrary pages cannot create counters. Server failures return no fake counts. Metric requests never block normal link navigation.
