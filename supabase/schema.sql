-- 48hours Neukölln Map — flat 2-table schema (ADR-022)
-- Apply in Supabase SQL Editor. Drops old 4-table schema first.

DROP TABLE IF EXISTS event_categories CASCADE;
DROP TABLE IF EXISTS events           CASCADE;
DROP TABLE IF EXISTS venues           CASCADE;
DROP TABLE IF EXISTS categories       CASCADE;

CREATE TABLE categories (
  id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  name       TEXT        NOT NULL UNIQUE,
  emoji      TEXT,
  colour     TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE events (
  id             UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
  title          TEXT             NOT NULL,
  day            TEXT,
  start_time     TEXT,
  end_time       TEXT,
  location       TEXT,
  address        TEXT,
  lat            DOUBLE PRECISION,
  lng            DOUBLE PRECISION,
  geocode_source TEXT,
  genres         TEXT[],
  emoji          TEXT[],
  link           TEXT,
  accessibility  BOOLEAN          NOT NULL DEFAULT FALSE,
  toilet         BOOLEAN          NOT NULL DEFAULT FALSE,
  scraped_at     TIMESTAMPTZ      DEFAULT NOW(),
  updated_at     TIMESTAMPTZ      DEFAULT NOW(),
  CONSTRAINT events_link_day_key UNIQUE (link, day)
);

ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE events      ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public read" ON categories FOR SELECT USING (true);
CREATE POLICY "public read" ON events     FOR SELECT USING (true);
