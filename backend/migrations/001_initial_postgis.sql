BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE data_sources (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_key text NOT NULL UNIQUE,
    name text NOT NULL,
    category text NOT NULL,
    source_agency text NOT NULL,
    public_metadata_url text,
    update_frequency text,
    license_name text,
    config_version text NOT NULL,
    is_enabled boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE import_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id uuid NOT NULL REFERENCES data_sources(id),
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    status text NOT NULL CHECK (status IN ('running', 'validated', 'published', 'failed')),
    downloaded_count integer,
    valid_count integer,
    invalid_count integer,
    published_count integer,
    quality_metrics jsonb NOT NULL DEFAULT '{}'::jsonb,
    error_summary text
);

CREATE TABLE raw_imports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id uuid NOT NULL REFERENCES data_sources(id),
    import_run_id uuid NOT NULL REFERENCES import_runs(id),
    fetched_at timestamptz NOT NULL DEFAULT now(),
    source_updated_at timestamptz,
    content_hash text NOT NULL,
    raw_data jsonb NOT NULL,
    record_count integer NOT NULL CHECK (record_count >= 0),
    import_status text NOT NULL,
    error_code text,
    error_message text,
    UNIQUE (data_source_id, content_hash)
);

CREATE TABLE places (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    public_id uuid NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    data_source_id uuid NOT NULL REFERENCES data_sources(id),
    external_id text NOT NULL,
    name text NOT NULL,
    normalized_name text NOT NULL,
    category text NOT NULL,
    subcategory text,
    address text,
    normalized_address text,
    city text,
    district text,
    latitude double precision,
    longitude double precision,
    geom geography(Point, 4326),
    phone text,
    opening_hours text,
    location_accuracy text NOT NULL CHECK (location_accuracy IN (
        'exact_coordinate', 'converted_coordinate', 'address_geocoded', 'district_only', 'invalid'
    )),
    properties jsonb NOT NULL DEFAULT '{}'::jsonb,
    canonical_group_key text,
    source_updated_at timestamptz,
    last_synced_at timestamptz NOT NULL DEFAULT now(),
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT places_data_source_id_external_id_key UNIQUE (data_source_id, external_id),
    CHECK ((latitude IS NULL) = (longitude IS NULL)),
    CHECK (latitude IS NULL OR latitude BETWEEN 21.5 AND 25.5),
    CHECK (longitude IS NULL OR longitude BETWEEN 119.0 AND 122.5),
    CHECK ((geom IS NULL) = (latitude IS NULL))
);

CREATE TABLE place_relations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    from_place_id uuid NOT NULL REFERENCES places(id),
    to_place_id uuid NOT NULL REFERENCES places(id),
    relation_type text NOT NULL CHECK (relation_type IN (
        'part_of', 'same_address', 'nearby', 'possible_same_entity'
    )),
    evidence_method text NOT NULL CHECK (evidence_method IN (
        'source_explicit', 'address_match', 'spatial_distance', 'manual_verified'
    )),
    confidence numeric(4, 3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    distance_meters numeric(10, 2) CHECK (distance_meters IS NULL OR distance_meters >= 0),
    evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (from_place_id, to_place_id, relation_type, evidence_method),
    CHECK (from_place_id <> to_place_id)
);

CREATE INDEX places_geom_active_gix ON places USING gist (geom) WHERE is_active AND geom IS NOT NULL;
CREATE INDEX places_category_area_idx ON places (category, city, district, is_active);
CREATE INDEX places_properties_gin ON places USING gin (properties);
CREATE INDEX places_name_trgm_idx ON places USING gin (normalized_name gin_trgm_ops);
CREATE INDEX places_address_trgm_idx ON places USING gin (normalized_address gin_trgm_ops);
CREATE INDEX place_relations_from_idx ON place_relations (from_place_id, relation_type);
CREATE INDEX place_relations_to_idx ON place_relations (to_place_id, relation_type);

COMMIT;
