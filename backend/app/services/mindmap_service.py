"""
Mindmap Service
思维导图生成服务
"""
import io
import logging
from typing import Dict, Any, Optional
import pdfplumber
from app.services.minio_service import MinIOService
from app.services.openai_service import OpenAIService
from app.models.chat import ChatMessage

logger = logging.getLogger(__name__)


class MindmapService:
    """思维导图生成服务"""
    
    def __init__(self, minio_service: MinIOService):
        """
        初始化思维导图服务
        
        Args:
            minio_service: MinIO服务实例
        """
        self.minio_service = minio_service
        try:
            self.openai_service = OpenAIService()
            logger.info("✓ MindmapService initialized successfully")
        except Exception as e:
            logger.warning(f"OpenAI service not available: {e}")
            self.openai_service = None
    
    async def extract_text_from_pdf(self, pdf_data: io.BytesIO) -> str:
        """
        从PDF中提取文本内容
        
        Args:
            pdf_data: PDF文件数据流
            
        Returns:
            str: 提取的文本内容
        """
        try:
            text_content = []
            
            with pdfplumber.open(pdf_data) as pdf:
                logger.info(f"PDF has {len(pdf.pages)} pages")
                
                # 提取前20页的内容（避免处理过大的文件）
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
    
    async def generate_mindmap_markdown(
        self, 
        text: str, 
        max_depth: int = 3,
        language: str = "zh"
    ) -> str:
        """
        使用AI生成思维导图的Markdown格式
        
        Args:
            text: PDF提取的文本
            max_depth: 最大深度
            language: 语言
            
        Returns:
            str: Markdown格式的思维导图
        """
        if not self.openai_service:
            raise Exception("OpenAI service is not available")
        
        # 限制文本长度（避免超过token限制）
        max_chars = 12000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n...(content truncated)"
        
        # 构建提示词 - 生成jsMind JSON格式
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
  "meta": {{
    "name": "论文思维导图",
    "version": "1.0"
  }},
  "format": "node_tree",
  "data": {{
    "id": "root",
    "topic": "论文标题",
    "children": [
      {{
        "id": "research",
        "topic": "研究背景与目标",
        "children": [
          {{"id": "r1", "topic": "研究背景"}},
          {{"id": "r2", "topic": "研究目标"}}
        ]
      }},
      {{
        "id": "method",
        "topic": "研究方法",
        "children": [
          {{"id": "m1", "topic": "方法1"}},
          {{"id": "m2", "topic": "方法2"}}
        ]
      }},
      {{
        "id": "findings",
        "topic": "主要发现",
        "children": [
          {{"id": "f1", "topic": "发现1"}},
          {{"id": "f2", "topic": "发现2"}}
        ]
      }},
      {{
        "id": "innovation",
        "topic": "创新点",
        "children": [
          {{"id": "i1", "topic": "创新描述"}}
        ]
      }},
      {{
        "id": "conclusion",
        "topic": "结论与展望",
        "children": [
          {{"id": "c1", "topic": "主要结论"}},
          {{"id": "c2", "topic": "未来工作"}}
        ]
      }}
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

Format example:
{{
  "meta": {{
    "name": "Paper Mindmap",
    "version": "1.0"
  }},
  "format": "node_tree",
  "data": {{
    "id": "root",
    "topic": "Paper Title",
    "children": [
      {{
        "id": "research",
        "topic": "Research Background",
        "children": [
          {{"id": "r1", "topic": "Background"}},
          {{"id": "r2", "topic": "Objectives"}}
        ]
      }},
      {{
        "id": "method",
        "topic": "Methodology",
        "children": [
          {{"id": "m1", "topic": "Method 1"}},
          {{"id": "m2", "topic": "Method 2"}}
        ]
      }},
      {{
        "id": "findings",
        "topic": "Main Findings",
        "children": [
          {{"id": "f1", "topic": "Finding 1"}},
          {{"id": "f2", "topic": "Finding 2"}}
        ]
      }},
      {{
        "id": "innovation",
        "topic": "Innovations",
        "children": [
          {{"id": "i1", "topic": "Innovation description"}}
        ]
      }},
      {{
        "id": "conclusion",
        "topic": "Conclusions",
        "children": [
          {{"id": "c1", "topic": "Main conclusion"}},
          {{"id": "c2", "topic": "Future work"}}
        ]
      }}
    ]
  }}
}}

Paper content:
{text}

Output JSON directly, without explanations or code block markers:"""
        
        try:
            # 调用OpenAI生成思维导图
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
            
            # 移除各种可能的代码块标记
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:].lstrip('\n')
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:].lstrip('\n')
            
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3].rstrip('\n')
            
            logger.info(f"Generated jsMind JSON: {cleaned_response[:100]}...")
            
            # 解析JSON以验证格式
            import json
            try:
                mindmap_json = json.loads(cleaned_response)
                logger.info(f"JSON validation successful, keys: {mindmap_json.keys()}")
                return mindmap_json
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                logger.error(f"Raw response (first 500 chars): {cleaned_response[:500]}")
                # 如果JSON解析失败，返回一个默认的简单结构
                logger.warning("Returning fallback mindmap structure")
                return {
                    "meta": {
                        "name": "Paper Mindmap",
                        "version": "1.0"
                    },
                    "format": "node_tree",
                    "data": {
                        "id": "root",
                        "topic": "论文分析",
                        "children": [
                            {
                                "id": "error",
                                "topic": f"JSON解析失败: {str(e)[:50]}",
                                "children": [
                                    {"id": "raw", "topic": cleaned_response[:100]}
                                ]
                            }
                        ]
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
        """
        为PDF文件生成思维导图
        
        Args:
            object_name: MinIO中的PDF对象名称
            max_depth: 最大深度
            language: 语言
            
        Returns:
            Dict: 包含思维导图数据的字典
        """
        try:
            # 1. 从MinIO下载PDF
            logger.info(f"Downloading PDF: {object_name}")
            pdf_data, file_info = await self.minio_service.download_file(object_name)
            
            # 将响应转换为BytesIO
            pdf_bytes = io.BytesIO()
            for chunk in pdf_data:
                pdf_bytes.write(chunk)
            pdf_bytes.seek(0)
            
            # 2. 提取PDF文本
            logger.info("Extracting text from PDF")
            text = await self.extract_text_from_pdf(pdf_bytes)
            
            if not text.strip():
                raise Exception("No text content extracted from PDF")
            
            # 3. 生成思维导图
            logger.info("Generating mindmap with AI")
            markdown = await self.generate_mindmap_markdown(
                text=text,
                max_depth=max_depth,
                language=language
            )
            
            # 4. 构建响应
            original_name = file_info.get("metadata", {}).get("X-Amz-Meta-Original_name", object_name)
            
            return {
                "success": True,
                "message": "Mindmap generated successfully",
                "mindmap_data": markdown,  # 现在是JSON对象
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

