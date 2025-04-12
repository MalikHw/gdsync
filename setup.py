from setuptools import setup

setup(
    name="gdsync",
    version="3.0.0",
    author="MalikHw47",
    author_email="help.malicorporation@gmail.com",
    description="Geometry Dash data sync tool",
    py_modules=["gdsync"],
    install_requires=[
        "PyQt6",
    ],
    data_files=[
        ('share/applications', ['debian/gdsync.desktop']),
        ('share/pixmaps', ['debian/gdsync.png']),
        ('share/gdsync/resources', ['resources/banner.png']),
    ],
    entry_points={
        'console_scripts': [
            'gdsync=gdsync:main',
        ],
    },
)
