from odoo import _, api, fields, models


class StargateTeam(models.Model):
    """An SGC field team (SG-1, SG-3, ...) sent off-world through the gate."""

    _name = 'stargate.team'
    _description = "SGC Team"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string="Designation", required=True, tracking=True,
                       help="Team designation, e.g. SG-1.")
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Color")
    specialty = fields.Selection(
        selection=[
            ('recon', "Reconnaissance"),
            ('combat', "Combat"),
            ('diplomatic', "Diplomatic"),
            ('scientific', "Scientific"),
            ('medical', "Medical"),
            ('search_rescue', "Search & Rescue"),
        ],
        string="Specialty",
        default='recon',
        tracking=True,
    )
    leader_id = fields.Many2one('res.users', string="Team Leader", tracking=True)
    member_ids = fields.Many2many('res.users', string="Members")
    member_count = fields.Integer(string="Members", compute='_compute_member_count')
    # Iris/GDO authorization code carried off-world (used by the future iris feature).
    idc_code = fields.Char(string="IDC Code", help="GDO identification code to clear the iris.")
    notes = fields.Html(string="Notes")

    mission_ids = fields.One2many('stargate.mission', 'team_id', string="Missions")
    mission_count = fields.Integer(string="Missions", compute='_compute_mission_count')

    @api.depends('member_ids')
    def _compute_member_count(self):
        for team in self:
            team.member_count = len(team.member_ids)

    @api.depends('mission_ids')
    def _compute_mission_count(self):
        for team in self:
            team.mission_count = len(team.mission_ids)

    def action_view_missions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Missions — %s", self.name),
            'res_model': 'stargate.mission',
            'view_mode': 'list,form,kanban',
            'domain': [('team_id', '=', self.id)],
            'context': {'default_team_id': self.id},
        }
