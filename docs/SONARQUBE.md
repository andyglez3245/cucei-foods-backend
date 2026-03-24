# SonarQube Integration - Cucei Foods Backend

Este documento explica cómo usar SonarQube para analizar la calidad del código y la cobertura de tests en el proyecto.

## 📋 Requisitos

- SonarQube Server (local o remoto)
- SonarQube Scanner CLI
- Python 3.12+
- pytest y pytest-cov

## 🚀 Instalación Rápida

### 1. Instalar dependencias
```bash
pip install -r requirements-dev.txt
```

### 2. Descargar SonarQube Scanner
```bash
# Windows
# Descarga desde: https://docs.sonarqube.org/latest/analyzing-source-code/scanners/sonarscanner/
# Y agrega a PATH

# Linux/Mac
brew install sonar-scanner  # Mac con Homebrew
# o descarga manualmente desde: https://docs.sonarqube.org/latest/analyzing-source-code/scanners/sonarscanner/
```

## 📊 Generar Reportes de Cobertura

### Opción 1: Usando scripts
```bash
# Windows
run_tests.bat sonar

# Linux/Mac
./run_tests.sh sonar
```

### Opción 2: Manualmente con pytest
```bash
pytest --cov=app \
       --cov-report=xml:coverage.xml \
       --cov-report=html \
       --junit-xml=test-results.xml
```

Esto genera:
- `coverage.xml` - Reporte de cobertura en formato Cobertura (para SonarQube)
- `test-results.xml` - Resultados de tests en formato JUnit (para SonarQube)
- `htmlcov/` - Reporte HTML interactivo (para visualizar localmente)

## 🔧 Configuración de SonarQube

### Local (Servidor SonarQube corriendo)

```bash
# 1. Asegurate que SonarQube esté corriendo en http://localhost:9000
# 2. Ejecuta el scanner:
sonar-scanner
```

### Remoto (SonarQube en servidor)

Actualiza `sonar-project.properties`:
```properties
sonar.host.url=https://tu-sonarqube-server.com
sonar.login=tu-token-aqui
```

Luego ejecuta:
```bash
sonar-scanner
```

## 🔑 Usar Token de Autenticación

### En local
Sin token normalmente (servidor por defecto en modo abierto)

### En remoto (importante)
```bash
# Opción 1: Variable de entorno
export SONAR_TOKEN=tu-token
sonar-scanner

# Opción 2: Parámetro directo
sonar-scanner -Dsonar.login=tu-token

# Opción 3: En sonar-project.properties
sonar.login=tu-token
```

## 📁 Estructura de Archivos Generados

```
project/
├── coverage.xml          ← SonarQube lee esto
├── test-results.xml      ← SonarQube lee esto
├── .coverage             ← Datos internos de coverage.py
├── htmlcov/              ← Reporte HTML (visualizar con navegador)
│   └── index.html
└── .scannerwork/         ← Cache de SonarQube Scanner
```

## ✅ Verificar en SonarQube

1. Abre `http://localhost:9000` (o tu URL de SonarQube)
2. Ve a **Proyectos**
3. Busca **"cucei-foods-backend"**
4. Verás:
   - 📊 **Cobertura**: % de código cubierto por tests
   - 🧪 **Tests**: Número de tests ejecutados
   - 🐛 **Bugs**: Bugs detectados por análisis estático
   - 🔒 **Vulnerabilidades**: Issues de seguridad
   - 💧 **Code Smells**: Problemas de calidad

## 🔄 Automatización con GitHub Actions

El proyecto incluye `.github/workflows/sonarqube.yml` que:
- Ejecuta tests automáticamente en cada push
- Genera reportes de cobertura
- Envía reportes a SonarQube automáticamente

### Configurar GitHub Actions

1. Ve a **Settings** > **Secrets and variables** > **Actions**
2. Agrega:
   - `SONAR_HOST_URL`: Tu URL de SonarQube (ej: `https://sonarqube.company.com`)
   - `SONAR_TOKEN`: Tu token de autenticación de SonarQube

3. El workflow se ejecutará automáticamente en cada push

## 📈 Métricas Importantes

| Métrica | Descripción | Objetivo |
|---------|------------|----------|
| **Cobertura** | % de código cubierto | > 80% |
| **Tests** | Número de tests | Aumentar |
| **Bugs** | Issues críticas | 0 |
| **Vulnerabilidades** | Issues de seguridad | 0 |
| **Code Smells** | Problemas de calidad | Reducir |
| **Duplicación** | Código duplicado | < 5% |

## 🛠️ Troubleshooting

### SonarQube no detecta tests
```bash
# Verifica que los archivos XML se generaron:
ls -la coverage.xml test-results.xml

# Verifica la configuración en sonar-project.properties:
cat sonar-project.properties
```

### Cobertura no se muestra
```bash
# Asegúrate de generar coverage.xml:
pytest --cov=app --cov-report=xml:coverage.xml

# Verifica que SonarQube lea el archivo correcto:
sonar-scanner -X  # Modo debug
```

### Error de autenticación
```bash
# Valida el token:
echo $SONAR_TOKEN

# Prueba con token en línea de comandos:
sonar-scanner -Dsonar.login=tu-token-valido
```

## 📚 Referencias

- [SonarQube Documentation](https://docs.sonarqube.org/)
- [SonarQube Python Plugin](https://github.com/SonarSource/sonar-python)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

## 🎯 Ejemplo Completo

```bash
# 1. Instalar dependencias
pip install -r requirements-dev.txt

# 2. Ejecutar tests con cobertura
pytest --cov=app --cov-report=xml:coverage.xml --junit-xml=test-results.xml

# 3. Ejecutar SonarQube Scanner
sonar-scanner

# 4. Ver resultados en http://localhost:9000
```

---

**Nota**: La primera vez que ejecutes SonarQube Scanner en un proyecto nuevo, deberás crear el proyecto en la interfaz de SonarQube o proporcionar credenciales admin.
