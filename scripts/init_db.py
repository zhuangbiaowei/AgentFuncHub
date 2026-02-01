"""
初始化脚本：加载示例函数到数据库
"""

import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src" / "server"))

import json

# 数据目录
DATA_DIR = project_root / "data"
DATA_DIR.mkdir(exist_ok=True)
FUNCTIONS_FILE = DATA_DIR / "functions.json"

# 内存存储
functions_db = {}


def load_example_functions():
    """加载 examples 目录下的所有函数"""
    examples_dir = project_root / "examples"
    
    loaded = 0
    for func_dir in examples_dir.iterdir():
        if func_dir.is_dir():
            manifest_file = func_dir / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    
                    func_id = manifest.get("function_id")
                    if func_id:
                        functions_db[func_id] = manifest
                        loaded += 1
                        print(f"✅ Loaded: {manifest.get('name')} ({func_id})")
                except Exception as e:
                    print(f"❌ Failed to load {func_dir.name}: {e}")
    
    return loaded


def save_functions():
    """保存函数数据到文件"""
    with open(FUNCTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(functions_db, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print("🚀 Initializing AgentFuncHub database...\n")
    
    count = load_example_functions()
    
    if count > 0:
        save_functions()
        print(f"\n✨ Successfully loaded {count} functions")
        print(f"💾 Data saved to: {FUNCTIONS_FILE}")
    else:
        print("\n⚠️ No functions loaded")
