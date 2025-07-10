"""Modelo para la configuración de conexión con DEHú."""

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DehuConfiguration(models.Model):
    """Modelo para gestionar la configuración de conexión con DEHú.

    Este modelo almacena los parámetros necesarios para conectarse al
    sistema DEHú del Gobierno de España.
    """

    _name = "dehu.configuration"
    _description = "Configuración DEHú"

    name = fields.Char("Nombre", required=True)
    environment = fields.Selection(
        [("production", "Producción"), ("sandbox", "Entorno de pruebas")],
        string="Entorno",
        required=True,
        default="sandbox",
    )
    wsdl_url = fields.Char("URL WSDL", compute="_compute_wsdl_url", store=True)
    api_key = fields.Char("API Key", required=True)
    certificate = fields.Binary("Certificado X.509")
    certificate_filename = fields.Char("Nombre del certificado")
    company_id = fields.Many2one(
        "res.company", string="Compañía", default=lambda self: self.env.company
    )
    active = fields.Boolean("Activo", default=True)

    @api.depends("environment")
    def _compute_wsdl_url(self):
        """Calcula la URL del WSDL según el entorno configurado."""
        for record in self:
            if record.environment == "production":
                record.wsdl_url = "https://gd-dehuws.redsara.es/ws/v2/lema?wsdl"
            else:
                record.wsdl_url = "https://se-gd-dehuws.redsara.es/ws/v2/lema?wsdl"
