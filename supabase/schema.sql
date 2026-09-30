-- EFFIONG AI - optional Supabase schema
-- Only needed if you set SUPABASE_URL + SUPABASE_KEY. Run this once in the Supabase SQL editor.
-- Enables: cloud-synced chat threads, a shared/cloud-synced heritage ledger, and (with pgvector)
-- a cloud tier for the self-learning knowledge memory alongside the always-on local SQLite tier.

create extension if not exists vector;

create table if not exists chat_threads (
    id text primary key,
    title text,
    updated_at timestamptz default now(),
    messages jsonb not null default '[]'::jsonb
);

create table if not exists heritage_records (
    id text primary key,
    title text,
    description text,
    node_type text,
    verification_class text,
    truth_classification text,
    status text,
    confidence numeric,
    assessment text,
    evidence_url text,
    evidence_sources jsonb,
    evidence_files jsonb,
    truth_matrix jsonb,
    contributor text,
    contributor_id text,
    created_at timestamptz,
    updated_at timestamptz,
    checked_at text,
    archives jsonb,
    record_sha256 text
);

-- Cloud tier for src/database/vector_mesh.py (dimension must stay 768 to match src/brain/embeddings.py)
create table if not exists knowledge (
    id text primary key,
    content text not null,
    metadata jsonb,
    emb_tag text not null default 'local-hash-768',
    embedding vector(768),
    created_at timestamptz default now()
);

create index if not exists knowledge_embedding_idx on knowledge using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create or replace function match_knowledge(query_embedding vector(768), match_count int, tag text)
returns table(id text, content text, metadata jsonb, similarity float)
language sql stable as $$
    select id, content, metadata, 1 - (embedding <=> query_embedding) as similarity
    from knowledge
    where emb_tag = tag
    order by embedding <=> query_embedding
    limit match_count;
$$;

alter table chat_threads enable row level security;
alter table heritage_records enable row level security;
alter table knowledge enable row level security;

-- The app talks to Supabase with the service/anon key server-side (inside Streamlit), so a single
-- permissive policy is enough for a single-tenant deployment. Tighten this if you expose the
-- Supabase keys to end users directly.
create policy if not exists "effiong service access chat" on chat_threads for all using (true) with check (true);
create policy if not exists "effiong service access heritage" on heritage_records for all using (true) with check (true);
create policy if not exists "effiong service access knowledge" on knowledge for all using (true) with check (true);
