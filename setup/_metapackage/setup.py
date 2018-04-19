import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-vertical-construction",
    description="Meta package for oca-vertical-construction Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-base_construction_architect',
        'odoo8-addon-crm_construction_architect',
        'odoo8-addon-crm_construction_calculator',
        'odoo8-addon-crm_construction_site',
        'odoo8-addon-project_construction_architect',
        'odoo8-addon-project_construction_site',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
