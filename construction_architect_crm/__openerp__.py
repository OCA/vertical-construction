# -*- coding: utf-8 -*-
{
    'name': "OCA Construction: Architect CRM",

    'summary': """
        Indicate the architect of an opportunity.""",

    'description': """
        This module allows you to:
            - Identify the architect of a lead/opportunity.
            - Filter/group/search opportunities by architect.
    """,

    'author': "Mathias Colpaert",

    'category': "construction",

    'version': '0.1',

    'depends': ['crm', 'construction_architect_base'],

    'data': ['views.xml'],
}