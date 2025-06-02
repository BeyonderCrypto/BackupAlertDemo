### **Requisitos previos**

1. **Node.js v18 LTS+** instalado localmente.
2. **Python 3.9+** instalado localmente.
3. **Azure Functions Core Tools** ([para desarrollo local](https://www.notion.so/Gu-a-instalar-Azure-Functions-Core-Tools-4-1ffc61fcf73080219314eb717c295b26?pvs=21)).
4. **Cuenta de Azure** (gratis para pruebas).
5. **Cuenta en Twilio** (trial gratuito con crédito inicial).
6. **Visual Studio Code** (opcional, pero recomendado).
    1. Extensión Azure Functions. ([instalar desde aquí](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions))

### **Paso 1: Crear el proyecto de Azure Functions**

Ejecuta estos comandos en tu terminal:

```bash
# Crear carpeta del proyecto
mkdir BackupAlertDemo
cd BackupAlertDemo

# Inicializar proyecto con el worker runtime de Python
func init . --worker-runtime python

# Crear función HTTP trigger
func new --name SendAlert --template "HTTP trigger"

```

---

### **Paso 2: Estructura del proyecto moderno**

La estructura será:

```
BackupAlertDemo/
├── .venv/                   # Entorno virtual (opcional)
├── SendAlert/
│   └── function.json       # Configuración de la función
├── function_app.py         # Código principal (nuevo modelo)
├── requirements.txt        # Dependencias
└── local.settings.json     # Variables locales

```

Nota:  **Crea un entorno virtual (si aún no tienes uno):** Es una buena práctica usar un entorno virtual para cada proyecto de Python para aislar sus dependencias. Si no tienes una carpeta como `.venv` en tu proyecto, créala:

```bash
python3 -m venv .venv
```

(Puedes nombrar la carpeta del entorno virtual como quieras, pero `.venv` es una convención común).

Tomar en cuenta que es recomendable instalar el requirements.txt desde el entorno virtual ejecutando antes en tu terminal desde la carpeta raíz de tu proyecto: 

```bash
source .venv/bin/activate
```

### **Paso 3: Instalar dependencias**

1. Edita el archivo `requirements.txt` y agrega:
    
    ```
    twilio
    azure-functions
    ```
    
2. Instala las dependencias ( sino tienes instalado pip: sudo apt install python3-pip -y):
    
    ```bash
    pip install -r requirements.txt
    ```
    

---

### **Paso 4: Implementar la lógica en function_app.py**

Reemplaza el contenido de `function_app.py` con:

```python
import azure.functions as func
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="SendAlert", methods=["POST"])
def send_alert(req: func.HttpRequest) -> func.HttpResponse:
    # Configurar Twilio
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    twilio_phone = os.environ["TWILIO_PHONE_NUMBER"]
    user_phone = "+51987654321"  # Reemplazar con número del alumno

    client = Client(account_sid, auth_token)

    # Simular evento de respaldo
    backup_data = {
        "status": "EXITO",
        "db_name": "MySQL_Inventario",
        "timestamp": "2024-05-20 22:00:00",
        "size": "2.5GB"
    }

    # Mensaje para WhatsApp
    alert_message = (
        f"🛡️ *Respaldo de BD Completo* 🛡️\\n"
        f"• Base de datos: {backup_data['db_name']}\\n"
        f"• Estado: {backup_data['status']}\\n"
        f"• Tamaño: {backup_data['size']}\\n"
        f"• Hora: {backup_data['timestamp']}"
    )

    # Enviar WhatsApp
    whatsapp = client.messages.create(
        from_=f'whatsapp:{twilio_phone}',
        body=alert_message,
        to=f'whatsapp:{user_phone}'
    )

    # Crear llamada de voz
    response = VoiceResponse()
    response.say(
        f"Alerta de sistema: Respaldo de {backup_data['db_name']} completado exitosamente. "
        f"Tamaño: {backup_data['size']}. Hora del respaldo: {backup_data['timestamp']}",
        voice="woman",
        language="es-MX"
    )

    call = client.calls.create(
        twiml=str(response),
        to=user_phone,
        from_=twilio_phone
    )

    return func.HttpResponse(
        f"✅ Alertas enviadas:\\nWhatsApp SID: {whatsapp.sid}\\nLlamada SID: {call.sid}",
        status_code=200
    )

```

---

### **Paso 5: Configurar function.json (HTTP Trigger)**  

Actualiza `SendAlert/function.json` para permitir POST (solo si existe el archivo en function.json):

```json
{
  "scriptFile": "../function_app.py",
  "bindings": [
    {
      "authLevel": "anonymous",
      "type": "httpTrigger",
      "direction": "in",
      "name": "req",
      "methods": ["post"]
    },
    {
      "type": "http",
      "direction": "out",
      "name": "$return"
    }
  ]
}

```

---

### **Paso 6: Configurar variables locales (local.settings.json)**

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "TWILIO_ACCOUNT_SID": "TU_SID",
    "TWILIO_AUTH_TOKEN": "TU_TOKEN",
    "TWILIO_PHONE_NUMBER": "+123456789"
  }
}

```

---

### **Paso 7: Ejecutar y probar localmente**

```bash
func start

```

Usa Postman o curl para probar:

```bash
curl -X POST http://localhost:7071/api/SendAlert

```

---

### **Resultado esperado en el teléfono:**

1. **SMS / WhatsApp**:
    
    ```
    🛡️ *Respaldo de BD Completo* 🛡️
    • Base de datos: MySQL_Inventario
    • Estado: EXITO
    • Tamaño: 2.5GB
    • Hora: 2024-05-20 22:00:00
    
    ```
