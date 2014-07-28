#!/usr/bin/env python

from distutils.core import setup

setup(name='jaguar',
      version='1.2.0',
      description='Jaguar EVM code compiler, based on python Serpent version.',
      author='Jasper den Ouden (based off Vitalik Buterins Serpent)',
      author_email='o.jasper@gmail.com',
      packages=['jaguar'],
      install_requires=['bitcoin', 'pysha3'],
      scripts=['scripts/serpent']
     )

# TODO
# setup(name='visualize',
#      version='1.2.0',
#      description='Jaguar/LLL code visualizer.',
#      author='Jasper den Ouden',
#      author_email='o.jasper@gmail.com',
#      packages=['visualize'],
#      install_requires=['bitcoin', 'pysha3'],
#      scripts=['scripts/visualize']
#     )
