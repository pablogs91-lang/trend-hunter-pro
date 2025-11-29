# 🔍 Trend Hunter Pro v4.0

> Herramienta profesional de análisis de tendencias de búsqueda con Google Trends API

![Version](https://img.shields.io/badge/version-4.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

## 📊 **Descripción**

Trend Hunter Pro es una aplicación web avanzada construida con Streamlit que permite analizar tendencias de búsqueda de marcas tecnológicas a través de Google Trends. Incluye análisis multi-país, visualizaciones interactivas, detección de patrones estacionales con IA y exportación de reportes.

### **Características Principales:**

- 📈 **Análisis de Estacionalidad** con detección automática de 6 patrones
- 🤖 **Explicaciones IA** y recomendaciones de marketing
- 🫧 **Bubble Chart** interactivo de temas relacionados
- 💬 **Tooltips mejorados** con información contextual
- 🎬 **Animaciones suaves** y micro-interacciones
- 📤 **Exportación múltiple**: CSV, Excel, JSON, PDF
- 🌍 **Multi-país**: España, México, Argentina, Colombia
- 🎨 **UI Premium** inspirada en Apple/Glimpse

---

## 🚀 **Instalación**

### **Requisitos:**
- Python 3.8+
- pip
- Cuenta SerpAPI (clave API)

### **Pasos:**

1. **Clonar repositorio:**
```bash
git clone https://github.com/tu-usuario/trend-hunter-pro.git
cd trend-hunter-pro
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar API Key:**

Edita `app.py` línea ~900 y añade tu clave de SerpAPI:
```python
SERPAPI_KEY = "tu_clave_aqui"
```

4. **Ejecutar aplicación:**
```bash
streamlit run app.py
```

5. **Abrir navegador:**
```
http://localhost:8501
```

---

## 📦 **Dependencias**

Ver `requirements.txt` para lista completa.

Principales:
- streamlit>=1.28.0
- pandas>=2.0.0
- plotly>=5.17.0
- reportlab>=4.0.0
- xlsxwriter>=3.1.0

---

## 🎯 **Uso Rápido**

1. Introduce nombre de marca (ej: "logitech")
2. Selecciona países a analizar
3. Click en "🔍 Analizar"
4. Explora métricas, estacionalidad y tendencias
5. Exporta reportes en formato deseado

---

## 🎨 **Features**

### **Sprint 1 - Core:**
✅ Análisis de estacionalidad  
✅ Query bars visuales  
✅ Paginación  
✅ Ordenamiento  

### **Sprint 2 - Visualizaciones:**
✅ Sparklines  
✅ Export CSV/Excel/JSON  

### **Sprint 3 - IA:**
✅ Detección de 6 patrones  
✅ Explicaciones automáticas  
✅ Bubble chart interactivo  
✅ Export PDF  

### **Sprint 4 - UX Premium:**
✅ Tooltips mejorados  
✅ Animaciones suaves  
✅ Empty states elegantes  
✅ Loading states  

---

## 📁 **Estructura**

```
trend-hunter-pro/
├── app.py                 # App principal (3132 líneas)
├── requirements.txt       # Dependencias
├── README.md             # Documentación
├── LICENSE               # Licencia MIT
└── docs/                 # Documentación detallada
```

---

## 📄 **Licencia**

MIT License - Ver archivo `LICENSE`

---

## 👨‍💻 **Autor**

**Pablo - PCComponentes**  
Competitive Intelligence Team

---

## 🙏 **Agradecimientos**

- Google Trends API (via SerpAPI)
- Streamlit Community
- Plotly Team

---

**⭐ Si te gusta el proyecto, dale una estrella!**
