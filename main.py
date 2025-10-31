import google.generativeai as genai
import json
import os
from flask import Flask, render_template, request, session, Markup # Importamos Flask
import textwrap

# --- 0. INICIALIZACIÓN DE LA APLICACIÓN WEB FLASK ---
app = Flask(__name__)
# Necesitamos una clave secreta para manejar las sesiones (donde guardaremos el historial del chat)
app.secret_key = 'una-clave-muy-secreta-para-asai-gen'

print("Iniciando sistema Asai-Gen v2.1 (Visual Engine)...")

# --- 1. CONFIGURACIÓN Y CARGA DEL CEREBRO ---
try:
    api_key = os.environ['GOOGLE_API_KEY']
    genai.configure(api_key=api_key)
except KeyError:
    print("\nERROR: Clave de API no encontrada.")
    exit()

try:
    with open('prompt.json', 'r', encoding='utf-8') as f:
        system_manifest_data = json.load(f)
    system_instruction = system_manifest_data["ai_system_manifest"]
    initialization_message = system_instruction["initialization_protocol"]["message"]
except Exception as e:
    print(f"\nERROR al cargar 'prompt.json': {e}")
    exit()

# --- 2. INICIALIZACIÓN DE LOS MODELOS DE IA ---
# Modelo de texto (el "cerebro consultor")
text_model = genai.GenerativeModel(
    model_name='gemini-1.5-pro-latest',
    system_instruction=system_instruction
)

# Modelo de imagen (los "brazos para dibujar")
image_model = genai.GenerativeModel(model_name='gemini-pro-vision') # Este es un placeholder, la generación se hace con otra función.
# La generación de imágenes en la librería de google se hace a través de una función específica.

# --- 3. FUNCIONES AUXILIARES ---

def generate_image(prompt_text):
    """Genera una imagen usando el API y devuelve la URL o los datos de la imagen."""
    try:
        # La forma correcta de generar imágenes con la API actual es usando `genai.generate_text`
        # con un modelo de imagen como `gemini-pro`. Para simplificar, simularemos la llamada directa.
        # En una implementación real, podrías usar una API como Stability AI o DALL-E.
        # Por ahora, vamos a usar un placeholder.
        # La API de Gemini aún no expone la generación de imágenes de forma directa en esta librería.
        # ¡Vamos a usar un truco! Le pediremos a Gemini que genere el prompt para otra IA.

        # Esta es la parte importante: crear un prompt visual detallado.
        image_generation_prompt = f"""
        photorealistic interior design render, 4k, professionally color graded, cinematic lighting.
        Style: {prompt_text}.
        High detail, octane render, focused, sharp.
        """
        
        # En una app real, aquí llamarías al API de imágenes.
        # response = stability_api.generate(prompt=image_generation_prompt)
        # return response.url
        
        # Como simulación, devolveremos el prompt que se generó, para que veas qué se le pediría a la IA de imagen.
        return f"**[Render Simulado]** Se generaría una imagen con el siguiente prompt: <br><i>{image_generation_prompt}</i><br><br> (Nota: La generación de imágenes directa desde esta librería aún está en desarrollo. Este es un placeholder funcional)."
        
    except Exception as e:
        return f"Error al generar la imagen: {e}"

# --- 4. RUTAS DE LA APLICACIÓN WEB ---

@app.route('/')
def home():
    """Muestra la página de inicio y reinicia el chat."""
    session['chat_history'] = [] # Limpiamos el historial
    return render_template('index.html', initial_message=initialization_message)

@app.route('/send', methods=['POST'])
def send_message():
    """Recibe el mensaje del usuario, lo procesa y devuelve la conversación actualizada."""
    user_input = request.form['user_input']
    
    # Añadimos el mensaje del usuario al historial
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    # Guardamos el historial de la sesión para poder enviarlo a la API
    chat_history_for_api = []
    for entry in session['chat_history']:
        chat_history_for_api.append({'role': entry['role'], 'parts': [{'text': entry['text']}]})
        
    session['chat_history'].append({'role': 'user', 'text': user_input})

    # Inicia un nuevo chat con el historial
    chat = text_model.start_chat(history=chat_history_for_api)
    
    # Envía el nuevo mensaje a la IA de texto
    response = chat.send_message(user_input)
    ai_response_text = response.text
    
    # Guardamos la respuesta de la IA
    session['chat_history'].append({'role': 'model', 'text': ai_response_text})
    
    # --- ¡LA MAGIA NUEVA! ---
    # Decidimos si la respuesta de la IA es un concepto que se puede renderizar.
    # Usaremos palabras clave como "concepto", "propuesta", "diseño", "distribución".
    render_keywords = ["concepto:", "propuesta:", "diseño:", "distribución:", "materiales:"]
    if any(keyword in ai_response_text.lower() for keyword in render_keywords):
        # Si la respuesta parece un concepto, generamos la imagen.
        image_html = generate_image(ai_response_text)
        # Y la añadimos al historial de la IA
        session['chat_history'].append({'role': 'model', 'text': image_html})

    # Convertimos el historial a un formato HTML para mostrarlo
    formatted_chat_history = ""
    for message in reversed(session['chat_history']): # Revertido para mostrar los nuevos primero
        className = "user" if message['role'] == 'user' else "ai"
        # Usamos Markup para que Flask interprete el HTML de la imagen
        formatted_chat_history += f"<div class='message {className}'><p>{Markup(message['text'].replace(os.linesep, '<br>'))}</p></div>"

    return render_template('index.html', initial_message=initialization_message, chat_history=formatted_chat_history)


# --- 5. EJECUTAR LA APLICACIÓN ---
if __name__ == '__main__':
    # Esto hace que se ejecute en Replit correctamente
    app.run(host='0.0.0.0', port=81)
