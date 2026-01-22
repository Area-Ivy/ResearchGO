"""
数据迁移脚本：将MinIO中已存在的论文数据导入到MySQL数据库

运行此脚本将：
1. 从MinIO读取所有已存在的PDF文件
2. 为每个文件在MySQL中创建元数据记录
3. user_id 默认设置为1（管理员），可以根据需要修改
"""
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加app目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
load_dotenv()

from app.database import SessionLocal, engine, Base
from app.models.paper import Paper
from app.utils.minio_client import get_minio_client, ensure_bucket_exists, MINIO_BUCKET
from minio.error import S3Error

def migrate_papers(default_user_id: int = 1):
    """
    迁移MinIO中的论文到MySQL
    
    Args:
        default_user_id: 默认的用户ID（因为旧数据没有user_id信息）
    """
    print("=" * 60)
    print("📦 论文数据迁移脚本")
    print("=" * 60)
    
    # 1. 创建数据库表
    print("\n1️⃣ 创建数据库表...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功")
    except Exception as e:
        print(f"❌ 创建数据库表失败: {e}")
        return
    
    # 2. 连接MinIO
    print("\n2️⃣ 连接MinIO...")
    try:
        minio_client = get_minio_client()
        ensure_bucket_exists(minio_client, MINIO_BUCKET)
        print("✅ MinIO连接成功")
    except Exception as e:
        print(f"❌ MinIO连接失败: {e}")
        print("   请确保MinIO服务正在运行，并检查.env配置")
        return
    
    # 3. 获取MinIO中的所有文件
    print("\n3️⃣ 获取MinIO中的文件列表...")
    try:
        objects_iter = minio_client.list_objects(MINIO_BUCKET, recursive=True)
        objects = []
        
        for obj in objects_iter:
            # 获取对象的元数据
            try:
                stat = minio_client.stat_object(MINIO_BUCKET, obj.object_name)
                objects.append({
                    'object_name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'content_type': stat.content_type if stat else 'application/pdf',
                    'metadata': stat.metadata if stat else {}
                })
            except Exception as e:
                logger.warning(f"Failed to get metadata for {obj.object_name}: {e}")
                objects.append({
                    'object_name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'content_type': 'application/pdf',
                    'metadata': {}
                })
        
        print(f"✅ 找到 {len(objects)} 个文件")
        
        if not objects:
            print("⚠️  MinIO中没有文件，无需迁移")
            return
            
    except Exception as e:
        print(f"❌ 获取文件列表失败: {e}")
        return
    
    # 4. 迁移数据
    print("\n4️⃣ 开始迁移数据...")
    db = SessionLocal()
    
    try:
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for obj in objects:
            object_name = obj.get('object_name')
            
            # 检查是否已存在
            existing = db.query(Paper).filter(Paper.object_name == object_name).first()
            if existing:
                print(f"⏭️  跳过（已存在）: {object_name}")
                skipped_count += 1
                continue
            
            try:
                # 提取元数据
                original_name = obj.get('metadata', {}).get('original-filename', object_name)
                file_size = obj.get('size', 0)
                content_type = obj.get('content_type', 'application/pdf')
                last_modified = obj.get('last_modified')
                
                # 创建数据库记录
                paper = Paper(
                    user_id=default_user_id,  # 使用默认用户ID
                    object_name=object_name,
                    original_name=original_name,
                    file_size=file_size,
                    content_type=content_type,
                    created_at=last_modified if last_modified else datetime.now(),
                    updated_at=datetime.now()
                )
                
                db.add(paper)
                db.commit()
                
                print(f"✅ 迁移成功: {original_name} ({file_size} bytes)")
                migrated_count += 1
                
            except Exception as e:
                print(f"❌ 迁移失败 {object_name}: {e}")
                db.rollback()
                error_count += 1
                continue
        
        # 5. 汇总结果
        print("\n" + "=" * 60)
        print("📊 迁移结果汇总")
        print("=" * 60)
        print(f"✅ 成功迁移: {migrated_count} 个文件")
        print(f"⏭️  跳过（已存在）: {skipped_count} 个文件")
        print(f"❌ 迁移失败: {error_count} 个文件")
        print(f"📦 总计: {len(objects)} 个文件")
        
        if migrated_count > 0:
            print("\n🎉 数据迁移完成！现在可以在论文列表中看到这些文件了。")
            print(f"⚠️  注意：所有迁移的论文的 user_id 都设置为 {default_user_id}")
            print("   如果需要修改，请手动更新数据库")
        
    except Exception as e:
        print(f"\n❌ 迁移过程出错: {e}")
        db.rollback()
    finally:
        db.close()


def check_status():
    """检查当前状态"""
    print("\n📋 检查当前状态...")
    
    # 检查数据库
    db = SessionLocal()
    try:
        paper_count = db.query(Paper).count()
        print(f"📊 MySQL中的论文记录: {paper_count} 条")
        
        if paper_count > 0:
            print("\n最近的论文记录:")
            recent_papers = db.query(Paper).order_by(Paper.created_at.desc()).limit(5).all()
            for paper in recent_papers:
                print(f"  - [{paper.id}] {paper.original_name} (user_id: {paper.user_id})")
    except Exception as e:
        print(f"❌ 查询数据库失败: {e}")
    finally:
        db.close()
    
    # 检查MinIO
    try:
        minio_client = get_minio_client()
        objects_iter = minio_client.list_objects(MINIO_BUCKET, recursive=True)
        objects = list(objects_iter)
        print(f"📦 MinIO中的文件: {len(objects)} 个")
        
        if objects:
            print("\nMinIO文件列表（前5个）:")
            for obj in objects[:5]:
                print(f"  - {obj.object_name} ({obj.size} bytes)")
    except Exception as e:
        print(f"❌ 查询MinIO失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='论文数据迁移脚本')
    parser.add_argument('--user-id', type=int, default=1, 
                       help='默认用户ID（默认：1）')
    parser.add_argument('--check', action='store_true',
                       help='只检查状态，不执行迁移')
    
    args = parser.parse_args()
    
    if args.check:
        check_status()
    else:
        print(f"\n⚠️  将使用默认 user_id: {args.user_id}")
        confirm = input("确认开始迁移？(y/n): ").lower()
        
        if confirm == 'y':
            migrate_papers(default_user_id=args.user_id)
            check_status()
        else:
            print("❌ 取消迁移")


if __name__ == "__main__":
    main()

