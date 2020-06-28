from setuptools import setup, find_packages

package_name = "drivedl"

with open("README.md", "r") as f:
    readme = f.read()

setup(
    name="drivedl",
    version="1.2",
    description="Download files from Google Drive (inclusive of teamdrives, shared with me and my drive) concurrently.",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/architdate/drivedl",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "google-api-python-client",
        "google-auth-httplib2",
        "google-auth-oauthlib",
        "tqdm",
        "colorama"
    ],
    license='MIT',
    zip_safe=False,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    author="Archit Date",
    author_email="architdate@gmail.com",
    entry_points={
        'console_scripts': [
            'drivedl=drivedl.drivedl:main',
        ],
    },
)