import codecs

from setuptools import setup

with codecs.open('README.md', encoding='utf8') as readme:
    long_description = readme.read()

setup(
    name='clanvas',
    version='0.3.0',
    url='https://github.com/marklalor/clanvas',
    license='MIT',
    author='Mark Lalor',
    author_email='markwlalor@gmail.com',
    install_requires=[
        'canvasapi==0.12.0', 'cmd2==0.9.12', 'tabulate>=0.8.3', 'tree-format>=0.1.2',
        'html2text', 'colorama', 'pytz', 'tzlocal'
    ],
    extras_require={
        'dev': ['requests-mock'],
    },
    packages=['clanvas'],
    entry_points={'console_scripts': ['clanvas = clanvas.clanvas:main']},
    description='Command-line client for Canvas by Instructure',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Topic :: Education',
        'Topic :: System :: Shells',
        'License :: OSI Approved :: MIT License'
    ]
)
