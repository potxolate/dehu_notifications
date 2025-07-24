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
    _description = _("Notificación DEHú")
    _order = "available_date desc"

    # Campos de identificación
    dehu_id = fields.Char(_("ID DEHú"), readonly=True)
    origin_code = fields.Integer(_("Código Origen"), readonly=True)
    notification_key = fields.Char(
        _("Clave única"), compute="_compute_notification_key", store=True
    )

    # Campos de metadatos
    subject = fields.Char(_("Asunto"), readonly=True)
    description = fields.Text(_("Descripción"), readonly=True)
    notification_type = fields.Selection(
        [
            ("1", _("Comunicación")),
            ("2", _("Notificación")),
        ],
        string=_("Tipo"),
        readonly=True,
    )
    available_date = fields.Datetime(_("Fecha puesta a disposición"), readonly=True)
    status = fields.Selection(
        [
            ("pending", _("Pendiente")),
            ("accepted", _("Aceptada")),
            ("rejected", _("Rechazada")),
            ("expired", _("Caducada")),
            ("read", _("Leída")),
        ],
        string=_("Estado"),
        default="pending",
        readonly=True,
    )

    # Campos de relación
    issuer_entity = fields.Char(_("Organismo emisor"), readonly=True)
    issuer_root_entity = fields.Char(_("Organismo emisor raíz"), readonly=True)
    holder_nif = fields.Char(_("NIF Titular"), readonly=True)
    holder_name = fields.Char(_("Nombre Titular"), readonly=True)
    recipient_nif = fields.Char(_("NIF Destinatario"), readonly=True)
    recipient_name = fields.Char(_("Nombre Destinatario"), readonly=True)

    # Campos de documentos
    document_name = fields.Char(_("Nombre documento"))
    document_content = fields.Binary(_("Documento"), readonly=True)
    document_mimetype = fields.Char(_("Tipo MIME documento"))
    document_hash = fields.Char(_("Hash documento"))
    document_hash_algorithm = fields.Char(_("Algoritmo hash"))
    document_metadata = fields.Text(_("Metadatos documento"))

    # Campos de anexos
    has_attachments = fields.Boolean(
        _("Tiene anexos"), compute="_compute_has_attachments"
    )
    attachment_ids = fields.One2many(
        "dehu.notification.attachment", "notification_id", string=_("Anexos")
    )

    # Campos de acuse
    receipt_reference = fields.Char(_("Referencia acuse PDF"))
    receipt_csv = fields.Char(_("CSV acuse"))

    # Campos de relación con Odoo
    partner_id = fields.Many2one("res.partner", string=_("Contacto relacionado"))
    related_document = fields.Reference(
        selection=[("res.partner", _("Contacto"))], string=_("Documento relacionado")
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
