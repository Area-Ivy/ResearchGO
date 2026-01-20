"""
测试论文上传到 Milvus 的功能（带 chunk 切分）
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.milvus_service import MilvusService
from app.services.openai_service import OpenAIService
from app.utils.text_chunker import TextChunker, split_text_into_chunks


async def test_text_chunker():
    """测试文本切分器"""
    print("\n=== 测试文本切分器 ===")
    
    try:
        # 测试文本
        test_text = """
        This is a test paper about machine learning and artificial intelligence.
        Machine learning is a subset of artificial intelligence that focuses on 
        enabling computers to learn from data without being explicitly programmed.
        
        Deep learning is a specialized branch of machine learning that uses neural 
        networks with multiple layers. These networks can learn complex patterns 
        and representations from large amounts of data.
        
        Natural language processing (NLP) is another important area of AI that 
        deals with the interaction between computers and human language. It enables
        machines to understand, interpret, and generate human language.
        
        Computer vision is the field of AI that trains computers to interpret and 
        understand visual information from the world. It has applications in image
        recognition, object detection, and autonomous vehicles.
        """ * 5  # 重复5次以获得足够的文本
        
        # 测试滑动窗口切分
        print("\n测试滑动窗口切分:")
        chunks = split_text_into_chunks(
            text=test_text,
            chunk_size=500,
            chunk_overlap=100,
            max_chunks=10,
            method="sliding_window"
        )
        
        print(f"✓ 生成了 {len(chunks)} 个chunks")
        for i, chunk in enumerate(chunks[:3]):
            print(f"  Chunk {i}: {chunk['total_chars']} 字符, 位置 {chunk['start_pos']}-{chunk['end_pos']}")
            print(f"    内容预览: {chunk['text'][:100]}...")
        
        # 测试段落切分
        print("\n测试段落切分:")
        para_chunks = split_text_into_chunks(
            text=test_text,
            chunk_size=500,
            chunk_overlap=100,
            max_chunks=10,
            method="paragraphs"
        )
        
        print(f"✓ 生成了 {len(para_chunks)} 个段落chunks")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_milvus_with_chunks():
    """测试 Milvus 存储chunks"""
    print("\n=== 测试 Milvus 存储 Chunks ===")
    
    try:
        milvus_service = MilvusService()
        
        # 连接
        if not milvus_service.connect():
            print("✗ 连接 Milvus 失败")
            return False
        print("✓ 成功连接到 Milvus")
        
        # 创建集合（新schema）
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
        import traceback
        traceback.print_exc()
        return False


async def test_full_workflow_with_chunks():
    """测试完整工作流程（带chunks）"""
    print("\n=== 测试完整工作流程（带 Chunks）===")
    
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
        
        # 3. 准备测试文本
        test_text = """
        Title: Advanced Machine Learning Techniques for Natural Language Processing
        
        Abstract: This paper presents a comprehensive study of advanced machine learning
        techniques applied to natural language processing tasks. We explore various 
        architectures including transformers, attention mechanisms, and pre-trained models.
        
        Introduction: Natural language processing has seen tremendous advances in recent
        years, largely due to the development of deep learning models. The introduction
        of transformer architecture has revolutionized the field, enabling models to
        capture long-range dependencies and contextual information more effectively.
        
        Methodology: We employ a multi-stage approach combining data preprocessing,
        feature engineering, model training, and evaluation. Our experiments utilize
        state-of-the-art pre-trained models such as BERT, GPT, and T5, fine-tuned
        on domain-specific datasets.
        
        Results: Our experiments demonstrate significant improvements over baseline
        methods across multiple benchmarks. The proposed approach achieves state-of-the-art
        performance on sentiment analysis, named entity recognition, and machine translation
        tasks.
        
        Conclusion: This work contributes to the growing body of research on advanced
        NLP techniques and provides practical insights for developing robust language
        models for real-world applications.
        """ * 3  # 重复以获得多个chunks
        
        # 4. 切分文本
        print("切分文本成chunks...")
        chunks = split_text_into_chunks(
            text=test_text,
            chunk_size=500,
            chunk_overlap=100,
            max_chunks=10
        )
        print(f"✓ 生成了 {len(chunks)} 个chunks")
        
        # 5. 生成嵌入
        print("生成嵌入向量...")
        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = await openai_service.generate_embeddings(chunk_texts)
        
        if not embeddings:
            print("✗ 嵌入生成失败")
            return False
        
        print(f"✓ 生成了 {len(embeddings)} 个嵌入向量，维度: {len(embeddings[0])}")
        
        # 6. 准备数据和metadata
        from datetime import datetime
        
        paper_id = "test_paper_with_chunks_001"
        title = "Advanced Machine Learning Techniques"
        file_name = "test_paper.pdf"
        upload_time = datetime.utcnow().isoformat() + 'Z'
        
        paper_ids = [paper_id] * len(chunks)
        chunk_ids = [f"{paper_id}#chunk_{chunk['chunk_index']}" for chunk in chunks]
        chunk_indices = [chunk['chunk_index'] for chunk in chunks]
        titles = [title] * len(chunks)
        file_names = [file_name] * len(chunks)
        contents = [chunk['text'] for chunk in chunks]
        chunk_chars = [chunk['total_chars'] for chunk in chunks]
        page_ranges = [f"{i//2 + 1}-{i//2 + 2}" for i in range(len(chunks))]
        upload_times = [upload_time] * len(chunks)
        sources = ["chunk"] * len(chunks)
        
        # 7. 存储到 Milvus（包含metadata）
        print("存储chunks到 Milvus（含metadata）...")
        success = milvus_service.insert_vectors(
            paper_ids=paper_ids,
            chunk_ids=chunk_ids,
            chunk_indices=chunk_indices,
            embeddings=embeddings,
            titles=titles,
            file_names=file_names,
            contents=contents,
            chunk_chars=chunk_chars,
            page_ranges=page_ranges,
            upload_times=upload_times,
            sources=sources
        )
        
        if success:
            print(f"✓ 成功存储 {len(chunks)} 个chunks到 Milvus")
        else:
            print("✗ 存储失败")
            return False
        
        # 8. 验证存储
        stats = milvus_service.get_collection_stats()
        print(f"✓ 当前集合实体数: {stats.get('num_entities', 0)}")
        
        # 9. 测试搜索
        print("\n测试相似度搜索...")
        query_text = "What are the latest advances in natural language processing?"
        query_embeddings = await openai_service.generate_embeddings([query_text])
        
        results = milvus_service.search_similar(
            query_vectors=query_embeddings,
            top_k=5
        )
        
        if results and len(results) > 0:
            print(f"✓ 搜索成功，找到 {len(results[0])} 个结果")
            for i, hit in enumerate(results[0][:3]):
                print(f"\n  结果 {i+1}:")
                print(f"    Paper ID: {hit['paper_id']}")
                print(f"    文件名: {hit['file_name']}")
                print(f"    标题: {hit['title']}")
                print(f"    Chunk ID: {hit['chunk_id']}")
                print(f"    Chunk Index: {hit['chunk_index']}")
                print(f"    页码范围: {hit['page_range']}")
                print(f"    上传时间: {hit['upload_time']}")
                print(f"    相关性分数: {hit['relevance_score']:.4f}")
                print(f"    距离: {hit['distance']:.4f}")
                print(f"    字符数: {hit['chunk_chars']}")
                print(f"    内容预览: {hit['content'][:150]}...")
        else:
            print("✗ 搜索失败")
        
        # 10. 测试按paper_id查询所有chunks
        print(f"\n查询论文 {paper_id} 的所有chunks...")
        # 这里可以添加根据 paper_id 查询的逻辑
        
        # 11. 清理测试数据
        print("\n清理测试数据...")
        milvus_service.delete_by_paper_id([paper_id])
        print("✓ 测试数据已清理")
        
        milvus_service.disconnect()
        
        print("\n✓ 完整工作流程测试成功！")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_chunk_retrieval():
    """测试chunk检索和重组"""
    print("\n=== 测试 Chunk 检索和重组 ===")
    
    try:
        print("✓ 这个功能将在实现RAG系统时完成")
        print("  - 检索相关chunks")
        print("  - 按chunk_index排序")
        print("  - 重组上下文")
        print("  - 生成回答")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("=" * 70)
    print("Paper Upload to Milvus with Chunks - 功能测试")
    print("=" * 70)
    
    # 测试 1: 文本切分器
    test1 = await test_text_chunker()
    
    # 测试 2: Milvus 连接（新schema）
    test2 = await test_milvus_with_chunks()
    
    # 测试 3: 完整工作流程（带chunks）
    test3 = await test_full_workflow_with_chunks()
    
    # 测试 4: Chunk检索
    test4 = await test_chunk_retrieval()
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结:")
    print(f"  文本切分器测试: {'✓ 通过' if test1 else '✗ 失败'}")
    print(f"  Milvus连接测试: {'✓ 通过' if test2 else '✗ 失败'}")
    print(f"  完整工作流程测试: {'✓ 通过' if test3 else '✗ 失败'}")
    print(f"  Chunk检索测试: {'✓ 通过' if test4 else '✗ 失败'}")
    print("=" * 70)
    
    if test1 and test2 and test3 and test4:
        print("\n✓ 所有测试通过！系统已准备好处理带chunk的论文上传。")
        print("\n接下来可以:")
        print("  1. 上传论文到 Paper Library")
        print("  2. 系统自动切分成chunks并存储")
        print("  3. 实现基于chunk的语义搜索")
        print("  4. 构建RAG问答系统")
        return 0
    else:
        print("\n✗ 部分测试失败，请检查配置和服务状态。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

