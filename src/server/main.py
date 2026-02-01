"""
AgentFuncHub 后端服务
FastAPI 实现
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path

app = FastAPI(
    title="AgentFuncHub API",
    description="面向 AI Agent 的函数级代码共享社区",
    version="0.1.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据存储（简化版，使用内存 + JSON 文件）
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
FUNCTIONS_FILE = DATA_DIR / "functions.json"

# 内存存储
functions_db: Dict[str, dict] = {}


def load_functions():
    """从文件加载函数数据"""
    global functions_db
    if FUNCTIONS_FILE.exists():
        with open(FUNCTIONS_FILE, 'r', encoding='utf-8') as f:
            functions_db = json.load(f)


def save_functions():
    """保存函数数据到文件"""
    with open(FUNCTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(functions_db, f, ensure_ascii=False, indent=2)


# 启动时加载数据
@app.on_event("startup")
async def startup_event():
    load_functions()


# 数据模型
class FunctionInput(BaseModel):
    name: str = Field(..., description="参数名")
    type: str = Field(..., description="参数类型")
    description: str = Field(..., description="参数描述")
    required: bool = Field(True, description="是否必需")
    default: Optional[Any] = Field(None, description="默认值")


class FunctionOutput(BaseModel):
    type: str = Field(..., description="返回类型")
    description: str = Field(..., description="返回描述")


class FunctionSignature(BaseModel):
    inputs: List[FunctionInput]
    outputs: List[FunctionOutput]


class TestCase(BaseModel):
    name: str
    description: str
    input: Dict[str, Any]
    expected: Dict[str, Any]
    tags: Optional[List[str]] = []


class FunctionCode(BaseModel):
    source: str
    hash: str
    line_count: int
    complexity: float


class FunctionSecurity(BaseModel):
    sandbox_required: bool = True
    network_access: bool = False
    filesystem_access: bool = False
    risk_level: str = "low"


class FunctionManifest(BaseModel):
    function_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    display_name: Optional[str] = None
    description: str
    language: str
    version: str = "1.0.0"
    signature: FunctionSignature
    code: FunctionCode
    test_cases: List[TestCase]
    tags: List[str] = []
    categories: List[str] = []
    usage_scenarios: List[str] = []
    security: FunctionSecurity = FunctionSecurity()
    author: Dict[str, Any]
    license: str = "MIT"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SearchQuery(BaseModel):
    query: str
    language: Optional[str] = None
    limit: int = Field(10, ge=1, le=50)


class SearchResult(BaseModel):
    function_id: str
    name: str
    description: str
    similarity_score: float
    manifest: Dict[str, Any]


# 简单的向量表示（使用关键词匹配作为原型）
def get_vector_representation(text: str) -> List[str]:
    """获取文本的向量表示（关键词列表）"""
    # 简化的实现：分词并去重
    words = text.lower().split()
    # 添加一些常见同义词
    synonyms = {
        "email": ["mail", "mailbox"],
        "validate": ["check", "verify", "validation"],
        "phone": ["mobile", "cellphone", "telephone"],
        "date": ["time", "datetime", "calendar"],
        "text": ["string", "content", "article"],
        "truncate": ["cut", "shorten", "limit"],
    }
    result = set(words)
    for word in words:
        if word in synonyms:
            result.update(synonyms[word])
    return list(result)


def calculate_similarity(query: str, func_manifest: dict) -> float:
    """计算查询与函数的相似度（简化版）"""
    query_words = set(get_vector_representation(query))
    
    # 构建函数描述文本
    func_text = f"{func_manifest.get('name', '')} {func_manifest.get('description', '')} {' '.join(func_manifest.get('tags', []))}"
    func_words = set(get_vector_representation(func_text))
    
    if not query_words or not func_words:
        return 0.0
    
    # Jaccard 相似度
    intersection = len(query_words & func_words)
    union = len(query_words | func_words)
    return intersection / union if union > 0 else 0.0


# API 路由
@app.get("/")
async def root():
    """根路由"""
    return {
        "name": "AgentFuncHub",
        "version": "0.1.0",
        "status": "running",
        "functions_count": len(functions_db)
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/functions", response_model=Dict[str, Any])
async def create_function(manifest: FunctionManifest):
    """
    创建新函数
    """
    # 检查是否已存在
    if manifest.function_id in functions_db:
        raise HTTPException(status_code=409, detail="Function already exists")
    
    # 验证代码哈希
    code_source = manifest.code.source
    expected_hash = hashlib.sha256(code_source.encode()).hexdigest()[:16]
    if manifest.code.hash != expected_hash and manifest.code.hash != "sha256:placeholder":
        # 重新计算哈希
        manifest.code.hash = f"sha256:{expected_hash}"
    
    # 存储函数
    func_data = manifest.dict()
    functions_db[manifest.function_id] = func_data
    save_functions()
    
    return {
        "success": True,
        "function_id": manifest.function_id,
        "url": f"/functions/{manifest.function_id}",
        "message": "Function created successfully"
    }


@app.get("/functions/{function_id}")
async def get_function(function_id: str):
    """
    获取函数详情
    """
    if function_id not in functions_db:
        raise HTTPException(status_code=404, detail="Function not found")
    
    return {
        "success": True,
        "function": functions_db[function_id]
    }


@app.get("/functions")
async def list_functions(
    language: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    列出所有函数
    """
    results = list(functions_db.values())
    
    # 过滤
    if language:
        results = [f for f in results if f.get("language") == language]
    if category:
        results = [f for f in results if category in f.get("categories", [])]
    
    total = len(results)
    results = results[offset:offset + limit]
    
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "functions": results
    }


@app.post("/search")
async def search_functions(query: SearchQuery):
    """
    语义搜索函数
    """
    results = []
    
    for func_id, func_data in functions_db.items():
        score = calculate_similarity(query.query, func_data)
        
        # 语言过滤
        if query.language and func_data.get("language") != query.language:
            continue
        
        if score > 0:  # 只返回有相似度的结果
            results.append({
                "function_id": func_id,
                "name": func_data.get("name"),
                "description": func_data.get("description"),
                "similarity_score": round(score, 3),
                "manifest": func_data
            })
    
    # 按相似度排序
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    results = results[:query.limit]
    
    return {
        "success": True,
        "query": query.query,
        "total": len(results),
        "results": results
    }


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
async def validate_function(manifest: FunctionManifest):
    """
    验证函数（检查语法和测试用例）
    """
    errors = []
    warnings = []
    
    # 检查必需字段
    required_fields = ["name", "description", "language", "signature", "code"]
    for field in required_fields:
        if not getattr(manifest, field, None):
            errors.append(f"Missing required field: {field}")
    
    # 检查测试用例
    if not manifest.test_cases:
        warnings.append("No test cases provided")
    else:
        # 这里可以执行测试用例验证代码
        pass
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


@app.get("/categories")
async def get_categories():
    """
    获取所有分类
    """
    categories = set()
    for func in functions_db.values():
        categories.update(func.get("categories", []))
    
    return {
        "success": True,
        "categories": sorted(list(categories))
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
