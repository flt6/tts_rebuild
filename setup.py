from setuptools import setup

setup(
    name="my-azure-tts",
    version="0.0.1",
    install_requires=["pydub","websockets","requests","rich"],
    # download_url="",
    packages=["mytts"]
)