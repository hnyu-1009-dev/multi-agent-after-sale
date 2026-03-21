from setuptools import setup, find_packages

# 启动之前需要的操作都可以写入这里
setup(
    name="knowledge",
    version="0.1.0",
    packages=find_packages(),
    # 如果没有requirements.txt的备选，运行后会下载到虚拟环境

    # install_requires=[
    #     "fastapi",
    #     "uvicorn",
    #     "requests",
    #     "python-dotenv",
    #     "langchain-core",
    #     "langchain-community",
    #     "langchain-openai",
    #     "langchain-chroma",
    #     "pydantic-settings",
    #     "markdownify",
    #     "scikit-learn",
    #     "jieba",
    #     "unstructured",
    #     "markdown",
    # ],
)
