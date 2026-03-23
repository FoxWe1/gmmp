# GMMP

> 一个基于 HelloAgents 的论文检索与下载 Agent，有记忆，支持自主选择工具，搜索论文、下载 PDF、构建本地知识库并进行 RAG 问答。

目录结构：
见strcture.txt

## Quickstart

### 1) Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment
创建 `.env`（参考 `.env.example`，如有）：

```bash
# LLM
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=optional
OPENAI_MODEL=gpt-4o-mini

# Optional search backends
TAVILY_API_KEY=optional
SERPAPI_API_KEY=optional

# Storage / paths (optional)
KB_DIR=knowledge_base
PAPERS_DIR=knowledge_base/papers
VECTOR_DB_DIR=knowledge_base/vector_db
```

### 3) Run
```bash
python main.py
```

## Usage

### Example prompts
- “帮我搜索 2020 年之后关于 diffusion model 的综述论文，列出 5 篇并下载前 2 篇。”
- “把刚下载的论文构建成本地知识库，然后回答：作者提出的核心贡献是什么？”
- “给我这篇论文的 BibTeX 引用。”

## Tools

### paper_search_tool
- 输入：query / limit / filters（如 year_from/year_to）
- 输出：结构化候选列表（title, authors, year, id, url, pdf_url）

### paper_download_tool
- 输入：arxiv_id 或 pdf_url，download_dir
- 输出：本地文件路径、大小、hash

### paper_rag_tool
- 输入：pdf_path 或 paper_id，chunk_size 等
- 输出：索引构建结果、检索结果、回答

## Configuration
所有配置集中在：
- `.env`：密钥与环境相关配置
- `config.py`：默认参数（目录、chunk 策略、模型选择等）

## Development
### 设计结构
1. 根据要求，选择适合的agent范式：React+Reflection（执行-反思-优化）组合范式；React可以调用工具，Reflection通过memory进行反思

## Roadmap
- [ ] 实现基础ReAct Agent
- [ ] 添加工具调用
- [ ] 集成Memory系统
- [ ] 加入Reflection机制
- [ ] 使用框架重构

## Contributing
欢迎 PR / Issue：
- 新工具（search / download / parser / vector store）
- 新数据源适配（arXiv / PubMed / ACL Anthology / OpenAlex）
- 更稳定的提示词与 tool calling 策略

## License
TBD

## Acknowledgements
- HelloAgents
- arXiv API (export.arxiv.org)