from setuptools import setup

version = "0.0.3"


setup(
    name="fastavro-gen",
    version=version,
    description="Generation of classes from Avro schemas",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Guðjón Ragnar Brynjarsson",
    license="MIT",
    url="https://github.com/gudjonragnar/fastavro-gen",
    packages=["fastavro_gen"],
    entry_points={
        "console_scripts": [
            "fastavro_gen = fastavro_gen.__main__:main",
        ]
    },
    classifiers=[],
    python_requires=">=3.8",
    extras_require={
        "codecs": ["python-snappy", "zstandard", "lz4"],
        "snappy": ["python-snappy"],
        "zstandard": ["zstandard"],
        "lz4": ["lz4"],
    },
    install_requires=["fastavro>=1.3.0", "black"],
    tests_require=["pytest", "mypy"],
    package_data={"fastavro_gen": ["py.typed"]},
)
