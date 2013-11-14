import multiprocessing, logging # Fix atexit bug
from setuptools import setup, find_packages


__version__ = '0.0.0-dev'
exec("c=__import__('compiler');a='__version__';l=[];g=lambda:[n.expr.value for"
        " n in l for o in n.nodes if o.name==a].pop();c.walk(c.parseFile('%s/_"
        "_init__.py'),type('v',(object,),{'visitAssign':lambda s,n:l.append(n)"
        "})());exec(a+'=g()');"%'pykismet')


def readme():
    try:
        return open('README.rst').read()
    except:
        pass
    return ''


setup(
        name='pykismet',
        version=__version__,
        author="Jacob Alheid",
        author_email="jacob.alheid@gmail.com",
        description="Python client for Akismet API",
        long_description=readme(),
        url='http://github.com/shakefu/pykismet',
        packages=find_packages(exclude=['test']),
        install_requires=[
            'urllib3',
            'pytool',
            ],
        test_suite='nose.collector',
        tests_require=[
            'nose',
            'mock',
            ],
        )

