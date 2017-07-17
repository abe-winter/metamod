import setuptools

ARGS = dict(
    name='metamod',
    version='0.0.4',
    description='ORM that uses __slots__ (for memory saving), plain DBAPI2 connections (to not break threading) and assumes the user knows SQL',
    author='Abe Winter',
    author_email='awinter.public@gmail.com',
    url='https://github.com/abe-winter/metamod',
    license='MIT',
    packages=['metamod'],
    install_requires=['six', 'pytest'],
    entry_points={'console_scripts':[]},
)

if __name__ == '__main__':
    setuptools.setup(**ARGS)
