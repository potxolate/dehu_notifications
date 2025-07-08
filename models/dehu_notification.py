from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class DehuNotification(models.Model):
    _name = 'dehu.notification'
    _description = 'Notificación DEHú'    
    _order = 'available_date desc'
    
    # Campos de identificación
    dehu_id = fields.Char('ID DEHú', readonly=True)
    origin_code = fields.Integer('Código Origen', readonly=True)
    notification_key = fields.Char('Clave única', compute='_compute_notification_key', store=True)
    
    # Campos de metadatos
    subject = fields.Char('Asunto', readonly=True)
    description = fields.Text('Descripción', readonly=True)
    notification_type = fields.Selection([
        ('1', 'Comunicación'),
        ('2', 'Notificación')
    ], string='Tipo', readonly=True)
    available_date = fields.Datetime('Fecha puesta a disposición', readonly=True)
    status = fields.Selection([
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
        ('expired', 'Caducada'),
        ('read', 'Leída')
    ], string='Estado', default='pending', readonly=True)
    
    # Campos de relación
    issuer_entity = fields.Char('Organismo emisor', readonly=True)
    issuer_root_entity = fields.Char('Organismo emisor raíz', readonly=True)
    holder_nif = fields.Char('NIF Titular', readonly=True)
    holder_name = fields.Char('Nombre Titular', readonly=True)
    recipient_nif = fields.Char('NIF Destinatario', readonly=True)
    recipient_name = fields.Char('Nombre Destinatario', readonly=True)
    
    # Campos de documentos
    document_name = fields.Char('Nombre documento')
    document_content = fields.Binary('Documento', readonly=True)
    document_mimetype = fields.Char('Tipo MIME documento')
    document_hash = fields.Char('Hash documento')
    document_hash_algorithm = fields.Char('Algoritmo hash')
    document_metadata = fields.Text('Metadatos documento')
    
    # Campos de anexos
    has_attachments = fields.Boolean('Tiene anexos', compute='_compute_has_attachments')
    attachment_ids = fields.One2many('dehu.notification.attachment', 'notification_id', string='Anexos')
    
    # Campos de acuse
    receipt_reference = fields.Char('Referencia acuse PDF')
    receipt_csv = fields.Char('CSV acuse')
    
    # Campos de relación con Odoo
    partner_id = fields.Many2one('res.partner', string='Contacto relacionado')
    related_document = fields.Reference(
        selection=[('res.partner', 'Contacto')],
        string='Documento relacionado'
    )
    
    @api.depends('dehu_id', 'origin_code')
    def _compute_notification_key(self):
        for record in self:
            record.notification_key = f"{record.dehu_id}-{record.origin_code}"
    
    @api.depends('attachment_ids')
    def _compute_has_attachments(self):
        for record in self:
            record.has_attachments = bool(record.attachment_ids) 