from setuptools import setup, find_packages

setup(
    name='rosstat-flc',
    version='0.7.2',
    description='Tool for format-logistic control of reports sent to RosStat',
    long_description=open('README.md', 'r').read(),
    long_description_content_type="text/markdown",
    author='Nikita Ryabinin',
    author_email='ryabinin.ne@gmail.com',
    install_requires=['lxml', 'ply'],
    url='https://github.com/WoolenSweater/rosstat_flc',
    packages=find_packages(),
    python_requires='>=3.7'
)
