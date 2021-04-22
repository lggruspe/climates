import setuptools

with open("README.md") as fp:
    long_description = fp.read()

setuptools.setup(
    name="climates",
    version="0.0.4",
    author="Levi Gruspe",
    author_email="mail.levig@gmail.com",
    description="Command-line interfaces made accessible to even simpletons",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lggruspe/climates",
    packages=setuptools.find_packages(),
    package_data={
        "climates": ["py.typed"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
    ],
    install_requires=["infer_parser==0.0.1"],
    python_requires=">=3.8",
)
