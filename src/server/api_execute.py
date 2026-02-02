"""
函数执行 API
提供安全的函数调用端点
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

# 导入数据库和执行器
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database import get_db_session
from database.repository import FunctionRepository
from database.models import Execution
from executor import get_executor

router = APIRouter(prefix="/execute", tags=["execution"])


# 数据模型

class ExecuteRequest(BaseModel):
    """执行请求"""
    input: Dict[str, Any] = Field(default_factory=dict, description="函数输入参数")
    timeout: Optional[int] = Field(30, ge=1, le=300, description="超时时间（秒）")
    async_exec: bool = Field(False, description="是否异步执行")


class ExecuteResponse(BaseModel):
    """执行响应"""
    success: bool
    execution_id: str
    function_id: str
    status: str  # success, error, timeout
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    duration_ms: float
    created_at: str


class ExecuteResult(BaseModel):
    """执行结果查询响应"""
    execution_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    created_at: str
    completed_at: Optional[str] = None


def get_db():
    """获取数据库会话"""
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


@router.post("/functions/{function_id}", response_model=ExecuteResponse)
async def execute_function(
    function_id: str,
    request: ExecuteRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    执行函数
    
    - **function_id**: 函数 spec_id (如: validation.email.basic)
    - **input**: 函数输入参数
    - **timeout**: 执行超时时间（默认 30 秒）
    """
    # 获取函数
    repo = FunctionRepository(db)
    func = repo.get_by_id(function_id)
    
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    
    # 创建执行记录
    execution = Execution(
        function_id=func.id,
        status="running",
        input_data=request.input,
        created_at=datetime.now()
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # 获取执行器
    executor = get_executor()
    
    # 准备函数 spec
    func_spec = {
        "entrypoint": {
            "kind": func.entrypoint_kind,
            "symbol": func.entrypoint_symbol,
            "code": func.entrypoint_code
        },
        "signature": {
            "inputs": func.signature_inputs,
            "outputs": func.signature_outputs
        }
    }
    
    # 执行函数
    success, result, duration_ms = executor.execute_function_spec(
        func_spec,
        request.input,
        timeout=request.timeout
    )
    
    # 更新执行记录
    execution.status = "success" if success else "error"
    execution.output_data = result.get("result") if success else None
    
    if not success:
        error_info = result.get("error", {})
        execution.error_type = error_info.get("type", "UnknownError")
        execution.error_message = error_info.get("message", "Unknown error")
    
    execution.duration_ms = int(duration_ms)
    execution.completed_at = datetime.now()
    
    db.commit()
    
    # 增加函数调用计数
    repo.increment_call_count(function_id)
    
    # 构建响应
    return ExecuteResponse(
        success=success,
        execution_id=str(execution.id),
        function_id=function_id,
        status=execution.status,
        result=result.get("result") if success else None,
        error=result.get("error") if not success else None,
        duration_ms=duration_ms,
        created_at=execution.created_at.isoformat()
    )


@router.get("/result/{execution_id}", response_model=ExecuteResult)
async def get_execution_result(
    execution_id: str,
    db = Depends(get_db)
):
    """
    获取执行结果
    
    - **execution_id**: 执行记录 ID
    """
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return ExecuteResult(
        execution_id=str(execution.id),
        status=execution.status,
        result=execution.output_data,
        error={
            "type": execution.error_type,
            "message": execution.error_message
        } if execution.error_type else None,
        duration_ms=execution.duration_ms,
        created_at=execution.created_at.isoformat() if execution.created_at else None,
        completed_at=execution.completed_at.isoformat() if execution.completed_at else None
    )


@router.post("/functions/{function_id}/test")
async def test_function(
    function_id: str,
    db = Depends(get_db)
):
    """
    使用测试用例测试函数
    
    自动执行函数的所有测试用例
    """
    # 获取函数
    repo = FunctionRepository(db)
    func = repo.get_by_id(function_id)
    
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    
    # 获取测试用例
    spec = func.spec_json or {}
    tests = spec.get("tests", {})
    test_cases = tests.get("cases", [])
    
    if not test_cases:
        return {
            "success": False,
            "message": "No test cases defined for this function"
        }
    
    # 执行所有测试用例
    executor = get_executor()
    func_spec = {
        "entrypoint": {
            "kind": func.entrypoint_kind,
            "symbol": func.entrypoint_symbol,
            "code": func.entrypoint_code
        }
    }
    
    results = []
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        test_name = test_case.get("name", "unnamed")
        test_input = test_case.get("input", {})
        expected = test_case.get("expect", {})
        
        success, result, duration = executor.execute_function_spec(
            func_spec, test_input
        )
        
        # 验证结果
        actual = result.get("result") if success else None
        
        # 简单的结果比较（可以根据需要改进）
        if success:
            # 检查是否包含期望的字段
            test_passed = all(
                actual.get(k) == v if isinstance(actual, dict) else False
                for k, v in expected.items()
            )
            if test_passed:
                passed += 1
            else:
                failed += 1
        else:
            failed += 1
        
        results.append({
            "name": test_name,
            "passed": test_passed if success else False,
            "duration_ms": duration,
            "actual": actual,
            "expected": expected,
            "error": result.get("error") if not success else None
        })
    
    return {
        "success": failed == 0,
        "function_id": function_id,
        "total": len(test_cases),
        "passed": passed,
        "failed": failed,
        "results": results
    }
