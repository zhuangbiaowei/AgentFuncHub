"""
AgentFuncHub Python SDK (Prototype)

用于与 AgentFuncHub 服务交互的 Python SDK。
"""

from typing import Any, Callable, Optional, Dict, List
import requests
import json


class Function:
    """表示一个注册的函数"""
    
    def __init__(self, function_id: str, manifest: dict, client: 'Client'):
        self.function_id = function_id
        self.manifest = manifest
        self._client = client
    
    def __repr__(self):
        return f"Function({self.manifest.get('name', 'unknown')})"
    
    def call(self, *args, **kwargs) -> Any:
        """调用此函数"""
        return self._client.call(self.function_id, *args, **kwargs)
    
    @property
    def name(self) -> str:
        return self.manifest.get('name', '')
    
    @property
    def description(self) -> str:
        return self.manifest.get('description', '')
    
    @property
    def signature(self) -> dict:
        return self.manifest.get('signature', {})


class Client:
    """AgentFuncHub 客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.agentfunchub.io/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def search(self, query: str, language: Optional[str] = None, 
               limit: int = 10) -> List[Function]:
        """搜索函数"""
        payload = {
            "query": query,
            "limit": limit
        }
        if language:
            payload["language"] = language
        
        resp = self.session.post(f"{self.base_url}/search", json=payload)
        resp.raise_for_status()
        
        data = resp.json()
        return [
            Function(r["function_id"], r["manifest"], self)
            for r in data.get("results", [])
        ]
    
    def call(self, function_id: str, *args, **kwargs) -> Any:
        """调用指定函数"""
        payload = {
            "args": args,
            "kwargs": kwargs
        }
        resp = self.session.post(
            f"{self.base_url}/functions/{function_id}/call",
            json=payload
        )
        resp.raise_for_status()
        return resp.json().get("result")
    
    def publish(self, func: Callable, manifest: Optional[dict] = None) -> Function:
        """发布函数到 AgentFuncHub"""
        import inspect
        
        # 自动提取函数信息
        name = func.__name__
        description = func.__doc__ or ""
        source = inspect.getsource(func)
        
        # 构建 manifest
        if manifest is None:
            manifest = {}
        
        manifest.setdefault("name", name)
        manifest.setdefault("description", description)
        
        # 解析签名
        sig = inspect.signature(func)
        inputs = []
        for param_name, param in sig.parameters.items():
            inputs.append({
                "name": param_name,
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                "required": param.default == inspect.Parameter.empty,
                "default": param.default if param.default != inspect.Parameter.empty else None
            })
        
        return_annotation = sig.return_annotation
        outputs = [{
            "type": str(return_annotation) if return_annotation != inspect.Parameter.empty else "Any"
        }]
        
        manifest["signature"] = {
            "inputs": inputs,
            "outputs": outputs
        }
        
        payload = {
            "manifest": manifest,
            "code": source
        }
        
        resp = self.session.post(f"{self.base_url}/functions", json=payload)
        resp.raise_for_status()
        
        data = resp.json()
        return Function(data["function_id"], manifest, self)
    
    def get(self, function_id: str) -> Optional[Function]:
        """获取函数详情"""
        resp = self.session.get(f"{self.base_url}/functions/{function_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        
        data = resp.json()
        return Function(data["function_id"], data["manifest"], self)


def publish(**manifest_kwargs):
    """装饰器：自动发布函数到 AgentFuncHub"""
    def decorator(func: Callable) -> Callable:
        # 这里可以实现自动发布逻辑
        # 暂时只是标记
        func._funchub_manifest = manifest_kwargs
        return func
    return decorator


def find(query: str, language: Optional[str] = None) -> Optional[Function]:
    """
    快速查找函数（使用默认客户端）
    注意：需要在环境变量中设置 AGENTFUNCHUB_API_KEY
    """
    import os
    api_key = os.getenv("AGENTFUNCHUB_API_KEY")
    if not api_key:
        raise ValueError("Please set AGENTFUNCHUB_API_KEY environment variable")
    
    client = Client(api_key)
    results = client.search(query, language, limit=1)
    return results[0] if results else None
