"""Modelo para la gestión de notificaciones DEHú."""

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class DehuNotification(models.Model):
    """Modelo para gestionar notificaciones de DEHú.

    Este modelo almacena y gestiona las notificaciones recibidas del sistema
    DEHú (Dirección Electrónica Habilitada Única) del Gobierno de España.
    """

    _name = "dehu.notification"
    _description = _("DEHU Notification")
    _order = "available_date desc"

    # Campos de identificación
    dehu_id = fields.Char(_("DEHU ID"), readonly=True)
    origin_code = fields.Integer(_("Origin Code"), readonly=True)
    notification_key = fields.Char(
        _("Unique Key"), compute="_compute_notification_key", store=True
    )

    # Campos de metadatos
    subject = fields.Char(_("Subject"), readonly=True)
    description = fields.Text(_("Description"), readonly=True)
    notification_type = fields.Selection(
        [
            ("1", _("Communication")),
            ("2", _("Notification")),
        ],
        string=_("Type"),
        readonly=True,
    )
    available_date = fields.Datetime(_("Available Date"), readonly=True)
    status = fields.Selection(
        [
            ("pending", _("Pending")),
            ("accepted", _("Accepted")),
            ("rejected", _("Rejected")),
            ("expired", _("Expired")),
            ("read", _("Read")),
        ],
        string=_("Status"),
        default="pending",
        readonly=True,
    )

    # Campos de relación
    issuer_entity = fields.Char(_("Issuer Entity"), readonly=True)
    issuer_root_entity = fields.Char(_("Root Issuer Entity"), readonly=True)
    holder_nif = fields.Char(_("Holder NIF"), readonly=True)
    holder_name = fields.Char(_("Holder Name"), readonly=True)
    recipient_nif = fields.Char(_("Recipient NIF"), readonly=True)
    recipient_name = fields.Char(_("Recipient Name"), readonly=True)

    # Campos de documentos
    document_name = fields.Char(_("Document Name"))
    document_content = fields.Binary(_("Document"), readonly=True)
    document_mimetype = fields.Char(_("Document MIME Type"))
    document_hash = fields.Char(_("Document Hash"))
    document_hash_algorithm = fields.Char(_("Hash Algorithm"))
    document_metadata = fields.Text(_("Document Metadata"))

    # Campos de anexos
    has_attachments = fields.Boolean(
        _("Has Attachments"), compute="_compute_has_attachments"
    )
    attachment_ids = fields.One2many(
        "dehu.notification.attachment", "notification_id", string=_("Attachments")
    )

    # Campos de acuse
    receipt_reference = fields.Char(_("PDF Receipt Reference"))
    receipt_csv = fields.Char(_("CSV Receipt"))

    # Campos de relación con Odoo
    partner_id = fields.Many2one("res.partner", string=_("Related Contact"))
    related_document = fields.Reference(
        selection=[("res.partner", _("Contact"))], string=_("Related Document")
    )

    @api.depends("dehu_id", "origin_code")
    def _compute_notification_key(self):
        """Calcula la clave única de la notificación.

        La clave se forma concatenando el ID DEHú y el código de origen.
        """
        for record in self:
            record.notification_key = f"{record.dehu_id}-{record.origin_code}"

    @api.depends("attachment_ids")
    def _compute_has_attachments(self):
        """Determina si la notificación tiene anexos."""
        for record in self:
            record.has_attachments = bool(record.attachment_ids)
