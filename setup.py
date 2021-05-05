import setuptools

with open("README.md") as fp:
    long_description = fp.read()

setuptools.setup(
    name="climux",
    version="0.1.0",
    author="Levi Gruspe",
    author_email="mail.levig@gmail.com",
    description="Library for writing command-line interfaces",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lggruspe/climux",
    packages=setuptools.find_packages(exclude=["tests"]),
    package_data={
        "climux": ["py.typed"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
    ],
    install_requires=["infer_parser==0.1.1"],
    python_requires=">=3.7",
)
