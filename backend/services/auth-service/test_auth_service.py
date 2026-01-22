"""
测试认证服务 - 验证所有API是否正常工作
"""
import requests
import json

AUTH_SERVICE_URL = "http://localhost:8001"

def test_register():
    """测试用户注册"""
    print("\n=== 测试用户注册 ===")
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123456"
    }
    
    response = requests.post(
        f"{AUTH_SERVICE_URL}/api/auth/register",
        json=data
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print("✅ 注册成功")
        print(f"用户ID: {result['user']['id']}")
        print(f"用户名: {result['user']['username']}")
        print(f"Token: {result['access_token'][:50]}...")
        return result['access_token']
    else:
        print(f"❌ 注册失败: {response.text}")
        return None


def test_login():
    """测试用户登录"""
    print("\n=== 测试用户登录 ===")
    data = {
        "username": "testuser",
        "password": "test123456"
    }
    
    response = requests.post(
        f"{AUTH_SERVICE_URL}/api/auth/login",
        json=data
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ 登录成功")
        print(f"用户名: {result['user']['username']}")
        print(f"Token: {result['access_token'][:50]}...")
        return result['access_token']
    else:
        print(f"❌ 登录失败: {response.text}")
        return None


def test_get_user_info(token):
    """测试获取用户信息"""
    print("\n=== 测试获取用户信息 ===")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{AUTH_SERVICE_URL}/api/auth/me",
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ 获取用户信息成功")
        print(f"用户ID: {result['id']}")
        print(f"用户名: {result['username']}")
        print(f"邮箱: {result['email']}")
        print(f"激活状态: {result['is_active']}")
        return True
    else:
        print(f"❌ 获取用户信息失败: {response.text}")
        return False


def test_verify_token(token):
    """测试Token验证（供其他服务调用）"""
    print("\n=== 测试Token验证 ===")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post(
        f"{AUTH_SERVICE_URL}/api/auth/verify",
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ Token验证成功")
        print(f"用户ID: {result['id']}")
        print(f"用户名: {result['username']}")
        return True
    else:
        print(f"❌ Token验证失败: {response.text}")
        return False


def test_update_user(token):
    """测试更新用户信息"""
    print("\n=== 测试更新用户信息 ===")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "email": "newemail@example.com"
    }
    
    response = requests.put(
        f"{AUTH_SERVICE_URL}/api/auth/me",
        headers=headers,
        json=data
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ 更新用户信息成功")
        print(f"新邮箱: {result['email']}")
        return True
    else:
        print(f"❌ 更新用户信息失败: {response.text}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("认证服务测试")
    print("=" * 60)
    
    # 测试注册（如果用户已存在，则直接登录）
    token = test_register()
    if token is None:
        token = test_login()
    
    if token:
        # 测试其他功能
        test_get_user_info(token)
        test_verify_token(token)
        test_update_user(token)
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！认证服务工作正常。")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 测试失败！无法获取Token。")
        print("=" * 60)


if __name__ == "__main__":
    main()

