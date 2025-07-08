from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from zeep import Client, Settings
from zeep.wsse.username import UsernameToken
import base64
import logging

_logger = logging.getLogger(__name__)


class DehuSynchronizer(models.Model):
    _name = 'dehu.synchronizer'
    _description = 'Sincronizador con DEHú'
    
    def _get_dehu_client(self, config):
        """Crea y configura el cliente SOAP para DEHú"""
        try:
            settings = Settings(
                strict=False,
                xml_huge_tree=True,
                extra_http_headers={
                    'Expect': '100-continue',
                    'Content-Length': '0'
                }
            )
            
            client = Client(config.wsdl_url, wsse=UsernameToken(config.api_key, ''), settings=settings)
            return client
        except Exception as e:
            _logger.error("Error creating DEHú client: %s", str(e))
            raise UserError(_("Error creating DEHú client: %s") % str(e))
    
    def fetch_pending_notifications(self):
        """Obtiene notificaciones pendientes de DEHú"""
        config = self.env['dehu.configuration'].search([('active', '=', True)], limit=1)
        if not config:
            raise UserError(_("No active DEHú configuration found"))
            
        try:
            client = self._get_dehu_client(config)
            
            # Parámetros para localiza()
            params = {
                'nifTitular': config.company_id.vat or '',
                'fechaDesde': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S'),
                'fechaHasta': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            }
            
            response = client.service.localiza(**params)
            
            notifications = []
            if hasattr(response, 'envios') and hasattr(response.envios, 'item'):
                notifications = response.envios.item
            
            Notification = self.env['dehu.notification']
            for notif in notifications:
                existing = Notification.search([
                    ('dehu_id', '=', notif.identificador),
                    ('origin_code', '=', notif.codigoOrigen)
                ], limit=1)
                
                if not existing:
                    Notification.create({
                        'dehu_id': notif.identificador,
                        'origin_code': notif.codigoOrigen,
                        'subject': notif.concepto,
                        'description': notif.descripcion,
                        'notification_type': notif.tipoEnvio,
                        'available_date': notif.fechaPuestaDisposicion,
                        'issuer_entity': notif.organismoEmisor.nombreOrganismo,
                        'issuer_root_entity': notif.organismoEmisorRaiz.nombreOrganismo,
                        'holder_nif': notif.titular.nifTitular,
                        'holder_name': notif.titular.nombreTitular,
                        'status': 'pending'
                    })
            
            return True
        except Exception as e:
            _logger.error("Error fetching DEHú notifications: %s", str(e))
            raise UserError(_("Error fetching notifications: %s") % str(e))
    
    def process_notification(self, notification):
        """Procesa una notificación (aceptar y descargar contenido)"""
        config = self.env['dehu.configuration'].search([('active', '=', True)], limit=1)
        if not config:
            raise UserError(_("No active DEHú configuration found"))
            
        try:
            client = self._get_dehu_client(config)
            
            # Parámetros para peticionAcceso()
            params = {
                'identificador': notification.dehu_id,
                'codigoOrigen': notification.origin_code,
                'nifReceptor': config.company_id.vat or '',
                'nombreReceptor': config.company_id.name,
                'evento': '1',  # Aceptada
                'concepto': notification.subject
            }
            
            response = client.service.peticionAcceso(**params)
            
            # Procesar respuesta
            if response.codigoRespuesta == '200':
                # Actualizar notificación
                notification.write({
                    'status': 'accepted',
                    'document_name': response.documento.nombre,
                    'document_mimetype': response.documento.mimeType,
                    'receipt_csv': response.documento.csvResguardo
                })
                
                # Descargar documento principal
                if hasattr(response.documento, 'contenido'):
                    notification.document_content = base64.b64encode(response.documento.contenido)
                
                # Procesar anexos si existen
                if hasattr(response, 'anexos'):
                    self._process_attachments(notification, response.anexos)
                
                return True
            else:
                raise UserError(_("DEHú error: %s - %s") % (
                    response.codigoRespuesta,
                    response.descripcionRespuesta
                ))
        except Exception as e:
            _logger.error("Error processing notification %s: %s", notification.notification_key, str(e))
            raise UserError(_("Error processing notification: %s") % str(e))
    
    def _process_attachments(self, notification, attachments):
        """Procesa los anexos de una notificación"""
        Attachment = self.env['dehu.notification.attachment']
        
        # Anexos por referencia
        if hasattr(attachments, 'anexosReferencia') and hasattr(attachments.anexosReferencia, 'anexoReferencia'):
            for anexo in attachments.anexosReferencia.anexoReferencia:
                # Descargar anexo usando consultaAnexos()
                try:
                    config = self.env['dehu.configuration'].search([('active', '=', True)], limit=1)
                    client = self._get_dehu_client(config)
                    
                    params = {
                        'nifReceptor': config.company_id.vat or '',
                        'Identificador': notification.dehu_id,
                        'codigoOrigen': notification.origin_code,
                        'referencia': anexo.referenciaDocumento
                    }
                    
                    response = client.service.consultaAnexos(**params)
                    
                    if response.codigoRespuesta == '200':
                        Attachment.create({
                            'name': anexo.nombre,
                            'notification_id': notification.id,
                            'mimetype': anexo.mimeType,
                            'reference': anexo.referenciaDocumento,
                            'content': base64.b64encode(response.documento.contenido) if hasattr(response.documento, 'contenido') else None,
                            'metadata': response.documento.metadatos if hasattr(response.documento, 'metadatos') else None
                        })
                except Exception as e:
                    _logger.error("Error downloading attachment %s: %s", anexo.nombre, str(e))
        
        # Anexos por URL (no se descargan, solo se registran)
        if hasattr(attachments, 'anexosUrl') and hasattr(attachments.anexosUrl, 'anexoUrl'):
            for anexo in attachments.anexosUrl.anexoUrl:
                Attachment.create({
                    'name': anexo.nombre,
                    'notification_id': notification.id,
                    'mimetype': anexo.mimeType,
                    'reference': anexo.enlaceDocumento,
                    'metadata': 'Enlace externo: ' + anexo.enlaceDocumento
                })
    
    def download_receipt_pdf(self, notification):
        """Descarga el acuse PDF de una notificación"""
        if not notification.receipt_csv:
            raise UserError(_("No receipt CSV available for this notification"))
            
        config = self.env['dehu.configuration'].search([('active', '=', True)], limit=1)
        if not config:
            raise UserError(_("No active DEHú configuration found"))
            
        try:
            client = self._get_dehu_client(config)
            
            params = {
                'nifReceptor': config.company_id.vat or '',
                'Identificador': notification.dehu_id,
                'codigoOrigen': notification.origin_code,
                'identificadorAcusePdf': {
                    'csvResguardo': notification.receipt_csv
                }
            }
            
            response = client.service.consultaAcusePdf(**params)
            
            if response.codigoRespuesta == '200':
                return {
                    'name': response.acusePdf.nombreAcuse,
                    'content': base64.b64encode(response.acusePdf.contenido),
                    'mimetype': response.acusePdf.mimeType
                }
            else:
                raise UserError(_("DEHú error: %s - %s") % (
                    response.codigoRespuesta,
                    response.descripcionRespuesta
                ))
        except Exception as e:
            _logger.error("Error downloading receipt PDF for %s: %s", notification.notification_key, str(e))
            raise UserError(_("Error downloading receipt: %s") % str(e))