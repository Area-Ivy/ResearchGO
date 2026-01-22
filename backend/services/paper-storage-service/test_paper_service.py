"""
测试论文存储服务 - 验证所有API是否正常工作
"""
import requests
import os

PAPER_SERVICE_URL = "http://localhost:8003"
AUTH_SERVICE_URL = "http://localhost:8001"

def get_test_token():
    """获取测试Token"""
    print("\n=== 获取测试Token ===")
    
    login_data = {
        "username": "testuser",
        "password": "test123456"
    }
    
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/api/auth/login",
            json=login_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 登录成功")
            return result['access_token']
        else:
            print("❌ 登录失败，尝试注册...")
            
            register_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password": "test123456"
            }
            
            response = requests.post(
                f"{AUTH_SERVICE_URL}/api/auth/register",
                json=register_data
            )
            
            if response.status_code == 201:
                result = response.json()
                print("✅ 注册成功")
                return result['access_token']
            else:
                print(f"❌ 注册失败: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ 获取Token失败: {e}")
        return None


def test_health_check():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    
    try:
        response = requests.get(f"{PAPER_SERVICE_URL}/health")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 服务健康: {result}")
            return True
        else:
            print(f"❌ 服务异常: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False


def test_upload_paper(token):
    """测试上传论文（需要一个测试PDF文件）"""
    print("\n=== 测试上传论文 ===")
    
    # 检查是否有测试PDF文件
    test_files = [
        "test.pdf",
        "../../../test.pdf",
        "../../test_paper.pdf"
    ]
    
    test_file = None
    for f in test_files:
        if os.path.exists(f):
            test_file = f
            break
    
    if not test_file:
        print("⚠️  未找到测试PDF文件，跳过上传测试")
        print("   提示：在当前目录创建一个 test.pdf 文件来测试上传功能")
        return None
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (os.path.basename(test_file), f, 'application/pdf')}
            response = requests.post(
                f"{PAPER_SERVICE_URL}/api/papers/upload",
                headers=headers,
                files=files
            )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 201:
            result = response.json()
            print("✅ 上传成功")
            print(f"对象名: {result['object_name']}")
            print(f"原始名: {result['original_name']}")
            print(f"大小: {result['size']} 字节")
            return result['object_name']
        else:
            print(f"❌ 上传失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        return None


def test_list_papers(token):
    """测试获取论文列表"""
    print("\n=== 测试获取论文列表 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(
            f"{PAPER_SERVICE_URL}/api/papers/list",
            headers=headers
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ 获取列表成功")
            print(f"论文总数: {result['total']}")
            
            if result['papers']:
                print("\n论文列表:")
                for paper in result['papers'][:5]:  # 显示前5个
                    print(f"  - ID: {paper['id']}, 名称: {paper['original_name']}")
                    print(f"    大小: {paper['file_size']} 字节, 上传时间: {paper['created_at']}")
            
            return True
        else:
            print(f"❌ 获取列表失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 获取列表失败: {e}")
        return False


def test_download_paper(token, object_name):
    """测试下载论文"""
    if not object_name:
        print("\n⚠️  跳过下载测试（没有可用的论文）")
        return False
    
    print("\n=== 测试下载论文 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(
            f"{PAPER_SERVICE_URL}/api/papers/download/{object_name}",
            headers=headers
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 下载成功")
            print(f"文件大小: {len(response.content)} 字节")
            return True
        else:
            print(f"❌ 下载失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False


def test_delete_paper(token, object_name):
    """测试删除论文"""
    if not object_name:
        print("\n⚠️  跳过删除测试（没有可用的论文）")
        return False
    
    print("\n=== 测试删除论文 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 询问是否删除
    print(f"⚠️  将要删除论文: {object_name}")
    confirm = input("确认删除？(y/n): ").lower()
    
    if confirm != 'y':
        print("取消删除")
        return False
    
    try:
        response = requests.delete(
            f"{PAPER_SERVICE_URL}/api/papers/delete/{object_name}",
            headers=headers
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ 删除成功")
            print(f"消息: {result['message']}")
            return True
        else:
            print(f"❌ 删除失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 删除失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("论文存储服务测试")
    print("=" * 60)
    
    # 测试健康检查
    if not test_health_check():
        print("\n❌ 服务未启动，请先启动论文存储服务")
        return
    
    # 获取Token
    token = get_test_token()
    if not token:
        print("\n❌ 无法获取Token，测试终止")
        return
    
    print(f"\n✅ Token获取成功: {token[:50]}...")
    
    # 测试上传
    object_name = test_upload_paper(token)
    
    # 测试列表
    test_list_papers(token)
    
    # 测试下载
    if object_name:
        test_download_paper(token, object_name)
        
        # 测试删除（可选）
        # test_delete_paper(token, object_name)
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
    print("\n提示：")
    print("- 如要测试上传功能，请在当前目录放置一个 test.pdf 文件")
    print("- 前端已配置为使用论文存储服务 (8003端口)")
    print("- 可以通过前端界面测试完整功能")


if __name__ == "__main__":
    main()

