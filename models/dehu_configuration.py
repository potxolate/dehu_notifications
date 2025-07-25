"""Modelo para la configuración de conexión con DEHú."""

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class DehuConfiguration(models.Model):
    """Modelo para gestionar la configuración de conexión con DEHú.

    Este modelo almacena los parámetros necesarios para conectarse al
    sistema DEHú del Gobierno de España.
    """

    _name = "dehu.configuration"
    _description = _("DEHU Configuration")

    name = fields.Char(_("Name"), required=True)
    environment = fields.Selection(
        [
            ("production", _("Production")),
            ("sandbox", _("Sandbox")),
        ],
        string=_("Environment"),
        default="sandbox",
    )
    wsdl_url = fields.Char(_("WSDL URL"), compute="_compute_wsdl_url", store=True)
    api_key = fields.Char(_("API Key"), required=True)
    certificate = fields.Binary(_("X.509 Certificate"))
    certificate_filename = fields.Char(_("Certificate Name"))
    company_id = fields.Many2one(
        "res.company", string=_("Company"), default=lambda self: self.env.company
    )
    active = fields.Boolean(_("Active"), default=True)

    @api.depends("environment")
    def _compute_wsdl_url(self):
        """Calcula la URL del WSDL según el entorno configurado."""
        for record in self:
            if record.environment == "production":
                record.wsdl_url = "https://gd-dehuws.redsara.es/ws/v2/lema?wsdl"
            else:
                record.wsdl_url = "https://se-gd-dehuws.redsara.es/ws/v2/lema?wsdl"
