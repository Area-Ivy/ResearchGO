"""
Literature Search Service 测试脚本
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8005"


async def test_health():
    """测试健康检查"""
    print("\n📋 测试健康检查...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/literature/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200


async def test_search():
    """测试文献搜索"""
    print("\n🔍 测试文献搜索...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/literature/search",
            json={
                "query": "machine learning",
                "page": 1,
                "per_page": 5,
                "sort": "cited_by_count"
            }
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total results: {data['total']}")
        print(f"Results on this page: {len(data['results'])}")
        
        if data['results']:
            first_work = data['results'][0]
            print(f"\n第一篇论文:")
            print(f"  - ID: {first_work['id']}")
            print(f"  - Title: {first_work['title'][:80]}...")
            print(f"  - Year: {first_work['publication_year']}")
            print(f"  - Citations: {first_work['cited_by_count']}")
            return first_work['id']
        return None


async def test_work_detail(work_id: str):
    """测试获取论文详情"""
    print(f"\n📄 测试获取论文详情: {work_id}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Extract just the ID part
        if work_id.startswith("http"):
            work_id = work_id.split("/")[-1]
        
        response = await client.get(f"{BASE_URL}/api/literature/work/{work_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Title: {data['title']}")
            print(f"Abstract: {data['abstract'][:200] if data.get('abstract') else 'N/A'}...")
            print(f"Authors: {', '.join([a['name'] for a in data['authors'][:3]])}")


async def test_related_works(work_id: str):
    """测试获取相关论文"""
    print(f"\n🔗 测试获取相关论文: {work_id}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        if work_id.startswith("http"):
            work_id = work_id.split("/")[-1]
        
        response = await client.get(f"{BASE_URL}/api/literature/related/{work_id}?limit=3")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"找到 {len(data)} 篇相关论文:")
            for i, work in enumerate(data[:3]):
                print(f"  {i+1}. {work['title'][:60]}... (Citations: {work['cited_by_count']})")


async def test_search_with_filters():
    """测试带过滤器的搜索"""
    print("\n🎯 测试带过滤器的搜索...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/literature/search",
            json={
                "query": "deep learning",
                "page": 1,
                "per_page": 5,
                "sort": "publication_date",
                "filters": {
                    "publication_year_start": 2020,
                    "publication_year_end": 2024,
                    "min_cited_by_count": 100,
                    "open_access_only": True
                }
            }
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total results: {data['total']}")
        
        if data['results']:
            print("\n符合条件的论文:")
            for i, work in enumerate(data['results'][:3]):
                oa_status = work.get('open_access', {}).get('is_oa', False)
                print(f"  {i+1}. [{work['publication_year']}] {work['title'][:50]}... (OA: {oa_status})")


async def test_export():
    """测试引用导出"""
    print("\n📤 测试引用导出 (BibTeX)...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 先搜索获取一些work_ids
        search_response = await client.post(
            f"{BASE_URL}/api/literature/search",
            json={"query": "transformer", "per_page": 2}
        )
        works = search_response.json()['results']
        work_ids = [w['id'] for w in works]
        
        # 导出BibTeX
        response = await client.post(
            f"{BASE_URL}/api/literature/export",
            json={
                "work_ids": work_ids,
                "format": "bibtex"
            }
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Format: {data['format']}")
            print(f"Content preview:\n{data['content'][:500]}...")


async def main():
    print("=" * 60)
    print("🧪 Literature Search Service 测试")
    print("=" * 60)
    
    try:
        # 基础测试
        await test_health()
        
        # 搜索测试
        work_id = await test_search()
        
        if work_id:
            # 详情测试
            await test_work_detail(work_id)
            
            # 相关论文测试
            await test_related_works(work_id)
        
        # 过滤器测试
        await test_search_with_filters()
        
        # 导出测试
        await test_export()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

