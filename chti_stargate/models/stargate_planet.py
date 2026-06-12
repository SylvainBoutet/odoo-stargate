from odoo import _, api, fields, models


class StargatePlanet(models.Model):
    """Une destination de la Porte des étoiles : un nom + une adresse (séquence de glyphes)."""

    _name = 'stargate.planet'
    _description = "Stargate Destination"
    _inherit = ['mail.thread', 'mail.activity.mixin']
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

    def _default_point_of_origin(self):
        # Earth's point of origin (glyph 01). Safe before data is loaded.
        return self.env.ref('chti_stargate.glyph_01', raise_if_not_found=False)

    @property
    def _coordinate_fields(self):
        return [
            'glyph_1_id', 'glyph_2_id', 'glyph_3_id',
            'glyph_4_id', 'glyph_5_id', 'glyph_6_id', 'glyph_7_id',
        ]

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
