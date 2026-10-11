"""The public address book: what a search engine finds of the Stargate pages.

The dialing computer is drawn in the browser, so these pages are the only part
of it a search engine can read.

@tagged post_install because an HttpCase needs the full registry.
"""

import re

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('-at_install', 'post_install')
class TestAddressBook(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Glyph = cls.env['stargate.glyph']
        cls.glyphs = [Glyph.create({
            'name': 'Test Constellation %s' % n,
            'number': 900 + n,
            'gate_type': 'milky_way',
        }) for n in range(7)]
        cls.planet = cls.env['stargate.planet'].create({
            'name': 'Test Haven',
            'designation': 'P0T-001',
            'summary': 'A quiet world used to test the address book.',
            **{'glyph_%s_id' % (i + 1): g.id for i, g in enumerate(cls.glyphs[:6])},
            'point_of_origin_id': cls.glyphs[6].id,
        })

    def assertLinks(self, path, body):
        # A language prefix (/en, /fr) depends on the site, not on this module.
        self.assertRegex(body, r'href="(/[a-z]{2}(_[A-Z]{2})?)?%s"' % re.escape(path))

    def _get(self, url):
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200, url)
        return response.text

    def test_slug_comes_from_the_name_and_stays(self):
        self.assertEqual(self.planet.slug, 'test-haven')
        self.planet.name = 'Test Haven Renamed'
        self.assertEqual(self.planet.slug, 'test-haven',
                         "renaming must not move a page search engines know")

    def test_the_book_lists_every_destination(self):
        body = self._get('/stargate/addresses')
        self.assertIn('<h1', body)
        self.assertLinks('/stargate/addresses/test-haven', body)
        self.assertIn('<meta name="description"', body)

    def test_a_destination_page_carries_its_address(self):
        body = self._get('/stargate/addresses/test-haven')
        title = re.search(r'<title>([^<]*)</title>', body).group(1)
        self.assertIn('Test Haven', title)
        self.assertIn('content="A quiet world used to test the address book."', body)
        self.assertIn('rel="canonical" href="', body)
        # the glyphs in dialing order, then the point of origin
        numbers = re.findall(r'o_sg_glyph_card__number">(\d+)<', body)
        self.assertEqual(numbers, [str(900 + n) for n in range(7)])
        self.assertLinks('/stargate?address=test-haven', body)

    def test_an_unknown_destination_is_the_site_404(self):
        response = self.url_open('/stargate/addresses/no-such-world')
        self.assertEqual(response.status_code, 404)
        self.assertIn('<html', response.text, "the site's 404 page, not a bare one")

    def test_the_pages_are_declared_in_the_sitemap(self):
        website = self.env['website'].sudo().search([], limit=1)
        self.env['ir.attachment'].sudo().search(
            [('url', '=like', '/sitemap%'), ('website_id', '=', website.id)]).unlink()
        sitemap = self._get('/sitemap.xml')
        self.assertIn('/stargate/addresses</loc>', sitemap)
        self.assertIn('/stargate/addresses/test-haven</loc>', sitemap)

    def test_the_dialing_computer_is_named_for_search_engines(self):
        body = self._get('/stargate')
        self.assertIn('<meta name="description"', body)
        self.assertIn('<h1', body)
        self.assertLinks('/stargate/addresses', body)

    def test_the_public_data_carries_the_slug(self):
        planets = self.url_open('/stargate/data').json()['planets']
        self.assertIn('test-haven', [p['slug'] for p in planets])


@tagged('standard', 'at_install')
class TestPlanetSummaries(TransactionCase):

    def test_summaries_do_not_overwrite_a_written_one(self):
        from odoo.addons.chti_stargate.hooks import set_planet_summaries
        abydos = self.env.ref('chti_stargate.planet_abydos')
        abydos.summary = 'Written by hand.'
        set_planet_summaries(self.env)
        self.assertEqual(abydos.summary, 'Written by hand.')
