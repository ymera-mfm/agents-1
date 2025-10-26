"""
Setup script for YMERA Enterprise Database Core
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="ymera-database-core",
    version="5.0.0",
    description="YMERA Enterprise Database Core - Production-Ready Database Management System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="YMERA Enterprise",
    author_email="dev@ymera.com",
    url="https://github.com/ymera/database-core",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.6.0",
            "ruff>=0.1.0",
        ],
        "api": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.0.0",
        ],
        "postgresql": [
            "asyncpg>=0.29.0",
        ],
        "mysql": [
            "aiomysql>=0.2.0",
        ],
        "all": [
            "asyncpg>=0.29.0",
            "aiomysql>=0.2.0",
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: AsyncIO",
        "Framework :: FastAPI",
        "Operating System :: OS Independent",
    ],
    keywords="database orm sqlalchemy async postgresql mysql sqlite enterprise",
    project_urls={
        "Documentation": "https://docs.ymera.com/database-core",
        "Source": "https://github.com/ymera/database-core",
        "Bug Reports": "https://github.com/ymera/database-core/issues",
    },
    include_package_data=True,
    zip_safe=False,
)
