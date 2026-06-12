from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StargateGlyph(models.Model):
    """Un glyphe gravé sur l'anneau d'une Porte des étoiles (= une constellation)."""

    _name = 'stargate.glyph'
    _description = "Stargate Glyph"
    _order = 'gate_type, number'

    name = fields.Char(string="Constellation", required=True)
    number = fields.Integer(string="Glyph Number", required=True)
    gate_type = fields.Selection(
        selection=[
            ('milky_way', "Milky Way"),
            ('pegasus', "Pegasus"),
            ('universe', "Universe"),
        ],
        string="Gate Type",
        default='milky_way',
    )
    is_point_of_origin = fields.Boolean(
        string="Point of Origin",
        help="Glyph used as the seventh symbol when dialing from this gate's world.",
    )
    # Symbol picture (raster). Shown in the backend and usable by the dialing
    # interface.
    image = fields.Image(string="Symbol Image", max_width=512, max_height=512)
    # Inline SVG markup for the glyph shape. Optional vector alternative to the
    # image; the backend works fine without either.
    svg = fields.Text(string="SVG Shape")
    active = fields.Boolean(default=True)

    _number_gate_type_uniq = models.Constraint(
        'unique(number, gate_type)',
        "A glyph number must be unique per gate type.",
    )

    @api.constrains('number')
    def _check_number(self):
        for glyph in self:
            if glyph.number < 1:
                raise ValidationError(_("Glyph number must be a positive integer."))

    @api.depends('number', 'name')
    def _compute_display_name(self):
        for glyph in self:
            glyph.display_name = f"{glyph.number:02d} · {glyph.name or ''}".strip(" ·")
