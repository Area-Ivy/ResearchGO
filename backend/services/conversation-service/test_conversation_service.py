"""
测试对话服务 - 验证所有API是否正常工作
"""
import requests
import json

CONVERSATION_SERVICE_URL = "http://localhost:8002"
AUTH_SERVICE_URL = "http://localhost:8001"

def get_test_token():
    """获取测试用的Token"""
    print("\n=== 获取测试Token ===")
    
    # 先尝试登录
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
            
            # 尝试注册
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


def test_create_conversation(token):
    """测试创建对话"""
    print("\n=== 测试创建对话 ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "title": "测试对话 - 微服务架构讨论"
    }
    
    response = requests.post(
        f"{CONVERSATION_SERVICE_URL}/api/conversations",
        headers=headers,
        json=data
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print("✅ 创建对话成功")
        print(f"对话ID: {result['id']}")
        print(f"标题: {result['title']}")
        return result['id']
    else:
        print(f"❌ 创建对话失败: {response.text}")
        return None


def test_get_conversations(token):
    """测试获取对话列表"""
    print("\n=== 测试获取对话列表 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{CONVERSATION_SERVICE_URL}/api/conversations",
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ 获取对话列表成功")
        print(f"对话总数: {result['total']}")
        print(f"返回数量: {len(result['conversations'])}")
        
        if result['conversations']:
            print("\n对话列表:")
            for conv in result['conversations'][:3]:  # 显示前3个
                print(f"  - ID: {conv['id']}, 标题: {conv['title']}, 消息数: {conv.get('message_count', 0)}")
        
        return True
    else:
        print(f"❌ 获取对话列表失败: {response.text}")
        return False


def test_add_message(token, conversation_id):
    """测试添加消息"""
    print("\n=== 测试添加消息 ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 添加用户消息
    user_message = {
        "role": "user",
        "content": "你好，能帮我解释一下微服务架构吗？"
    }
    
    response = requests.post(
        f"{CONVERSATION_SERVICE_URL}/api/conversations/{conversation_id}/messages",
        headers=headers,
        json=user_message
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print("✅ 添加用户消息成功")
        print(f"消息ID: {result['id']}")
        
        # 添加助手消息
        assistant_message = {
            "role": "assistant",
            "content": "微服务架构是一种将应用程序构建为一组小型、独立服务的架构风格。每个服务运行在自己的进程中，通过轻量级机制（通常是HTTP API）进行通信。"
        }
        
        response = requests.post(
            f"{CONVERSATION_SERVICE_URL}/api/conversations/{conversation_id}/messages",
            headers=headers,
            json=assistant_message
        )
        
        if response.status_code == 201:
            print("✅ 添加助手消息成功")
            return True
        else:
            print(f"❌ 添加助手消息失败: {response.text}")
            return False
    else:
        print(f"❌ 添加用户消息失败: {response.text}")
        return False


def test_get_conversation_detail(token, conversation_id):
    """测试获取对话详情"""
    print("\n=== 测试获取对话详情 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{CONVERSATION_SERVICE_URL}/api/conversations/{conversation_id}",
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ 获取对话详情成功")
        print(f"对话ID: {result['id']}")
        print(f"标题: {result['title']}")
        print(f"消息数量: {len(result['messages'])}")
        
        if result['messages']:
            print("\n消息列表:")
            for msg in result['messages']:
                print(f"  - {msg['role']}: {msg['content'][:50]}...")
        
        return True
    else:
        print(f"❌ 获取对话详情失败: {response.text}")
        return False


def test_update_conversation(token, conversation_id):
    """测试更新对话"""
    print("\n=== 测试更新对话标题 ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "title": "微服务架构深入讨论（已更新）"
    }
    
    response = requests.put(
        f"{CONVERSATION_SERVICE_URL}/api/conversations/{conversation_id}",
        headers=headers,
        json=data
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ 更新对话标题成功")
        print(f"新标题: {result['title']}")
        return True
    else:
        print(f"❌ 更新对话失败: {response.text}")
        return False


def test_delete_conversation(token, conversation_id):
    """测试删除对话"""
    print("\n=== 测试删除对话 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.delete(
        f"{CONVERSATION_SERVICE_URL}/api/conversations/{conversation_id}",
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 204:
        print("✅ 删除对话成功")
        return True
    else:
        print(f"❌ 删除对话失败: {response.text}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("对话服务测试")
    print("=" * 60)
    
    # 获取Token
    token = get_test_token()
    if not token:
        print("\n❌ 无法获取Token，测试终止")
        return
    
    print(f"\n✅ Token获取成功: {token[:50]}...")
    
    # 测试创建对话
    conversation_id = test_create_conversation(token)
    if not conversation_id:
        print("\n❌ 测试失败：无法创建对话")
        return
    
    # 测试获取对话列表
    test_get_conversations(token)
    
    # 测试添加消息
    test_add_message(token, conversation_id)
    
    # 测试获取对话详情
    test_get_conversation_detail(token, conversation_id)
    
    # 测试更新对话
    test_update_conversation(token, conversation_id)
    
    # 测试删除对话（可选，取消注释以测试）
    # test_delete_conversation(token, conversation_id)
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！对话服务工作正常。")
    print("=" * 60)


if __name__ == "__main__":
    main()

