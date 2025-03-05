from setuptools import setup, find_packages

setup(
    name='agent-tooling',
    version='0.1.0',
    author='Your Name',
    author_email='daniel.stewart77@gmail.com',
    description='A lightweight tool registry for function metadata management',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/danielstewart77/agent-tooling',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.8',
    keywords='tools metadata function-registry ai-agents',
    install_requires=[
        # Add any dependencies here
    ],
    extras_require={
        'dev': [
            'pytest',
            'twine',
            'build',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/danielstewart77/agent-tooling/issues',
        'Source': 'https://github.com/danielstewart77/agent-tooling',
    },
)