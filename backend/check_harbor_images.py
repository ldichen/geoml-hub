#!/usr/bin/env python3
"""
检查Harbor中的镜像
"""

import asyncio
from app.services.harbor_client import HarborClient
from app.config import settings

async def check_harbor_images():
    """检查Harbor中的镜像"""
    print("=== 检查Harbor镜像 ===")
    
    try:
        async with HarborClient() as harbor_client:
            # 检查连接
            is_connected = await harbor_client.test_connection()
            print(f"Harbor连接状态: {'✅ 连接成功' if is_connected else '❌ 连接失败'}")
            
            if not is_connected:
                return
            
            # 获取项目中的所有仓库
            project_name = settings.harbor_default_project
            print(f"\n检查项目: {project_name}")
            
            repositories = await harbor_client.list_repositories(project_name)
            print(f"找到 {len(repositories)} 个仓库")
            
            if not repositories:
                print("❌ Harbor中没有任何仓库")
                return
            
            # 检查每个仓库的镜像
            for repo in repositories:
                repo_name = repo['name']
                print(f"\n仓库: {repo_name}")
                
                # 提取短名称
                if '/' in repo_name:
                    short_name = repo_name.split('/')[-1]
                else:
                    short_name = repo_name
                
                # 获取仓库中的artifacts
                artifacts = await harbor_client.list_artifacts(project_name, short_name)
                print(f"  Artifacts数量: {len(artifacts)}")
                
                if artifacts:
                    for i, artifact in enumerate(artifacts):
                        print(f"  Artifact {i+1}:")
                        print(f"    Digest: {artifact.get('digest', 'N/A')}")
                        print(f"    Size: {artifact.get('size', 'N/A')} bytes")
                        print(f"    Push Time: {artifact.get('push_time', 'N/A')}")
                        
                        # 获取标签
                        try:
                            tags = await harbor_client.get_artifact_tags(project_name, short_name, artifact['digest'])
                            if tags:
                                print(f"    Tags: {[tag['name'] for tag in tags]}")
                            else:
                                print(f"    Tags: 无标签")
                        except Exception as e:
                            print(f"    Tags: 获取失败 - {e}")
                else:
                    print("  ❌ 仓库为空")
            
            # 检查特定镜像是否存在
            print(f"\n=== 检查特定镜像 ===")
            target_repo = "redis-7-1"
            target_tag = "latest"
            
            try:
                artifact = await harbor_client.get_artifact(project_name, target_repo, target_tag)
                if artifact:
                    print(f"✅ 找到镜像: {project_name}/{target_repo}:{target_tag}")
                    print(f"   Digest: {artifact.get('digest')}")
                    print(f"   Size: {artifact.get('size')} bytes")
                else:
                    print(f"❌ 镜像不存在: {project_name}/{target_repo}:{target_tag}")
            except Exception as e:
                print(f"❌ 检查镜像失败: {e}")
                
    except Exception as e:
        print(f"❌ 检查Harbor失败: {e}")

if __name__ == "__main__":
    asyncio.run(check_harbor_images())