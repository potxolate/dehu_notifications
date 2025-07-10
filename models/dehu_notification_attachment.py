from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class DehuNotificationAttachment(models.Model):
    """Modelo para gestionar anexos de notificaciones DEHú.

    Este modelo almacena los archivos adjuntos que vienen con las
    notificaciones del sistema DEHú.
    """

    _name = "dehu.notification.attachment"
    _description = "Anexo de notificación DEHú"

    name = fields.Char("Nombre", required=True)
    notification_id = fields.Many2one(
        "dehu.notification",
        string="Notificación",
        required=True,
        ondelete="cascade"
    )
    content = fields.Binary("Contenido", readonly=True)
    mimetype = fields.Char("Tipo MIME", readonly=True)
    reference = fields.Char("Referencia", readonly=True)
    metadata = fields.Text("Metadatos", readonly=True)