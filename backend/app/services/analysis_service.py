"""
Analysis Service
论文分析服务
"""
import io
import logging
from typing import Dict, Any
import pdfplumber
from app.services.minio_service import MinIOService
from app.services.openai_service import OpenAIService
from app.models.chat import ChatMessage

logger = logging.getLogger(__name__)


class AnalysisService:
    """论文分析服务"""
    
    def __init__(self, minio_service: MinIOService):
        """
        初始化论文分析服务
        
        Args:
            minio_service: MinIO服务实例
        """
        self.minio_service = minio_service
        try:
            self.openai_service = OpenAIService()
            logger.info("✓ AnalysisService initialized successfully")
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
                
                # 提取前30页的内容以获取更完整的信息
                max_pages = min(len(pdf.pages), 30)
                
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
    
    async def analyze_paper(
        self, 
        text: str, 
        language: str = "zh"
    ) -> Dict[str, str]:
        """
        使用AI分析论文内容
        
        Args:
            text: PDF提取的文本
            language: 语言
            
        Returns:
            Dict[str, str]: 分析结果字典
        """
        if not self.openai_service:
            raise Exception("OpenAI service is not available")
        
        # 限制文本长度（避免超过token限制）
        max_chars = 15000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n...(content truncated)"
        
        # 构建提示词
        if language == "zh":
            prompt = f"""你是一位专业的中文学术论文分析专家。请用中文对以下学术论文进行全面深入的分析。

重要提示：
- 必须使用中文回答
- 即使论文是英文的，你的分析也必须用中文撰写
- 使用专业的中文学术术语

论文内容：
{text}

请按照以下格式输出JSON（不要有代码块标记，直接输出JSON）：
{{
  "title": "论文标题（从论文中提取，如果是英文论文，保持原英文标题）",
  "abstract": "论文摘要（用中文概括，如果论文中有摘要请提取并翻译为中文；否则生成简短的中文摘要，150-200字）",
  "research_background": "研究背景（用中文描述，200-300字）：描述论文的研究领域、当前研究现状、存在的问题和挑战",
  "research_problem": "研究问题（用中文描述，150-200字）：明确指出论文要解决的核心问题和研究目标",
  "methodology": "研究方法（用中文描述，300-400字）：详细描述论文使用的研究方法、技术手段、实验设计等",
  "key_findings": "主要发现（用中文描述，300-400字）：总结论文的关键实验结果、数据发现和主要贡献",
  "innovations": "创新点（用中文描述，200-300字）：指出论文的创新之处，与现有研究相比的突破",
  "limitations": "局限性（用中文描述，150-200字）：分析论文存在的不足、潜在问题或未解决的挑战",
  "future_work": "未来工作（用中文描述，150-200字）：论文提出的未来研究方向或可能的改进方向",
  "conclusion": "结论（用中文描述，200-250字）：总结论文的整体贡献和意义"
}}

要求：
1. 严格按照JSON格式输出
2. 所有字段都必须用中文填写，内容要详细充实
3. 使用专业的中文学术语言
4. 确保逻辑清晰、结构完整
5. 不要添加任何代码块标记（如```json），直接输出JSON
6. 再次强调：所有分析内容必须使用中文撰写"""
        else:
            prompt = f"""Please provide a comprehensive and in-depth analysis of the following academic paper. Provide a detailed, structured analysis report covering all the following aspects:

Paper content:
{text}

Please output in the following JSON format (no code block markers, output JSON directly):
{{
  "title": "Paper title (extracted from the paper)",
  "abstract": "Paper abstract (extract if available; otherwise generate a brief abstract, 100-150 words)",
  "research_background": "Research background (150-200 words): Describe the research field, current state of research, existing problems and challenges",
  "research_problem": "Research problem (100-150 words): Clearly state the core problem and research objectives",
  "methodology": "Methodology (200-300 words): Describe the research methods, technical approaches, and experimental design",
  "key_findings": "Key findings (200-300 words): Summarize key experimental results, data findings, and main contributions",
  "innovations": "Innovations (150-200 words): Point out the innovative aspects and breakthroughs compared to existing research",
  "limitations": "Limitations (100-150 words): Analyze shortcomings, potential issues, or unresolved challenges",
  "future_work": "Future work (100-150 words): Proposed future research directions or possible improvements",
  "conclusion": "Conclusion (150-200 words): Summarize the overall contribution and significance"
}}

Requirements:
1. Strictly follow JSON format
2. All fields must be filled with detailed content
3. Use professional academic language
4. Ensure clear logic and complete structure
5. Do not add code block markers (like ```json), output JSON directly"""
        
        try:
            # 调用OpenAI生成分析
            system_prompt = (
                "你是一位专业的中文学术论文分析专家，精通各个学科领域。请用中文提供深入、全面的分析。" 
                if language == "zh" 
                else "You are an expert academic paper analyst with deep knowledge across multiple fields. Provide thorough, insightful analysis."
            )
            
            messages = [
                ChatMessage(
                    role="system", 
                    content=system_prompt
                ),
                ChatMessage(role="user", content=prompt)
            ]
            
            response = await self.openai_service.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=3000
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
            
            logger.info(f"Generated analysis JSON (first 200 chars): {cleaned_response[:200]}...")
            
            # 解析JSON以验证格式
            import json
            try:
                analysis_dict = json.loads(cleaned_response)
                logger.info(f"JSON validation successful, keys: {analysis_dict.keys()}")
                
                # 确保所有必需字段都存在
                required_fields = [
                    "title", "abstract", "research_background", "research_problem",
                    "methodology", "key_findings", "innovations", "limitations",
                    "future_work", "conclusion"
                ]
                for field in required_fields:
                    if field not in analysis_dict:
                        analysis_dict[field] = "暂无内容" if language == "zh" else "Not available"
                
                return analysis_dict
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                logger.error(f"Raw response (first 500 chars): {cleaned_response[:500]}")
                raise Exception(f"Failed to parse AI response as JSON: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error analyzing paper with AI: {e}", exc_info=True)
            raise Exception(f"Failed to analyze paper: {str(e)}")
    
    async def generate_analysis(
        self,
        object_name: str,
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        为PDF文件生成分析报告
        
        Args:
            object_name: MinIO中的PDF对象名称
            language: 语言
            
        Returns:
            Dict: 包含分析数据的字典
        """
        try:
            # 1. 从MinIO下载PDF
            logger.info(f"Downloading PDF for analysis: {object_name}")
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
            
            # 3. 生成分析
            logger.info("Analyzing paper with AI")
            analysis = await self.analyze_paper(
                text=text,
                language=language
            )
            
            # 4. 构建响应
            original_name = file_info.get("metadata", {}).get("X-Amz-Meta-Original_name", object_name)
            
            return {
                "success": True,
                "message": "Analysis generated successfully",
                "analysis": analysis,
                "pdf_info": {
                    "object_name": object_name,
                    "original_name": original_name,
                    "size": file_info.get("size", 0),
                    "content_type": file_info.get("content_type", "application/pdf")
                }
            }
            
        except Exception as e:
            logger.error(f"Error in generate_analysis: {e}", exc_info=True)
            return {
                "success": False,
                "message": str(e),
                "analysis": None,
                "pdf_info": None
            }

