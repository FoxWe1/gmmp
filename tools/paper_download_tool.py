
import os
import re
from typing import Any, Dict, List

import requests

from hello_agents.tools.base import Tool, ToolParameter


class PaperDownloadTool(Tool):
    def __init__(self):
        super().__init__("paper_download_tool", "从arxiv下载学术论文PDF")

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="input", type="string", description="arXiv ID 或论文页面/PDF链接", required=True),
            ToolParameter(name="dest_dir", type="string", description="保存目录", required=False, default="./knowledge_base/papers"),
        ]

    def run(self, parameters: Dict[str, Any]) -> str:
        input_value = (parameters.get("input") or "").strip()
        dest_dir = (parameters.get("dest_dir") or "./knowledge_base/papers").strip() or "../knowledge_base/papers"

        if not input_value:
            return "错误：请输入 arXiv ID 或链接"

        if input_value.startswith("http://") or input_value.startswith("https://"):
            url_parts = input_value.split("/")
            arxiv_id = url_parts[-1] if url_parts else ""

            pdf_url = input_value.replace("/abs/", "/pdf/")
            if not pdf_url.lower().endswith(".pdf"):
                pdf_url = pdf_url + ".pdf"
        else:
            arxiv_id = input_value
            pdf_url = f"http://arxiv.org/pdf/{arxiv_id}.pdf"

        arxiv_id = re.sub(r"\.pdf$", "", (arxiv_id or "").strip(), flags=re.IGNORECASE)
        clean_arxiv_id = re.sub(r"v\d+$", "", arxiv_id)

        os.makedirs(dest_dir, exist_ok=True)
        pdf_path = os.path.join(dest_dir, f"{clean_arxiv_id}.pdf")

        if os.path.exists(pdf_path):
            print(f"PDF 文件已存在: {pdf_path}")
            return pdf_path

        print(f"正在下载 PDF: {pdf_url}")

        try:
            with requests.get(
                pdf_url,
                stream=True,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ArXiv-MCP-Server/1.0)"},
            ) as resp:
                resp.raise_for_status()
                with open(pdf_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            f.write(chunk)
            print(f"PDF 下载完成: {pdf_path}")
            return pdf_path
        except Exception as e:
            print(f"PDF 下载失败: {e}")
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except Exception:
                    pass
            return f"错误：下载失败：{e}"


if __name__ == "__main__":
    tool = PaperDownloadTool()
    print(tool.run({"input": "https://arxiv.org/abs/2305.04242"}))
    # print(tool.run({"input": "2305.04242v1"}))