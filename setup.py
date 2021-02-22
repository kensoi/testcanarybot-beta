import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="testcanarybot",
    version="0.993",
    author="andprokofieff",
    author_email="prokofieff.help@gmail.com",
    description="VKontakte asynchronous bot framework like Django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kensoi/testcanarybot",
    packages = setuptools.find_packages(exclude=('assets', 'assets.*', 'examples', 'examples.*', 'library', 'library.*', 'modules', 'modules.*')),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires = ["aiohttp"],
    python_requires='>=3.7',
)
