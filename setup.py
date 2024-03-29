from setuptools import setup, find_packages

setup(
    name='rosstat-flc',
    version='1.3.1',
    packages=find_packages(),
    description='Tool for format-logistic control of reports sent to RosStat',
    long_description=open('README.md', 'r').read(),
    long_description_content_type="text/markdown",
    author='Nikita Ryabinin',
    author_email='ryabinin.ne@gmail.com',
    license='MIT',
    license_file='LICENSE',
    url='https://github.com/WoolenSweater/rosstat_flc',
    install_requires=['lxml', 'ply'],
    python_requires='>=3.7',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: Russian',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Information Analysis'
    ],
    keywords=[
        'control',
        'flc',
        'format-logistic',
        'processing',
        'russian-specific',
        'report',
        'rosstat'
    ]
)
