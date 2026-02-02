"""
沙箱执行器
基于 Docker 的安全函数执行环境
"""

import json
import uuid
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
try:
    import docker
    from docker.errors import ContainerError, ImageNotFound, APIError
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


class SandboxExecutor:
    """Docker 沙箱执行器"""
    
    # 默认资源限制
    DEFAULT_MEMORY_LIMIT = "512m"
    DEFAULT_CPU_LIMIT = "1.0"
    DEFAULT_TIMEOUT = 30  # 秒
    
    # Python 执行器镜像
    EXECUTOR_IMAGE = "python:3.10-slim"
    
    def __init__(self):
        """初始化 Docker 客户端"""
        self.client = None
        if not DOCKER_AVAILABLE:
            print("⚠️  Docker SDK not installed")
            return
            
        try:
            self.client = docker.from_env()
            # 测试连接
            self.client.ping()
            print("✅ Docker client connected")
        except Exception as e:
            print(f"⚠️  Docker not available: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """检查 Docker 是否可用"""
        return self.client is not None
    
    def _generate_wrapper_code(self, func_code: str, func_symbol: str, input_data: Dict) -> str:
        """
        生成包装器代码
        
        包装器负责:
        1. 导入必要的模块
        2. 定义用户函数
        3. 解析输入参数
        4. 执行函数
        5. 序列化输出
        """
        wrapper = f'''
import json
import sys
import signal
import traceback

# 设置超时
def timeout_handler(signum, frame):
    raise TimeoutError("Function execution timed out")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm({self.DEFAULT_TIMEOUT})

# 用户函数代码
{func_code}

# 安全限制
def _disable_dangerous_modules():
    """禁用危险的模块"""
    import sys
    dangerous_modules = ['os', 'subprocess', 'socket', 'sys']
    for mod in dangerous_modules:
        if mod in sys.modules:
            sys.modules[mod] = None

_disable_dangerous_modules()

# 主执行逻辑
def main():
    try:
        # 读取输入
        with open('/app/input.json', 'r') as f:
            input_data = json.load(f)
        
        # 调用函数
        result = {func_symbol}(**input_data)
        
        # 输出结果
        output = {{
            "success": True,
            "result": result,
            "error": None
        }}
        
    except TimeoutError as e:
        output = {{
            "success": False,
            "result": None,
            "error": {{
                "type": "TimeoutError",
                "message": str(e)
            }}
        }}
    except Exception as e:
        output = {{
            "success": False,
            "result": None,
            "error": {{
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            }}
        }}
    
    # 写入输出
    with open('/app/output.json', 'w') as f:
        json.dump(output, f)
    
    sys.exit(0 if output["success"] else 1)

if __name__ == "__main__":
    main()
'''
        return wrapper
    
    def execute(
        self,
        func_code: str,
        func_symbol: str,
        input_data: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any], float]:
        """
        在沙箱中执行函数
        
        Args:
            func_code: 函数代码字符串
            func_symbol: 函数名
            input_data: 输入参数
            timeout: 超时时间（秒）
        
        Returns:
            (success, result_or_error, duration_ms)
        """
        if not self.client:
            return False, {"error": "Docker not available"}, 0.0
        
        timeout = timeout or self.DEFAULT_TIMEOUT
        execution_id = str(uuid.uuid4())[:8]
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # 写入输入文件
            with open(tmpdir / "input.json", "w") as f:
                json.dump(input_data, f)
            
            # 生成并写入包装器代码
            wrapper_code = self._generate_wrapper_code(func_code, func_symbol, input_data)
            with open(tmpdir / "execute.py", "w") as f:
                f.write(wrapper_code)
            
            # 准备 Docker 运行参数
            volumes = {
                str(tmpdir): {
                    "bind": "/app",
                    "mode": "ro"
                }
            }
            
            start_time = datetime.now()
            
            try:
                # 运行容器
                container = self.client.containers.run(
                    self.EXECUTOR_IMAGE,
                    command=["python", "/app/execute.py"],
                    volumes=volumes,
                    mem_limit=self.DEFAULT_MEMORY_LIMIT,
                    memswap_limit=self.DEFAULT_MEMORY_LIMIT,  # 禁止 swap
                    cpu_quota=int(float(self.DEFAULT_CPU_LIMIT) * 100000),  # CPU 限制
                    network_mode="none",  # 禁止网络访问
                    detach=True,
                    working_dir="/app"
                )
                
                # 等待容器完成
                result = container.wait(timeout=timeout)
                
                # 获取日志
                logs = container.logs().decode('utf-8')
                
                # 清理容器
                container.remove(force=True)
                
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                # 读取输出
                output_file = tmpdir / "output.json"
                if output_file.exists():
                    with open(output_file, "r") as f:
                        output = json.load(f)
                else:
                    output = {
                        "success": False,
                        "error": {"type": "ExecutionError", "message": "No output produced"}
                    }
                
                return output.get("success", False), output, duration
                
            except ContainerError as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                return False, {
                    "error": {
                        "type": "ContainerError",
                        "message": str(e),
                        "exit_code": e.exit_status
                    }
                }, duration
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                return False, {
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e)
                    }
                }, duration
    
    def execute_function_spec(
        self,
        func_spec: Dict[str, Any],
        input_data: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any], float]:
        """
        从 FunctionSpec 执行函数
        
        Args:
            func_spec: FunctionSpec 字典
            input_data: 输入参数
            timeout: 超时时间
        
        Returns:
            (success, result_or_error, duration_ms)
        """
        entrypoint = func_spec.get("entrypoint", {})
        
        if entrypoint.get("kind") != "inline":
            return False, {"error": "Only inline entrypoint supported"}, 0.0
        
        func_code = entrypoint.get("code", "")
        func_symbol = entrypoint.get("symbol", "")
        
        if not func_code or not func_symbol:
            return False, {"error": "Missing function code or symbol"}, 0.0
        
        return self.execute(func_code, func_symbol, input_data, timeout)


class LocalExecutor:
    """
    本地执行器（用于开发和测试，不安全！）
    """
    
    def execute(
        self,
        func_code: str,
        func_symbol: str,
        input_data: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any], float]:
        """本地执行（不安全，仅用于测试）"""
        from datetime import datetime
        import traceback
        
        start_time = datetime.now()
        
        try:
            # 创建命名空间
            namespace = {}
            
            # 执行函数定义
            exec(func_code, namespace)
            
            # 获取函数
            func = namespace.get(func_symbol)
            if not func:
                return False, {"error": f"Function {func_symbol} not found"}, 0.0
            
            # 执行函数
            result = func(**input_data)
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return True, {"result": result}, duration
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return False, {
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc()
                }
            }, duration
    
    def execute_function_spec(
        self,
        func_spec: Dict[str, Any],
        input_data: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any], float]:
        """从 FunctionSpec 执行"""
        entrypoint = func_spec.get("entrypoint", {})
        
        if entrypoint.get("kind") != "inline":
            return False, {"error": "Only inline entrypoint supported"}, 0.0
        
        func_code = entrypoint.get("code", "")
        func_symbol = entrypoint.get("symbol", "")
        
        return self.execute(func_code, func_symbol, input_data, timeout)
    
    def is_available(self) -> bool:
        """始终可用"""
        return True


def get_executor():
    """获取可用的执行器"""
    # 优先使用 Docker
    docker_executor = SandboxExecutor()
    if docker_executor.is_available():
        return docker_executor
    
    # 降级到本地执行（不安全）
    print("⚠️  Using local executor (unsafe for production)")
    return LocalExecutor()
