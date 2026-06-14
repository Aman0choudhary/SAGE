CREATE TABLE IF NOT EXISTS memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_full_name TEXT NOT NULL,
  memory_ref TEXT NOT NULL,
  memory_type TEXT NOT NULL,
  title TEXT NOT NULL,
  vector_store_file_id TEXT,
  source_type TEXT NOT NULL,
  source_id INTEGER,
  source_url TEXT,
  author_github TEXT,
  files_affected TEXT[],
  domains TEXT[],
  risk_level TEXT,
  is_overridden BOOLEAN DEFAULT FALSE,
  overridden_by UUID REFERENCES memories(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memories_repo ON memories (repo_full_name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_memories_repo_ref ON memories (repo_full_name, memory_ref);

CREATE TABLE IF NOT EXISTS patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_full_name TEXT NOT NULL,
  pattern_ref TEXT NOT NULL,
  rule TEXT NOT NULL,
  source_pr INTEGER,
  stated_by TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  violation_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patterns_repo ON patterns (repo_full_name);

CREATE TABLE IF NOT EXISTS promises (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_full_name TEXT NOT NULL,
  issue_number INTEGER NOT NULL,
  pr_number INTEGER,
  promise TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  made_by TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_promises_repo_issue ON promises (repo_full_name, issue_number);

CREATE TABLE IF NOT EXISTS commit_ledger (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_full_name TEXT NOT NULL,
  commit_sha TEXT NOT NULL,
  author TEXT NOT NULL,
  files_changed TEXT[],
  domains_touched TEXT[],
  breaking_risk TEXT,
  committed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_commit_ledger_repo ON commit_ledger (repo_full_name);

CREATE TABLE IF NOT EXISTS repo_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_full_name TEXT UNIQUE NOT NULL,
  openai_vector_store_id TEXT,
  memory_counter INTEGER DEFAULT 0,
  pattern_counter INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  installed_at TIMESTAMPTZ DEFAULT NOW()
);
