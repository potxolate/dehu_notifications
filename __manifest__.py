{
    'name': 'DEHU Notifications',
    'version': '1.0',
    'category': 'Custom',
    'summary': 'Recibe y almacena notificaciones de DEHU',
    'author': 'potxolate',
    'depends': ['base'],
    'data': [
        'views/dehu_notification_views.xml',
        'views/dehu_configuration_views.xml',
        'security/ir.model.access.csv',
        'data/dehu_data.xml'
    ],
    'installable': True,
    'application': True,
} 