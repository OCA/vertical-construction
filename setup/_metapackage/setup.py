import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-vertical-construction",
    description="Meta package for oca-vertical-construction Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-bc3_importer',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
