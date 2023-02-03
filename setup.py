from setuptools import setup

setup(
    name="my-azure-tts",
    version="0.0.2",
    install_requires=["pydub","websockets","requests","rich"],
    # download_url="",
    packages=["mytts"]
)