from setuptools import setup

setup(
    name="quickquestion",
    version="0.1",
    author="Paul Edwards",
    author_email="paul.edwards@microsoft.com",
    description="A simple command-line tool for quick questions.",
    long_description="A simple command-line tool for quick questions.",
    long_description_content_type="text/plain",
    url="https://github.com/edwardsp/quickquestion",
    py_modules=["qq"],
    install_requires=[
        "openai>=0.28.0",
        "psutil>=5.9.5",
        "pyperclip>=1.8.2",
        "rich>=13.5.3"
    ],
    entry_points={
        "console_scripts": [
            "qq=qq:quickquestion",
        ],
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    # Added to support bdist_wheel
    setup_requires=["setuptools", "wheel"],
)
