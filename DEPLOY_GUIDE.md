# 📤 GUÍA DE DEPLOY - GITHUB

## ✅ **ARCHIVOS LISTOS PARA SUBIR**

### **Archivos Principales (OBLIGATORIOS):**

1. **app.py** ⭐
   - Aplicación principal
   - 3132 líneas
   - Sin errores
   
2. **requirements.txt** ⭐
   - Dependencias del proyecto
   - 7 paquetes principales

3. **README.md** ⭐
   - Documentación principal
   - Instrucciones de instalación
   - Features completas

4. **.gitignore** ⭐
   - Archivos a ignorar
   - Protege API keys

5. **LICENSE** ⭐
   - Licencia MIT
   - Open source

---

## 📂 **ESTRUCTURA RECOMENDADA**

```
trend-hunter-pro/
├── app.py                          ⭐ OBLIGATORIO
├── requirements.txt                ⭐ OBLIGATORIO
├── README.md                       ⭐ OBLIGATORIO
├── .gitignore                      ⭐ OBLIGATORIO
├── LICENSE                         ⭐ OBLIGATORIO
└── docs/                           📁 OPCIONAL
    ├── SPRINT1_DOCUMENTATION.md
    ├── SPRINT2_DOCUMENTATION.md
    ├── SPRINT3_FINAL.md
    ├── SPRINT4_FINAL.md
    ├── SPRINT4_TOOLTIPS.md
    ├── SPRINT4_ANIMATIONS.md
    ├── SPRINT4_EMPTY_STATES.md
    └── AUDITORIA_COMPLETA.md
```

---

## 🚀 **PASOS PARA SUBIR A GITHUB**

### **Opción A: GitHub Web (Más Fácil)**

1. **Ir a GitHub.com**
   - Login en tu cuenta
   - Click en "+" → "New repository"

2. **Crear Repositorio:**
   - Name: `trend-hunter-pro`
   - Description: "Herramienta profesional de análisis de tendencias con Google Trends"
   - Public o Private (tú eliges)
   - ✅ Add README (NO marcar, ya tenemos)
   - ✅ Add .gitignore (NO marcar, ya tenemos)
   - ✅ Choose license (NO marcar, ya tenemos)
   - Click "Create repository"

3. **Subir Archivos:**
   - Click "uploading an existing file"
   - Arrastra estos 5 archivos:
     * app.py
     * requirements.txt
     * README.md
     * .gitignore
     * LICENSE
   - Commit message: "Initial commit - Trend Hunter Pro v4.0"
   - Click "Commit changes"

4. **Opcional - Subir Docs:**
   - Click "Add file" → "Create new file"
   - Name: `docs/SPRINT1_DOCUMENTATION.md`
   - Copy/paste contenido
   - Repeat para cada doc

---

### **Opción B: Git Command Line**

1. **Descargar archivos de Claude:**
   - app.py
   - requirements.txt
   - README.md
   - .gitignore
   - LICENSE

2. **Crear carpeta local:**
```bash
mkdir trend-hunter-pro
cd trend-hunter-pro
```

3. **Copiar archivos descargados a la carpeta**

4. **Inicializar Git:**
```bash
git init
git add .
git commit -m "Initial commit - Trend Hunter Pro v4.0"
```

5. **Conectar con GitHub:**
```bash
git remote add origin https://github.com/TU-USUARIO/trend-hunter-pro.git
git branch -M main
git push -u origin main
```

---

## ⚠️ **IMPORTANTE ANTES DE SUBIR**

### **Proteger API Key:**

1. **Buscar en app.py:**
   - Línea ~900: `SERPAPI_KEY = "..."`

2. **Reemplazar con:**
```python
import os
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "YOUR_KEY_HERE")
```

3. **Añadir a .gitignore:**
```
.env
config.py
```

### **Crear .env (NO SUBIR A GITHUB):**
```
SERPAPI_KEY=tu_clave_real_aqui
```

---

## 📝 **CHECKLIST PRE-DEPLOY**

**Antes de subir, verificar:**

- [ ] API key NO está hardcodeada
- [ ] .gitignore incluye .env
- [ ] README.md está completo
- [ ] requirements.txt tiene todas las deps
- [ ] LICENSE está presente
- [ ] app.py compila sin errores
- [ ] Comentarios sensibles removidos
- [ ] URLs internas removidas (si las hay)

---

## 📚 **DOCUMENTACIÓN OPCIONAL**

Si quieres incluir docs técnicas, crea carpeta `docs/` y añade:

```
docs/
├── SPRINT1_DOCUMENTATION.md    (Feature: Estacionalidad, Query Bars)
├── SPRINT2_DOCUMENTATION.md    (Feature: Sparklines, Export)
├── SPRINT3_FINAL.md            (Feature: IA, Bubble, PDF)
├── SPRINT4_FINAL.md            (Feature: Tooltips, Animations, UX)
├── SPRINT4_TOOLTIPS.md         (Detalle: Tooltips)
├── SPRINT4_ANIMATIONS.md       (Detalle: Animaciones)
├── SPRINT4_EMPTY_STATES.md     (Detalle: Empty States)
└── AUDITORIA_COMPLETA.md       (Auditoría código)
```

---

## 🎯 **DESPUÉS DEL DEPLOY**

### **1. Configurar Streamlit Cloud (Opcional):**

- Ir a: https://share.streamlit.io
- Connect GitHub repo
- Deploy automático
- Añadir SERPAPI_KEY en Secrets

### **2. Añadir Badges al README:**

Ya incluidos en README.md:
- ![Version](https://img.shields.io/badge/version-4.0-blue)
- ![Python](https://img.shields.io/badge/python-3.8+-green)
- ![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red)

### **3. Añadir Screenshots (Recomendado):**

Crear carpeta `screenshots/` con:
- dashboard.png
- seasonality.png
- bubble-chart.png
- export.png

Luego actualizar README.md con imágenes.

---

## 🔐 **SEGURIDAD**

**NUNCA subir a GitHub:**
- ❌ API Keys
- ❌ Passwords
- ❌ Tokens
- ❌ Archivos .env
- ❌ Datos sensibles

**SIEMPRE usar:**
- ✅ Variables de entorno
- ✅ .gitignore
- ✅ Secrets de Streamlit Cloud
- ✅ Config files en .gitignore

---

## 📞 **AYUDA**

Si tienes problemas:

1. **Git no reconocido:**
   - Instala Git: https://git-scm.com/downloads

2. **Permission denied:**
   - Verifica SSH keys o usa HTTPS

3. **Merge conflicts:**
   - Pull primero: `git pull origin main`
   - Resuelve conflictos
   - Commit y push

---

## ✅ **VERIFICACIÓN POST-DEPLOY**

Después de subir, verifica en GitHub:

- [ ] README.md se ve correctamente
- [ ] app.py está presente
- [ ] requirements.txt visible
- [ ] LICENSE presente
- [ ] .gitignore funcionando
- [ ] No hay archivos sensibles
- [ ] Badges se muestran

---

## 🎉 **¡LISTO!**

Tu proyecto está en GitHub y listo para:
- 📥 Clones
- ⭐ Stars
- 🍴 Forks
- 🤝 Contribuciones
- 🚀 Deploy en Streamlit Cloud

---

**Próximo paso:** Deploy en Streamlit Cloud para tener URL pública
