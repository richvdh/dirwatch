import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dirwatch",
    version="0.1.0",
    author="Richard van der Hoff",
    author_email="python@richvdh.org",
    description="Watches a directory and runs a command when it is updated",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/richvdh/dirwatch",
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=["inotify>=0.2.10"],
    entry_points={"console_scripts": ["dirwatch = dirwatch.__main__:main"]},
)
