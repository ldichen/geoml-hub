#!/usr/bin/env python3
"""
生成JWT密钥的脚本
"""
import secrets
import string
import base64
import os

def generate_secret_key(length=32):
    """生成随机密钥"""
    return secrets.token_urlsafe(length)

def generate_hex_key(length=32):
    """生成十六进制密钥"""
    return secrets.token_hex(length)

def generate_base64_key(length=32):
    """生成Base64编码的密钥"""
    random_bytes = secrets.token_bytes(length)
    return base64.b64encode(random_bytes).decode('utf-8')

def generate_complex_key(length=64):
    """生成复杂的字符串密钥"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    print("🔑 JWT密钥生成器")
    print("=" * 50)
    
    print("\n1. URL安全密钥 (推荐用于JWT_SECRET_KEY):")
    jwt_key = generate_secret_key(32)
    print(f"JWT_SECRET_KEY={jwt_key}")
    
    print("\n2. 外部认证密钥 (推荐用于EXTERNAL_AUTH_SECRET_KEY):")
    external_key = generate_secret_key(32)
    print(f"EXTERNAL_AUTH_SECRET_KEY={external_key}")
    
    print("\n3. 十六进制密钥:")
    hex_key = generate_hex_key(32)
    print(f"HEX_KEY={hex_key}")
    
    print("\n4. Base64密钥:")
    base64_key = generate_base64_key(32)
    print(f"BASE64_KEY={base64_key}")
    
    print("\n5. 复杂字符串密钥:")
    complex_key = generate_complex_key(64)
    print(f"COMPLEX_KEY={complex_key}")
    
    print("\n" + "=" * 50)
    print("📝 使用说明:")
    print("1. 复制上面的密钥到你的 .env 文件")
    print("2. 不要在代码中硬编码密钥")
    print("3. 生产环境使用不同的密钥")
    print("4. 定期更换密钥以提高安全性")
    
    print("\n🔒 安全建议:")
    print("- 密钥长度至少32字符")
    print("- 使用随机生成的密钥")
    print("- 不要在版本控制中提交密钥")
    print("- 生产环境使用环境变量")