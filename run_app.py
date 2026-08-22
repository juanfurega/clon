"""Script principal para iniciar el servidor de Cuequi y abrir el navegador automáticamente."""

import time
import webbrowser
import threading
import uvicorn
from interface.api import app

URL = "http://localhost:8000"


def open_browser():
    """Espera a que el servidor esté activo y abre el navegador automáticamente."""
    time.sleep(1.2)
    print(f"\n🚀 Abriendo navegador en: {URL} ...\n")
    webbrowser.open(URL)


def main():
    print("=" * 60)
    print("🤖 INICIANDO CLON DIGITAL — CUEQUI")
    print(f"🌐 Servidor web: {URL}")
    print("=" * 60)

    # Iniciar hilo para abrir el navegador sin bloquear el inicio del servidor
    threading.Thread(target=open_browser, daemon=True).start()

    # Iniciar servidor Uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
