-- Run once in the dedicated website-metrics D1 database. Re-running is safe.
CREATE TABLE IF NOT EXISTS metrics_totals (
  key TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  path TEXT NOT NULL,
  total INTEGER NOT NULL DEFAULT 0,
  first_recorded TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_recorded TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- An opaque per-item session receipt. No IPs, emails, referrers or user agents.
CREATE TABLE IF NOT EXISTS metrics_receipts (
  key TEXT NOT NULL,
  receipt TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  PRIMARY KEY (key, receipt)
);
CREATE INDEX IF NOT EXISTS metrics_receipts_age ON metrics_receipts(created_at);
CREATE TRIGGER IF NOT EXISTS metrics_count_insert AFTER INSERT ON metrics_receipts
BEGIN
  UPDATE metrics_totals SET total=total+1, last_recorded=CURRENT_TIMESTAMP WHERE key=NEW.key;
END;
