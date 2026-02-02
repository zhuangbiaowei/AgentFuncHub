#!/usr/bin/env python3
"""
FunctionSpec 验证工具
验证 function.yaml 文件是否符合 FunctionSpec v0.1 规范

用法:
    python validate_spec.py <path/to/function.yaml>
    python validate_spec.py --all  # 验证所有 examples 下的函数
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]


class FunctionSpecValidator:
    """FunctionSpec v0.1 验证器"""
    
    REQUIRED_FIELDS = {
        "spec_version",
        "id",
        "version",
        "name",
        "description",
        "language",
        "entrypoint",
        "signature",
    }
    
    ENTRYPOINT_KINDS = {"inline", "file", "container", "wasm"}
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
    
    def validate(self, data: Dict) -> ValidationResult:
        """验证函数定义"""
        self.errors = []
        self.warnings = []
        self.info = []
        
        if not data:
            self.errors.append("Empty YAML data")
            return ValidationResult(False, self.errors, self.warnings, self.info)
        
        # 检查必需字段
        self._validate_required_fields(data)
        
        # 验证 spec_version
        self._validate_spec_version(data.get("spec_version"))
        
        # 验证 id 格式
        self._validate_id(data.get("id"))
        
        # 验证 version
        self._validate_version(data.get("version"))
        
        # 验证 language
        self._validate_language(data.get("language"))
        
        # 验证 entrypoint
        self._validate_entrypoint(data.get("entrypoint"))
        
        # 验证 signature
        self._validate_signature(data.get("signature"))
        
        # 验证 tests（如果有）
        if "tests" in data:
            self._validate_tests(data.get("tests"))
        
        # 验证 semantics（如果有）
        if "semantics" in data:
            self._validate_semantics(data.get("semantics"))
        
        # 验证 tags（如果有）
        if "tags" in data:
            self._validate_tags(data.get("tags"))
        
        # 验证 quality（如果有）
        if "quality" in data:
            self._validate_quality(data.get("quality"))
        
        return ValidationResult(
            valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
            info=self.info
        )
    
    def _validate_required_fields(self, data: Dict):
        """验证必需字段"""
        missing = self.REQUIRED_FIELDS - set(data.keys())
        if missing:
            self.errors.append(f"Missing required fields: {', '.join(missing)}")
    
    def _validate_spec_version(self, version):
        """验证 spec_version"""
        if not version:
            self.errors.append("spec_version is required")
        elif version != "0.1":
            self.warnings.append(f"Unknown spec_version: {version}, expected '0.1'")
    
    def _validate_id(self, func_id):
        """验证 ID 格式"""
        if not func_id:
            self.errors.append("id is required")
            return
        
        if not isinstance(func_id, str):
            self.errors.append("id must be a string")
            return
        
        # ID 应该是点分格式
        parts = func_id.split(".")
        if len(parts) < 2:
            self.warnings.append(f"id '{func_id}' should use dot notation (e.g., 'domain.category.name')")
        
        # 检查非法字符
        for part in parts:
            if not part.replace("_", "").replace("-", "").isalnum():
                self.warnings.append(f"id part '{part}' contains invalid characters")
    
    def _validate_version(self, version):
        """验证 version"""
        if not version:
            self.errors.append("version is required")
        elif not isinstance(version, str):
            self.errors.append("version must be a string")
        elif not self._is_valid_semver(version):
            self.warnings.append(f"version '{version}' should follow semantic versioning (e.g., '1.0.0')")
    
    def _is_valid_semver(self, version: str) -> bool:
        """检查是否是有效的语义化版本"""
        parts = version.split(".")
        if len(parts) != 3:
            return False
        try:
            for p in parts:
                int(p)
            return True
        except ValueError:
            return False
    
    def _validate_language(self, language):
        """验证 language"""
        if not language:
            self.errors.append("language is required")
            return
        
        if not isinstance(language, dict):
            self.errors.append("language must be an object")
            return
        
        if "name" not in language:
            self.errors.append("language.name is required")
        elif not isinstance(language["name"], str):
            self.errors.append("language.name must be a string")
    
    def _validate_entrypoint(self, entrypoint):
        """验证 entrypoint"""
        if not entrypoint:
            self.errors.append("entrypoint is required")
            return
        
        if not isinstance(entrypoint, dict):
            self.errors.append("entrypoint must be an object")
            return
        
        # 验证 kind
        kind = entrypoint.get("kind")
        if not kind:
            self.errors.append("entrypoint.kind is required")
        elif kind not in self.ENTRYPOINT_KINDS:
            self.errors.append(f"entrypoint.kind must be one of: {', '.join(self.ENTRYPOINT_KINDS)}")
        
        # 验证 symbol
        if not entrypoint.get("symbol"):
            self.errors.append("entrypoint.symbol is required")
        
        # 验证 code（inline 时必须）
        if kind == "inline" and not entrypoint.get("code"):
            self.errors.append("entrypoint.code is required when kind is 'inline'")
        
        # 验证 file（file 时必须）
        if kind == "file" and not entrypoint.get("file"):
            self.errors.append("entrypoint.file is required when kind is 'file'")
    
    def _validate_signature(self, signature):
        """验证 signature"""
        if not signature:
            self.errors.append("signature is required")
            return
        
        if not isinstance(signature, dict):
            self.errors.append("signature must be an object")
            return
        
        # 验证 inputs
        inputs = signature.get("inputs")
        if inputs is None:
            self.warnings.append("signature.inputs is empty (function takes no arguments)")
        elif not isinstance(inputs, dict):
            self.errors.append("signature.inputs must be an object (map of parameter name to schema)")
        else:
            for param_name, param_schema in inputs.items():
                self._validate_parameter(param_name, param_schema, "input")
        
        # 验证 outputs
        outputs = signature.get("outputs")
        if not outputs:
            self.warnings.append("signature.outputs is empty")
        elif not isinstance(outputs, dict):
            self.errors.append("signature.outputs must be an object (map of parameter name to schema)")
        else:
            for param_name, param_schema in outputs.items():
                self._validate_parameter(param_name, param_schema, "output")
    
    def _validate_parameter(self, name: str, schema: Dict, param_type: str):
        """验证参数定义"""
        if not isinstance(schema, dict):
            self.errors.append(f"{param_type} parameter '{name}' must be an object")
            return
        
        if "type" not in schema:
            self.errors.append(f"{param_type} parameter '{name}' missing 'type'")
        
        # 验证 description（建议有）
        if not schema.get("description"):
            self.warnings.append(f"{param_type} parameter '{name}' missing 'description'")
    
    def _validate_tests(self, tests):
        """验证测试定义"""
        if not isinstance(tests, dict):
            self.errors.append("tests must be an object")
            return
        
        framework = tests.get("framework")
        if not framework:
            self.warnings.append("tests.framework not specified, assuming 'builtin'")
        
        cases = tests.get("cases", [])
        if not cases:
            self.warnings.append("tests.cases is empty (no test cases)")
        elif not isinstance(cases, list):
            self.errors.append("tests.cases must be an array")
        else:
            for i, case in enumerate(cases):
                self._validate_test_case(case, i)
    
    def _validate_test_case(self, case: Dict, index: int):
        """验证单个测试用例"""
        if not isinstance(case, dict):
            self.errors.append(f"Test case {index} must be an object")
            return
        
        if "name" not in case:
            self.warnings.append(f"Test case {index} missing 'name'")
        
        if "input" not in case:
            self.errors.append(f"Test case {index} missing 'input'")
        
        if "expect" not in case:
            self.errors.append(f"Test case {index} missing 'expect'")
    
    def _validate_semantics(self, semantics):
        """验证语义声明"""
        if not isinstance(semantics, dict):
            self.errors.append("semantics must be an object")
            return
        
        # 验证 deterministic
        if "deterministic" in semantics:
            if not isinstance(semantics["deterministic"], bool):
                self.errors.append("semantics.deterministic must be a boolean")
        
        # 验证 side_effects
        if "side_effects" in semantics:
            if not isinstance(semantics["side_effects"], list):
                self.errors.append("semantics.side_effects must be an array")
        
        # 验证 security
        if "security" in semantics:
            security = semantics["security"]
            if not isinstance(security, dict):
                self.errors.append("semantics.security must be an object")
            elif "sandbox_required" in security:
                if not isinstance(security["sandbox_required"], bool):
                    self.errors.append("semantics.security.sandbox_required must be a boolean")
    
    def _validate_tags(self, tags):
        """验证标签"""
        if not isinstance(tags, list):
            self.errors.append("tags must be an array")
        else:
            for tag in tags:
                if not isinstance(tag, str):
                    self.warnings.append(f"Tag '{tag}' should be a string")
    
    def _validate_quality(self, quality):
        """验证质量声明"""
        if not isinstance(quality, dict):
            self.errors.append("quality must be an object")
            return
        
        # 验证 coverage
        if "coverage" in quality:
            coverage = quality["coverage"]
            if not isinstance(coverage, (int, float)):
                self.errors.append("quality.coverage must be a number")
            elif not 0 <= coverage <= 1:
                self.warnings.append("quality.coverage should be between 0 and 1")


def validate_file(yaml_path: Path) -> Tuple[bool, ValidationResult]:
    """验证单个 YAML 文件"""
    print(f"\n📄 Validating: {yaml_path}")
    print("-" * 50)
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ YAML parse error: {e}")
        return False, ValidationResult(False, [f"YAML parse error: {e}"], [], [])
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False, ValidationResult(False, [f"Error reading file: {e}"], [], [])
    
    validator = FunctionSpecValidator()
    result = validator.validate(data)
    
    # 打印结果
    if result.valid:
        print("✅ Valid FunctionSpec v0.1")
    else:
        print("❌ Validation failed")
    
    if result.errors:
        print("\n🔴 Errors:")
        for err in result.errors:
            print(f"   - {err}")
    
    if result.warnings:
        print("\n🟡 Warnings:")
        for warn in result.warnings:
            print(f"   - {warn}")
    
    if result.info:
        print("\n🔵 Info:")
        for info in result.info:
            print(f"   - {info}")
    
    return result.valid, result


def validate_all(examples_dir: Path) -> Tuple[int, int]:
    """验证所有函数"""
    print("\n" + "=" * 60)
    print("🔍 FunctionSpec v0.1 批量验证")
    print("=" * 60)
    
    valid_count = 0
    invalid_count = 0
    
    for func_dir in sorted(examples_dir.iterdir()):
        if func_dir.is_dir():
            yaml_path = func_dir / "function.yaml"
            if yaml_path.exists():
                is_valid, _ = validate_file(yaml_path)
                if is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 验证结果: {valid_count} 通过, {invalid_count} 失败")
    print("=" * 60)
    
    return valid_count, invalid_count


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print(f"  {sys.argv[0]} <path/to/function.yaml>")
        print(f"  {sys.argv[0]} --all")
        sys.exit(1)
    
    if sys.argv[1] == "--all":
        # 验证所有示例函数
        script_dir = Path(__file__).parent
        examples_dir = script_dir.parent / "examples"
        
        if not examples_dir.exists():
            print(f"❌ Examples directory not found: {examples_dir}")
            sys.exit(1)
        
        valid, invalid = validate_all(examples_dir)
        
        if invalid > 0:
            sys.exit(1)
    else:
        # 验证单个文件
        yaml_path = Path(sys.argv[1])
        if not yaml_path.exists():
            print(f"❌ File not found: {yaml_path}")
            sys.exit(1)
        
        is_valid, _ = validate_file(yaml_path)
        sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
