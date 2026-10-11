from odoo import _, api, fields, models


class StargatePlanet(models.Model):
    """Une destination de la Porte des étoiles : un nom + une adresse (séquence de glyphes)."""

    _name = 'stargate.planet'
    _description = "Stargate Destination"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'website.seo.metadata']
    _order = 'name'

    name = fields.Char(string="Name", required=True, tracking=True)
    designation = fields.Char(
        string="Designation",
        help="SGC catalog code, e.g. P3X-116.",
        tracking=True,
    )
    active = fields.Boolean(default=True)
    gate_type = fields.Selection(
        selection=[
            ('milky_way', "Milky Way"),
            ('pegasus', "Pegasus"),
            ('universe', "Universe"),
        ],
        string="Gate Type",
        default='milky_way',
        tracking=True,
    )
    region = fields.Char(string="Region / Galaxy")
    # The public address book serves one page per destination at
    # /stargate/addresses/<slug>. Set once from the name and kept: renaming a
    # destination must not move a page search engines already know.
    slug = fields.Char(
        string="URL Slug",
        compute='_compute_slug', store=True, readonly=False,
        copy=False, index=True,
    )
    summary = fields.Text(
        string="Public Summary",
        translate=True,
        help="A few sentences shown on the destination's public page and used "
             "as its search engine description.",
    )
    image_1920 = fields.Image(string="Image", max_width=1920, max_height=1920)
    notes = fields.Html(string="Notes")

    # Six coordinate glyphs. glyph_7_id is only used for 8-symbol addresses
    # (e.g. extra-galactic destinations such as Othala).
    glyph_1_id = fields.Many2one('stargate.glyph', string="Glyph 1")
    glyph_2_id = fields.Many2one('stargate.glyph', string="Glyph 2")
    glyph_3_id = fields.Many2one('stargate.glyph', string="Glyph 3")
    glyph_4_id = fields.Many2one('stargate.glyph', string="Glyph 4")
    glyph_5_id = fields.Many2one('stargate.glyph', string="Glyph 5")
    glyph_6_id = fields.Many2one('stargate.glyph', string="Glyph 6")
    glyph_7_id = fields.Many2one('stargate.glyph', string="Glyph 7")
    point_of_origin_id = fields.Many2one(
        'stargate.glyph',
        string="Point of Origin",
        default=lambda self: self._default_point_of_origin(),
    )

    address_display = fields.Char(
        string="Address",
        compute='_compute_address_display',
        store=True,
        help="Coordinate glyphs, then the point of origin.",
    )
    glyph_count = fields.Integer(
        string="Symbols",
        compute='_compute_glyph_count',
    )

    dial_log_ids = fields.One2many('stargate.dial.log', 'planet_id', string="Dial Log")
    dial_count = fields.Integer(string="Dials", compute='_compute_dial_count')
    last_dial = fields.Datetime(string="Last Dialed", compute='_compute_dial_count')

    mission_ids = fields.One2many('stargate.mission', 'planet_id', string="Missions")
    mission_count = fields.Integer(string="Missions", compute='_compute_mission_count')

    _slug_unique = models.Constraint('UNIQUE(slug)', "Destination URL slug must be unique.")

    def _default_point_of_origin(self):
        # Earth's point of origin (glyph 01). Safe before data is loaded.
        return self.env.ref('chti_stargate.glyph_01', raise_if_not_found=False)

    @property
    def _coordinate_fields(self):
        return [
            'glyph_1_id', 'glyph_2_id', 'glyph_3_id',
            'glyph_4_id', 'glyph_5_id', 'glyph_6_id', 'glyph_7_id',
        ]

    @api.depends('name')
    def _compute_slug(self):
        IrHttp = self.env['ir.http']
        for planet in self:
            if not planet.slug and planet.name:
                planet.slug = IrHttp._slugify(planet.name)

    def _address_glyphs(self):
        """Coordinate glyphs in dialing order, then the point of origin."""
        self.ensure_one()
        glyphs = [self[field] for field in self._coordinate_fields if self[field]]
        return glyphs, self.point_of_origin_id

    def _default_website_meta(self):
        # Without this every destination page carries the site description.
        res = super()._default_website_meta()
        description = self.summary or _(
            "Stargate address of %(name)s: %(address)s. The glyphs to dial, "
            "with their constellations.",
            name=self.name, address=self.address_display or "",
        )
        res['default_opengraph']['og:description'] = description
        res['default_twitter']['twitter:description'] = description
        res['default_meta_description'] = description
        return res

    @api.depends(
        'glyph_1_id', 'glyph_2_id', 'glyph_3_id', 'glyph_4_id',
        'glyph_5_id', 'glyph_6_id', 'glyph_7_id', 'point_of_origin_id',
    )
    def _compute_address_display(self):
        for planet in self:
            coords = [planet[f].number for f in planet._coordinate_fields if planet[f]]
            address = "-".join(str(n) for n in coords)
            if planet.point_of_origin_id:
                address = f"{address} · PoO {planet.point_of_origin_id.number}"
            planet.address_display = address or False

    @api.depends(
        'glyph_1_id', 'glyph_2_id', 'glyph_3_id', 'glyph_4_id',
        'glyph_5_id', 'glyph_6_id', 'glyph_7_id', 'point_of_origin_id',
    )
    def _compute_glyph_count(self):
        for planet in self:
            count = len([f for f in planet._coordinate_fields if planet[f]])
            planet.glyph_count = count + (1 if planet.point_of_origin_id else 0)

    @api.depends('dial_log_ids')
    def _compute_dial_count(self):
        for planet in self:
            logs = planet.dial_log_ids
            planet.dial_count = len(logs)
            planet.last_dial = max(logs.mapped('dial_date')) if logs else False

    @api.depends('mission_ids')
    def _compute_mission_count(self):
        for planet in self:
            planet.mission_count = len(planet.mission_ids)

    def action_dial(self):
        """Compose l'adresse : journalise la connexion (et, plus tard, pilote la maquette ESP32)."""
        self.ensure_one()
        self.env['stargate.dial.log'].create({
            'planet_id': self.id,
            'success': True,
        })
        self.message_post(
            body=_("Chevron locked. Wormhole established to %s.", self.name)
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Wormhole established"),
                'message': _("Dialing %s — %s", self.name, self.address_display or ""),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_view_dial_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Dial Log — %s", self.name),
            'res_model': 'stargate.dial.log',
            'view_mode': 'list,form',
            'domain': [('planet_id', '=', self.id)],
            'context': {'default_planet_id': self.id},
        }

    def action_view_missions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Missions — %s", self.name),
            'res_model': 'stargate.mission',
            'view_mode': 'list,form,kanban',
            'domain': [('planet_id', '=', self.id)],
            'context': {'default_planet_id': self.id},
        }
