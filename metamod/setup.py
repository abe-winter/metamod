import setuptools

ARGS = dict(
    name='metamod',
    version='0.0.0', # todo: include git version and read VERSION from an init file
    description='ORM that uses __slots__ (for memory saving), plain DBAPI2 connections (to not break threading) and assumes the user knows SQL',
    author='Abe Winter',
    author_email='internal-software@outlin.es',
    url='https://outlin.es',
    license='INTERNAL USE ONLY. DO NOT PUBLISH, DO NOT SHARE',
    packages=['metamod'],
    install_requires=['six', 'pytest'],
    entry_points={'console_scripts':[]},
)

if __name__ == '__main__':
    setuptools.setup(**ARGS)
