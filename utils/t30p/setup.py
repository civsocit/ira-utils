import sys
from setuptools import setup

try:
    import py2exe
except ImportError:
    if len(sys.argv) >= 2 and sys.argv[1] == 'py2exe':
        print('Cannot import py2exe', file=sys.stderr)
        exit(1)

if len(sys.argv) >= 2 and sys.argv[1] == 'py2exe':
    params = {
        'console': ['t30p.py'],
        'options': {
            'py2exe': {
                'includes': ['aiohttp'],
                'bundle_files': 1,
                'compressed': 1,
                'optimize': 2,
            },
        },
        'zipfile': None,
    }
else:
    params = {
        'scripts': ['t30p.py'],
    }

setup(
    name='t30p',
    version='0.0.1',
    url='https://github.com/civsocit/ira-utils',
    python_requires='>=3.6',
    install_requires=[
        'aiohttp',
    ],
    **params
)
