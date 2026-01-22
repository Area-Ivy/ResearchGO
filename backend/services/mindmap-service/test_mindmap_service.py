"""
Mindmap Service 测试脚本
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8007"


async def test_health():
    """测试健康检查"""
    print("\n📋 测试健康检查...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/mindmap/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200


async def test_generate_mindmap(object_name: str):
    """测试生成思维导图"""
    print(f"\n🧠 测试生成思维导图: {object_name}")
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/mindmap/generate",
            json={
                "object_name": object_name,
                "max_depth": 3,
                "language": "zh"
            }
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Message: {data['message']}")
            if data.get('mindmap_data'):
                print(f"Mindmap root topic: {data['mindmap_data'].get('data', {}).get('topic', 'N/A')}")
        else:
            print(f"Error: {response.text}")


async def main():
    print("=" * 60)
    print("🧪 Mindmap Service 测试")
    print("=" * 60)
    
    try:
        # 健康检查
        await test_health()
        
        # 提示用户输入PDF对象名
        print("\n" + "-" * 60)
        object_name = input("请输入 MinIO 中的 PDF 对象名 (例如: 20260122_paper.pdf): ").strip()
        
        if object_name:
            await test_generate_mindmap(object_name)
        else:
            print("跳过思维导图生成测试（未提供对象名）")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

