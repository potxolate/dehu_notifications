"""Modelo para la gestión de anexos de notificaciones DEHú."""

import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class DehuNotificationAttachment(models.Model):
    """Modelo para gestionar anexos de notificaciones DEHú.

    Este modelo almacena los archivos adjuntos que vienen con las
    notificaciones del sistema DEHú.
    """

    _name = "dehu.notification.attachment"
    _description = _("DEHU Notification Attachment")

    name = fields.Char(_("Name"), required=True)
    notification_id = fields.Many2one(
        "dehu.notification", string=_("Notification"), required=True, ondelete="cascade"
    )
    content = fields.Binary(_("Content"), readonly=True)
    mimetype = fields.Char(_("MIME Type"), readonly=True)
    reference = fields.Char(_("Reference"), readonly=True)
    metadata = fields.Text(_("Metadata"), readonly=True)
