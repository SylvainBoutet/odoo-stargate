from markupsafe import Markup

from odoo import _, http  # noqa: F401
from odoo.http import request

# Coordinate glyph fields exposed to the public dialing computer.
COORDINATE_FIELDS = [
    'glyph_1_id', 'glyph_2_id', 'glyph_3_id',
    'glyph_4_id', 'glyph_5_id', 'glyph_6_id', 'glyph_7_id',
]


# The destination pages take a free-text slug, which Odoo cannot enumerate:
# without these functions they never reach sitemap.xml.
def sitemap_addresses(env, rule, qs):
    if not qs or qs.lower() in '/stargate/addresses':
        yield {'loc': '/stargate/addresses'}


def sitemap_address(env, rule, qs):
    for planet in env['stargate.planet'].sudo().search([('slug', '!=', False)]):
        loc = '/stargate/addresses/%s' % planet.slug
        if not qs or qs.lower() in loc:
            yield {'loc': loc, 'lastmod': planet.write_date.date()}


class StargatePublic(http.Controller):
    """Public, login-free access to the immersive dialing computer."""

    # website=True is what puts request.website in the rendering values.
    # Without it web.frontend_layout raises KeyError: 'website' as soon
    # as a website theme is installed -- the page renders until it does
    # not, and the cause is nowhere near the symptom.
    @http.route('/stargate', type='http', auth='public', website=True,
                sitemap=True)
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
            ['name', 'slug', 'designation', 'address_display']
            + COORDINATE_FIELDS + ['point_of_origin_id'],
            order='name',
        )
        return request.make_json_response({'glyphs': glyphs, 'planets': planets})

    @http.route('/stargate/addresses', type='http', auth='public',
                website=True, sitemap=sitemap_addresses)
    def address_book(self, **kw):
        planets = request.env['stargate.planet'].sudo().search([('slug', '!=', False)])
        glyphs = request.env['stargate.glyph'].sudo().search(
            [('gate_type', '=', 'milky_way')], order='number')
        return request.render('chti_stargate.address_book_page', {
            'planets': planets,
            'glyphs': glyphs,
            'svgs': self._glyph_svgs(glyphs),
            'page_title': request.env._("Stargate addresses"),
        })

    @http.route('/stargate/addresses/<string:slug>', type='http', auth='public',
                website=True, sitemap=sitemap_address)
    def address_page(self, slug, **kw):
        Planet = request.env['stargate.planet'].sudo()
        planet = Planet.search([('slug', '=', slug)], limit=1)
        if not planet:
            # Raised, not returned: the site's own 404 page, not a bare one.
            raise request.not_found()
        others = Planet.search([('slug', '!=', False), ('id', '!=', planet.id)])
        coordinates, origin = planet._address_glyphs()
        return request.render('chti_stargate.address_page', {
            'planet': planet,
            'coordinates': coordinates,
            'origin': origin,
            'others': others,
            'svgs': self._glyph_svgs(request.env['stargate.glyph'].sudo().browse(
                [g.id for g in coordinates] + origin.ids)),
            'page_title': request.env._("%(name)s: Stargate address", name=planet.name),
            # The destination, not the view, names the page: title,
            # description and share data come from it.
            'main_object': planet,
        })

    @staticmethod
    def _glyph_svgs(glyphs):
        # The shapes ship with the module (data file, Wikimedia Commons), they
        # are not user input: safe to render as markup.
        return {glyph.id: Markup(glyph.svg) for glyph in glyphs if glyph.svg}
