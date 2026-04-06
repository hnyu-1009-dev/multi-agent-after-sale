from pathlib import Path

from setuptools import find_packages, setup


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent


setup(
    name="its_app",
    version="0.1.0",
    package_dir={"": str(PROJECT_ROOT)},
    packages=find_packages(
        where=str(PROJECT_ROOT),
        include=["app", "app.*"],
    ),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-dotenv",
        "pydantic",
        "pydantic-settings",
        "openai",
        "openai-agents",
        "pymysql",
        "dbutils",
        "pystun3",
    ],
)
