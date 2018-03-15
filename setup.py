from setuptools import setup

setup(
    name='clanvas',
    version='0.1.1',
    url='https://github.com/MarkLalor/Clanvas',
    license='MIT',
    author='Mark Lalor',
    author_email='markwlalor@gmail.com',
    install_requires=['canvasapi', 'cmd2', 'tabulate', 'colorama', 'pytz', 'tzlocal', 'tree-format'],
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
