# 🚀 Trend Hunter Pro

**Versión**: 8.4.0  
**Status**: ✅ Production Ready  
**Última actualización**: 2024-12-01

---

## 📖 Descripción

**Trend Hunter Pro** es una aplicación profesional de análisis de tendencias multi-plataforma que permite investigar marcas, productos y keywords a través de **Google Trends**, **Amazon** y **YouTube**.

### ✨ Características Principales

- 🌐 **Análisis de Google Trends** (5 países)
- 🛍️ **Intelligence de Amazon** con métricas y comparación
- 🎥 **Análisis de YouTube** con keywords extraídas
- 📊 **Comparación Multi-plataforma** con correlaciones
- 🗺️ **Mapas regionales** de interés
- 📈 **Estacionalidad** con análisis estadístico
- 🎨 **Visualizaciones interactivas** con Plotly
- 📥 **Exportación** a CSV/Excel/PDF
- 🎯 **Separación de datos por fuente** (Google/Amazon/YouTube)

---

## 🆕 Novedades v8.4.0

### **🎯 Separación Multi-Fuente** (MAJOR FEATURE)

Ahora los datos están **100% separados** por plataforma con:

- **4 Tabs principales**: Google, Amazon, YouTube, Comparación
- **Badges visuales**: Cada sección indica su fuente
- **"Dónde buscan más"**: Comparación explícita de volumen
- **Correlaciones**: Google vs Amazon vs YouTube
- **Keywords YouTube**: Extraídas de títulos de videos
- **Amazon searches**: Separadas de Google queries

**Antes**: Datos mezclados, origen confuso ❌  
**Ahora**: Origen siempre claro, datos separados ✅

---

## 🚀 Quick Start

### **1. Clonar repositorio**
```bash
git clone https://github.com/tu-usuario/trend-hunter-pro.git
cd trend-hunter-pro
```

### **2. Instalar dependencias**
```bash
pip install -r requirements.txt
```

### **3. Configurar API Key**
```bash
# Crear archivo de secrets
cp secrets.toml.example .streamlit/secrets.toml

# Editar y añadir tu SERPAPI_KEY
nano .streamlit/secrets.toml
```

```toml
# .streamlit/secrets.toml
SERPAPI_KEY = "tu_api_key_aqui"
```

### **4. Ejecutar aplicación**
```bash
streamlit run app.py
```

Abre tu navegador en: `http://localhost:8501`

---

## 📦 Requisitos

### **Python**: 3.8+

### **Dependencias principales**:
```
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.17.0
requests>=2.31.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
Pillow>=10.0.0
```

Ver [`requirements.txt`](requirements.txt) para lista completa.

---

## 🔑 API Key (SerpAPI)

Esta aplicación usa **SerpAPI** para acceder a:
- Google Trends
- Amazon Products
- YouTube Videos
- Google News

### **Obtener API Key**:
1. Regístrate en [SerpAPI.com](https://serpapi.com)
2. Obtén tu API key del dashboard
3. Añádela a `.streamlit/secrets.toml`

### **Planes SerpAPI**:
- **Free**: 100 búsquedas/mes
- **Developer**: 5,000 búsquedas/mes ($50)
- **Production**: 15,000 búsquedas/mes ($130)

**Nota**: La app usa cache (1 hora) para optimizar consumo.

---

## 📊 Estructura de Datos por Fuente

### **🌐 Google Trends**
```
├─ Queries relacionadas (top + rising)
├─ Topics relacionados (bubble chart)
├─ Trending Now (keywords en tendencia)
├─ Interest by Region (mapa interactivo)
└─ Tendencia temporal (5 años, configurable)
```

### **🛍️ Amazon**
```
├─ Métricas generales
│   ├─ Total productos
│   ├─ Rating promedio
│   ├─ % con Prime
│   └─ Total reviews
├─ Comparación con Google Trends
│   └─ Insights: Aligned/Opportunity/Warning
├─ Búsquedas relacionadas (Amazon-specific)
└─ Top 5 productos por reviews
```

### **🎥 YouTube**
```
├─ Métricas de videos
│   ├─ Total videos
│   ├─ Views totales/promedio
│   └─ Actividad reciente
├─ Top videos ordenados por views
└─ Keywords extraídas de títulos
```

### **📊 Comparación Multi-plataforma**
```
├─ Gráfico de volumen por plataforma
├─ Tabla comparativa
├─ Insight: "Dónde buscan más"
└─ Correlaciones cruzadas
```

---

## 🎨 Capturas de Pantalla

### Dashboard Principal
![Dashboard](docs/screenshots/dashboard.png)

### Separación por Fuente (v8.4.0)
![Multi-source](docs/screenshots/multisource.png)

### Comparación de Marcas
![Comparison](docs/screenshots/comparison.png)

---

## 📚 Documentación

### **Guías de Usuario**:
- [README_FINAL.md](README_FINAL.md) - Guía detallada
- [DASHBOARD.md](DASHBOARD.md) - Explicación del dashboard
- [DEPLOYMENT.md](DEPLOYMENT.md) - Despliegue a producción

### **Documentación Técnica**:
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Todas las APIs
- [AMAZON_API_DOCUMENTATION.md](AMAZON_API_DOCUMENTATION.md) - Amazon específica
- [CHANGELOG.md](CHANGELOG.md) - Historial de versiones

### **Features Recientes**:
- [FEATURE_MULTISOURCE_COMPLETE.md](FEATURE_MULTISOURCE_COMPLETE.md) - Separación multi-fuente v8.4.0
- [FEATURE_TEMPORAL_SELECTOR.md](FEATURE_TEMPORAL_SELECTOR.md) - Selector temporal v8.3.0

---

## 🏗️ Arquitectura

```
trend-hunter-pro/
├── app.py                      # Aplicación principal (5,797 líneas)
├── requirements.txt            # Dependencias Python
├── config.toml                 # Configuración Streamlit
├── secrets.toml.example        # Template de secrets
├── .gitignore                  # Git ignore
│
├── .streamlit/                 # Configuración Streamlit
│   ├── config.toml
│   └── secrets.toml           # ⚠️ NO subir a Git
│
├── docs/                       # Documentación
│   ├── API_DOCUMENTATION.md
│   ├── AMAZON_API_DOCUMENTATION.md
│   ├── FEATURE_*.md
│   ├── AUDIT_*.md
│   └── screenshots/
│
└── README.md                   # Este archivo
```

---

## 🔒 Seguridad

### **✅ Implementado**:
- [x] HTML escaping en todos los outputs
- [x] No hay SQL injection (no usa DB)
- [x] API keys en secrets (no hardcoded)
- [x] Input sanitization
- [x] Error handling robusto
- [x] HTTPS para API calls
- [x] Rate limiting con cache

### **⚠️ Importante**:
- **NUNCA** subas `secrets.toml` a Git
- Usa `.gitignore` para excluir secrets
- Rota API keys periódicamente

---

## 🧪 Testing

### **Testing Manual**:
```bash
# Ejecutar app
streamlit run app.py

# Probar flujo completo:
1. Buscar "Logitech"
2. Verificar 4 tabs visibles
3. Comprobar badges de fuente
4. Ver comparación multi-plataforma
5. Exportar CSV
```

### **Checklist**:
- [ ] Tab Google Trends funciona
- [ ] Tab Amazon funciona
- [ ] Tab YouTube funciona
- [ ] Tab Comparación funciona
- [ ] Badges visibles en cada tab
- [ ] Gráficos se renderizan
- [ ] Exportación funciona
- [ ] No hay errores en consola

---

## 🚢 Deployment

### **Streamlit Cloud** (Recomendado):
```bash
# 1. Push a GitHub
git push origin main

# 2. Conectar Streamlit Cloud
- Ir a share.streamlit.io
- Conectar repo de GitHub
- Añadir SERPAPI_KEY en secrets
- Deploy automático
```

### **Docker**:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

### **Heroku**:
Ver [DEPLOYMENT.md](DEPLOYMENT.md) para guía completa.

---

## 📈 Historial de Versiones

| Versión | Fecha | Tipo | Descripción |
|---------|-------|------|-------------|
| 8.4.0 | 2024-12-01 | Major | Separación multi-fuente completa |
| 8.3.0 | 2024-12-01 | Feature | Selector de rango temporal |
| 8.2.4 | 2024-12-01 | Fix | UnboundLocalError + HTML escaping |
| 8.2.3 | 2024-12-01 | Fix | HTML tooltip newlines |
| 8.2.2 | 2024-12-01 | Fix | CSV encoding UTF-8 |
| 8.2.1 | 2024-11-30 | Enhancement | Edge cases + accessibility |
| 8.2 | 2024-11-30 | Major | Auditoría completa + fixes |

Ver [CHANGELOG.md](CHANGELOG.md) para historial completo.

---

## 🤝 Contribuir

### **Cómo contribuir**:
1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/nueva-feature`
3. Commit cambios: `git commit -m 'feat: nueva feature'`
4. Push: `git push origin feature/nueva-feature`
5. Abre un Pull Request

### **Convención de commits**:
```
feat: nueva característica
fix: corrección de bug
docs: documentación
style: formateo
refactor: refactorización
test: tests
chore: mantenimiento
```

---

## 📄 Licencia

Este proyecto está bajo licencia **MIT**.

---

## 👥 Autores

**PCComponentes Competitive Intelligence Team**

---

## 🆘 Soporte

### **Issues**:
Reporta bugs o solicita features en [GitHub Issues](https://github.com/tu-usuario/trend-hunter-pro/issues)

### **Contacto**:
- Email: support@example.com
- Slack: #trend-hunter-pro

---

## 🙏 Agradecimientos

- **SerpAPI** - Por el acceso a datos de Google/Amazon/YouTube
- **Streamlit** - Framework de la aplicación
- **Plotly** - Visualizaciones interactivas
- **Comunidad Open Source**

---

## ⭐ Si te gusta este proyecto

Dale una ⭐ en GitHub!

---

**Última actualización**: 2024-12-01  
**Versión**: 8.4.0  
**Status**: ✅ Production Ready
