# This setup.py file is for a Python package named "pii_redactor". It includes metadata about the package, such as its name, version, description, author, and license. It also specifies the required dependencies and entry points for command-line execution. The `find_packages()` function automatically discovers all packages and subpackages in the directory.
# The `install_requires` list specifies the dependencies that need to be installed for the package to work. The `entry_points` section allows you to define console scripts, enabling users to run the package from the command line.

from setuptools import setup, find_packages

setup(
    name="pii_redactor",
    version="1.0.0",
    description="Multilingual PDF PII Redaction Tool using Regex and LLMs",
    author="Manjusha Raavi",
    author_email="manjushaa.raavi@gmail.com",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "streamlit",
        "pandas",
        "openai>=1.0.0",
        "langdetect",
        "python-dotenv",
        "PyMuPDF",
        "pytest",
    ],
    entry_points={
        "console_scripts": [
            "pii-redactor=pii_redactor.main:main",  # This allows CLI execution with `pii-redactor`
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
