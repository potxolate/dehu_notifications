# DEHU Notifications

Módulo para gestionar notificaciones del sistema DEHú (Dirección Electrónica Habilitada Única) del Gobierno de España.

## Descripción

Este módulo permite a las empresas recibir y gestionar notificaciones electrónicas del sistema DEHú del Gobierno de España, que es el sistema oficial para la recepción de comunicaciones y notificaciones administrativas.

## Características

- **Recepción automática**: Sincronización automática de notificaciones pendientes
- **Gestión de documentos**: Descarga y almacenamiento de documentos principales
- **Gestión de anexos**: Manejo de archivos adjuntos a las notificaciones
- **Integración con contactos**: Vinculación con contactos de Odoo
- **Configuración flexible**: Soporte para entornos de producción y pruebas
- **Webhooks**: Endpoint para recibir actualizaciones en tiempo real

## Instalación

1. Copia el módulo en tu directorio de addons personalizados
2. Actualiza la lista de módulos en Odoo
3. Instala el módulo "DEHU Notifications"
4. Configura los parámetros de conexión en Configuración > DEHú

## Configuración

### Configuración de DEHú

1. Ve a **Configuración > DEHú**
2. Crea una nueva configuración con:
   - **Nombre**: Identificador de la configuración
   - **Entorno**: Producción o Entorno de pruebas
   - **API Key**: Clave de acceso proporcionada por DEHú
   - **Certificado X.509**: Certificado digital (opcional)

### Configuración del Cron

El módulo incluye una tarea programada que se ejecuta cada hora para obtener notificaciones pendientes. Puedes modificar la frecuencia en **Configuración > Técnico > Automatización > Tareas programadas**.

## Uso

### Ver Notificaciones

1. Ve a **DEHú > Notificaciones**
2. Las notificaciones se muestran ordenadas por fecha de disponibilidad
3. Usa los filtros para buscar notificaciones específicas

### Procesar Notificaciones

1. Selecciona una notificación pendiente
2. Haz clic en "Procesar" para aceptar y descargar el contenido
3. El documento principal y los anexos se descargarán automáticamente

### Webhooks

El módulo proporciona un endpoint webhook en `/dehu/notification/update` para recibir actualizaciones en tiempo real desde el sistema DEHú.

## Modelos

### dehu.notification

Modelo principal para almacenar las notificaciones recibidas.

**Campos principales:**
- `dehu_id`: Identificador único de DEHú
- `subject`: Asunto de la notificación
- `description`: Descripción detallada
- `status`: Estado (pendiente, aceptada, rechazada, etc.)
- `available_date`: Fecha de puesta a disposición
- `document_content`: Contenido del documento principal
- `attachment_ids`: Anexos de la notificación

### dehu.configuration

Modelo para gestionar la configuración de conexión con DEHú.

**Campos principales:**
- `environment`: Entorno (producción/pruebas)
- `api_key`: Clave de acceso
- `wsdl_url`: URL del servicio web
- `certificate`: Certificado digital

### dehu.notification.attachment

Modelo para gestionar los anexos de las notificaciones.

**Campos principales:**
- `name`: Nombre del archivo
- `content`: Contenido del archivo
- `mimetype`: Tipo MIME
- `reference`: Referencia del anexo

## Dependencias

- `base`: Módulo base de Odoo
- `zeep`: Cliente SOAP para Python (requerido para la comunicación con DEHú)

## Licencia

Este módulo está licenciado bajo LGPL-3.

## Autor

potxolate

## Contribuir

Para contribuir al desarrollo de este módulo:

1. Fork el repositorio
2. Crea una rama para tu feature
3. Asegúrate de que el código cumple con las OCA guidelines
4. Envía un pull request

## Soporte

Para reportar bugs o solicitar nuevas características, por favor crea un issue en el repositorio del proyecto. 