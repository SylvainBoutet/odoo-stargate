from odoo import _, http  # noqa: F401
from odoo.http import request

# Coordinate glyph fields exposed to the public dialing computer.
COORDINATE_FIELDS = [
    'glyph_1_id', 'glyph_2_id', 'glyph_3_id',
    'glyph_4_id', 'glyph_5_id', 'glyph_6_id', 'glyph_7_id',
]


class StargatePublic(http.Controller):
    """Public, login-free access to the immersive dialing computer."""

    @http.route('/stargate', type='http', auth='public', sitemap=True)
    def stargate_page(self, **kw):
        return request.render('chti_stargate.dialing_public_page')

    @http.route('/stargate/data', type='http', auth='public', methods=['GET'])
    def stargate_data(self, **kw):
        """Read-only glyphs and gate addresses for the public front-end.

        Served with sudo so no model needs to be exposed to the public user.
        """
        glyphs = request.env['stargate.glyph'].sudo().search_read(
            [('gate_type', '=', 'milky_way')],
            ['number', 'name', 'is_point_of_origin', 'svg'],
            order='number',
        )
        planets = request.env['stargate.planet'].sudo().search_read(
            [],
            ['name', 'designation', 'address_display']
            + COORDINATE_FIELDS + ['point_of_origin_id'],
            order='name',
        )
        return request.make_json_response({'glyphs': glyphs, 'planets': planets})
