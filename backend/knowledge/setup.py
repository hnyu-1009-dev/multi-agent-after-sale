from pathlib import Path

from setuptools import find_packages, setup


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent


setup(
    name="knowledge",
    version="0.1.0",
    package_dir={"": str(PROJECT_ROOT)},
    packages=find_packages(
        where=str(PROJECT_ROOT),
        include=["knowledge", "knowledge.*"],
    ),
    install_requires=[
        "fastapi",
        "uvicorn",
        "requests",
        "python-dotenv",
        "langchain-core",
        "langchain-community",
        "langchain-openai",
        "langchain-chroma",
        "pydantic-settings",
        "markdownify",
        "scikit-learn",
        "jieba",
        "unstructured",
        "markdown",
    ],
)
