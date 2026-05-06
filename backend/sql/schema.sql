-- SQLite schema — UK Savings & Cash ISA Rate Tracker
-- Local-first, audit-friendly: stable offers + immutable snapshots + source traceability.

PRAGMA foreign_keys = ON;

-- =========================
-- Providers and products
-- =========================
CREATE TABLE IF NOT EXISTS provider (
  provider_id            INTEGER PRIMARY KEY,
  name                   TEXT NOT NULL,
  provider_type          TEXT,                -- e.g., 'bank', 'building_society', NULL unknown
  fscs_protected         INTEGER,             -- 0/1/NULL
  fscs_notes             TEXT,
  created_at             TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at             TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS product (
  product_id             INTEGER PRIMARY KEY,
  provider_id            INTEGER NOT NULL REFERENCES provider(provider_id) ON DELETE CASCADE,
  name                   TEXT NOT NULL,
  product_type           TEXT NOT NULL,       -- 'fixed_savings' | 'cash_isa'
  created_at             TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at             TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE(provider_id, name, product_type)
);

-- =========================
-- Offers (stable “thing we rank”) + snapshots (time-versioned facts)
-- =========================
CREATE TABLE IF NOT EXISTS product_offer (
  offer_id               INTEGER PRIMARY KEY,
  product_id             INTEGER NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,

  -- Comparable set keys
  category               TEXT NOT NULL,       -- 'fixed_savings' | 'cash_isa_easy_access' | 'cash_isa_fixed' | 'cash_isa_notice'
  term_months            INTEGER NOT NULL DEFAULT -1,  -- fixed term, or -1 when not applicable/unknown
  isa_subtype            TEXT NOT NULL DEFAULT '',     -- 'easy_access'|'fixed'|'notice' or '' when not applicable/unknown

  -- State & pointers
  status                 TEXT NOT NULL DEFAULT 'active', -- 'active'|'withdrawn'|'unknown'
  current_snapshot_id    INTEGER REFERENCES offer_snapshot(snapshot_id) ON DELETE SET NULL,

  created_at             TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at             TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),

  -- Uniqueness: stable identity of an offer variant
  UNIQUE(product_id, category, term_months, isa_subtype)
);

CREATE TABLE IF NOT EXISTS offer_snapshot (
  snapshot_id                    INTEGER PRIMARY KEY,
  offer_id                       INTEGER NOT NULL REFERENCES product_offer(offer_id) ON DELETE CASCADE,

  verified_at                    TEXT NOT NULL,  -- when data was checked/observed

  -- Rates
  aer_percent                    REAL,           -- NULL unknown
  gross_percent                  REAL,
  rate_type                      TEXT,           -- 'fixed'|'variable'|NULL
  is_conditional_rate            INTEGER,        -- 0/1/NULL

  -- Bonus/intro
  bonus_percent                  REAL,
  bonus_end_date                 TEXT,           -- ISO date, or NULL
  reversion_aer_percent          REAL,

  -- Interest mechanics
  payout_frequency               TEXT,           -- 'monthly'|'annual'|'at_maturity'|NULL

  -- Balances & funding
  min_opening_deposit_gbp        INTEGER,
  min_ongoing_balance_gbp        INTEGER,
  max_balance_gbp                INTEGER,
  funding_window_days            INTEGER,

  -- Access & penalties
  withdrawals_allowed            INTEGER,        -- 0/1/NULL
  notice_days                    INTEGER,
  early_closure_allowed          INTEGER,        -- 0/1/NULL
  penalty_model_text             TEXT,           -- store canonical text like "90 days interest"

  -- Fixed savings specifics
  deposits_during_term_allowed   INTEGER,        -- 0/1/NULL
  maturity_handling_text         TEXT,
  grace_period_days              INTEGER,

  -- ISA specifics
  is_flexible_isa                INTEGER,        -- 0/1/NULL
  transfer_in_supported          INTEGER,        -- 0/1/NULL
  partial_transfers_allowed      INTEGER,        -- 0/1/NULL
  transfer_out_restrictions_text TEXT,

  -- Eligibility
  uk_residency_required          INTEGER,        -- 0/1/NULL
  min_age_years                  INTEGER,
  max_age_years                  INTEGER,
  new_customer_only              INTEGER,        -- 0/1/NULL
  new_money_required             INTEGER,        -- 0/1/NULL
  eligibility_notes              TEXT,

  -- Channels
  open_method                    TEXT,           -- 'online'|'app'|'branch'|'post'|NULL
  managed_via                    TEXT,           -- 'online'|'app'|'branch'|NULL

  -- Operational
  status                         TEXT NOT NULL DEFAULT 'active', -- snapshot's view of status

  created_at                     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),

  -- Prevent duplicate snapshots for the same check time
  UNIQUE(offer_id, verified_at)
);

-- =========================
-- Source traceability
-- =========================
CREATE TABLE IF NOT EXISTS source (
  source_id              INTEGER PRIMARY KEY,
  source_type            TEXT NOT NULL DEFAULT 'provider_page', -- 'provider_page'|'fca_register'|'other'
  url                    TEXT NOT NULL,
  retrieved_at           TEXT,         -- when fetched
  content_hash           TEXT,         -- optional: detect page changes
  created_at             TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE(url)
);

CREATE TABLE IF NOT EXISTS snapshot_source (
  snapshot_id            INTEGER NOT NULL REFERENCES offer_snapshot(snapshot_id) ON DELETE CASCADE,
  source_id              INTEGER NOT NULL REFERENCES source(source_id) ON DELETE CASCADE,
  PRIMARY KEY(snapshot_id, source_id)
);

-- =========================
-- Schema versioning
-- =========================
CREATE TABLE IF NOT EXISTS schema_version (
  version               INTEGER PRIMARY KEY,
  applied_at            TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

INSERT OR IGNORE INTO schema_version(version) VALUES (1);

-- =========================
-- Indexes for table queries
-- =========================
CREATE INDEX IF NOT EXISTS idx_offer_category_term_status
  ON product_offer(category, term_months, status);

CREATE INDEX IF NOT EXISTS idx_snapshot_offer_verified
  ON offer_snapshot(offer_id, verified_at DESC);

CREATE INDEX IF NOT EXISTS idx_snapshot_aer
  ON offer_snapshot(aer_percent DESC);

CREATE INDEX IF NOT EXISTS idx_snapshot_deposit_bounds
  ON offer_snapshot(min_opening_deposit_gbp, max_balance_gbp);

CREATE INDEX IF NOT EXISTS idx_snapshot_restrictions
  ON offer_snapshot(new_customer_only, new_money_required, uk_residency_required);

