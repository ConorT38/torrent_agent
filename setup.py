from setuptools import setup, find_packages

setup(
    name='torrent_agent',
    version='0.1.0',  
    description='Home media torrent utility agent',
    author='Conor Thompson',  
    author_email='github.com/ConorT38',  
    packages=find_packages(),
    install_requires=[
        'mysql-connector-python',
        'prometheus-client',
        'asyncio',      
        'python-dotenv', 
        'opencv-python', 
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',  
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    entry_points={
        'console_scripts': [
            'torrent_agent=torrent_agent.torrent_agent:main', 
        ],
    },
)