from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request
import time
import os
import warnings
import re
from openai import OpenAI

warnings.filterwarnings("ignore")

# ========================================
# CONFIGURACIÓN
# ========================================
# ⚠️ IMPORTANTE: Reemplaza esto con tu NUEVA API Key. La anterior fue expuesta.
OPENAI_API_KEY = "TU_NUEVA_API_KEY_AQUI"
client = OpenAI(api_key=OPENAI_API_KEY)

def convertir_palabras_a_numeros(texto):
    """
    Convierte palabras numéricas en inglés a sus dígitos correspondientes.
    Ejemplo: "Five two zero" -> "520"
    """
    mapa_numeros = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9'
    }
    
    # Normalizar texto: minúsculas y quitar puntuación
    texto = texto.lower()
    texto = re.sub(r'[.,]', '', texto) # Quitar puntos y comas
    
    palabras = texto.split()
    resultado = ""
    
    for palabra in palabras:
        if palabra in mapa_numeros:
            resultado += mapa_numeros[palabra]
        elif palabra.isdigit():
            resultado += palabra
            
    return resultado

def transcribir_audio_automaticamente(audio_path):
    try:
        print("🎧 Transcribiendo audio con Whisper AI...")
        
        with open(audio_path, "rb") as audio_file:
            transcript_obj = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="text",
                language="en"
            )
        
        # Whisper devuelve un string directo cuando response_format="text"
        texto_crudo = str(transcript_obj)
        print(f"📝 Whisper escuchó: '{texto_crudo.strip()}'")

        # Procesar el texto para obtener solo los números
        texto_limpio = convertir_palabras_a_numeros(texto_crudo)
        
        # Si la conversión falló (Whisper devolvió algo raro), intentamos extraer dígitos crudos
        if not texto_limpio:
             texto_limpio = ''.join(filter(str.isdigit, texto_crudo))

        print(f"✓ Texto procesado para enviar: '{texto_limpio}'")
        return texto_limpio
    
    except Exception as e:
        print(f"✗ Error al transcribir audio: {e}")
        return None

def resolver_recaptcha_automatico(url="https://www.google.com/recaptcha/api2/demo", max_intentos=3):
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    # Argumentos anti-detección básicos
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    wait = WebDriverWait(driver, 15) # Aumentado tiempo de espera a 15s

    try:
        print(f"🌐 Navegando a {url}...")
        driver.get(url)
        time.sleep(2)

        # 1. ENTRAR AL IFRAME DEL CHECKBOX
        print("👆 Buscando checkbox...")
        iframe_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'recaptcha') and contains(@src, 'anchor')]")))
        driver.switch_to.frame(iframe_checkbox)
        
        checkbox = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-anchor")))
        checkbox.click()
        print("👆 Clic en checkbox realizado.")
        
        driver.switch_to.default_content()
        time.sleep(3)

        # 2. VERIFICAR SI PIDIÓ CHALLENGE
        # Buscamos el iframe del desafío (bframe)
        iframes_challenge = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'bframe')]")
        
        # Verificar si el checkbox ya está marcado (sin desafío visual/audio)
        driver.switch_to.frame(iframe_checkbox)
        is_checked = driver.find_element(By.ID, "recaptcha-anchor").get_attribute("aria-checked")
        driver.switch_to.default_content()

        if is_checked == "true":
            print("🎉 ¡Captcha resuelto directo (One-Click)!")
            time.sleep(3)
            driver.quit()
            return True

        if not iframes_challenge:
            print("⚠️ No se encontró desafío, pero tampoco está marcado. Algo raro pasó.")
            driver.quit()
            return False

        # 3. CAMBIAR AL MODO AUDIO
        print("🎯 Desafío detectado, cambiando a iframe de desafío...")
        driver.switch_to.frame(iframes_challenge[0])
        time.sleep(1)
        
        audio_button = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-audio-button")))
        audio_button.click()
        print("🔊 Cambiado a modo audio.")
        time.sleep(2)

        # Verificar si Google nos bloqueó el audio temporalmente
        try:
            error_msg = driver.find_element(By.CLASS_NAME, "rc-audiochallenge-error-message")
            if error_msg.is_displayed():
                print("❌ Google dice: 'Tu ordenador o red envían tráfico automatizado'. IP Bloqueada temporalmente.")
                driver.quit()
                return False
        except:
            pass # No hay mensaje de error, continuamos

        # 4. DESCARGAR AUDIO
        audio_source = wait.until(EC.presence_of_element_located((By.ID, "audio-source")))
        audio_url = audio_source.get_attribute("src")
        
        print("⬇️ Descargando audio...")
        # Usamos requests o urllib con headers para no ser bloqueados en la descarga
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(audio_url, "captcha_audio.mp3")
        
        # 5. TRANSCRIBIR Y ENVIAR
        texto_transcrito = transcribir_audio_automaticamente("captcha_audio.mp3")
        
        if not texto_transcrito:
            print("❌ Transcripción vacía.")
            driver.quit()
            return False

        print(f"📝 Enviando respuesta: {texto_transcrito}")
        audio_response = driver.find_element(By.ID, "audio-response")
        audio_response.send_keys(texto_transcrito)
        time.sleep(1)
        
        verify_button = driver.find_element(By.ID, "recaptcha-verify-button")
        verify_button.click()
        time.sleep(3)
        
        # 6. VERIFICACIÓN FINAL
        driver.switch_to.default_content()
        driver.switch_to.frame(iframe_checkbox)
        is_checked = driver.find_element(By.ID, "recaptcha-anchor").get_attribute("aria-checked")
        
        if is_checked == "true":
            print("\n🎉 ¡CAPTCHA RESUELTO CON ÉXITO! 🎉\n")
            time.sleep(3)
            driver.quit()
            # Limpieza
            if os.path.exists("captcha_audio.mp3"):
                os.remove("captcha_audio.mp3")
            return True
        else:
            print("❌ Falló la verificación.")
            driver.quit()
            return False

    except Exception as e:
        print(f"⚠️ Error general: {e}")
        try:
            driver.quit()
        except:
            pass
        return False

if __name__ == "__main__":
    resolver_recaptcha_automatico()