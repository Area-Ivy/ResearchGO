"""
为已存在的论文创建向量索引
运行此脚本将为所有未索引的论文创建向量索引
"""
import os
import sys
import io
import asyncio
import httpx
import pdfplumber
from dotenv import load_dotenv

# 添加app目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.database import SessionLocal
from app.models.paper import Paper
from app.utils.minio_client import get_minio_client, MINIO_BUCKET

# 配置
VECTOR_SEARCH_SERVICE_URL = os.getenv("VECTOR_SEARCH_SERVICE_URL", "http://localhost:8004")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")


def extract_text_from_pdf(pdf_data: bytes, max_pages: int = 50) -> str:
    """从PDF中提取文本"""
    try:
        text_content = []
        pdf_stream = io.BytesIO(pdf_data)
        
        with pdfplumber.open(pdf_stream) as pdf:
            total_pages = len(pdf.pages)
            pages_to_extract = min(total_pages, max_pages)
            
            print(f"  提取 {pages_to_extract}/{total_pages} 页...")
            
            for i, page in enumerate(pdf.pages[:pages_to_extract]):
                try:
                    text = page.extract_text()
                    if text:
                        text_content.append(f"--- Page {i+1} ---\n{text}")
                except Exception as e:
                    print(f"  ⚠️ 第 {i+1} 页提取失败: {e}")
                    continue
        
        full_text = "\n\n".join(text_content)
        return full_text.strip()
        
    except Exception as e:
        print(f"  ❌ PDF提取失败: {e}")
        return ""


async def get_token(username: str = None, password: str = None):
    """获取认证Token"""
    print("\n获取认证Token...")
    
    # 如果没有提供用户名密码，则提示输入
    if not username:
        username = input("请输入用户名: ").strip()
    if not password:
        password = input("请输入密码: ").strip()
    
    login_data = {
        "username": username,
        "password": password
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/api/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 用户 {username} 登录成功")
                return result['access_token']
            else:
                print(f"❌ 登录失败: {response.text}")
                return None
                    
        except Exception as e:
            print(f"❌ 获取Token失败: {e}")
            return None


async def index_paper(paper_id: str, title: str, file_name: str, content: str, token: str):
    """索引单篇论文"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{VECTOR_SEARCH_SERVICE_URL}/api/vector/index",
                json={
                    "paper_id": paper_id,
                    "title": title,
                    "file_name": file_name,
                    "content": content,
                    "max_chunk_size": 1000
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return True, result.get('chunks_created', 0)
            else:
                return False, response.text
                
        except Exception as e:
            return False, str(e)


async def main(username: str = None, password: str = None):
    """主函数"""
    print("=" * 60)
    print("📚 论文向量索引工具")
    print("=" * 60)
    
    # 获取Token
    token = await get_token(username, password)
    if not token:
        print("\n❌ 无法获取Token，退出")
        return
    
    # 获取MinIO客户端
    minio_client = get_minio_client()
    
    # 获取数据库中的论文列表
    db = SessionLocal()
    try:
        papers = db.query(Paper).all()
        print(f"\n📋 找到 {len(papers)} 篇论文")
        
        if not papers:
            print("没有论文需要索引")
            return
        
        indexed_count = 0
        failed_count = 0
        
        for i, paper in enumerate(papers, 1):
            print(f"\n[{i}/{len(papers)}] 处理: {paper.original_name}")
            
            try:
                # 从MinIO获取PDF
                response = minio_client.get_object(MINIO_BUCKET, paper.object_name)
                pdf_data = response.read()
                
                # 提取文本
                content = extract_text_from_pdf(pdf_data)
                
                if not content or len(content) < 100:
                    print(f"  ⚠️ 文本内容不足，跳过")
                    failed_count += 1
                    continue
                
                print(f"  📝 提取了 {len(content)} 字符")
                
                # 索引到向量数据库
                success, result = await index_paper(
                    paper_id=paper.object_name,
                    title=paper.title or paper.original_name.replace('.pdf', ''),
                    file_name=paper.original_name,
                    content=content,
                    token=token
                )
                
                if success:
                    print(f"  ✅ 索引成功，创建了 {result} 个chunks")
                    indexed_count += 1
                else:
                    print(f"  ❌ 索引失败: {result}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
                failed_count += 1
        
        print("\n" + "=" * 60)
        print("📊 索引结果")
        print("=" * 60)
        print(f"✅ 成功: {indexed_count}")
        print(f"❌ 失败: {failed_count}")
        print(f"📚 总计: {len(papers)}")
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='为已有论文创建向量索引')
    parser.add_argument('--username', '-u', type=str, help='用户名')
    parser.add_argument('--password', '-p', type=str, help='密码')
    
    args = parser.parse_args()
    
    asyncio.run(main(args.username, args.password))

