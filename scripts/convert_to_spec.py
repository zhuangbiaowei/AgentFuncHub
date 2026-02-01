#!/usr/bin/env python3
"""
批量转换 manifest.json 到 function.yaml
"""

import json
import yaml
import os
from pathlib import Path

def convert_manifest_to_spec(manifest_path):
    """转换单个 manifest.json 到 function.yaml"""
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    # 构建新的 spec
    spec = {
        "spec_version": "0.1",
        "id": manifest.get("function_id", "").replace("func-", "").replace("-", "."),
        "version": manifest.get("version", "1.0.0"),
        "name": manifest.get("display_name", manifest.get("name", "")),
        "description": manifest.get("description", ""),
        "license": manifest.get("license", "MIT"),
        "authors": [
            {
                "name": manifest.get("author", {}).get("name", "Unknown"),
                "contact": manifest.get("author", {}).get("contact", "")
            }
        ],
        "language": {
            "name": manifest.get("language", "python"),
            "runtime": "python>=3.8"
        },
        "entrypoint": {
            "kind": "inline",
            "symbol": manifest.get("name", ""),
            "code": manifest.get("code", {}).get("source", "")
        },
        "signature": {
            "inputs": {},
            "outputs": {}
        },
        "semantics": {
            "deterministic": True,
            "side_effects": ["none"],
            "security": {
                "sandbox_required": manifest.get("security", {}).get("sandbox_required", False),
                "data_sensitivity": manifest.get("security", {}).get("risk_level", "low")
            }
        },
        "tests": {
            "framework": "builtin",
            "cases": []
        },
        "tags": manifest.get("tags", []),
        "quality": {
            "maturity": "stable"
        },
        "provenance": {
            "created_at": manifest.get("created_at", ""),
            "updated_at": manifest.get("updated_at", ""),
            "source": {
                "kind": "manual"
            }
        }
    }
    
    # 转换 signature inputs
    sig = manifest.get("signature", {})
    for inp in sig.get("inputs", []):
        name = inp.get("name", "")
        spec["signature"]["inputs"][name] = {
            "type": inp.get("type", "string"),
            "required": inp.get("required", False),
            "description": inp.get("description", "")
        }
        if "default" in inp:
            spec["signature"]["inputs"][name]["default"] = inp["default"]
        if "constraints" in inp:
            spec["signature"]["inputs"][name]["constraints"] = inp["constraints"]
    
    # 转换 signature outputs
    for i, out in enumerate(sig.get("outputs", [])):
        name = out.get("name", f"output_{i}")
        spec["signature"]["outputs"][name] = {
            "type": out.get("type", "string"),
            "description": out.get("description", "")
        }
    
    # 转换 test cases
    for test in manifest.get("test_cases", []):
        case = {
            "name": test.get("name", ""),
            "input": test.get("input", {}),
            "expect": test.get("expected", {})
        }
        spec["tests"]["cases"].append(case)
    
    return spec

def main():
    examples_dir = Path("/home/mlf/AgentFuncHub/examples")
    
    for func_dir in examples_dir.iterdir():
        if not func_dir.is_dir():
            continue
            
        manifest_path = func_dir / "manifest.json"
        if not manifest_path.exists():
            continue
            
        try:
            spec = convert_manifest_to_spec(manifest_path)
            
            # 写入 function.yaml
            output_path = func_dir / "function.yaml"
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(spec, f, allow_unicode=True, sort_keys=False, width=100)
            
            # 删除旧文件
            manifest_path.unlink()
            
            print(f"✅ Converted: {func_dir.name}")
            
        except Exception as e:
            print(f"❌ Failed: {func_dir.name} - {e}")

if __name__ == "__main__":
    main()
