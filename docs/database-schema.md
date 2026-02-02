# AgentFuncHub 数据库设计

> FunctionSpec v0.1 数据持久化方案
> 
> 数据库: PostgreSQL 15+
> ORM: SQLAlchemy 2.0

---

## 实体关系图 (ERD)

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    users    │       │  functions  │       │ executions  │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │──┐    │ id (PK)     │◄─────│ id (PK)     │
│ username    │  │    │ spec_id     │       │ function_id │
│ email       │  └───►│ owner_id    │       │ user_id     │
│ github_id   │       │ name        │       │ status      │
│ api_key     │       │ description │       │ input       │
│ created_at  │       │ spec_json   │       │ output      │
└─────────────┘       │ version     │       │ duration_ms │
                      │ language    │       │ error       │
                      │ tags        │       │ created_at  │
                      │ search_text │       └─────────────┘
                      │ created_at  │
                      │ updated_at  │
                      └─────────────┘
                              │
                              │ (GIN index on tags, search_text)
                              ▼
                       ┌─────────────┐
                       │  pgvector   │
                       │ embedding   │
                       └─────────────┘
```

---

## 表结构定义

### 1. users - 用户表

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    github_id VARCHAR(100) UNIQUE,  -- GitHub OAuth
    api_key VARCHAR(64) UNIQUE,      -- API 访问密钥
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_github_id ON users(github_id);
CREATE INDEX idx_users_api_key ON users(api_key);
```

### 2. functions - 函数表

```sql
CREATE TABLE functions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spec_id VARCHAR(255) UNIQUE NOT NULL,  -- FunctionSpec id, e.g., "validation.email.basic"
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- 基本信息
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    
    -- 语言和运行时
    language VARCHAR(50) NOT NULL,  -- 'python', 'javascript', etc.
    runtime VARCHAR(100),           -- 'python>=3.8'
    
    -- 完整 FunctionSpec JSON
    spec_json JSONB NOT NULL,
    
    -- 入口点信息
    entrypoint_kind VARCHAR(20) NOT NULL,  -- 'inline', 'file', 'container', 'wasm'
    entrypoint_symbol VARCHAR(255) NOT NULL,
    entrypoint_code TEXT,  -- inline code
    
    -- 签名信息 (提取用于查询)
    signature_inputs JSONB DEFAULT '{}',
    signature_outputs JSONB DEFAULT '{}',
    
    -- 语义信息
    semantics_deterministic BOOLEAN DEFAULT TRUE,
    semantics_side_effects JSONB DEFAULT '["none"]',
    semantics_purity VARCHAR(20) DEFAULT 'pure',
    semantics_security JSONB DEFAULT '{}',
    
    -- 标签和分类 (GIN 索引)
    tags TEXT[] DEFAULT '{}',
    
    -- 搜索文本 (用于全文搜索)
    search_text TSVECTOR,
    
    -- 向量嵌入 (用于语义搜索)
    embedding VECTOR(384),  -- 使用 all-MiniLM-L6-v2 模型
    
    -- 统计信息
    view_count INTEGER DEFAULT 0,
    call_count INTEGER DEFAULT 0,
    rating_avg DECIMAL(3,2) DEFAULT 0.00,
    rating_count INTEGER DEFAULT 0,
    
    -- 质量信息
    quality_maturity VARCHAR(20) DEFAULT 'experimental',
    quality_coverage DECIMAL(3,2) DEFAULT 0.00,
    
    -- 许可证和溯源
    license VARCHAR(50) DEFAULT 'MIT',
    provenance_created_at TIMESTAMP WITH TIME ZONE,
    provenance_updated_at TIMESTAMP WITH TIME ZONE,
    provenance_source_kind VARCHAR(50),  -- 'manual', 'agent', 'imported'
    
    -- 元数据
    is_public BOOLEAN DEFAULT TRUE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_functions_spec_id ON functions(spec_id);
CREATE INDEX idx_functions_owner ON functions(owner_id);
CREATE INDEX idx_functions_language ON functions(language);
CREATE INDEX idx_functions_tags ON functions USING GIN(tags);
CREATE INDEX idx_functions_search ON functions USING GIN(search_text);
CREATE INDEX idx_functions_created ON functions(created_at DESC);

-- 向量相似度搜索索引
CREATE INDEX idx_functions_embedding ON functions USING ivfflat(embedding vector_cosine_ops);
```

### 3. executions - 执行记录表

```sql
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    function_id UUID REFERENCES functions(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- 执行状态
    status VARCHAR(20) NOT NULL,  -- 'pending', 'running', 'success', 'error', 'timeout'
    
    -- 输入输出 (JSON 格式)
    input JSONB,
    output JSONB,
    
    -- 性能指标
    duration_ms INTEGER,  -- 执行耗时
    memory_mb INTEGER,    -- 内存使用
    
    -- 错误信息
    error_type VARCHAR(50),
    error_message TEXT,
    stack_trace TEXT,
    
    -- 沙箱信息
    sandbox_id VARCHAR(100),  -- Docker container ID
    sandbox_logs TEXT,        -- 执行日志
    
    -- 元数据
    client_ip INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_executions_function ON executions(function_id);
CREATE INDEX idx_executions_user ON executions(user_id);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_created ON executions(created_at DESC);
```

### 4. function_versions - 函数版本历史

```sql
CREATE TABLE function_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    function_id UUID REFERENCES functions(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    spec_json JSONB NOT NULL,
    change_notes TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(function_id, version)
);

CREATE INDEX idx_versions_function ON function_versions(function_id);
```

### 5. ratings - 评分表

```sql
CREATE TABLE ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    function_id UUID REFERENCES functions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(function_id, user_id)
);

CREATE INDEX idx_ratings_function ON ratings(function_id);
```

---

## 扩展: pgvector

### 安装

```sql
-- 使用 Docker 镜像时:
-- docker pull ankane/pgvector

-- 或手动安装:
CREATE EXTENSION IF NOT EXISTS vector;
```

### 向量维度

| 模型 | 维度 |
|------|------|
| all-MiniLM-L6-v2 | 384 |
| text-embedding-3-small | 1536 |
| text-embedding-3-large | 3072 |

默认使用 **384 维** (all-MiniLM-L6-v2)，兼顾性能和准确性。

---

## 搜索查询示例

### 1. 全文搜索

```sql
-- 使用 tsvector 进行全文搜索
SELECT * FROM functions
WHERE search_text @@ plainto_tsquery('chinese', '验证邮箱')
ORDER BY ts_rank(search_text, plainto_tsquery('chinese', '验证邮箱')) DESC
LIMIT 10;
```

### 2. 向量相似度搜索

```sql
-- 使用 pgvector 进行语义搜索
SELECT 
    spec_id, name, description,
    embedding <-> query_embedding AS distance
FROM functions
ORDER BY embedding <-> query_embedding
LIMIT 10;
```

### 3. 混合搜索

```sql
-- 结合关键词和向量搜索
WITH keyword_results AS (
    SELECT spec_id, 1.0 AS keyword_score
    FROM functions
    WHERE tags @> ARRAY['validation', 'email']
),
vector_results AS (
    SELECT 
        spec_id,
        1 - (embedding <=> query_embedding) AS vector_score
    FROM functions
    ORDER BY embedding <=> query_embedding
    LIMIT 20
)
SELECT 
    f.spec_id, f.name, f.description,
    COALESCE(k.keyword_score, 0) * 0.3 + 
    COALESCE(v.vector_score, 0) * 0.7 AS combined_score
FROM functions f
LEFT JOIN keyword_results k ON f.spec_id = k.spec_id
LEFT JOIN vector_results v ON f.spec_id = v.spec_id
WHERE k.spec_id IS NOT NULL OR v.spec_id IS NOT NULL
ORDER BY combined_score DESC
LIMIT 10;
```

---

## 数据迁移策略

### 从 function.yaml 迁移

```python
# 伪代码
for yaml_file in examples_dir.glob("*/function.yaml"):
    spec = yaml.safe_load(yaml_file)
    
    # 提取搜索文本
    search_text = extract_search_text(spec)
    
    # 生成向量嵌入
    embedding = model.encode(search_text)
    
    # 插入数据库
    db.execute("""
        INSERT INTO functions (
            spec_id, name, description, version,
            language, runtime, spec_json,
            entrypoint_kind, entrypoint_symbol, entrypoint_code,
            signature_inputs, signature_outputs,
            semantics_deterministic, semantics_side_effects, semantics_purity,
            tags, search_text, embedding,
            quality_maturity, quality_coverage, license,
            provenance_created_at, provenance_updated_at, provenance_source_kind
        ) VALUES (...)
    """)
```

---

## ORM 模型 (SQLAlchemy)

见 `src/server/database/models.py`

---

## 性能优化

1. **索引策略**
   - GIN 索引: tags, search_text (支持数组和全文搜索)
   - IVFFlat 索引: embedding (向量相似度搜索)
   - B-tree 索引: 常用查询字段

2. **查询优化**
   - 使用 `SELECT` 只取需要的字段
   - 分页: `LIMIT` + `OFFSET`
   - 缓存热点数据到 Redis

3. **写入优化**
   - 批量插入
   - 异步更新搜索索引

---

*设计日期: 2026-02-02*
