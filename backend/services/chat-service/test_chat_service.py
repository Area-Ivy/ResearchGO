"""
Chat Service 测试脚本
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8006"


async def test_health():
    """测试健康检查"""
    print("\n📋 测试健康检查...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/chat/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200


async def test_chat_non_streaming():
    """测试非流式聊天"""
    print("\n💬 测试非流式聊天...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/chat/message",
            json={
                "message": "Hello! What is 2 + 2?",
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 100
            }
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data['message'][:200]}...")
        else:
            print(f"Error: {response.text}")


async def test_chat_streaming():
    """测试流式聊天"""
    print("\n🌊 测试流式聊天...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/chat/message",
            json={
                "message": "Tell me a very short joke.",
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 200
            }
        ) as response:
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("Response (streaming): ", end="", flush=True)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            if "content" in data:
                                print(data["content"], end="", flush=True)
                            elif "status" in data and data["status"] == "complete":
                                print("\n[Stream Complete]")
                        except json.JSONDecodeError:
                            pass
            else:
                print(f"Error: {await response.aread()}")


async def test_chat_with_history():
    """测试带历史记录的聊天"""
    print("\n📚 测试带历史记录的聊天...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/chat/message",
            json={
                "message": "What did I just ask you?",
                "conversation_history": [
                    {"role": "user", "content": "My name is Alice."},
                    {"role": "assistant", "content": "Nice to meet you, Alice!"},
                    {"role": "user", "content": "What is 2 + 2?"},
                    {"role": "assistant", "content": "2 + 2 equals 4."}
                ],
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 200
            }
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data['message']}")
        else:
            print(f"Error: {response.text}")


async def main():
    print("=" * 60)
    print("🧪 Chat Service 测试")
    print("=" * 60)
    
    try:
        # 基础测试
        await test_health()
        
        # 非流式聊天测试
        await test_chat_non_streaming()
        
        # 流式聊天测试
        await test_chat_streaming()
        
        # 带历史记录测试
        await test_chat_with_history()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

