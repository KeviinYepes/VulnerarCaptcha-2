from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import speech_recognition as sr
import urllib.request
import time
import os
import warnings
import requests
import io

# Suprimir advertencias
warnings.filterwarnings("ignore")

# Configuración de Chrome
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

wait = WebDriverWait(driver, 10)

def solve_audio_captcha(audio_url):
    """Resolver captcha de audio sin dependencias externas"""
    try:
        # Descargar audio
        response = requests.get(audio_url)
        audio_content = response.content
        
        # Guardar como MP3 temporalmente
        with open("temp_audio.mp3", "wb") as f:
            f.write(audio_content)
        
        # Método 1: Intentar con pydub si está disponible
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3("temp_audio.mp3")
            audio.export("temp_audio.wav", format="wav")
            
            recognizer = sr.Recognizer()
            with sr.AudioFile("temp_audio.wav") as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language="en-US")
                return text
                
        except ImportError:
            print("ℹ pydub no disponible, usando método alternativo...")
        except Exception as e:
            print(f"ℹ Error con pydub: {e}, usando método alternativo...")
        
        # Método 2: Usar un servicio online de conversión
        try:
            return convert_audio_online(audio_content)
        except:
            pass
            
        # Método 3: Reproducir audio y pedir entrada manual
        print("🔊 No se pudo procesar automáticamente. Reproduciendo audio...")
        return manual_audio_input("temp_audio.mp3")
        
    except Exception as e:
        print(f"✗ Error procesando audio: {e}")
        return None
    finally:
        # Limpiar archivos temporales
        for file in ["temp_audio.mp3", "temp_audio.wav"]:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass

def convert_audio_online(audio_content):
    """Intentar conversión usando servicio online (opcional)"""
    # Puedes integrar con un servicio como CloudConvert
    print("ℹ Intentando conversión online...")
    return None

def manual_audio_input(audio_file):
    """Método manual: reproducir audio y pedir entrada"""
    try:
        # Intentar reproducir el audio
        import subprocess
        if os.path.exists(audio_file):
            subprocess.run(["start", audio_file], shell=True, check=True)
    except:
        print("🔊 Abre el archivo 'temp_audio.mp3' manualmente para escuchar el audio")
    
    # Pedir entrada al usuario
    text = input("🎤 Por favor, ingresa el texto que escuchaste en el audio: ")
    return text.strip()

try:
    driver.get("https://www.google.com/recaptcha/api2/demo")
    time.sleep(3)

    # ========================================
    # UBICAR EL IFRAME DEL CHECKBOX
    # ========================================
    iframe_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'recaptcha')]")))
    driver.switch_to.frame(iframe_checkbox)
    time.sleep(1)

    # ========================================
    # HACER CLIC EN EL CHECKBOX
    # ========================================
    checkbox = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-anchor")))
    checkbox.click()
    time.sleep(3)

    # Volver al contexto principal
    driver.switch_to.default_content()
    time.sleep(2)

    # ========================================
    # VERIFICAR SI APARECIÓ EL DESAFÍO
    # ========================================
    try:
        # Buscar el iframe del desafío
        iframe_challenge = wait.until(EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'recaptcha') and contains(@src, 'bframe')]")))
        driver.switch_to.frame(iframe_challenge)
        time.sleep(2)
        
        # ========================================
        # HACER CLIC EN EL BOTÓN DE AUDIO
        # ========================================
        audio_button = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-audio-button")))
        audio_button.click()
        time.sleep(2)
        
        # ========================================
        # OBTENER URL DEL AUDIO
        # ========================================
        try:
            audio_source = wait.until(EC.presence_of_element_located((By.ID, "audio-source")))
            audio_url = audio_source.get_attribute("src")
        except:
            download_link = driver.find_element(By.CSS_SELECTOR, "body > div > div > div.rc-audiochallenge-tdownload > a")
            audio_url = download_link.get_attribute("href")
        
        print(f"URL del audio: {audio_url}")
        
        # ========================================
        # RESOLVER CAPTCHA DE AUDIO
        # ========================================
        text = solve_audio_captcha(audio_url)
        
        if text:
            print(f"✓ Texto reconocido: {text}")
            
            # ========================================
            # ESCRIBIR LA RESPUESTA
            # ========================================
            audio_response = wait.until(EC.presence_of_element_located((By.ID, "audio-response")))
            audio_response.clear()
            audio_response.send_keys(text.lower())
            time.sleep(1)
            
            # ========================================
            # HACER CLIC EN VERIFICAR
            # ========================================
            verify_button = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-verify-button")))
            verify_button.click()
            time.sleep(3)
            
            print("✓ Respuesta enviada")
        else:
            print("✗ No se pudo obtener texto del audio")
        
        # Volver al contexto principal
        driver.switch_to.default_content()
        time.sleep(2)
        
        # ========================================
        # VERIFICAR SI SE RESOLVIÓ EL CAPTCHA
        # ========================================
        driver.switch_to.frame(iframe_checkbox)
        is_checked = driver.find_element(By.ID, "recaptcha-anchor").get_attribute("aria-checked")
        
        if is_checked == "true":
            print("✓✓✓ ¡CAPTCHA RESUELTO CON ÉXITO! ✓✓✓")
        else:
            print("✗ El captcha no se resolvió correctamente")
        
        driver.switch_to.default_content()

    except Exception as e:
        print(f"✓ No apareció desafío adicional: {e}")

    time.sleep(3)

except Exception as e:
    print(f"✗ Error general: {e}")

finally:
    driver.quit()