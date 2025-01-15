from setuptools import setup, find_packages

setup(
    name="quiz_bot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot>=20.0",
        "deep-translator>=1.10.0",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.8.0",
    ],
) 