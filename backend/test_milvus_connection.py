"""
快速测试 Milvus 连接和基本功能
"""

from pymilvus import connections, utility
import sys

def test_connection():
    """测试 Milvus 连接"""
    print("=" * 60)
    print("测试 Milvus 连接")
    print("=" * 60)
    
    try:
        # 连接到 Milvus
        print("\n1. 连接到 Milvus...")
        connections.connect(
            alias="default",
            host="localhost",
            port="19530"
        )
        print("✅ 连接成功!")
        
        # 检查版本
        print(f"\n2. 检查服务器信息...")
        try:
            collections = utility.list_collections()
            print(f"✅ 当前集合数: {len(collections)}")
            if collections:
                print(f"   集合列表: {', '.join(collections)}")
            else:
                print("   (暂无集合)")
        except Exception as e:
            print(f"⚠️  获取集合列表时出错: {e}")
        
        # 断开连接
        print("\n3. 断开连接...")
        connections.disconnect("default")
        print("✅ 已断开连接")
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！Milvus 工作正常！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        print("\n💡 提示:")
        print("   1. 确保 Milvus 服务已启动: docker-compose ps")
        print("   2. 检查服务状态: docker-compose logs milvus")
        print("   3. 重启服务: docker-compose restart milvus")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

