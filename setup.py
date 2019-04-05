import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rain_and_wind_auto_park",
    version="0.0.1",
    author="Hazal Goksu, Dominik Neise",
    author_email="",
    description="",
    long_description=long_description,
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'auto_park=rain_and_wind_auto_park.script:entry'
        ],
    },
    install_requires=[
        'docopt',
    ]

)
