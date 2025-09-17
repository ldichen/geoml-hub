#!/usr/bin/env python3
"""
测试统一错误处理方案
"""
import requests
import json

API_BASE = "http://localhost:8000"

def get_auth_token():
    """获取认证token"""
    auth_data = {
        "email": "admin@geoml-hub.com",
        "password": "admin123"
    }

    try:
        # 获取外部token
        response = requests.post(
            f"{API_BASE}/api/auth/mock-external-auth",
            json=auth_data
        )

        if response.status_code == 200:
            external_token = response.json()["external_token"]

            # 交换访问token
            login_response = requests.post(
                f"{API_BASE}/api/auth/login",
                json={"external_token": external_token}
            )

            if login_response.status_code == 200:
                access_token = login_response.json()["access_token"]
                return access_token
    except Exception as e:
        print(f"认证失败: {e}")

    return None

def test_repository_already_exists_error():
    """测试仓库已存在错误"""
    print("\n=== 测试仓库已存在错误 ===")

    token = get_auth_token()
    if not token:
        print("❌ 无法获取认证token")
        return

    # 创建重复的仓库名
    repo_data = {
        "name": "duplicate-repo-test",
        "description": "测试重复仓库名错误",
        "repo_type": "model",
        "visibility": "public"
    }

    headers = {'Authorization': f'Bearer {token}'}

    # 第一次创建（应该成功）
    response1 = requests.post(
        f"{API_BASE}/api/repositories/",
        json=repo_data,
        headers=headers
    )

    print(f"第一次创建状态: {response1.status_code}")

    # 第二次创建（应该失败，返回统一错误格式）
    response2 = requests.post(
        f"{API_BASE}/api/repositories/",
        json=repo_data,
        headers=headers
    )

    print(f"第二次创建状态: {response2.status_code}")

    if response2.status_code == 409:
        try:
            error_data = response2.json()
            print("✅ 收到统一错误响应格式:")
            print(json.dumps(error_data, indent=2, ensure_ascii=False))

            # 验证错误格式
            expected_fields = ['success', 'error', 'timestamp']
            for field in expected_fields:
                if field in error_data:
                    print(f"✅ 包含字段: {field}")
                else:
                    print(f"❌ 缺少字段: {field}")

            if 'error' in error_data:
                error = error_data['error']
                if 'code' in error and 'message' in error:
                    print(f"✅ 错误代码: {error['code']}")
                    print(f"✅ 错误消息: {error['message']}")
                else:
                    print("❌ 错误详情格式不正确")

        except Exception as e:
            print(f"❌ 解析错误响应失败: {e}")
            print(f"响应内容: {response2.text}")
    else:
        print(f"❌ 未预期的状态码: {response2.status_code}")


def test_invalid_file_type_error():
    """测试无效文件类型错误"""
    print("\n=== 测试无效文件类型错误 ===")

    token = get_auth_token()
    if not token:
        print("❌ 无法获取认证token")
        return

    # 创建无效的README文件（非.md后缀）
    repo_data = {
        "name": "invalid-file-test-" + str(int(__import__('time').time())),
        "description": "测试无效文件类型",
        "repo_type": "model",
        "visibility": "public"
    }

    # 准备表单数据，使用非.md文件
    files = {
        'readme_file': ('README.txt', b'This is a test file', 'text/plain')
    }

    data = {
        'repo_data': json.dumps(repo_data)
    }

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.post(
        f"{API_BASE}/api/repositories/with-readme",
        files=files,
        data=data,
        headers=headers
    )

    print(f"响应状态: {response.status_code}")

    if response.status_code == 400:
        try:
            error_data = response.json()
            print("✅ 收到统一错误响应格式:")
            print(json.dumps(error_data, indent=2, ensure_ascii=False))

            # 验证特定错误代码
            if 'error' in error_data and error_data['error']['code'] == 'INVALID_FILE_TYPE':
                print("✅ 正确的错误代码: INVALID_FILE_TYPE")
            else:
                print("❌ 错误代码不正确")

        except Exception as e:
            print(f"❌ 解析错误响应失败: {e}")
    else:
        print(f"❌ 未预期的状态码: {response.status_code}")


def test_validation_error():
    """测试验证错误"""
    print("\n=== 测试验证错误 ===")

    token = get_auth_token()
    if not token:
        print("❌ 无法获取认证token")
        return

    # 发送无效的仓库数据（缺少必需字段）
    invalid_data = {}  # 空数据，应该触发验证错误

    headers = {'Authorization': f'Bearer {token}'}

    response = requests.post(
        f"{API_BASE}/api/repositories/",
        json=invalid_data,
        headers=headers
    )

    print(f"响应状态: {response.status_code}")

    if response.status_code == 422:
        try:
            error_data = response.json()
            print("✅ 收到统一错误响应格式:")
            print(json.dumps(error_data, indent=2, ensure_ascii=False))

            # 验证验证错误格式
            if 'error' in error_data and error_data['error']['code'] == 'VALIDATION_ERROR':
                print("✅ 正确的错误代码: VALIDATION_ERROR")

                if 'context' in error_data['error'] and 'validation_errors' in error_data['error']['context']:
                    print("✅ 包含验证错误详情")
                    for validation_error in error_data['error']['context']['validation_errors']:
                        print(f"   - 字段: {validation_error.get('field')}")
                        print(f"     错误: {validation_error.get('message')}")
                else:
                    print("❌ 缺少验证错误详情")
            else:
                print("❌ 错误代码不正确")

        except Exception as e:
            print(f"❌ 解析错误响应失败: {e}")
    else:
        print(f"❌ 未预期的状态码: {response.status_code}")


def test_successful_creation():
    """测试成功创建（确保正常功能不受影响）"""
    print("\n=== 测试成功创建 ===")

    token = get_auth_token()
    if not token:
        print("❌ 无法获取认证token")
        return

    # 正常的仓库数据
    repo_data = {
        "name": "success-test-" + str(int(__import__('time').time())),
        "description": "测试成功创建",
        "repo_type": "model",
        "visibility": "public"
    }

    headers = {'Authorization': f'Bearer {token}'}

    response = requests.post(
        f"{API_BASE}/api/repositories/",
        json=repo_data,
        headers=headers
    )

    print(f"响应状态: {response.status_code}")

    if response.status_code == 200:
        try:
            result = response.json()
            print("✅ 仓库创建成功:")
            print(f"   - ID: {result.get('id')}")
            print(f"   - 名称: {result.get('name')}")
            print(f"   - 完整名称: {result.get('full_name')}")
        except Exception as e:
            print(f"❌ 解析成功响应失败: {e}")
    else:
        print(f"❌ 创建失败: {response.status_code}")
        if response.text:
            print(f"错误内容: {response.text}")


if __name__ == "__main__":
    print("🧪 统一错误处理方案测试")
    print("=" * 50)

    test_successful_creation()
    test_repository_already_exists_error()
    test_invalid_file_type_error()
    test_validation_error()

    print("\n" + "=" * 50)
    print("✅ 测试完成！")