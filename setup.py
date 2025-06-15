from setuptools import setup, find_packages

setup(
    name='torrent_agent',
    version='0.1.0',  # Or your desired version
    description='Home media torrent utility agent',
    author='Your Name',  # Replace with your name
    author_email='your.email@example.com',  # Replace with your email
    packages=find_packages(),
    install_requires=[
        'mysql-connector-python',
        'prometheus-client',
        'asyncio',       # <--- Add this line
        'python-dotenv', # <--- Add this line
        'opencv-python', # <--- Add this line
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',  # Or appropriate status
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  # Or your license
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    entry_points={
        'console_scripts': [
            'torrent_agent=torrent_agent.torrent_agent:main',  # Corrected module name
        ],
    },
)