from setuptools import setup, find_packages

setup(
    name='ArchesDevTools',
    version='0.1.0',
    author='Adam Cox',
    author_email='adam@legiongis.com',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    scripts=[],
    url='https://github.com/legiongis/arches-dev-tools',
    license='LICENSE.txt',
    description='Extra tools to aid with Arches development process.',
    long_description=open('README.md').read(),
    install_requires=open('requirements.txt').readlines(),
)