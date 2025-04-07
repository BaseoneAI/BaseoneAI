import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()


__version__ = "0.0.0"

REPO_NAME = "BaseoneAI"
AUTHOR_USER_NAME = "BaseoneAI"
SRC_REPO = "BaseoneAI"
AUTHOR_EMAIL = "kamesh.kumar@baseone.uk"


setuptools.setup(
    name=SRC_REPO,
    version=__version__,
    author=AUTHOR_USER_NAME,
    author_email=AUTHOR_EMAIL,
    description="Agentic_Linkedin",
    long_description=long_description,
    long_description_content="text/markdown",
    url=f"https://github.com/{BaseoneAI}/{BaseoneAI}",
    project_urls={
        "Bug Tracker": f"https://github.com/{BaseoneAI}/{BaseoneAI}/issues",
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src")
)