"""
AgentFuncHub 后端服务
FastAPI 实现 - FunctionSpec 格式支持
支持文件存储和 PostgreSQL/SQLite 数据库
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
import yaml
import os

app = FastAPI(
    title="AgentFuncHub API",
    description="面向 AI Agent 的函数级代码共享社区 - FunctionSpec v0.1",
    version="0.2.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据存储目录
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
FUNCTIONS_FILE = DATA_DIR / "functions.json"

# 示例函数目录
EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"

# 内存存储
functions_db: Dict[str, dict] = {}

# 数据库支持（可选）
USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"

db_session = None
if USE_DATABASE:
    try:
        from database import get_db_session, USE_SQLITE
        from database.repository import FunctionRepository
        db_session = get_db_session
        print(f"[DB] Database mode enabled ({'SQLite' if USE_SQLITE else 'PostgreSQL'})")
    except Exception as e:
        print(f"[WARN] Database not available: {e}")
        USE_DATABASE = False


def load_function_yaml(yaml_path: Path) -> Optional[Dict]:
    """从 YAML 文件加载函数定义"""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {yaml_path}: {e}")
        return None


def load_functions():
    """从 examples 目录加载所有 function.yaml"""
    global functions_db
    functions_db = {}
    
    if not EXAMPLES_DIR.exists():
        print(f"[WARN] Examples directory not found: {EXAMPLES_DIR}")
        return
    
    # 遍历 examples 目录下的所有子目录
    for func_dir in EXAMPLES_DIR.iterdir():
        if func_dir.is_dir():
            yaml_path = func_dir / "function.yaml"
            if yaml_path.exists():
                func_data = load_function_yaml(yaml_path)
                if func_data:
                    func_id = func_data.get('id')
                    if func_id:
                        functions_db[func_id] = func_data
                        print(f"[OK] Loaded: {func_id}")
    
    print(f"[DATA] Loaded {len(functions_db)} functions from {EXAMPLES_DIR}")
    
    # 同时加载持久化数据（如果有）
    if FUNCTIONS_FILE.exists():
        try:
            with open(FUNCTIONS_FILE, 'r', encoding='utf-8') as f:
                persisted = json.load(f)
                # 合并数据（YAML优先）
                for func_id, func_data in persisted.items():
                    if func_id not in functions_db:
                        functions_db[func_id] = func_data
            print(f"[DATA] Loaded {len(persisted)} persisted functions")
        except Exception as e:
            print(f"[WARN] Failed to load persisted functions: {e}")


def save_functions():
    """保存函数数据到文件"""
    with open(FUNCTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(functions_db, f, ensure_ascii=False, indent=2)


# 导入向量搜索
try:
    from vector_search import VectorSearchService, keyword_search
except ImportError:
    # 降级处理
    class VectorSearchService:
        def __init__(self):
            self.model = None
            self.model_name = "fallback"
            self.function_ids = []
        
        def add_function(self, func_id, data):
            return False
        
        def search(self, query, top_k=10):
            return []
        
        def search_hybrid(self, query, matches, top_k=10):
            return []
    
    def keyword_search(query, data):
        return 0.0


# 初始化向量搜索服务
vector_service = VectorSearchService()


@app.on_event("startup")
async def startup_event():
    """启动时加载数据"""
    if USE_DATABASE:
        try:
            from database import init_db
            init_db()
        except Exception as e:
            print(f"[WARN] Database initialization skipped: {e}")

    load_functions()
    
    # 加载到向量索引
    for func_id, func_data in functions_db.items():
        vector_service.add_function(func_id, func_data)
    
    print(f"[SERVER] Started with {len(functions_db)} functions indexed")


# 数据模型 - FunctionSpec v0.1 格式

class ParameterSchema(BaseModel):
    type: str
    required: bool = True
    description: Optional[str] = None
    default: Optional[Any] = None
    example: Optional[Any] = None
    constraints: Optional[Dict[str, Any]] = None
    enum: Optional[List[Any]] = None


class SignatureSchema(BaseModel):
    inputs: Dict[str, ParameterSchema]
    outputs: Dict[str, ParameterSchema]
    errors: Optional[List[Dict[str, str]]] = None


class EntrypointSchema(BaseModel):
    kind: str  # inline/file/container/wasm
    symbol: str
    code: Optional[str] = None
    file: Optional[str] = None


class LanguageSchema(BaseModel):
    name: str
    runtime: Optional[str] = None


class SemanticsSchema(BaseModel):
    deterministic: bool = True
    side_effects: List[str] = ["none"]
    purity: str = "pure"
    concurrency: Optional[Dict[str, bool]] = None
    security: Optional[Dict[str, Any]] = None


class TestCase(BaseModel):
    name: str
    input: Dict[str, Any]
    expect: Dict[str, Any]


class TestSuite(BaseModel):
    framework: str = "builtin"
    cases: List[TestCase]


class FunctionSpec(BaseModel):
    """FunctionSpec v0.1 主模型"""
    spec_version: str = "0.1"
    id: str
    version: str = "1.0.0"
    name: str
    description: str
    license: str = "MIT"
    authors: Optional[List[Dict[str, str]]] = None
    language: LanguageSchema
    entrypoint: EntrypointSchema
    signature: SignatureSchema
    semantics: Optional[SemanticsSchema] = None
    dependencies: Optional[Dict[str, List[Dict]]] = None
    examples: Optional[List[Dict[str, Any]]] = None
    tests: Optional[TestSuite] = None
    tags: Optional[List[str]] = None
    quality: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None


class SearchQuery(BaseModel):
    query: str
    language: Optional[str] = None
    limit: int = Field(10, ge=1, le=50)


class SearchResult(BaseModel):
    function_id: str
    name: str
    description: str
    similarity_score: float
    spec: Dict[str, Any]


# API 路由

@app.get("/")
async def root():
    """根路由"""
    storage_mode = "database" if USE_DATABASE else "file"
    
    return {
        "name": "AgentFuncHub",
        "version": "0.2.0",
        "spec_version": "0.1",
        "status": "running",
        "storage_mode": storage_mode,
        "functions_count": len(functions_db),
        "search": {
            "method": "hybrid" if vector_service.model else "keyword",
            "indexed_count": len(vector_service.function_ids) if vector_service.model else 0,
            "model": vector_service.model_name if vector_service.model else None
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "functions_loaded": len(functions_db),
        "spec_version": "0.1"
    }


@app.post("/functions", response_model=Dict[str, Any])
async def create_function(spec: FunctionSpec):
    """
    创建新函数 (FunctionSpec 格式)
    """
    # 检查是否已存在
    if spec.id in functions_db:
        raise HTTPException(status_code=409, detail="Function already exists")
    
    # 验证代码哈希（如果是 inline）
    if spec.entrypoint.kind == "inline" and spec.entrypoint.code:
        code_source = spec.entrypoint.code
        # 重新计算哈希
        hash_val = hashlib.sha256(code_source.encode()).hexdigest()[:16]
    
    # 存储函数
    func_data = spec.model_dump()
    functions_db[spec.id] = func_data
    save_functions()
    
    # 添加到向量索引
    indexed = vector_service.add_function(spec.id, func_data)
    
    return {
        "success": True,
        "function_id": spec.id,
        "url": f"/functions/{spec.id}",
        "message": "Function created successfully",
        "indexed": indexed
    }


@app.get("/functions/{function_id}")
async def get_function(function_id: str):
    """
    获取函数详情 (FunctionSpec 格式)
    """
    if function_id not in functions_db:
        raise HTTPException(status_code=404, detail="Function not found")
    
    return {
        "success": True,
        "spec_version": "0.1",
        "function": functions_db[function_id]
    }


@app.get("/functions")
async def list_functions(
    language: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    列出所有函数
    """
    results = list(functions_db.values())
    
    # 过滤
    if language:
        results = [f for f in results if f.get("language", {}).get("name") == language]
    if tag:
        results = [f for f in results if tag in f.get("tags", [])]
    
    total = len(results)
    results = results[offset:offset + limit]
    
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "spec_version": "0.1",
        "functions": results
    }


@app.post("/search")
async def search_functions(query: SearchQuery):
    """
    语义搜索函数（使用向量搜索）
    """
    # 关键词匹配
    keyword_matches = []
    for func_id, func_data in functions_db.items():
        score = keyword_search_funcspec(query.query, func_data)
        if score > 0.1:
            keyword_matches.append(func_id)
    
    # 混合搜索或关键词搜索
    if vector_service.model:
        search_results = vector_service.search_hybrid(
            query.query,
            keyword_matches,
            top_k=query.limit * 2
        )
    else:
        search_results = []
        for func_id in keyword_matches:
            func_data = functions_db[func_id]
            score = keyword_search_funcspec(query.query, func_data)
            search_results.append((func_id, score))
        search_results.sort(key=lambda x: x[1], reverse=True)
        search_results = search_results[:query.limit]
    
    # 构建结果
    results = []
    for func_id, score in search_results:
        func_data = functions_db.get(func_id)
        if not func_data:
            continue
        
        # 语言过滤
        if query.language:
            if func_data.get("language", {}).get("name") != query.language:
                continue
        
        results.append({
            "function_id": func_id,
            "name": func_data.get("name"),
            "description": func_data.get("description"),
            "similarity_score": round(score, 3),
            "spec": func_data
        })
    
    results = results[:query.limit]
    
    return {
        "success": True,
        "query": query.query,
        "total": len(results),
        "spec_version": "0.1",
        "search_method": "hybrid" if vector_service.model else "keyword",
        "results": results
    }


def keyword_search_funcspec(query: str, func_data: Dict) -> float:
    """
    基于关键词的简单搜索（适配 FunctionSpec 格式）
    """
    query_words = set(query.lower().split())
    
    # 构建函数文本
    texts = [
        func_data.get('name', ''),
        func_data.get('description', ''),
        ' '.join(func_data.get('tags', [])),
    ]
    
    # 添加签名信息
    signature = func_data.get('signature', {})
    for param_name in signature.get('inputs', {}).keys():
        texts.append(param_name)
    for param_name in signature.get('outputs', {}).keys():
        texts.append(param_name)
    
    func_text = ' '.join(texts).lower()
    func_words = set(func_text.split())
    
    # 同义词扩展
    synonyms = {
        'email': ['mail', 'mailbox', '邮箱'],
        'phone': ['mobile', 'cellphone', 'telephone', '电话', '手机'],
        'validate': ['check', 'verify', 'validation', '验证'],
        'date': ['time', 'datetime', 'calendar', '日期', '时间'],
        'password': ['pwd', 'passwd', '密码'],
        'json': ['json', 'json格式'],
        'encode': ['encoding', 'decode', '编码'],
    }
    
    expanded_query = set(query_words)
    for word in query_words:
        if word in synonyms:
            expanded_query.update(synonyms[word])
    
    # 计算 Jaccard 相似度
    intersection = len(expanded_query & func_words)
    union = len(expanded_query | func_words)
    
    return intersection / union if union > 0 else 0.0


@app.delete("/functions/{function_id}")
async def delete_function(function_id: str):
    """
    删除函数
    """
    if function_id not in functions_db:
        raise HTTPException(status_code=404, detail="Function not found")
    
    del functions_db[function_id]
    save_functions()
    
    return {
        "success": True,
        "message": "Function deleted successfully"
    }


@app.post("/validate")
async def validate_function(spec: FunctionSpec):
    """
    验证函数（检查 FunctionSpec 格式和测试用例）
    """
    errors = []
    warnings = []
    
    # 检查必需字段
    if not spec.id:
        errors.append("Missing required field: id")
    if not spec.name:
        errors.append("Missing required field: name")
    if not spec.description:
        errors.append("Missing required field: description")
    if not spec.signature:
        errors.append("Missing required field: signature")
    
    # 检查 entrypoint
    if not spec.entrypoint:
        errors.append("Missing required field: entrypoint")
    elif spec.entrypoint.kind == "inline" and not spec.entrypoint.code:
        errors.append("Inline entrypoint requires 'code' field")
    
    # 检查测试用例
    if not spec.tests or not spec.tests.cases:
        warnings.append("No test cases provided")
    
    # 检查语义声明
    if not spec.semantics:
        warnings.append("No semantics declaration provided")
    
    return {
        "valid": len(errors) == 0,
        "spec_version": "0.1",
        "errors": errors,
        "warnings": warnings
    }


@app.get("/tags")
async def get_tags():
    """
    获取所有标签
    """
    tags = set()
    for func in functions_db.values():
        tags.update(func.get("tags", []))
    
    return {
        "success": True,
        "tags": sorted(list(tags))
    }


@app.get("/languages")
async def get_languages():
    """
    获取所有编程语言
    """
    languages = set()
    for func in functions_db.values():
        lang = func.get("language", {}).get("name")
        if lang:
            languages.add(lang)
    
    return {
        "success": True,
        "languages": sorted(list(languages))
    }


# 导入并注册额外 API 模块
try:
    # 数据库 API (可选)
    if USE_DATABASE:
        from api_db import router as db_router
        app.include_router(db_router)
        print("[OK] Database API routes registered")
except Exception as e:
    print(f"[WARN] Database API not loaded: {e}")

try:
    # 执行 API
    from api_execute import router as execute_router
    app.include_router(execute_router)
    print("[OK] Execute API routes registered")
except Exception as e:
    print(f"[WARN] Execute API not loaded: {e}")

try:
    # 认证 API
    from api_auth import router as auth_router
    app.include_router(auth_router)
    print("[OK] Auth API routes registered")
except Exception as e:
    print(f"[WARN] Auth API not loaded: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
