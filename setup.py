from setuptools import setup


with open('requirements.txt') as f:
    install_requires = f.read().splitlines()


setup(
    name='jwallet-assets-tools',
    version='0.0.1',
    description='Jwallet assets tools (validator)',
    packages=[
        'jwallet_tools',
        'jwallet_tools.assets_validator',
        'jwallet_tools.blockexplorer',
    ],
    zip_safe=False,
    platforms='any',
    install_requires=install_requires,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'jwallet-assets-tools=jwallet_tools.__main__:main',
        ]
    }
)
