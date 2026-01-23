"""
Agent Service Test Script
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8009"


async def test_health():
    """测试健康检查"""
    print("\n" + "=" * 60)
    print("测试 1: 健康检查")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/agent/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200


async def test_list_tools():
    """测试获取工具列表"""
    print("\n" + "=" * 60)
    print("测试 2: 获取工具列表")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/agent/tools")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"工具数量: {len(data['tools'])}")
        for tool in data['tools']:
            print(f"  - {tool['name']}: {tool['description'][:50]}...")
        assert response.status_code == 200


async def test_execute_tool():
    """测试直接执行工具"""
    print("\n" + "=" * 60)
    print("测试 3: 直接执行工具 (search_literature)")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/agent/tools/search_literature/execute",
            json={"query": "transformer attention", "limit": 3}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Success: {data.get('success')}")
        if data.get('success'):
            results = data.get('data', {}).get('results', [])
            print(f"找到 {len(results)} 篇论文:")
            for r in results[:3]:
                print(f"  - {r.get('title', 'N/A')[:60]}...")
        else:
            print(f"Error: {data.get('error')}")


async def test_chat_non_stream():
    """测试非流式对话"""
    print("\n" + "=" * 60)
    print("测试 4: 非流式对话")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/agent/chat",
            json={
                "message": "帮我找一篇关于 BERT 的论文",
                "stream": False
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"回答: {data.get('message', '')[:200]}...")
            print(f"思考过程: {data.get('thoughts', [])}")
        else:
            print(f"Error: {response.text}")


async def test_chat_stream():
    """测试流式对话"""
    print("\n" + "=" * 60)
    print("测试 5: 流式对话")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/agent/chat",
            json={
                "message": "搜索一下 GPT-4 相关的论文",
                "stream": True
            }
        ) as response:
            print(f"Status: {response.status_code}")
            print("接收事件流:")
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    event_type = line.replace("event:", "").strip()
                    print(f"\n📌 Event: {event_type}")
                elif line.startswith("data:"):
                    data = line.replace("data:", "").strip()
                    if data:
                        try:
                            parsed = json.loads(data)
                            if isinstance(parsed, str):
                                print(f"   {parsed[:100]}...")
                            else:
                                print(f"   {json.dumps(parsed, ensure_ascii=False)[:100]}...")
                        except:
                            print(f"   {data[:100]}...")


async def main():
    """运行所有测试"""
    print("\n" + "🤖 Agent Service 测试" + "\n")
    
    try:
        await test_health()
        await test_list_tools()
        await test_execute_tool()
        await test_chat_non_stream()
        await test_chat_stream()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

