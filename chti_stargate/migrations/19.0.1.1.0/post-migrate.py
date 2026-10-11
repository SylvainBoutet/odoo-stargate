from odoo import SUPERUSER_ID, api
from odoo.addons.chti_stargate.hooks import add_address_menu, set_planet_summaries


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    set_planet_summaries(env)
    add_address_menu(env)
