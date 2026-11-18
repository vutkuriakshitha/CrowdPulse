-- VigilantTwin core DDL (PostgreSQL / TimescaleDB)

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE venues (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  timezone TEXT DEFAULT 'UTC',
  boundary JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE zones (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  venue_id UUID REFERENCES venues(id),
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  polygon JSONB NOT NULL,
  area_m2 DOUBLE PRECISION NOT NULL,
  capacity INT NOT NULL,
  exits JSONB DEFAULT '[]',
  adjacent JSONB DEFAULT '[]',
  is_ingress BOOLEAN DEFAULT FALSE,
  UNIQUE(venue_id, code)
);

CREATE TABLE cameras (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  venue_id UUID REFERENCES venues(id),
  code TEXT NOT NULL,
  stream_url TEXT,
  homography JSONB,
  fps INT DEFAULT 10,
  edge_node_id TEXT,
  is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE fused_counts (
  time TIMESTAMPTZ NOT NULL,
  zone_id UUID NOT NULL REFERENCES zones(id),
  count INT,
  density DOUBLE PRECISION,
  mean_speed DOUBLE PRECISION,
  flow_vector JSONB
);
SELECT create_hypertable('fused_counts', 'time', if_not_exists => TRUE);

CREATE TABLE risk_scores (
  time TIMESTAMPTZ NOT NULL,
  zone_id UUID NOT NULL REFERENCES zones(id),
  dcrs DOUBLE PRECISION,
  band TEXT,
  horizon_minutes INT DEFAULT 0,
  forecast_json JSONB
);
SELECT create_hypertable('risk_scores', 'time', if_not_exists => TRUE);

CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  zone_id UUID REFERENCES zones(id),
  severity TEXT,
  status TEXT DEFAULT 'open',
  dcrs DOUBLE PRECISION,
  band TEXT,
  explanation JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE decisions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  alert_id UUID REFERENCES alerts(id),
  rationale TEXT,
  actions JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE simulations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  venue_id UUID REFERENCES venues(id),
  scenario JSONB,
  result JSONB,
  status TEXT DEFAULT 'completed',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE incident_reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_name TEXT,
  venue_name TEXT,
  markdown TEXT,
  pdf_uri TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
