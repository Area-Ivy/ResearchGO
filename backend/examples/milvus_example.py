"""
Milvus 向量数据库使用示例
演示如何使用 MilvusService 进行向量存储和检索
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.milvus_service import MilvusService
import random


def generate_random_embedding(dim: int = 768) -> list:
    """生成随机向量（实际使用中应该使用真实的文本嵌入）"""
    return [random.random() for _ in range(dim)]


def main():
    """主函数"""
    print("=" * 60)
    print("Milvus 向量数据库使用示例")
    print("=" * 60)
    
    # 1. 初始化服务
    print("\n1. 初始化 Milvus 服务...")
    milvus = MilvusService(
        host="localhost",
        port="19530",
        collection_name="demo_papers"
    )
    
    # 2. 连接到数据库
    print("2. 连接到 Milvus...")
    if not milvus.connect():
        print("❌ 连接失败！请确保 Milvus 服务已启动")
        return
    print("✅ 连接成功")
    
    # 3. 创建集合
    print("\n3. 创建向量集合...")
    if not milvus.create_collection(dim=768):
        print("❌ 创建集合失败")
        return
    print("✅ 集合创建成功")
    
    # 4. 创建索引
    print("\n4. 创建向量索引...")
    if not milvus.create_index(
        index_type="IVF_FLAT",
        metric_type="L2",
        nlist=128
    ):
        print("❌ 创建索引失败")
        return
    print("✅ 索引创建成功")
    
    # 5. 插入示例数据
    print("\n5. 插入示例向量数据...")
    
    paper_ids = [f"paper_{i:04d}" for i in range(1, 11)]
    embeddings = [generate_random_embedding(768) for _ in range(10)]
    titles = [
        "Deep Learning for Natural Language Processing",
        "Attention Is All You Need",
        "BERT: Pre-training of Deep Bidirectional Transformers",
        "GPT-3: Language Models are Few-Shot Learners",
        "Vision Transformer for Image Recognition",
        "Contrastive Learning of Visual Representations",
        "Self-Supervised Learning: A Survey",
        "Graph Neural Networks: A Review",
        "Reinforcement Learning: An Introduction",
        "Meta-Learning: A Survey"
    ]
    abstracts = [f"这是论文 {i} 的摘要内容..." for i in range(1, 11)]
    sources = ["abstract"] * 10
    
    if not milvus.insert_vectors(
        paper_ids=paper_ids,
        embeddings=embeddings,
        titles=titles,
        abstracts=abstracts,
        sources=sources
    ):
        print("❌ 插入数据失败")
        return
    print(f"✅ 成功插入 {len(paper_ids)} 条数据")
    
    # 6. 获取集合统计信息
    print("\n6. 获取集合统计信息...")
    stats = milvus.get_collection_stats()
    print(f"   集合名称: {stats.get('collection_name')}")
    print(f"   实体数量: {stats.get('num_entities')}")
    print(f"   加载状态: {stats.get('is_loaded')}")
    
    # 7. 搜索相似向量
    print("\n7. 搜索相似向量...")
    query_vector = generate_random_embedding(768)
    results = milvus.search_similar(
        query_vectors=[query_vector],
        top_k=5,
        metric_type="L2"
    )
    
    if results and results[0]:
        print(f"   找到 {len(results[0])} 个相似结果：")
        for i, hit in enumerate(results[0], 1):
            print(f"\n   结果 {i}:")
            print(f"     论文ID: {hit['paper_id']}")
            print(f"     标题: {hit['title']}")
            print(f"     距离: {hit['distance']:.4f}")
    else:
        print("   未找到相似结果")
    
    # 8. 删除指定数据（可选）
    print("\n8. 删除示例数据...")
    choice = input("   是否删除刚才插入的数据？(y/n): ")
    if choice.lower() == 'y':
        if milvus.delete_by_paper_id(paper_ids[:3]):
            print(f"   ✅ 成功删除 3 条数据")
        
        # 再次查看统计信息
        stats = milvus.get_collection_stats()
        print(f"   当前实体数量: {stats.get('num_entities')}")
    
    # 9. 删除集合（可选）
    print("\n9. 清理操作...")
    choice = input("   是否删除整个集合？(y/n): ")
    if choice.lower() == 'y':
        if milvus.drop_collection():
            print("   ✅ 集合已删除")
    
    # 10. 断开连接
    print("\n10. 断开连接...")
    milvus.disconnect()
    print("✅ 已断开连接")
    
    print("\n" + "=" * 60)
    print("示例程序执行完毕！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

