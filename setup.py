from setuptools import setup

setup(
    name="my-azure-tts",
    version="0.0.1",
    requires=["pydub","websockets","requests"],
    # download_url="",
    packages=["mytts"]
)