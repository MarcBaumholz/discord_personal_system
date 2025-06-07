from setuptools import setup, find_packages

setup(
    name="discord_bots",
    version="0.1.0",
    description="Collection of utility Discord bots",
    author="SideHustl",
    packages=find_packages(),
    install_requires=[
        "discord.py>=2.3.2",
        "python-dotenv>=1.0.0",
        "requests",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 