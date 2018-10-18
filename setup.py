from setuptools import setup

setup(
    name='clanvas',
    version='0.2.3',
    url='https://github.com/marklalor/clanvas',
    license='MIT',
    author='Mark Lalor',
    author_email='markwlalor@gmail.com',
    install_requires=['canvasapi>=0.11,<0.12', 'cmd2<0.10.0', 'tabulate', 'tree-format',
                      'html2text', 'colorama', 'pytz', 'tzlocal'],
    packages=['clanvas'],
    entry_points={'console_scripts': ['clanvas = clanvas.clanvas:main']},
    description='Command-line client for Canvas by Instructure',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Education',
        'Topic :: System :: Shells',
        'License :: OSI Approved :: MIT License'
    ]
)
