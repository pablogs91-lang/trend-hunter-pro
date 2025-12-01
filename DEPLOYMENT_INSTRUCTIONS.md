# 🚀 INSTRUCCIONES DE DEPLOYMENT - v8.4.0

**Versión**: 8.4.0  
**Fecha**: 2024-12-01  
**Status**: ✅ LISTO PARA PRODUCCIÓN

---

## 📦 CONTENIDO DEL PAQUETE

### **Archivos Core** (REQUERIDOS):
```
✅ app.py                    # Aplicación principal (5,797 líneas)
✅ requirements.txt          # Dependencias Python
✅ README.md                 # Documentación principal
✅ .gitignore               # Git ignore rules
✅ CHANGELOG.md             # Historial de versiones

✅ .streamlit/
   ├── config.toml          # Configuración Streamlit
   └── secrets.toml.example # Template de secrets
```

### **Documentación** (OPCIONAL):
```
📄 README_FINAL.md
📄 DASHBOARD.md
📄 API_DOCUMENTATION.md
📄 AMAZON_API_DOCUMENTATION.md
📄 FEATURE_MULTISOURCE_COMPLETE.md
📄 FEATURE_TEMPORAL_SELECTOR.md
📄 DEPLOYMENT.md
📄 AUDIT_*.md
```

---

## 🚀 OPCIÓN 1: DEPLOY A GITHUB (RECOMENDADO)

### **Paso 1: Preparar Repositorio Local**

```bash
# Si ya tienes el repo clonado:
cd tu-repositorio-existente

# O clonar de nuevo:
git clone https://github.com/tu-usuario/trend-hunter-pro.git
cd trend-hunter-pro
```

### **Paso 2: Reemplazar Todos los Archivos**

```bash
# OPCIÓN A: Descargar archivos manualmente de Claude.ai
# Luego copiarlos a tu repo:

# Archivos obligatorios:
- Sobrescribir: app.py
- Sobrescribir: requirements.txt
- Sobrescribir: README.md
- Sobrescribir: CHANGELOG.md
- Sobrescribir: .gitignore

# Carpeta .streamlit:
- Sobrescribir: .streamlit/config.toml
- Sobrescribir: .streamlit/secrets.toml.example

# OPCIÓN B: Si tienes los archivos en /mnt/user-data/outputs:
cp /mnt/user-data/outputs/app.py .
cp /mnt/user-data/outputs/requirements.txt .
cp /mnt/user-data/outputs/README.md .
cp /mnt/user-data/outputs/CHANGELOG.md .
cp /mnt/user-data/outputs/.gitignore .
cp -r /mnt/user-data/outputs/.streamlit .

# Archivos de documentación (opcional):
cp /mnt/user-data/outputs/*.md docs/
```

### **Paso 3: Verificar Cambios**

```bash
# Ver qué cambió:
git status

# Deberías ver:
# modified: app.py
# modified: requirements.txt
# modified: README.md
# modified: CHANGELOG.md
# y otros...
```

### **Paso 4: Commit y Push**

```bash
# Añadir todos los cambios:
git add .

# Commit con mensaje descriptivo:
git commit -m "feat: multi-source data separation v8.4.0

MAJOR UPDATE:
- Complete data separation by source (Google/Amazon/YouTube)
- 4 main tabs with visual source badges
- Multi-platform comparison dashboard
- Correlation analysis
- YouTube keywords extraction
- Amazon searches separated
- Temporal range selector (v8.3.0)
- Multiple bug fixes (v8.2.2-8.2.4)

Breaking Changes: None
All features are additive and backward compatible.

Closes #XX"

# Crear tag de versión:
git tag -a v8.4.0 -m "Release v8.4.0 - Multi-source separation"

# Push todo a GitHub:
git push origin main
git push origin v8.4.0
```

### **Paso 5: Verificar en GitHub**

Abre tu repositorio en GitHub y verifica:
- [ ] Archivos actualizados visible
- [ ] README.md se muestra correctamente
- [ ] Tag v8.4.0 aparece en releases
- [ ] .gitignore protege secrets

---

## 🌐 OPCIÓN 2: DEPLOY A STREAMLIT CLOUD

### **Prerequisitos**:
- Cuenta en [share.streamlit.io](https://share.streamlit.io)
- Repo de GitHub con el código
- API key de SerpAPI

### **Paso 1: Conectar GitHub**

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Click en "New app"
3. Conecta tu cuenta de GitHub
4. Selecciona el repositorio

### **Paso 2: Configurar App**

```
Repository: tu-usuario/trend-hunter-pro
Branch: main
Main file path: app.py
App URL: trend-hunter-pro (o el que prefieras)
```

### **Paso 3: Añadir Secrets**

En Streamlit Cloud:
1. Click en "Advanced settings"
2. Sección "Secrets"
3. Añade:

```toml
SERPAPI_KEY = "tu_api_key_real_aqui"
```

⚠️ **IMPORTANTE**: Usa tu API key REAL, no el placeholder.

### **Paso 4: Deploy**

1. Click "Deploy!"
2. Espera ~2-3 minutos
3. La app estará disponible en: `https://tu-app.streamlit.app`

---

## 🐳 OPCIÓN 3: DEPLOY CON DOCKER

### **Paso 1: Crear Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicación
COPY . .

# Exponer puerto
EXPOSE 8501

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Comando de inicio
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### **Paso 2: Crear .dockerignore**

```
# .dockerignore
__pycache__
*.pyc
.env
.streamlit/secrets.toml
.git
.gitignore
venv/
*.md
docs/
```

### **Paso 3: Build y Run**

```bash
# Build image
docker build -t trend-hunter-pro:8.4.0 .

# Run container
docker run -p 8501:8501 \
  -e SERPAPI_KEY="tu_api_key" \
  trend-hunter-pro:8.4.0

# Con docker-compose:
# Crear docker-compose.yml primero
docker-compose up -d
```

### **docker-compose.yml**:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - SERPAPI_KEY=${SERPAPI_KEY}
    restart: unless-stopped
```

---

## ☁️ OPCIÓN 4: DEPLOY A HEROKU

### **Paso 1: Preparar Archivos**

Crear `Procfile`:
```
web: sh setup.sh && streamlit run app.py
```

Crear `setup.sh`:
```bash
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

### **Paso 2: Deploy**

```bash
# Login a Heroku
heroku login

# Crear app
heroku create trend-hunter-pro

# Añadir buildpack Python
heroku buildpacks:add heroku/python

# Set API key
heroku config:set SERPAPI_KEY="tu_api_key"

# Deploy
git push heroku main

# Abrir app
heroku open
```

---

## 🔧 CONFIGURACIÓN POST-DEPLOYMENT

### **1. Verificar Secrets**

```bash
# En Streamlit Cloud, verifica que secrets esté configurado
# En local, crea .streamlit/secrets.toml:
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
nano .streamlit/secrets.toml

# Añade tu API key real:
SERPAPI_KEY = "tu_api_key_real"
```

### **2. Testing Post-Deploy**

Abre la app y verifica:

#### **Test 1: Búsqueda básica**
```
1. Buscar "Logitech"
2. Ver resultados
3. Verificar 4 tabs visibles
```

#### **Test 2: Multi-fuente**
```
1. Tab Google Trends → ✅ Badge azul
2. Tab Amazon → ✅ Badge naranja
3. Tab YouTube → ✅ Badge rojo
4. Tab Comparación → ✅ Badge púrpura
```

#### **Test 3: Comparación**
```
1. Ir a tab "Comparación"
2. Ver gráfico de barras
3. Leer insight "Mayor actividad en..."
4. Verificar correlaciones
```

#### **Test 4: Exportación**
```
1. Buscar cualquier marca
2. Click "Exportar CSV"
3. Verificar descarga
4. Abrir CSV y revisar
```

### **3. Monitoreo**

```bash
# Streamlit Cloud: Ver logs en dashboard

# Heroku: Ver logs
heroku logs --tail

# Docker: Ver logs
docker logs -f <container_id>

# Local: Ver en terminal
streamlit run app.py
```

---

## ⚠️ TROUBLESHOOTING

### **Error: ModuleNotFoundError**
```bash
# Solución: Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### **Error: API Key not found**
```bash
# Solución: Verificar secrets
# Streamlit Cloud: Settings → Secrets
# Local: .streamlit/secrets.toml
# Heroku: heroku config:get SERPAPI_KEY
```

### **Error: Port already in use**
```bash
# Solución: Cambiar puerto
streamlit run app.py --server.port=8502
```

### **Error: Cannot connect to API**
```bash
# Verificar:
1. API key válida
2. Cuota disponible (check serpapi.com dashboard)
3. Conexión a internet
4. Firewall no bloquea
```

---

## 📊 CHECKLIST FINAL

### **Pre-Deploy**:
- [ ] Código actualizado a v8.4.0
- [ ] requirements.txt con todas las deps
- [ ] .gitignore protege secrets
- [ ] README.md actualizado
- [ ] CHANGELOG.md con v8.4.0
- [ ] Tests locales pasados

### **Durante Deploy**:
- [ ] Git push exitoso
- [ ] Tag v8.4.0 creado
- [ ] Secrets configurados
- [ ] Build sin errores
- [ ] App desplegada

### **Post-Deploy**:
- [ ] App accesible en URL
- [ ] Búsqueda funciona
- [ ] 4 tabs visibles
- [ ] Badges correctos
- [ ] Gráficos renderizan
- [ ] Exportación funciona
- [ ] No hay errores en logs

---

## 🎉 SUCCESS CRITERIA

La implementación es exitosa si:

✅ **App está online** y accesible  
✅ **Búsqueda funciona** sin errores  
✅ **4 tabs** (Google/Amazon/YouTube/Comparación) visibles  
✅ **Badges de fuente** correctos en cada tab  
✅ **Tab Comparación** muestra "Mayor actividad en..."  
✅ **Gráficos** se renderizan correctamente  
✅ **Exportación** CSV/Excel funciona  
✅ **No hay errores** en logs  

---

## 🆘 SOPORTE

### **Si tienes problemas**:

1. **Revisa logs** primero
2. **Verifica API key** está configurada
3. **Check cuota** SerpAPI disponible
4. **Testing local** antes de deploy
5. **GitHub Issues** para reportar bugs

### **Contacto**:
- GitHub Issues: [repo]/issues
- Email: support@example.com

---

## 📝 NOTAS IMPORTANTES

### **⚠️ Secrets Management**:
```
✅ Usar secrets.toml en Streamlit Cloud
✅ Usar environment variables en Docker/Heroku
❌ NUNCA hardcodear API keys
❌ NUNCA subir secrets.toml a Git
```

### **💰 API Costs**:
```
Con cache (1 hora):
- Búsqueda inicial: ~5 calls
- Búsquedas siguientes: 0 calls (cache)
- Estimado: 100-200 calls/día uso normal
- Plan Free: Suficiente para testing
- Plan Developer: Recomendado para producción
```

### **🔄 Updates Futuros**:
```bash
# Para actualizar a versiones futuras:
git pull origin main
pip install -r requirements.txt --upgrade
streamlit cache clear
streamlit run app.py
```

---

**Deployment preparado por**: Experto Python Senior  
**Versión**: 8.4.0  
**Fecha**: 2024-12-01  
**Status**: ✅ LISTO PARA PRODUCCIÓN
