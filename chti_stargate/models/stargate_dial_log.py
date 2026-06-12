from odoo import api, fields, models


class StargateDialLog(models.Model):
    """Historique des connexions : une ligne par numérotation d'une adresse."""

    _name = 'stargate.dial.log'
    _description = "Stargate Dial Log"
    _order = 'dial_date desc'

    planet_id = fields.Many2one(
        'stargate.planet',
        string="Destination",
        required=True,
        ondelete='cascade',
    )
    dial_date = fields.Datetime(
        string="Dialed On",
        default=fields.Datetime.now,
        required=True,
    )
    success = fields.Boolean(string="Wormhole Established", default=True)
    user_id = fields.Many2one(
        'res.users',
        string="Dialed By",
        default=lambda self: self.env.user,
    )
    note = fields.Char(string="Note")
    address_display = fields.Char(
        related='planet_id.address_display',
        string="Address",
        store=False,
    )

    @api.depends('planet_id', 'dial_date')
    def _compute_display_name(self):
        for log in self:
            label = log.planet_id.name or ""
            log.display_name = f"{label} — {log.dial_date or ''}".strip(" —")
