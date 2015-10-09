# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Mathias Colpaert
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "OCA Construction: Architect CRM",
    'summary': """Indicate the architect of a lead/opportunity.""",
    'description': """
        This module allows you to:
            - Identify the architect of a lead/opportunity.
            - Filter/group/search opportunities by architect.
    """,
    'author': "Mathias Colpaert, Odoo Community Association (OCA)",
    'category': "construction",
    'version': '8.0.0.1.0',
    'depends': ['crm', 'base_construction_architect'],
    'data': ['views.xml'],
}
