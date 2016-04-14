import setuptools

ARGS = dict(
    name='metamod',
    version='0.0.1',
    description='ORM that uses __slots__ (for memory saving), plain DBAPI2 connections (to not break threading) and assumes the user knows SQL',
    author='Abe Winter',
    author_email='internal-software@outlin.es',
    url='https://outlin.es',
    license='MIT',
    packages=['metamod'],
    install_requires=['six', 'pytest'],
    entry_points={'console_scripts':[]},
)

if __name__ == '__main__':
    setuptools.setup(**ARGS)
