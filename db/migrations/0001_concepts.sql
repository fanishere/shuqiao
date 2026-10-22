-- SHU-13: language concepts schema
-- Idempotent by design; rerunning converges to the same schema.

CREATE TABLE IF NOT EXISTS concepts (
    id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kind      TEXT NOT NULL CHECK (kind IN ('vocab', 'grammar')),
    -- HSK 7-9 exist (the "advanced" band above the old 6-level list); upper
    -- levels are out of scope for now but must not be illegal.
    hsk_level SMALLINT NOT NULL CHECK (hsk_level BETWEEN 1 AND 9),
    meaning   TEXT NOT NULL,
    UNIQUE (id, kind)
);

CREATE TABLE IF NOT EXISTS vocabulary (
    id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hanzi TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS vocabulary_concepts (
    concept_id    BIGINT NOT NULL REFERENCES concepts (id),
    vocabulary_id BIGINT NOT NULL REFERENCES vocabulary (id),
    hanzi         TEXT NOT NULL,
    pinyin        TEXT NOT NULL,
    pos           TEXT[] NOT NULL,
    meaning       TEXT NOT NULL,
    examples      JSONB NOT NULL DEFAULT '[]',
    sense_index   INT NOT NULL,
    -- hanzi/pinyin/meaning are per-sense text and may legitimately differ from
    -- the vocabulary headword row; the denormalization is intentional, do not
    -- "fix" it in the SHU-16 importer. sense_index orders the senses of one
    -- concept; examples items are {hanzi, pinyin, english} objects.
    PRIMARY KEY (concept_id, sense_index)
);

CREATE TABLE IF NOT EXISTS grammar_categories (
    id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS grammar_concepts (
    concept_id  BIGINT NOT NULL REFERENCES concepts (id),
    category_id BIGINT NOT NULL REFERENCES grammar_categories (id),
    name        TEXT NOT NULL,
    pattern     TEXT NOT NULL,
    explanation TEXT NOT NULL,
    examples    JSONB NOT NULL DEFAULT '[]',
    PRIMARY KEY (concept_id)
);

CREATE TABLE IF NOT EXISTS user_concepts (
    user_id       TEXT NOT NULL,
    concept_id    BIGINT NOT NULL REFERENCES concepts (id),
    status        TEXT NOT NULL CHECK (status IN ('learning', 'known')),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    known_at      TIMESTAMPTZ,
    -- user_id is TEXT: no users table yet, auth lands in SHU-15.
    CHECK ((status = 'known') = (known_at IS NOT NULL)),
    UNIQUE (user_id, concept_id)
);

CREATE INDEX IF NOT EXISTS vocabulary_concepts_vocabulary_idx ON vocabulary_concepts (vocabulary_id);
CREATE INDEX IF NOT EXISTS grammar_concepts_category_idx ON grammar_concepts (category_id);
CREATE INDEX IF NOT EXISTS concepts_hsk_idx ON concepts (hsk_level, kind);
