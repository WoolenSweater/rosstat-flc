from setuptools import setup, find_packages

setup(
    name='rosstat-flc',
    version='0.2.1',
    author='Nikita Ryabinin',
    install_requires=['lxml', 'ply'],
    url='https://github.com/WoolenSweater/rosstat_flc',
    packages=find_packages()
)
