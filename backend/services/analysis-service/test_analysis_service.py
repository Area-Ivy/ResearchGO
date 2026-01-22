"""
Analysis Service 测试脚本
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8008"


async def test_health():
    """测试健康检查"""
    print("\n📋 测试健康检查...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/analysis/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200


async def test_generate_analysis(object_name: str):
    """测试生成论文分析"""
    print(f"\n📊 测试生成论文分析: {object_name}")
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/analysis/generate",
            json={
                "object_name": object_name,
                "language": "zh"
            }
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Message: {data['message']}")
            if data.get('analysis'):
                print(f"\n论文标题: {data['analysis'].get('title', 'N/A')}")
                print(f"摘要: {data['analysis'].get('abstract', 'N/A')[:200]}...")
        else:
            print(f"Error: {response.text}")


async def main():
    print("=" * 60)
    print("🧪 Analysis Service 测试")
    print("=" * 60)
    
    try:
        # 健康检查
        await test_health()
        
        # 提示用户输入PDF对象名
        print("\n" + "-" * 60)
        object_name = input("请输入 MinIO 中的 PDF 对象名 (例如: 20260122_paper.pdf): ").strip()
        
        if object_name:
            await test_generate_analysis(object_name)
        else:
            print("跳过论文分析测试（未提供对象名）")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

