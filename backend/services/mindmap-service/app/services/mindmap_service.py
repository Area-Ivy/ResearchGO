"""
Mindmap Service
思维导图生成服务
"""
import io
import json
import logging
from typing import Dict, Any
import pdfplumber
from app.services.minio_service import get_minio_service
from app.services.openai_service import get_openai_service
from app.models.chat import ChatMessage

logger = logging.getLogger(__name__)


class MindmapService:
    """思维导图生成服务"""
    
    def __init__(self):
        """初始化思维导图服务"""
        self.minio_service = get_minio_service()
        try:
            self.openai_service = get_openai_service()
            logger.info("✓ MindmapService initialized successfully")
        except Exception as e:
            logger.warning(f"OpenAI service not available: {e}")
            self.openai_service = None
    
    async def extract_text_from_pdf(self, pdf_data: io.BytesIO) -> str:
        """从PDF中提取文本内容"""
        try:
            text_content = []
            
            with pdfplumber.open(pdf_data) as pdf:
                logger.info(f"PDF has {len(pdf.pages)} pages")
                
                # 提取前20页的内容
                max_pages = min(len(pdf.pages), 20)
                
                for i, page in enumerate(pdf.pages[:max_pages]):
                    try:
                        text = page.extract_text()
                        if text:
                            text_content.append(f"--- Page {i+1} ---\n{text}")
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {i+1}: {e}")
                        continue
            
            full_text = "\n\n".join(text_content)
            logger.info(f"Extracted {len(full_text)} characters from PDF")
            
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}", exc_info=True)
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    async def generate_mindmap_json(
        self, 
        text: str, 
        max_depth: int = 3,
        language: str = "zh"
    ) -> Dict[str, Any]:
        """使用AI生成思维导图的JSON格式"""
        if not self.openai_service:
            raise Exception("OpenAI service is not available")
        
        # 限制文本长度
        max_chars = 12000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n...(content truncated)"
        
        # 构建提示词
        if language == "zh":
            prompt = f"""请分析以下学术论文内容，生成一个结构化的思维导图JSON数据。

要求：
1. 输出严格的JSON格式，符合jsMind格式规范
2. 最多{max_depth}层深度
3. 提取论文的核心内容：研究背景、研究方法、主要发现、创新点、结论
4. 每个节点的topic简洁明了，不超过15个字
5. 使用中文
6. 确保JSON格式正确，可以直接解析

输出格式示例：
{{
  "meta": {{"name": "论文思维导图", "version": "1.0"}},
  "format": "node_tree",
  "data": {{
    "id": "root",
    "topic": "论文标题",
    "children": [
      {{"id": "research", "topic": "研究背景与目标", "children": [{{"id": "r1", "topic": "背景"}}]}},
      {{"id": "method", "topic": "研究方法", "children": [{{"id": "m1", "topic": "方法1"}}]}},
      {{"id": "findings", "topic": "主要发现", "children": [{{"id": "f1", "topic": "发现1"}}]}},
      {{"id": "conclusion", "topic": "结论与展望", "children": [{{"id": "c1", "topic": "结论"}}]}}
    ]
  }}
}}

论文内容：
{text}

请直接输出JSON格式，不要有任何其他说明文字和代码块标记："""
        else:
            prompt = f"""Analyze the following academic paper and create a structured mind map in jsMind JSON format.

Requirements:
1. Output strict JSON format conforming to jsMind specifications
2. Maximum {max_depth} levels deep
3. Extract core content: background, methodology, findings, innovations, conclusions
4. Keep each topic concise (max 10 words)
5. Use English
6. Ensure valid JSON that can be parsed directly

Paper content:
{text}

Output JSON directly, without explanations or code block markers:"""
        
        try:
            messages = [
                ChatMessage(role="system", content="You are an expert at analyzing academic papers and creating mind maps."),
                ChatMessage(role="user", content=prompt)
            ]
            
            response = await self.openai_service.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )
            
            # 清理JSON代码块标记
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:].lstrip('\n')
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:].lstrip('\n')
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3].rstrip('\n')
            
            # 解析JSON
            try:
                mindmap_json = json.loads(cleaned_response)
                logger.info(f"JSON validation successful")
                return mindmap_json
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                # 返回fallback结构
                return {
                    "meta": {"name": "Paper Mindmap", "version": "1.0"},
                    "format": "node_tree",
                    "data": {
                        "id": "root",
                        "topic": "论文分析",
                        "children": [{"id": "error", "topic": f"JSON解析失败: {str(e)[:50]}"}]
                    }
                }
            
        except Exception as e:
            logger.error(f"Error generating mindmap with AI: {e}", exc_info=True)
            raise Exception(f"Failed to generate mindmap: {str(e)}")
    
    async def generate_mindmap(
        self,
        object_name: str,
        max_depth: int = 3,
        language: str = "zh"
    ) -> Dict[str, Any]:
        """为PDF文件生成思维导图"""
        try:
            # 1. 从MinIO下载PDF
            logger.info(f"Downloading PDF: {object_name}")
            pdf_data, file_info = await self.minio_service.download_file(object_name)
            
            # 2. 提取PDF文本
            logger.info("Extracting text from PDF")
            text = await self.extract_text_from_pdf(pdf_data)
            
            if not text.strip():
                raise Exception("No text content extracted from PDF")
            
            # 3. 生成思维导图
            logger.info("Generating mindmap with AI")
            mindmap_data = await self.generate_mindmap_json(
                text=text,
                max_depth=max_depth,
                language=language
            )
            
            # 4. 构建响应
            original_name = file_info.get("metadata", {}).get("X-Amz-Meta-Original_name", object_name)
            
            return {
                "success": True,
                "message": "Mindmap generated successfully",
                "mindmap_data": mindmap_data,
                "pdf_info": {
                    "object_name": object_name,
                    "original_name": original_name,
                    "size": file_info.get("size", 0),
                    "content_type": file_info.get("content_type", "application/pdf")
                }
            }
            
        except Exception as e:
            logger.error(f"Error in generate_mindmap: {e}", exc_info=True)
            return {
                "success": False,
                "message": str(e),
                "mindmap_data": None,
                "pdf_info": None
            }


# 单例服务实例
_mindmap_service = None

def get_mindmap_service() -> MindmapService:
    """获取思维导图服务实例"""
    global _mindmap_service
    if _mindmap_service is None:
        _mindmap_service = MindmapService()
    return _mindmap_service

