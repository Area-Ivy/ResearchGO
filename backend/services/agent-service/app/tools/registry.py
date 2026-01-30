"""
Tool Registry - 工具注册中心
"""
from typing import Dict, List, Any
from .base import BaseTool
from .literature_tools import (
    SearchLiteratureTool,
    GetWorkDetailTool,
    GetRelatedWorksTool,
    ExportCitationTool
)
from .paper_tools import (
    SearchUserPapersTool,
    GetPaperContentTool
)
from .vector_tools import (
    SemanticSearchTool,
    AskPaperTool
)
from .analysis_tools import (
    AnalyzePaperTool,
    GenerateMindmapTool,
    ComparePapersTool
)


class ToolRegistry:
    """工具注册中心"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        default_tools = [
            # 文献检索工具
            SearchLiteratureTool(),
            GetWorkDetailTool(),
            GetRelatedWorksTool(),
            ExportCitationTool(),
            # 论文存储工具
            SearchUserPapersTool(),
            GetPaperContentTool(),
            # 向量搜索工具
            SemanticSearchTool(),
            AskPaperTool(),
            # 分析工具
            AnalyzePaperTool(),
            GenerateMindmapTool(),
            ComparePapersTool(),
        ]
        
        for tool in default_tools:
            self.register(tool)
    
    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> BaseTool:
        """获取工具"""
        return self._tools.get(name)
    
    def get_all(self) -> List[BaseTool]:
        """获取所有工具"""
        return list(self._tools.values())
    
    def get_openai_functions(self) -> List[dict]:
        """获取 OpenAI Function Calling 格式的工具列表"""
        return [tool.to_openai_function() for tool in self._tools.values()]
    
    def get_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())
    
    def get_tool_descriptions(self) -> str:
        """获取工具描述摘要（用于 System Prompt）"""
        descriptions = []
        for tool in self._tools.values():
            descriptions.append(f"- {tool.name}: {tool.description.split('.')[0]}")
        return "\n".join(descriptions)
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """
        获取所有工具的熔断器状态
        
        Returns:
            {tool_name: status_dict}
        """
        status = {}
        for name, tool in self._tools.items():
            circuit_status = tool.get_circuit_status()
            if circuit_status:
                status[name] = circuit_status
        return status
    
    def get_degraded_tools(self) -> List[str]:
        """
        获取当前被熔断的工具列表
        
        Returns:
            被熔断的工具名称列表
        """
        degraded = []
        for name, tool in self._tools.items():
            if tool.breaker and tool.breaker.is_open:
                degraded.append(name)
        return degraded
    
    def get_available_tools_prompt(self) -> str:
        """
        获取当前可用工具的描述（排除熔断的工具）
        用于动态更新 System Prompt
        """
        descriptions = []
        degraded = self.get_degraded_tools()
        
        for tool in self._tools.values():
            if tool.name in degraded:
                descriptions.append(f"- {tool.name}: ⚠️ 服务暂时不可用，请勿调用")
            else:
                descriptions.append(f"- {tool.name}: {tool.description.split('.')[0]}")
        
        return "\n".join(descriptions)


# 全局工具注册中心实例
tool_registry = ToolRegistry()


def get_all_tools() -> List[BaseTool]:
    """获取所有注册的工具"""
    return tool_registry.get_all()


def get_circuit_status() -> Dict[str, Any]:
    """获取所有熔断器状态"""
    return tool_registry.get_circuit_breaker_status()


def get_degraded_tools() -> List[str]:
    """获取被熔断的工具列表"""
    return tool_registry.get_degraded_tools()

