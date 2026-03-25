


class PaperDownloadTool(Tool):
    def __init__(self):
        super().__init__("paper_download", "下载学术论文PDF")

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="input", type="string", description="PDF链接或页面地址", required=True),
            ToolParameter(name="dest_dir", type="string", description="保存目录", required=False, default="./downloads"),
            ToolParameter(name="filename", type="string", description="保存文件名", required=False, default=None),
        ]

    def run(self, parameters: Dict[str, Any]) -> str:
        url = (parameters.get("input") or "").strip()
        dest_dir = parameters.get("dest_dir", "./downloads") or "./downloads"
        filename = parameters.get("filename")
        if not url:
            return "错误：请输入下载链接"
        if "arxiv.org/abs/" in url:
            url = url.replace("/abs/", "/pdf/") + ".pdf"
        if not filename:
            base = os.path.basename(urllib.parse.urlparse(url).path)
            if not base or not base.endswith(".pdf"):
                base = f"paper_{int(time.time())}.pdf"
            filename = base
        try:
            os.makedirs(dest_dir, exist_ok=True)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                final_name = filename if filename.endswith(".pdf") else f"{filename}.pdf"
                path = os.path.join(dest_dir, final_name)
                with open(path, "wb") as f:
                    shutil.copyfileobj(resp, f)
            return json.dumps({"path": os.path.abspath(path), "url": url}, ensure_ascii=False)
        except Exception as e:
            return f"错误：下载失败：{e}"

if __name__ == "__main__":
    tool = PaperDownloadTool()
    print(tool.run({"input": "https://arxiv.org/pdf/2305.04242.pdf"}))