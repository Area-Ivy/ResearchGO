"""
Milvus 快速入门示例
演示最基本的 Milvus 操作流程
"""

from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import random


def main():
    """Milvus 快速入门"""
    
    print("=" * 60)
    print("Milvus 向量数据库 - 快速入门")
    print("=" * 60)
    
    # 步骤 1: 连接到 Milvus
    print("\n📡 步骤 1: 连接到 Milvus...")
    try:
        connections.connect(
            alias="default",
            host="localhost",
            port="19530"
        )
        print("✅ 连接成功！")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n💡 提示: 请确保 Milvus 服务已启动")
        print("   运行命令: docker-compose up -d")
        return
    
    # 步骤 2: 创建集合（类似关系型数据库的表）
    print("\n📦 步骤 2: 创建集合...")
    
    collection_name = "quick_start_demo"
    
    # 如果集合已存在，先删除
    if utility.has_collection(collection_name):
        utility.drop_collection(collection_name)
        print(f"   已删除旧集合: {collection_name}")
    
    # 定义集合的字段（schema）
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="text_id", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),  # 128维向量
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=500),
    ]
    
    schema = CollectionSchema(fields, description="快速入门示例集合")
    collection = Collection(name=collection_name, schema=schema)
    print(f"✅ 集合创建成功: {collection_name}")
    
    # 步骤 3: 创建索引（加速搜索）
    print("\n🔍 步骤 3: 创建向量索引...")
    
    index_params = {
        "metric_type": "L2",       # 使用欧氏距离
        "index_type": "IVF_FLAT",  # 索引类型
        "params": {"nlist": 128}    # 聚类中心数
    }
    
    collection.create_index(
        field_name="embedding",
        index_params=index_params
    )
    print("✅ 索引创建成功！")
    
    # 步骤 4: 插入数据
    print("\n💾 步骤 4: 插入向量数据...")
    
    # 模拟一些文本和对应的向量
    # 实际应用中，这些向量应该由文本嵌入模型生成
    texts = [
        "机器学习是人工智能的一个分支",
        "深度学习使用多层神经网络",
        "自然语言处理理解人类语言",
        "计算机视觉处理图像和视频",
        "强化学习通过试错来学习",
    ]
    
    # 生成随机向量（实际应用中应使用真实的嵌入向量）
    def generate_vector(dim=128):
        return [random.random() for _ in range(dim)]
    
    # 准备数据
    data = [
        [f"text_{i}" for i in range(len(texts))],  # text_id
        [generate_vector() for _ in range(len(texts))],  # embedding
        texts,  # text
    ]
    
    # 插入数据
    insert_result = collection.insert(data)
    collection.flush()  # 确保数据写入磁盘
    
    print(f"✅ 成功插入 {len(texts)} 条数据")
    print(f"   插入的 ID: {insert_result.primary_keys[:3]}... (共{len(insert_result.primary_keys)}个)")
    
    # 步骤 5: 加载集合到内存
    print("\n⚡ 步骤 5: 加载集合到内存...")
    collection.load()
    print("✅ 集合已加载，可以开始搜索！")
    
    # 步骤 6: 向量搜索
    print("\n🔎 步骤 6: 执行相似度搜索...")
    
    # 生成一个查询向量
    query_vector = [generate_vector()]
    
    # 搜索参数
    search_params = {
        "metric_type": "L2",
        "params": {"nprobe": 10}
    }
    
    # 执行搜索
    results = collection.search(
        data=query_vector,
        anns_field="embedding",
        param=search_params,
        limit=3,  # 返回最相似的3个结果
        output_fields=["text_id", "text"]
    )
    
    # 显示搜索结果
    print("\n📊 搜索结果（最相似的 3 条）：")
    print("-" * 60)
    
    for i, hits in enumerate(results):
        for rank, hit in enumerate(hits, 1):
            print(f"\n排名 {rank}:")
            print(f"  ID: {hit.entity.get('text_id')}")
            print(f"  文本: {hit.entity.get('text')}")
            print(f"  距离: {hit.distance:.4f} (越小越相似)")
    
    print("\n" + "-" * 60)
    
    # 步骤 7: 查询数据（不涉及向量搜索）
    print("\n📋 步骤 7: 条件查询...")
    
    expr = "text_id == 'text_0'"
    query_results = collection.query(
        expr=expr,
        output_fields=["text_id", "text"]
    )
    
    if query_results:
        print(f"✅ 查询到 {len(query_results)} 条数据：")
        for result in query_results:
            print(f"   {result}")
    
    # 步骤 8: 获取统计信息
    print("\n📈 步骤 8: 获取集合统计信息...")
    
    collection.flush()
    num_entities = collection.num_entities
    
    print(f"✅ 集合名称: {collection_name}")
    print(f"✅ 数据总数: {num_entities}")
    
    # 步骤 9: 清理（可选）
    print("\n🧹 步骤 9: 清理资源...")
    
    choice = input("\n是否删除示例集合？(y/n): ")
    if choice.lower() == 'y':
        collection.release()  # 释放内存
        utility.drop_collection(collection_name)
        print(f"✅ 集合 '{collection_name}' 已删除")
    else:
        print(f"✅ 集合 '{collection_name}' 保留")
        print(f"   可以在 Attu (http://localhost:9002) 中查看")
    
    # 断开连接
    connections.disconnect("default")
    print("\n✅ 已断开连接")
    
    # 总结
    print("\n" + "=" * 60)
    print("🎉 快速入门完成！")
    print("=" * 60)
    print("\n你已经学会了：")
    print("  1. ✅ 连接到 Milvus")
    print("  2. ✅ 创建集合和定义 schema")
    print("  3. ✅ 创建向量索引")
    print("  4. ✅ 插入向量数据")
    print("  5. ✅ 执行相似度搜索")
    print("  6. ✅ 条件查询")
    print("  7. ✅ 获取统计信息")
    print("\n📚 下一步学习：")
    print("  - 查看 docs/MILVUS_USAGE.md 了解更多高级用法")
    print("  - 运行 backend/examples/milvus_example.py 查看完整示例")
    print("  - 访问 http://localhost:9002 使用 Attu 可视化管理")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

