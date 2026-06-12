{
    'name': "Chti Stargate",
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'summary': "Stargate address book: glyphs, gate addresses and a dialing computer (CHTI-TECH).",
    'description': """
Stargate Address Book
=====================

Manage Stargate destinations the way SG-1 does:

* The 39 canonical Milky Way glyphs (constellations + point of origin).
* Gate addresses as ordered glyph sequences (6 coordinates + point of origin).
* A catalog of known planets/destinations from the show.
* A dialing log to keep the history of every connection.

Backend management first; an immersive OWL "Dialing Computer" interface
(reproducing the on-screen dialing computer) comes next.
""",
    'author': "CHTI-TECH",
    'website': "https://chti-tech.fr",
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/stargate_glyph_data.xml',
        'data/stargate_glyph_svg_data.xml',
        'data/stargate_planet_data.xml',
        'views/stargate_glyph_views.xml',
        'views/stargate_planet_views.xml',
        'views/stargate_dial_log_views.xml',
        'views/stargate_dialing_computer.xml',
        'views/stargate_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'chti_stargate/static/src/dialing_computer/dialing_computer.scss',
            'chti_stargate/static/src/dialing_computer/dialing_computer.js',
            'chti_stargate/static/src/dialing_computer/dialing_computer.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
