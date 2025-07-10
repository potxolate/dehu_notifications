# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "DEHU Notifications",
    "version": "1.0.0",
    "category": "Government",
    "summary": "Recibe y almacena notificaciones de DEHU",
    "description": """
        Módulo para gestionar notificaciones del sistema DEHú
        (Dirección Electrónica Habilitada Única) del Gobierno de España.

        Características:
        - Recepción automática de notificaciones
        - Gestión de documentos y anexos
        - Integración con contactos de Odoo
        - Configuración flexible de entornos
    """,
    "author": "potxolate",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/dehu_data.xml",
        "views/dehu_notification_views.xml",
        "views/dehu_configuration_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
