import setuptools

with open("README.md", "r", encoding='utf8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="streamlit-qs",
    version="0.3.0",
    author="Alexander Martin",
    author_email="fauxjunk-1@yahoo.com",
    description="A small library to add extra functionality on top of streamlit's st.query_params API",
    license="Apache 2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Asaurus1/streamlit-qs",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    package_data={"streamlit_qs": ["py.typed"]},
    install_requires=["streamlit>=1.30.0"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
