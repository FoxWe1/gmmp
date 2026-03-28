import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import requests

from hello_agents.tools.base import Tool,ToolParameter
from typing import Dict, Any, List
import json


class PaperSearchTool(Tool):
    def __init__(self):
        super().__init__(name="paper_search_tool", description="一个arxiv论文搜索工具，根据关键字从arxiv学术数据库搜索论文信息")

    def get_parameters(self) -> List[ToolParameter]:
        '''
        声明该工具的“参数规范"
        用于ToolRegistry通过get_tools_description调用，获得工具的参数信息
        用于支持FunctionCalling
        '''
        return [
            ToolParameter(name="input", type="string", description="检索关键词；也支持形如：'diffusion models | 8' 指定返回条数", required=True),
            ToolParameter(name="max_results", type="integer", description="返回条数（仅在结构化调用时生效；默认 2）", required=False, default=2),
            ToolParameter(name="start", type="integer", description="起始偏移（默认 0）", required=False, default=0) # 分页，从第几条搜索结果开始返回
        ]

    def run(self, parameters: Dict[str, Any]) -> str:
        raw = (parameters.get("input") or "").strip()
        if not raw:
            return "错误：搜索关键词不能为空"
        # 1. 对要查询的进行解析
        # 对查询的输入进行解析，提取查询关键词和返回条数
        query, inline_max = self._parse_inline_query(raw)
        max_results = inline_max if inline_max is not None else int(parameters.get("max_results", 5) or 5)
        start = int(parameters.get("start", 0) or 0)
        
        # 2. 执行搜索
        try:
            payload = self._search_arxiv(query=query, start=start, max_results=max_results)
            print(json.dumps(payload, ensure_ascii=False,indent=2))
            return json.dumps(payload, ensure_ascii=False)
        except Exception as e:
            return f"错误：arXiv 搜索失败：{e}"

    def _parse_inline_query(self, text: str) -> tuple[str, Optional[int]]:
        '''
        "diffusion models | 8" 表示搜索关键词 "diffusion models"，返回 8 条结果
        解析出来返回关键词和返回条数，默认返回 1 条结果
        '''
        m = re.match(r"^(.*)\|\s*(\d+)\s*$", text)
        if not m:
            return text, None
        query = m.group(1).strip()
        limit = int(m.group(2))
        return query, max(1, min(limit, 50))

    def _search_arxiv(self, *, query: str, start: int, max_results: int) -> Dict[str, Any]:
        '''
        搜索arxiv论文数据库
        支持按照关键词搜索，也支持按照关键词+返回条数的格式搜索
        例如："diffusion models | 8" 表示搜索关键词 "diffusion models"，返回 8 条结果
        '''
        search_query = f"all:{query}"
        if " " in query and '"' not in query:
            search_query = f'all:"{query}"'

        params = {
            "search_query": search_query,
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        resp = requests.get(
            "https://export.arxiv.org/api/query",
            params=params,
            headers={"User-Agent": "HelloAgents/1.0"},
            timeout=20,
        )
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        ns = {
            "a": "http://www.w3.org/2005/Atom",
            "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
        }
        # 统计查询在 arxiv 一共匹配到多少篇论文
        total_text = root.findtext("opensearch:totalResults", default="0", namespaces=ns)
        total_results = int(total_text) if (total_text or "0").isdigit() else 0

        papers: list[dict[str, Any]] = []
        for entry in root.findall("a:entry", ns):
            abs_url = (entry.findtext("a:id", default="", namespaces=ns) or "").strip()
            title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
            summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip()
            published = (entry.findtext("a:published", default="", namespaces=ns) or "").strip()

            authors = []
            for author in entry.findall("a:author", ns):
                name = (author.findtext("a:name", default="", namespaces=ns) or "").strip()
                if name:
                    authors.append(name)

            pdf_url = ""
            for link in entry.findall("a:link", ns):
                href = (link.attrib.get("href") or "").strip()
                type_ = (link.attrib.get("type") or "").strip()
                title_attr = (link.attrib.get("title") or "").strip().lower()
                if href and (type_ == "application/pdf" or title_attr == "pdf" or href.endswith(".pdf")):
                    pdf_url = href
                    break
            if not pdf_url and abs_url and "/abs/" in abs_url:
                pdf_url = abs_url.replace("/abs/", "/pdf/") + ".pdf"

            arxiv_id = abs_url.rstrip("/").split("/")[-1] if abs_url else ""

            papers.append(
                {
                    "id": arxiv_id,
                    "url": abs_url,
                    "pdf_url": pdf_url,
                    "title": " ".join(title.split()),
                    "summary": " ".join(summary.split()),
                    "published": published,
                    "authors": authors,
                }
            )
        print(f"相关论文一共有{total_results}篇")
        # return {"source": "arxiv", "query": query, "start": start, "max_results": max_results, "total_results": total_results, "papers": papers}
        return papers


if __name__ == "__main__":
    tool = PaperSearchTool()
    raw = tool.run({"input": " medical | 1"})
    # data = json.loads(raw)
    # print(json.dumps(data, ensure_ascii=False, indent=2))
    # print(data)