"""
测试论文上传到 Milvus 的功能
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.milvus_service import MilvusService
from app.services.openai_service import OpenAIService


async def test_milvus_connection():
    """测试 Milvus 连接"""
    print("\n=== 测试 Milvus 连接 ===")
    
    try:
        milvus_service = MilvusService()
        
        # 连接
        if milvus_service.connect():
            print("✓ 成功连接到 Milvus")
        else:
            print("✗ 连接 Milvus 失败")
            return False
        
        # 创建集合
        if milvus_service.create_collection(dim=1536):
            print("✓ 集合创建/验证成功")
        else:
            print("✗ 集合创建失败")
            return False
        
        # 创建索引
        if milvus_service.create_index():
            print("✓ 索引创建成功")
        else:
            print("✗ 索引创建失败")
            return False
        
        # 获取统计信息
        stats = milvus_service.get_collection_stats()
        print(f"✓ 集合统计信息: {stats}")
        
        milvus_service.disconnect()
        print("✓ 已断开 Milvus 连接")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


async def test_openai_embeddings():
    """测试 OpenAI 嵌入生成"""
    print("\n=== 测试 OpenAI 嵌入生成 ===")
    
    try:
        openai_service = OpenAIService()
        print("✓ OpenAI 服务初始化成功")
        
        # 测试生成嵌入
        test_texts = [
            "This is a test paper about machine learning and artificial intelligence.",
            "这是一篇关于深度学习的测试论文。"
        ]
        
        embeddings = await openai_service.generate_embeddings(test_texts)
        
        if embeddings and len(embeddings) == 2:
            print(f"✓ 成功生成 {len(embeddings)} 个嵌入向量")
            print(f"  - 向量维度: {len(embeddings[0])}")
            print(f"  - 前5个值: {embeddings[0][:5]}")
            return True
        else:
            print("✗ 嵌入生成失败")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


async def test_full_workflow():
    """测试完整工作流程"""
    print("\n=== 测试完整工作流程 ===")
    
    try:
        # 1. 初始化服务
        milvus_service = MilvusService()
        openai_service = OpenAIService()
        
        # 2. 连接 Milvus
        if not milvus_service.connect():
            print("✗ 连接 Milvus 失败")
            return False
        
        milvus_service.create_collection(dim=1536)
        milvus_service.create_index()
        
        # 3. 准备测试数据
        test_data = {
            "paper_id": "test_paper_001",
            "title": "Test Paper: Machine Learning Applications",
            "abstract": "This is a test abstract about machine learning applications in various domains.",
            "text": "This is a test paper content. It discusses various aspects of machine learning..."
        }
        
        # 4. 生成嵌入
        print("生成嵌入向量...")
        embeddings = await openai_service.generate_embeddings([test_data["text"]])
        
        if not embeddings:
            print("✗ 嵌入生成失败")
            return False
        
        print(f"✓ 生成嵌入成功，维度: {len(embeddings[0])}")
        
        # 5. 存储到 Milvus
        print("存储到 Milvus...")
        success = milvus_service.insert_vectors(
            paper_ids=[test_data["paper_id"]],
            embeddings=embeddings,
            titles=[test_data["title"]],
            abstracts=[test_data["abstract"]],
            sources=["full_text"]
        )
        
        if success:
            print("✓ 成功存储到 Milvus")
        else:
            print("✗ 存储失败")
            return False
        
        # 6. 验证存储
        stats = milvus_service.get_collection_stats()
        print(f"✓ 当前集合实体数: {stats.get('num_entities', 0)}")
        
        # 7. 测试搜索
        print("测试相似度搜索...")
        query_text = "machine learning applications"
        query_embeddings = await openai_service.generate_embeddings([query_text])
        
        results = milvus_service.search_similar(
            query_vectors=query_embeddings,
            top_k=5
        )
        
        if results and len(results) > 0:
            print(f"✓ 搜索成功，找到 {len(results[0])} 个结果")
            for i, hit in enumerate(results[0][:3]):
                print(f"  {i+1}. 标题: {hit['title']}")
                print(f"     距离: {hit['distance']:.4f}")
        else:
            print("✗ 搜索失败")
        
        # 8. 清理测试数据
        print("清理测试数据...")
        milvus_service.delete_by_paper_id([test_data["paper_id"]])
        print("✓ 测试数据已清理")
        
        milvus_service.disconnect()
        
        print("\n✓ 完整工作流程测试成功！")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("Paper Upload to Milvus - 功能测试")
    print("=" * 60)
    
    # 测试 1: Milvus 连接
    test1 = await test_milvus_connection()
    
    # 测试 2: OpenAI 嵌入
    test2 = await test_openai_embeddings()
    
    # 测试 3: 完整工作流程
    test3 = await test_full_workflow()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"  Milvus 连接测试: {'✓ 通过' if test1 else '✗ 失败'}")
    print(f"  OpenAI 嵌入测试: {'✓ 通过' if test2 else '✗ 失败'}")
    print(f"  完整工作流程测试: {'✓ 通过' if test3 else '✗ 失败'}")
    print("=" * 60)
    
    if test1 and test2 and test3:
        print("\n✓ 所有测试通过！系统已准备好处理论文上传。")
        return 0
    else:
        print("\n✗ 部分测试失败，请检查配置和服务状态。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

