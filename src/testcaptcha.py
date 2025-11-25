from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request
import time
import os
import warnings
from openai import OpenAI  # Cambiamos Anthropic por OpenAI

# Suprimir advertencias
warnings.filterwarnings("ignore")

# ========================================
# CONFIGURAR API (USANDO OPENAI WHISPER)
# ========================================
# OpenAI Whisper es mucho mejor para transcripción de audio ruidoso
OPENAI_API_KEY = "tu-api-key-de-openai-aqui"  # ⚠️ Reemplaza con tu API key
client = OpenAI(api_key=OPENAI_API_KEY)

def transcribir_audio_con_whisper(audio_path):
    """
    Usa OpenAI Whisper para transcribir el audio del captcha.
    Whisper es ideal porque limpia el ruido de fondo automáticamente.
    """
    try:
        print("🎧 Procesando audio con Whisper...")
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="text" # Obtenemos texto directo
            )
        
        # Limpiar el texto (quitar puntos, espacios extra)
        texto_limpio = transcript.strip().replace(".", "").lower()
        return texto_limpio
    
    except Exception as e:
        print(f"✗ Error al transcribir: {e}")
        return None

# Configuración de Chrome
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled") # Ayuda a evitar detección básica
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

try:
    print("🌐 Iniciando navegador...")
    driver.get("https://www.google.com/recaptcha/api2/demo")
    time.sleep(3)

    # ========================================
    # UBICAR EL IFRAME DEL CHECKBOX
    # ========================================
    iframe_checkbox = driver.find_element(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
    driver.switch_to.frame(iframe_checkbox)
    time.sleep(1)

    # ========================================
    # HACER CLIC EN EL CHECKBOX
    # ========================================
    print("👆 Clic en el checkbox...")
    checkbox = driver.find_element(By.ID, "recaptcha-anchor")
    checkbox.click()
    time.sleep(4) # Espera un poco más por si aparece el desafío visual

    # Volver al contexto principal
    driver.switch_to.default_content()
    
    # ========================================
    # VERIFICAR SI APARECIÓ EL DESAFÍO
    # ========================================
    # Buscar el iframe del desafío (bframe)
    iframes_challenge = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'bframe')]")
    
    if len(iframes_challenge) > 0:
        driver.switch_to.frame(iframes_challenge[0])
        time.sleep(2)
        
        # ========================================
        # HACER CLIC EN EL BOTÓN DE AUDIO
        # ========================================
        print("🔊 Cambiando a desafío de audio...")
        audio_button = driver.find_element(By.ID, "recaptcha-audio-button")
        audio_button.click()
        time.sleep(4) # Importante esperar a que cargue el audio
        
        # ========================================
        # DESCARGAR EL AUDIO DEL CAPTCHA
        # ========================================
        try:
            audio_source = driver.find_element(By.ID, "audio-source")
            audio_url = audio_source.get_attribute("src")
            
            print(f"⬇️ Descargando audio desde: {audio_url[:30]}...")
            
            # Usamos un header básico para que no bloqueen la descarga
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(audio_url, "captcha_audio.mp3")
            
            # ========================================
            # TRANSCRIBIR
            # ========================================
            texto_transcrito = transcribir_audio_con_whisper("captcha_audio.mp3")
            
            if texto_transcrito:
                print(f"📝 Texto obtenido: '{texto_transcrito}'")
                
                # ========================================
                # ESCRIBIR LA RESPUESTA
                # ========================================
                audio_response = driver.find_element(By.ID, "audio-response")
                audio_response.send_keys(texto_transcrito)
                time.sleep(1)
                
                # ========================================
                # HACER CLIC EN VERIFICAR
                # ========================================
                verify_button = driver.find_element(By.ID, "recaptcha-verify-button")
                verify_button.click()
                print("📨 Respuesta enviada.")
                time.sleep(4)
            else:
                print("✗ No se obtuvo transcripción.")

        except Exception as e:
            print(f"⚠️ Error en el proceso de audio (puede que Google te haya bloqueado temporalmente): {e}")
        
        # Volver al contexto principal
        driver.switch_to.default_content()
        
    else:
        print("✅ El captcha se resolvió solo con el clic (No challenge).")

    # ========================================
    # VERIFICACIÓN FINAL
    # ========================================
    driver.switch_to.frame(iframe_checkbox)
    is_checked = driver.find_element(By.ID, "recaptcha-anchor").get_attribute("aria-checked")
    
    if is_checked == "true":
        print("\n🎉 ¡CAPTCHA RESUELTO CON ÉXITO! 🎉")
    else:
        print("\n❌ Falló la resolución del captcha.")

except Exception as e:
    print(f"Error general: {e}")

finally:
    # Limpieza
    if os.path.exists("captcha_audio.mp3"):
        os.remove("captcha_audio.mp3")
    print("🧹 Limpieza terminada. Cerrando en 5 segundos...")
    time.sleep(5)
    driver.quit()