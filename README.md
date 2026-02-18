# 📋 Formularios de Mantenimiento Digitalizados

Aplicación web para digitalizar y completar los formularios de mantenimiento del Butetown Link Tunnel.

## 🎯 Características

✅ **191 formularios individualizados** extraídos del documento DOCX original
- Cada formulario tiene sus propias tareas específicas
- Información de ubicaciones y frecuencias
- Referencias de sección (2.1.3, 2.1.4, etc.)

✅ **Funcionalidades completas:**
- ☑️ Tareas checkeables (marcable cada tarea completada)
- 💬 Campo de comentarios y observaciones
- 📷 Carga de fotografías (drag & drop)
- ✍️ Dos firmas digitales (Ingeniero + Supervisor)
- 💾 Guardado automático en JSON
- 🖨️ Imprimible
- 🔍 Búsqueda de formularios por sección

## 🚀 Cómo usar

### Opción 1: Servidor Local (Recomendado)

```bash
cd c:\TempApp\Cardiff Forms
python server.py
```

Luego abre en tu navegador: **http://localhost:8080**

### Opción 2: Abrir directamente

Doble-clic en `index.html` (puede tener limitaciones de seguridad en algunos navegadores)

## 📁 Archivos

- **index.html** - Aplicación web principal
- **forms_parsed.json** - Datos de todos los 191 formularios extraídos
- **server.py** - Servidor local
- **Section 4 Schedule of Reports Word Nuevo.docx** - Documento original
- **parse_forms.py** - Script para extraer formularios del DOCX

## 📝 Flujo de uso

1. **Seleccionar formulario** - Haz clic en la sección en el panel izquierdo
2. **Completar información** - Rellenallos campos visibles
3. **Marcar tareas** - Checkea las tareas completadas
4. **Añadir fotos** - Sube imágenes de contexto
5. **Firmar** - Dibuja las dos firmas digitales
6. **Guardar** - Se descarga JSON automáticamente y se guarda en el navegador

## 💾 Almacenamiento

- Los formularios completados se guardan en **localStorage** del navegador
- Se descarga un archivo **JSON** con los datos completos
- Las fotos se incluyen en base64 dentro del JSON

## 🔧 Personalización

### Agregar más campos
Edita el archivo `index.html` en la sección `<!-- INFORMACIÓN GENERAL -->` y añade nuevos `<div class="form-group">`

### Cambiar estilos
Modifica las variables CSS en el bloque `<style>` al inicio del HTML

### Exportar datos completos
Los datos se guardan en localStorage. Accede desde la consola del navegador:
```javascript
JSON.parse(localStorage.getItem('completedForms'))
```

## 🌐 Navegadores soportados

- Chrome/Chromium
- Firefox
- Edge
- Safari

## 📞 Soporte

Para problemas:
1. Asegúrate que el servidor está corriendo (`python server.py`)
2. Limpia el caché del navegador (Ctrl+Shift+Del)
3. Intenta en otro navegador

---

**Version 1.0** - Aplicación creada automaticamente desde DOCX
