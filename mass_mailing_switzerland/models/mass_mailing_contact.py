##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from time import sleep

from odoo import api, models, fields
from odoo.addons.queue_job.job import job


class MassMailingContact(models.Model):

    _inherit = "mail.mass_mailing.contact"

    partner_id = fields.Many2one(
        "res.partner", "Associated contact", ondelete="cascade",
    )

    @api.model
    def create(self, vals_list):
        records = super().create(vals_list)
        for contact in records:
            if not contact.partner_id:
                contact.write({"partner_id": contact.get_partner(contact.email)})
        return records

    @api.multi
    def get_partner(self, email):
        """Override to fetch partner directly from relation if set."""
        self.ensure_one()
        if self.partner_id:
            return self.partner_id.id
        else:
            return super().get_partner(email)

    @api.model
    def launch_job_update_mailchimp(self, partner_ids=None):
        self.with_delay().update_all_merge_fields_job(partner_ids)
        return True

    @job(default_channel="root.mass_mailing_switzerland.update_mailchimp")
    @api.model
    def update_all_merge_fields_job(self, partner_ids=None):
        """ Update all contacts merge fields
        :return: List of partner_ids that failed to update
        """
        search_criterias = [("partner_id", "!=", False)]
        if partner_ids:
            search_criterias.append(("partner_id", "in", partner_ids))
        failed = []
        for partner in self.search(search_criterias):
            try:
                partner.action_update_to_mailchimp()
            except:
                failed.append(partner.id)
                # Allows network to recover
                sleep(1)
        return failed

    @api.multi
    def action_export_to_mailchimp(self):
        """
        Always export in english so that all tags are set in English
        """
        if self.env.context.get("skip_mailchimp"):
            return True
        return super(MassMailingContact,
                     self.with_context(lang="en_US")).action_export_to_mailchimp()

    @api.multi
    def action_update_to_mailchimp(self):
        """
        Always export in english so that all tags are set in English
        """
        if self.env.context.get("skip_mailchimp"):
            return True
        return super(MassMailingContact,
                     self.with_context(lang="en_US")).action_update_to_mailchimp()
