import json
import logging

from dateutil import parser as date_parser
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class DehuController(http.Controller):
    """Controlador para manejar webhooks de DEHú."""

    @http.route(
        "/dehu/notification/update",
        type="json",
        auth="none",
        methods=["POST"]
    )
    def notification_update(self, **kwargs):
        """Endpoint para recibir actualizaciones de DEHú (webhook).

        Args:
            **kwargs: Parámetros de la petición

        Returns:
            dict: Respuesta con el estado del procesamiento
        """
        try:
            # Compatibilidad: obtener JSON del cuerpo
            if hasattr(request, "jsonrequest"):
                data = request.jsonrequest
            else:
                data = json.loads(
                    request.httprequest.get_data().decode("utf-8")
                )
            notifications = data.get("notifications", [])
            Notification = request.env["dehu.notification"].sudo()

            for notif_data in notifications:
                # Adaptar fecha ISO a formato Odoo
                fecha = notif_data.get("fechaPuestaDisposicion")
                if fecha:
                    try:
                        # Soporta ISO 8601 y zonas horarias
                        fecha_odoo = fields.Datetime.to_string(
                            date_parser.parse(fecha)
                        )
                    except Exception:
                        fecha_odoo = False
                else:
                    fecha_odoo = False

                notification = Notification.search([
                    ("dehu_id", "=", notif_data.get("identificador")),
                    ("origin_code", "=", notif_data.get("codigoOrigen"))
                ], limit=1)

                if notification:
                    # Actualizar notificación existente
                    notification.write({
                        "status": notif_data.get("estado", "pending"),
                        "available_date": fecha_odoo,
                    })
                else:
                    # Crear nueva notificación
                    organismo_emisor = notif_data.get("organismoEmisor", {})
                    titular = notif_data.get("titular", {})
                    
                    Notification.create({
                        "dehu_id": notif_data.get("identificador"),
                        "origin_code": notif_data.get("codigoOrigen"),
                        "subject": notif_data.get("concepto"),
                        "description": notif_data.get("descripcion"),
                        "notification_type": notif_data.get("tipoEnvio"),
                        "available_date": fecha_odoo,
                        "issuer_entity": organismo_emisor.get("nombreOrganismo"),
                        "holder_nif": titular.get("nifTitular"),
                        "holder_name": titular.get("nombreTitular"),
                        "status": "pending"
                    })

            return {
                "status": "success",
                "message": "Notificaciones procesadas"
            }
        except Exception as e:
            _logger.error(
                "Error processing DEHú notifications: %s",
                str(e)
            )
            return {"status": "error", "message": str(e)}