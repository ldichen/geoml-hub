import frontmatter
import yaml
from typing import Dict, Any, Optional, Tuple
import re


class YAMLFrontmatterParser:
    """YAML Frontmatter 解析器，用于解析 README.md 中的元数据"""
    
    def __init__(self):
        self.yaml_loader = yaml.SafeLoader

    def parse(self, content: str) -> Optional[Dict[str, Any]]:
        """
        解析包含 YAML frontmatter 的内容
        
        Args:
            content: 包含 YAML frontmatter 的文本内容
            
        Returns:
            解析出的元数据字典，如果没有 frontmatter 则返回 None
        """
        try:
            post = frontmatter.loads(content)
            return post.metadata if post.metadata else None
        except Exception as e:
            # 如果 frontmatter 库解析失败，尝试手动解析
            return self._manual_parse(content)

    def _manual_parse(self, content: str) -> Optional[Dict[str, Any]]:
        """
        手动解析 YAML frontmatter
        """
        try:
            # 检查是否以 --- 开始
            if not content.startswith('---'):
                return None
            
            # 找到结束的 ---
            end_match = re.search(r'\n---\s*\n', content)
            if not end_match:
                return None
            
            # 提取 YAML 部分
            yaml_content = content[3:end_match.start()]
            
            # 解析 YAML
            metadata = yaml.safe_load(yaml_content)
            return metadata if isinstance(metadata, dict) else None
            
        except Exception:
            return None

    def extract_content(self, content: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        提取 YAML frontmatter 和正文内容
        
        Args:
            content: 包含 YAML frontmatter 的文本内容
            
        Returns:
            (metadata, content) 元组
        """
        try:
            post = frontmatter.loads(content)
            return post.metadata, post.content
        except Exception:
            # 如果解析失败，尝试手动提取
            metadata = self._manual_parse(content)
            if metadata:
                # 移除 frontmatter 部分
                end_match = re.search(r'\n---\s*\n', content)
                if end_match:
                    content_only = content[end_match.end():]
                    return metadata, content_only
            return None, content

    def validate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和清理元数据
        
        Args:
            metadata: 原始元数据
            
        Returns:
            清理后的元数据
        """
        if not isinstance(metadata, dict):
            return {}
        
        validated = {}
        
        # 处理标准字段
        standard_fields = {
            'title': str,
            'description': str,
            'version': str,
            'author': str,
            'license': str,
            'tags': list,
            'base_model': str,
            'framework': str,
            'task': str,
            'dataset': str,
            'metrics': dict,
            'model_type': str,
            'language': (str, list),
            'pipeline_tag': str,
            'datasets': list,
            'thumbnail': str,
            'inference': (bool, dict),
            'widget': list,
            'model_index': list
        }
        
        for field, expected_type in standard_fields.items():
            if field in metadata:
                value = metadata[field]
                if isinstance(expected_type, tuple):
                    # 多种类型都可以
                    if any(isinstance(value, t) for t in expected_type):
                        validated[field] = value
                elif isinstance(value, expected_type):
                    validated[field] = value
                elif expected_type == list and not isinstance(value, list):
                    # 将单个值转换为列表
                    validated[field] = [value]
        
        # 处理自定义字段（保留其他所有字段）
        for field, value in metadata.items():
            if field not in standard_fields:
                validated[field] = value
        
        return validated

    def create_frontmatter(self, metadata: Dict[str, Any], content: str = "") -> str:
        """
        创建包含 YAML frontmatter 的文档
        
        Args:
            metadata: 元数据字典
            content: 正文内容
            
        Returns:
            包含 frontmatter 的完整文档
        """
        try:
            post = frontmatter.Post(content, **metadata)
            return frontmatter.dumps(post)
        except Exception:
            # 如果失败，手动创建
            yaml_str = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
            return f"---\n{yaml_str}---\n\n{content}"

    def update_frontmatter(self, original_content: str, new_metadata: Dict[str, Any]) -> str:
        """
        更新现有文档的 frontmatter
        
        Args:
            original_content: 原始文档内容
            new_metadata: 新的元数据
            
        Returns:
            更新后的文档内容
        """
        try:
            current_metadata, content = self.extract_content(original_content)
            
            # 合并元数据
            if current_metadata:
                current_metadata.update(new_metadata)
                merged_metadata = current_metadata
            else:
                merged_metadata = new_metadata
            
            return self.create_frontmatter(merged_metadata, content)
            
        except Exception:
            # 如果更新失败，直接添加新的 frontmatter
            return self.create_frontmatter(new_metadata, original_content)

    def extract_model_info(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        从元数据中提取模型相关信息
        
        Args:
            metadata: 元数据字典
            
        Returns:
            模型信息字典
        """
        model_info = {}
        
        # 基础信息
        if 'title' in metadata:
            model_info['name'] = metadata['title']
        if 'description' in metadata:
            model_info['description'] = metadata['description']
        if 'version' in metadata:
            model_info['version'] = metadata['version']
        if 'author' in metadata:
            model_info['author'] = metadata['author']
        if 'license' in metadata:
            model_info['license'] = metadata['license']
        if 'tags' in metadata:
            model_info['tags'] = metadata['tags']
        
        # 模型特定信息
        if 'base_model' in metadata:
            model_info['base_model'] = metadata['base_model']
        if 'framework' in metadata:
            model_info['framework'] = metadata['framework']
        if 'model_type' in metadata:
            model_info['model_type'] = metadata['model_type']
        if 'task' in metadata:
            model_info['task'] = metadata['task']
        
        # 数据集和指标
        if 'dataset' in metadata:
            model_info['dataset'] = metadata['dataset']
        if 'datasets' in metadata:
            model_info['datasets'] = metadata['datasets']
        if 'metrics' in metadata:
            model_info['metrics'] = metadata['metrics']
        
        # 其他信息
        if 'language' in metadata:
            model_info['language'] = metadata['language']
        if 'pipeline_tag' in metadata:
            model_info['pipeline_tag'] = metadata['pipeline_tag']
        if 'thumbnail' in metadata:
            model_info['thumbnail'] = metadata['thumbnail']
        
        return model_info

    def extract_classification_info(self, metadata: Dict[str, Any]) -> Optional[str]:
        """
        从元数据中提取分类信息
        
        Args:
            metadata: 元数据字典
            
        Returns:
            分类名称或ID，如果没有分类信息则返回 None
        """
        # 检查各种可能的分类字段
        classification_fields = [
            'classification',       # 标准分类字段
            'category',            # 类别字段
            'task',               # 任务类型（可能对应分类）
            'application',        # 应用领域
            'domain',             # 领域
            'field'               # 学科领域
        ]
        
        for field in classification_fields:
            if field in metadata:
                value = metadata[field]
                if isinstance(value, str) and value.strip():
                    return value.strip()
                elif isinstance(value, (int, float)):
                    return str(value)
        
        return None

    def is_valid_frontmatter(self, content: str) -> bool:
        """
        检查内容是否包含有效的 YAML frontmatter
        
        Args:
            content: 文档内容
            
        Returns:
            是否包含有效的 frontmatter
        """
        try:
            metadata = self.parse(content)
            return metadata is not None and len(metadata) > 0
        except Exception:
            return False