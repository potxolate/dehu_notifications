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
    _description = _("Anexo de notificación DEHú")

    name = fields.Char(_("Nombre"), required=True)
    notification_id = fields.Many2one(
        "dehu.notification", string=_("Notificación"), required=True, ondelete="cascade"
    )
    content = fields.Binary(_("Contenido"), readonly=True)
    mimetype = fields.Char(_("Tipo MIME"), readonly=True)
    reference = fields.Char(_("Referencia"), readonly=True)
    metadata = fields.Text(_("Metadatos"), readonly=True)
