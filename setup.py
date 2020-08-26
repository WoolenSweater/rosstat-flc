from setuptools import setup, find_packages

setup(
    name='rosstat-flc',
    version='0.4.0',
    author='Nikita Ryabinin',
    install_requires=['lxml', 'ply'],
    url='https://github.com/WoolenSweater/rosstat_flc',
    packages=find_packages()
)
