from distutils.core import setup

setup(
    name='skython',
    version='1.0',
    packages=['skython'],
    url='',
    license='MIT',
    author='nick petosa',
    author_email='nick.petosa@gmail.com',
    description='Automated, scheduled, intelligent web scraping server and client.',
    install_requires=['pytest==3.0.6', 'pymongo==3.3.0', "testfixtures==5.1.1", "Flask==0.11.1", "Flask-RESTful==0.3.6", "ordereddict", "requests==2.12.4", "gunicorn==19.7.1", "Flask-Cors==2.1.2"]
)
