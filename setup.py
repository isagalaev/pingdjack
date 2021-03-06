from setuptools import setup


setup(
    name='pingdjack',
    version='0.4',
    packages=[
        'pingdjack',
    ],

    author='Ivan Sagalaev',
    author_email='maniac@softwaremaniacs.org',
    description='Library for sites made with Django that implements server and client parts of Pingback protocol',
    url='https://github.com/isagalaev/pingdjack/',
    install_requires = [
        'html5lib',
        'django',
    ]
)
