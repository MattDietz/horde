from distutils.core import setup

from pip.req import parse_requirements

def install_path(path):
    install_reqs = parse_requirements(path, session=False)
    return [str(ir.req) for ir in install_reqs]


setup(name='Horde',
      version='0.01',
      description='Extensible parallel testing framework',
      author='Matt Dietz',
      author_email='matthew.dietz@gmail.com',
      install_requires=install_path("requirements.txt"),
      test_requires=install_path("test-requirements.txt"),
     )
