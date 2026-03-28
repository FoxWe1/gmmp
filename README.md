# GMMP

> 一个基于 HelloAgents 的论文检索与下载 Agent，有记忆功能，能自动整理并恢复历史记忆，支持自主选择工具，搜索论文、下载 PDF，下载的内容构造本地知识库+RAG，RAG会持续增长、根据RAG问答问题。

## 📝 项目简介

- 作为研究僧，手动检索文档复杂低效；对于本地论文无法使用大模型进行高效检索和问答
- 使用Agent，自动根据需求对论文进行查找、下载、构建知识库、问答
- 适用于广大研究生同志

## ✨ 核心功能

- [✅] 功能1:根据用户提出的文献内容，自主搜索文献
- [ ] 功能2:根据搜索结果，用户决定下载指定论文
- [ ] 功能2:根据本地RAG，对用户提的问题进行搜索和回答
- [ ] 功能3:Agent有记忆功能，能自动整理并恢复历史记忆

## 🛠️ 技术栈

- HelloAgents框架
- 使用的智能体范式：ReAct
- 使用的工具和API
- 其他依赖库

## 🚀 快速开始

### 环境要求

- Python 3.10+
- 其他要求
- ollama run qwen3:4b (启动本地ollama大模型)

### 安装依赖

pip install -r requirements.txt

### 配置API密钥


# 创建.env文件
cp .env.example .env

# 编辑.env文件，填入你的API密钥


### 运行项目


# 启动Jupyter Notebook
jupyter lab

# 打开main.ipynb并运行


## 📖 使用示例

展示如何使用你的项目，最好包含代码示例和运行结果。

## 🎯 项目亮点

- 亮点1:说明
- 亮点2:说明
- 亮点3:说明

## 📊 性能评估

如果有评估结果，展示在这里:
- 准确率:XX%
- 响应时间:XX秒
- 其他指标

## 🔮 未来计划

- [ ] 待实现的功能1
- [ ] 待实现的功能2
- [ ] 待优化的部分

## 🤝 贡献指南

欢迎提出Issue和Pull Request！

## 📄 许可证

MIT License

## 👤 作者

- GitHub: [@FoxWe1](https://github.com/FoxWe1)
- Email: foxwe1@163.com

## 🙏 致谢

感谢Datawhale社区和Hello-Agents项目！