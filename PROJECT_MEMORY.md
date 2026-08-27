# OmniUSB Farm Manager - Memoria del Proyecto

Este documento contiene todo el contexto, arquitectura y estado actual del proyecto OmniUSB Farm Manager para que cualquier nuevo agente de IA pueda retomarlo instantáneamente.

## 1. Descripción General
OmniUSB Farm Manager es una aplicación de escritorio para Windows construida con **Python** y **CustomTkinter** (CTK). Actúa como un panel centralizado para gestionar una granja de dispositivos Android físicos (celulares) a través de ADB (Android Debug Bridge).

- **Ruta principal:** `c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager`
- **Archivo principal:** `app.py` (Aplicación monolítica con hilos)
- **Controlador UI:** CustomTkinter
- **Dependencias core:** `adb-utils`, `scrcpy`

## 2. Características Principales Implementadas
1. **Escaneo y Conexión Automática:**
   - Detecta dispositivos conectados mediante ADB.
   - Lee el modelo y nivel de batería automáticamente.
2. **Panel de Control (Dashboard):**
   - Muestra tarjetas de estado por dispositivo con su IP, IMEI y batería.
   - Permite inyectar proxys estáticos globales de forma silenciosa (usando `settings put global http_proxy`).
   - Botón para abrir **Scrcpy** y ver/controlar la pantalla del dispositivo físicamente.
3. **Plataformas Extra (Inyección de Listas):**
   - Despliegue de URLs y manipulación básica en aplicaciones de música.
4. **Creador de Cuentas (Spotify Bot a ciegas):**
   - Interfaz con casillas de verificación (chulitos) para seleccionar múltiples dispositivos a la vez.
   - Generación de correos electrónicos únicos agregando un número aleatorio a un prefijo (ej: `andro.bot12345@gmail.com`).
   - Automatización mediante toques ADB ciegos y `UIAutomator` para encontrar botones de texto como "Siguiente".
   - **Flujo de Seguridad Actual:** El bot escribe el correo, da siguiente, **espera 8 segundos** (para que cargue la app), escribe la contraseña global proporcionada por el usuario, da a Siguiente y **se detiene intencionalmente** en la selección de la Fecha de Nacimiento para que el usuario termine el proceso manualmente. Las instancias se lanzan con un retraso escalonado de 4 segundos para no saturar ADB ni el PC.

## 3. Estado Técnico y Arquitectura (app.py)
- **Interfaz (GUI):** Está organizada por pestañas (Tabs) como `Panel de Control`, `Tráfico de Datos en Vivo`, `Plataformas Extra` y `Creador de Cuentas`.
- **Multihilo:** Cada automatización en lotes lanza un hilo `threading.Thread` independiente (ej. `_spotify_app_signup_thread`) para no congelar la GUI de Tkinter.
- **Interacciones ADB:** Utiliza comandos `shell input tap`, `shell input text` y `shell input keyevent` para simular acciones humanas.
- **Actualizador Integrado:** `updater.py` maneja las actualizaciones del repositorio, con un fallback seguro a extracción de ZIP si Git falla. (Última versión conocida: 4.5.17).

## 4. Problemas Conocidos y Resoluciones Pasadas
- **Problema de Swipe en Fechas:** Las automatizaciones de deslizar (swipe) la rueda de fechas de Spotify fallaban por resoluciones diferentes o duraciones muy rápidas. Se ajustó a swipes de >1500ms simulando el dedo humano, pero finalmente **se acordó que el bot se detendría antes de la fecha** para que el usuario lo hiciera manualmente.
- **Congelamientos de Interfaz:** Se ha implementado el uso intensivo de `self.after()` y colas de mensajes (`queue`) para evitar fallos de Tkinter al recibir logs desde los hilos de trabajo asíncronos.
- **Saturación ADB:** Se solucionó escalonando el inicio de los hilos del bot a ciegas con pausas.

## 5. Próximos Pasos Pendientes
- Mejorar el monitoreo general de la salud (salud real de la red del proxy inyectado).
- Integración potencial con un backend para reportar cuentas creadas.
