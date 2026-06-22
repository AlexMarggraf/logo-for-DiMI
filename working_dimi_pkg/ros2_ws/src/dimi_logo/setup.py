from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'dimi_logo'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('lib', 'python3.10', 'site-packages', package_name),
        glob(os.path.join(package_name, '*.lark')) + 
        glob(os.path.join(package_name, '*.json'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'server = dimi_logo.server:main'
        ],
    },
)
