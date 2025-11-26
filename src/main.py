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


OPENAI_API_KEY = "TU_NUEVA_API_KEY_AQUI"
client = OpenAI(api_key=OPENAI_API_KEY)

def convertir_palabras_a_numeros(texto):
    mapa_numeros = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9'
    }
    
    texto = texto.lower()
    texto = re.sub(r'[.,]', '', texto)
    
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
        print("Transcribiendo audio con Whisper...")
        
        with open(audio_path, "rb") as audio_file:
            transcript_obj = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
                language="en"
            )
        
        texto_crudo = str(transcript_obj)
        print(f"Texto crudo detectado: '{texto_crudo.strip()}'")

        texto_limpio = convertir_palabras_a_numeros(texto_crudo)
        
        if not texto_limpio:
            texto_limpio = ''.join(filter(str.isdigit, texto_crudo))

        print(f"Texto procesado: '{texto_limpio}'")
        return texto_limpio
    
    except Exception as e:
        print(f"Error al transcribir audio: {e}")
        return None

def resolver_recaptcha_automatico(url="https://www.google.com/recaptcha/api2/demo", max_intentos=3):
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    wait = WebDriverWait(driver, 15)

    try:
        print(f"Navegando a {url}...")
        driver.get(url)
        time.sleep(2)

        print("Buscando checkbox...")
        iframe_checkbox = wait.until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'recaptcha') and contains(@src, 'anchor')]"))
        )
        driver.switch_to.frame(iframe_checkbox)
        
        checkbox = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-anchor")))
        checkbox.click()
        print("Checkbox presionado.")
        
        driver.switch_to.default_content()
        time.sleep(3)

        iframes_challenge = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'bframe')]")
        
        driver.switch_to.frame(iframe_checkbox)
        is_checked = driver.find_element(By.ID, "recaptcha-anchor").get_attribute("aria-checked")
        driver.switch_to.default_content()

        if is_checked == "true":
            print("Captcha resuelto sin desafío adicional.")
            time.sleep(3)
            driver.quit()
            return True

        if not iframes_challenge:
            print("No se encontró desafío y el captcha no está marcado.")
            driver.quit()
            return False

        print("Desafío detectado, cambiando iframe...")
        driver.switch_to.frame(iframes_challenge[0])
        time.sleep(1)
        
        audio_button = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-audio-button")))
        audio_button.click()
        print("Modo audio activado.")
        time.sleep(2)

        try:
            error_msg = driver.find_element(By.CLASS_NAME, "rc-audiochallenge-error-message")
            if error_msg.is_displayed():
                print("Google bloqueó el audio temporalmente. IP restringida.")
                driver.quit()
                return False
        except:
            pass

        audio_source = wait.until(EC.presence_of_element_located((By.ID, "audio-source")))
        audio_url = audio_source.get_attribute("src")
        
        print("Descargando audio...")
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(audio_url, "captcha_audio.mp3")
        
        texto_transcrito = transcribir_audio_automaticamente("captcha_audio.mp3")
        
        if not texto_transcrito:
            print("Transcripción vacía.")
            driver.quit()
            return False

        print(f"Enviando respuesta: {texto_transcrito}")
        audio_response = driver.find_element(By.ID, "audio-response")
        audio_response.send_keys(texto_transcrito)
        time.sleep(1)
        
        verify_button = driver.find_element(By.ID, "recaptcha-verify-button")
        verify_button.click()
        time.sleep(3)
        
        driver.switch_to.default_content()
        driver.switch_to.frame(iframe_checkbox)
        is_checked = driver.find_element(By.ID, "recaptcha-anchor").get_attribute("aria-checked")
        
        if is_checked == "true":
            print("Captcha resuelto correctamente.")
            time.sleep(3)
            driver.quit()

            if os.path.exists("captcha_audio.mp3"):
                os.remove("captcha_audio.mp3")
            return True
        else:
            print("La verificación falló.")
            driver.quit()
            return False

    except Exception as e:
        print(f"Error general: {e}")
        try:
            driver.quit()
        except:
            pass
        return False

if __name__ == "__main__":
    resolver_recaptcha_automatico()
