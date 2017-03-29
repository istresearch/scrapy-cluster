import sys
import re
from setuptools import setup, find_packages


def get_version():
    with open('scutils/version.py') as version_file:
        return re.search(r"""__version__\s+=\s+(['"])(?P<version>.+?)\1""",
                         version_file.read()).group('version')


def readme():
    ''' Returns README.rst contents as str '''
    with open('README.rst') as f:
        return f.read()

install_requires = [
    'python-json-logger==0.1.7',
    'ConcurrentLogHandler>=0.9.1',
    'redis==2.10.5',
    'kazoo>=2.2.1',
    'mock==2.0.0',
    'testfixtures==4.13.5',
    'ujson==1.35',
    'future==0.16.0'
]

lint_requires = [
    'pep8',
    'pyflakes'
]

tests_require = [
    'mock==2.0.0',
    'testfixtures==4.13.5'
]

dependency_links = []
setup_requires = []
extras_require = {
    'test': tests_require,
    'all': install_requires + tests_require,
    'docs': ['sphinx'] + tests_require,
    'lint': lint_requires
}

if 'nosetests' in sys.argv[1:]:
    setup_requires.append('nose')

setup(
    name='scutils',
    version=get_version(),
    description='Utilities for Scrapy Cluster',
    long_description=readme(),
    author='Madison Bahmer',
    author_email='madison.bahmer@istresearch.com',
    license='MIT',
    url='https://github.com/istresearch/scrapy-cluster',
    keywords=['scrapy', 'scrapy-cluster', 'utilities'],
    packages=find_packages(),
    package_data={},
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=setup_requires,
    extras_require=extras_require,
    dependency_links=dependency_links,
    zip_safe=True,
    include_package_data=True,
)
