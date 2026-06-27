from odoo import _, api, fields, models


class StargateMission(models.Model):
    """An off-world mission report: a team sent to a destination, its objective and outcome."""

    _name = 'stargate.mission'
    _description = "SGC Mission Report"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(string="Mission", required=True, tracking=True)
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Color")

    planet_id = fields.Many2one(
        'stargate.planet',
        string="Destination",
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    designation = fields.Char(related='planet_id.designation', string="Designation", store=True)
    address_display = fields.Char(related='planet_id.address_display', string="Address")

    team_id = fields.Many2one('stargate.team', string="Assigned Team", tracking=True)
    leader_id = fields.Many2one(
        'res.users',
        string="Mission Commander",
        compute='_compute_leader_id',
        store=True,
        readonly=False,
    )

    objective = fields.Html(string="Objective")
    malp_recon = fields.Boolean(
        string="MALP Recon Done",
        help="Whether a MALP performed remote reconnaissance before sending the team.",
    )
    threat_level = fields.Selection(
        selection=[
            ('none', "None"),
            ('low', "Low"),
            ('moderate', "Moderate"),
            ('high', "High"),
            ('extreme', "Extreme"),
        ],
        string="Threat Level",
        default='none',
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('scheduled', "Scheduled"),
            ('in_progress', "In Progress"),
            ('success', "Success"),
            ('failed', "Failed"),
            ('mia', "MIA"),
        ],
        string="Status",
        default='draft',
        required=True,
        tracking=True,
    )
    date_start = fields.Datetime(string="Departure")
    date_end = fields.Datetime(string="Return")
    report = fields.Html(string="Mission Report")

    @api.depends('team_id')
    def _compute_leader_id(self):
        for mission in self:
            if mission.team_id and not mission.leader_id:
                mission.leader_id = mission.team_id.leader_id

    def action_schedule(self):
        self.write({'state': 'scheduled'})

    def action_start(self):
        for mission in self:
            vals = {'state': 'in_progress'}
            if not mission.date_start:
                vals['date_start'] = fields.Datetime.now()
            mission.write(vals)

    def action_success(self):
        self._close('success')

    def action_failed(self):
        self._close('failed')

    def action_mia(self):
        self.write({'state': 'mia'})

    def action_reset(self):
        self.write({'state': 'draft'})

    def _close(self, state):
        for mission in self:
            vals = {'state': state}
            if not mission.date_end:
                vals['date_end'] = fields.Datetime.now()
            mission.write(vals)
