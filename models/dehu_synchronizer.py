import base64
import logging
from datetime import datetime, timedelta

from odoo import _, models
from odoo.exceptions import UserError
from zeep import Client, Settings
from zeep.wsse.username import UsernameToken

_logger = logging.getLogger(__name__)

DEHU_CONFIGURATION_MODEL = "dehu.configuration"
DEHU_NOTIFICATION_MODEL = "dehu.notification"
DEHU_NOTIFICATION_ATTACHMENT_MODEL = "dehu.notification.attachment"
NO_ACTIVE_CONFIG_ERROR = _("No active DEHú configuration found")


class DehuSynchronizer(models.Model):
    """Sincronizador con DEHú: gestiona la comunicación con el sistema DEHú del Gobierno de España."""

    _name = "dehu.synchronizer"
    _description = "Sincronizador con DEHú"

    def _get_dehu_client(self, config):
        """Crea y configura el cliente SOAP para DEHú.

        Args:
            config: Configuración de DEHú

        Returns:
            Client: Cliente SOAP configurado

        Raises:
            UserError: Si hay error al crear el cliente
        """
        try:
            settings = Settings(
                strict=False,
                xml_huge_tree=True,
                extra_http_headers={"Expect": "100-continue", "Content-Length": "0"},
            )

            client = Client(
                config.wsdl_url,
                wsse=UsernameToken(config.api_key, ""),
                settings=settings,
            )
            return client
        except Exception as e:
            _logger.error("Error creating DEHú client: %s", str(e))
            raise UserError(_("Error creating DEHú client: %s") % str(e)) from e

    def fetch_pending_notifications(self):
        """Obtiene notificaciones pendientes de DEHú.

        Returns:
            bool: True si la operación fue exitosa

        Raises:
            UserError: Si no hay configuración activa o hay errores
        """
        config = self.env[DEHU_CONFIGURATION_MODEL].search(
            [("active", "=", True)], limit=1
        )
        if not config:
            raise UserError(NO_ACTIVE_CONFIG_ERROR)

        try:
            client = self._get_dehu_client(config)

            # Parámetros para localiza()
            fecha_desde = (datetime.now() - timedelta(days=30)).strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
            fecha_hasta = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

            params = {
                "nifTitular": config.company_id.vat or "",
                "fechaDesde": fecha_desde,
                "fechaHasta": fecha_hasta,
            }

            response = client.service.localiza(**params)

            notifications = []
            if hasattr(response, "envios") and hasattr(response.envios, "item"):
                notifications = response.envios.item

            notification_model = self.env[DEHU_NOTIFICATION_MODEL]
            for notif in notifications:
                existing = notification_model.search(
                    [
                        ("dehu_id", "=", notif.identificador),
                        ("origin_code", "=", notif.codigoOrigen),
                    ],
                    limit=1,
                )

                if not existing:
                    notification_model.create(
                        {
                            "dehu_id": notif.identificador,
                            "origin_code": notif.codigoOrigen,
                            "subject": notif.concepto,
                            "description": notif.descripcion,
                            "notification_type": notif.tipoEnvio,
                            "available_date": notif.fechaPuestaDisposicion,
                            "issuer_entity": (notif.organismoEmisor.nombreOrganismo),
                            "issuer_root_entity": (
                                notif.organismoEmisorRaiz.nombreOrganismo
                            ),
                            "holder_nif": notif.titular.nifTitular,
                            "holder_name": notif.titular.nombreTitular,
                            "status": "pending",
                        }
                    )

            return True
        except Exception as e:
            _logger.error("Error fetching DEHú notifications: %s", str(e))
            raise UserError(_("Error fetching notifications: %s") % str(e)) from e

    def process_notification(self, notification):
        """Procesa una notificación (aceptar y descargar contenido).

        Args:
            notification: Notificación a procesar

        Returns:
            bool: True si la operación fue exitosa

        Raises:
            UserError: Si no hay configuración activa o hay errores
        """
        config = self.env[DEHU_CONFIGURATION_MODEL].search(
            [("active", "=", True)], limit=1
        )
        if not config:
            raise UserError(NO_ACTIVE_CONFIG_ERROR)

        try:
            client = self._get_dehu_client(config)

            # Parámetros para peticionAcceso()
            params = {
                "identificador": notification.dehu_id,
                "codigoOrigen": notification.origin_code,
                "nifReceptor": config.company_id.vat or "",
                "nombreReceptor": config.company_id.name,
                "evento": "1",  # Aceptada
                "concepto": notification.subject,
            }

            response = client.service.peticionAcceso(**params)

            # Procesar respuesta
            if response.codigoRespuesta == "200":
                # Actualizar notificación
                notification.write(
                    {
                        "status": "accepted",
                        "document_name": response.documento.nombre,
                        "document_mimetype": response.documento.mimeType,
                        "receipt_csv": response.documento.csvResguardo,
                    }
                )

                # Descargar documento principal
                if hasattr(response.documento, "contenido"):
                    notification.document_content = base64.b64encode(
                        response.documento.contenido
                    )

                # Procesar anexos si existen
                if hasattr(response, "anexos"):
                    self._process_attachments(notification, response.anexos)

                return True
            raise UserError(
                _("DEHú error: %s - %s")
                % (response.codigoRespuesta, response.descripcionRespuesta)
            )
        except Exception as e:
            _logger.error(
                "Error processing notification %s: %s",
                notification.notification_key,
                str(e),
            )
            raise UserError(_("Error processing notification: %s") % str(e)) from e

    def _process_attachments(self, notification, attachments):
        """Procesa los anexos de una notificación."""
        attachment_model = self.env[DEHU_NOTIFICATION_ATTACHMENT_MODEL]
        self._process_reference_attachments(notification, attachments, attachment_model)
        self._process_url_attachments(notification, attachments, attachment_model)

    def _process_reference_attachments(
        self, notification, attachments, attachment_model
    ):
        if hasattr(attachments, "anexosReferencia") and hasattr(
            attachments.anexosReferencia, "anexoReferencia"
        ):
            for anexo in attachments.anexosReferencia.anexoReferencia:
                self._download_and_create_attachment(
                    notification, anexo, attachment_model
                )

    def _download_and_create_attachment(self, notification, anexo, attachment_model):
        try:
            config = self.env[DEHU_CONFIGURATION_MODEL].search(
                [("active", "=", True)], limit=1
            )
            client = self._get_dehu_client(config)
            params = {
                "nifReceptor": config.company_id.vat or "",
                "Identificador": notification.dehu_id,
                "codigoOrigen": notification.origin_code,
                "referencia": anexo.referenciaDocumento,
            }
            response = client.service.consultaAnexos(**params)
            if response.codigoRespuesta == "200":
                content = None
                if hasattr(response.documento, "contenido"):
                    content = base64.b64encode(response.documento.contenido)
                metadata = None
                if hasattr(response.documento, "metadatos"):
                    metadata = response.documento.metadatos
                attachment_model.create(
                    {
                        "name": anexo.nombre,
                        "notification_id": notification.id,
                        "mimetype": anexo.mimeType,
                        "reference": anexo.referenciaDocumento,
                        "content": content,
                        "metadata": metadata,
                    }
                )
        except Exception as e:
            _logger.error("Error downloading attachment %s: %s", anexo.nombre, str(e))

    def _process_url_attachments(self, notification, attachments, attachment_model):
        if hasattr(attachments, "anexosUrl") and hasattr(
            attachments.anexosUrl, "anexoUrl"
        ):
            for anexo in attachments.anexosUrl.anexoUrl:
                attachment_model.create(
                    {
                        "name": anexo.nombre,
                        "notification_id": notification.id,
                        "mimetype": anexo.mimeType,
                        "reference": anexo.enlaceDocumento,
                        "metadata": "Enlace externo: " + anexo.enlaceDocumento,
                    }
                )

    def download_receipt_pdf(self, notification):
        """Descarga el acuse PDF de una notificación.

        Args:
            notification: Notificación de la que descargar el acuse

        Returns:
            dict: Información del acuse PDF descargado

        Raises:
            UserError: Si no hay CSV de acuse o hay errores
        """
        if not notification.receipt_csv:
            raise UserError(_("No receipt CSV available for this notification"))

        config = self.env[DEHU_CONFIGURATION_MODEL].search(
            [("active", "=", True)], limit=1
        )
        if not config:
            raise UserError(NO_ACTIVE_CONFIG_ERROR)

        try:
            client = self._get_dehu_client(config)

            params = {
                "nifReceptor": config.company_id.vat or "",
                "Identificador": notification.dehu_id,
                "codigoOrigen": notification.origin_code,
                "identificadorAcusePdf": {"csvResguardo": notification.receipt_csv},
            }

            response = client.service.consultaAcusePdf(**params)

            if response.codigoRespuesta == "200":
                return {
                    "name": response.acusePdf.nombreAcuse,
                    "content": base64.b64encode(response.acusePdf.contenido),
                    "mimetype": response.acusePdf.mimeType,
                }
            raise UserError(
                _("DEHú error: %s - %s")
                % (response.codigoRespuesta, response.descripcionRespuesta)
            )
        except Exception as e:
            _logger.error(
                "Error downloading receipt PDF for %s: %s",
                notification.notification_key,
                str(e),
            )
            raise UserError(_("Error downloading receipt: %s") % str(e)) from e
