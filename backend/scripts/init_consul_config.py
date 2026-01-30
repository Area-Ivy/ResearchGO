"""
初始化 Consul KV 配置
运行此脚本将默认配置写入 Consul KV Store
"""
import asyncio
import os
import sys
import httpx

# Windows console encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Consul 地址
CONSUL_URL = os.getenv("CONSUL_URL", "http://localhost:8500")

# 默认配置
DEFAULT_CONFIGS = {
    # OpenAI 配置
    "config/openai/model": "gpt-4o",
    "config/openai/embedding_model": "text-embedding-3-small",
    "config/openai/max_tokens": "4096",
    "config/openai/temperature": "0.7",
    
    # Agent 配置
    "config/agent/max_iterations": "10",
    "config/agent/timeout": "120",
    "config/agent/enable_tools": "true",
    
    # Memory 配置
    "config/memory/sliding_window_size": "10",
    "config/memory/max_context_tokens": "4000",
    "config/memory/enable_summary": "true",
    "config/memory/summary_threshold": "20",
    "config/memory/enable_semantic": "true",
    "config/memory/semantic_top_k": "5",
    
    # RAG 配置
    "config/rag/chunk_size": "1000",
    "config/rag/chunk_overlap": "200",
    "config/rag/top_k": "5",
    "config/rag/enable_reranker": "false",
    "config/rag/enable_hybrid_search": "true",
    "config/rag/enable_query_translation": "true",
    
    # 服务配置
    "config/services/auth/port": "8001",
    "config/services/conversation/port": "8002",
    "config/services/paper-storage/port": "8003",
    "config/services/vector-search/port": "8004",
    "config/services/literature-search/port": "8005",
    "config/services/mindmap/port": "8007",
    "config/services/analysis/port": "8008",
    
    # 熔断器配置 - 默认配置
    "config/circuit-breaker/default/fail_threshold": "5",
    "config/circuit-breaker/default/reset_timeout": "30",
    "config/circuit-breaker/default/half_open_max_calls": "3",
    "config/circuit-breaker/default/success_threshold": "2",
    
    # 熔断器配置 - 外部API依赖工具（更敏感）
    "config/circuit-breaker/search_literature/fail_threshold": "3",
    "config/circuit-breaker/search_literature/reset_timeout": "60",
    "config/circuit-breaker/get_work_detail/fail_threshold": "3",
    "config/circuit-breaker/get_work_detail/reset_timeout": "60",
    "config/circuit-breaker/get_related_works/fail_threshold": "3",
    "config/circuit-breaker/get_related_works/reset_timeout": "60",
    
    # 熔断器配置 - 内部服务工具
    "config/circuit-breaker/semantic_search/fail_threshold": "5",
    "config/circuit-breaker/semantic_search/reset_timeout": "30",
    "config/circuit-breaker/analyze_paper/fail_threshold": "5",
    "config/circuit-breaker/analyze_paper/reset_timeout": "45",
    "config/circuit-breaker/generate_mindmap/fail_threshold": "5",
    "config/circuit-breaker/generate_mindmap/reset_timeout": "45",
}


async def set_config(key: str, value: str) -> bool:
    """设置单个配置"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.put(
                f"{CONSUL_URL}/v1/kv/{key}",
                content=value.encode('utf-8')
            )
            return response.status_code == 200
    except Exception as e:
        print(f"  ❌ 设置失败 ({key}): {e}")
        return False


async def get_config(key: str) -> str:
    """获取配置"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{CONSUL_URL}/v1/kv/{key}",
                params={"raw": "true"}
            )
            if response.status_code == 200:
                return response.text
            return None
    except Exception:
        return None


async def init_configs(force: bool = False):
    """初始化所有配置"""
    print(f"🔧 初始化 Consul KV 配置...")
    print(f"   Consul URL: {CONSUL_URL}")
    print()
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for key, value in DEFAULT_CONFIGS.items():
        # 检查是否已存在
        existing = await get_config(key)
        
        if existing is not None and not force:
            print(f"  ⏭️  {key} = {existing} (已存在，跳过)")
            skip_count += 1
            continue
        
        if await set_config(key, value):
            print(f"  ✅ {key} = {value}")
            success_count += 1
        else:
            fail_count += 1
    
    print()
    print(f"📊 结果统计:")
    print(f"   ✅ 成功: {success_count}")
    print(f"   ⏭️  跳过: {skip_count}")
    print(f"   ❌ 失败: {fail_count}")
    
    return fail_count == 0


async def list_all_configs():
    """列出所有配置"""
    print(f"📋 当前 Consul KV 配置:")
    print(f"   Consul URL: {CONSUL_URL}")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{CONSUL_URL}/v1/kv/config/",
                params={"recurse": "true"}
            )
            
            if response.status_code == 200:
                import base64
                data = response.json()
                for item in data:
                    key = item.get("Key", "")
                    value_b64 = item.get("Value")
                    if value_b64:
                        value = base64.b64decode(value_b64).decode('utf-8')
                        print(f"  {key} = {value}")
            elif response.status_code == 404:
                print("  (无配置)")
            else:
                print(f"  ❌ 获取失败: {response.status_code}")
                
    except Exception as e:
        print(f"  ❌ 错误: {e}")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Consul KV 配置管理")
    parser.add_argument("command", choices=["init", "list", "force-init"],
                       help="命令: init(初始化), list(列出), force-init(强制覆盖)")
    args = parser.parse_args()
    
    if args.command == "init":
        await init_configs(force=False)
    elif args.command == "force-init":
        await init_configs(force=True)
    elif args.command == "list":
        await list_all_configs()


if __name__ == "__main__":
    asyncio.run(main())

