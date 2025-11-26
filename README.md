# VulnerarCaptcha-2

> ⚠️ **Aviso legal y ético** — Este proyecto demuestra vulnerabilidades en mecanismos CAPTCHA. Su uso debe ser estrictamente con fines educativos, de auditoría o investigación. No promuevas ni uses estas técnicas para actividades maliciosas, automatización indebida o vulnerar la privacidad de terceros.

## 📄 ¿Qué es VulnerarCaptcha-2?

VulnerarCaptcha-2 es un script en Python cuyo propósito es mostrar cómo ciertos sistemas CAPTCHA pueden ser vulnerables bajo determinadas condiciones. El proyecto permite —bajo un entorno controlado y con fines de auditoría— analizar la robustez de un CAPTCHA, sirviendo como ejercicio didáctico sobre seguridad y análisis de vulnerabilidades.

## 🧪 Casos de uso / Cuándo usarlo

- Auditorías de seguridad en desarrollos propios.  
- Evaluación de mecanismos CAPTCHA en entornos de prueba.  
- Investigación académica o formativa sobre seguridad web.  
- Comprender cómo funcionan los ataques automatizados (para mitigar vulnerabilidades, no explotarlas).  

## 🔧 Requisitos

- Python 3.x  
- Dependencias que se listan en `requirements.txt` (si existe) — de lo contrario, instalar manualmente las librerías que use el script.  
- Un entorno de prueba privado: **no uses este proyecto contra sitios de terceros sin autorización explícita.**

## 🚀 Instalación / Ejecución

```bash
# Clonar el repositorio
git clone https://github.com/KeviinYepes/VulnerarCaptcha-2.git
cd VulnerarCaptcha-2

# (Opcional) crear un entorno virtual
python -m venv venv
source venv/bin/activate  # en Linux/Mac
venv\Scripts\activate     # en Windows

# Instalar dependencias
pip install -r requirements.txt   # si hay archivo de requerimientos

# Ejecutar el script principal (ajusta el nombre según lo que haya en src/)
python src/main.py   # o el script que corresponda
