# Guía Rápida: SonarQube + Tests + Cobertura

## 🎯 Resumen Ejecutivo

He configurado tu proyecto para que **SonarQube detecte automáticamente tus tests y la cobertura de código**. Ahora los reportes se generan en los formatos que SonarQube espera.

## 📊 Qué Se Generó

### Archivos de Configuración
- **`sonar-project.properties`** - Configuración de SonarQube
- **`pytest.ini`** - Configuración de pytest para generar reportes XML
- **`requirements-dev.txt`** - Dependencias necesarias
- **`.github/workflows/sonarqube.yml`** - CI/CD automático (opcional)

### Archivos de Scripts
- **`run_tests.bat`** - Script Windows para ejecutar tests
- **`run_tests.sh`** - Script Linux/Mac para ejecutar tests
- **`docs/SONARQUBE.md`** - Documentación completa

### Reportes Generados (en tests)
- **`coverage.xml`** - Reporte de cobertura (formato Cobertura)
- **`test-results.xml`** - Resultados de tests (formato JUnit)
- **`htmlcov/`** - Reporte HTML interactivo

## 🚀 Uso Rápido

### Windows
```bash
# Ejecutar tests con cobertura y reportes para SonarQube
run_tests.bat sonar

# O manualmente
pytest --cov=app --cov-report=xml:coverage.xml --junit-xml=test-results.xml
```

### Linux/Mac
```bash
# Ejecutar tests con cobertura y reportes para SonarQube
./run_tests.sh sonar

# O manualmente
pytest --cov=app --cov-report=xml:coverage.xml --junit-xml=test-results.xml
```

## 📋 Después de Ejecutar Tests

Los siguientes archivos se generarán automáticamente:

```
project-root/
├── coverage.xml          ← SonarQube lee esto (cobertura)
├── test-results.xml      ← SonarQube lee esto (tests)
├── .coverage             ← Datos internos (ignorar)
├── htmlcov/              ← Ver con navegador para reporte visual
│   └── index.html
└── .scannerwork/         ← Cache de SonarQube Scanner (ignorar)
```

## 🔧 Pasos Uno a Uno para SonarQube Local

### 1. **Instalar SonarQube** (si no está ya)
```bash
# Windows
# Descarga desde: https://www.sonarqube.org/downloads/

# Mac (con Homebrew)
brew install sonarqube

# Linux
# Descarga y extrae desde: https://www.sonarqube.org/downloads/
```

### 2. **Instalar SonarQube Scanner**
```bash
# Windows
# Descarga: https://docs.sonarqube.org/latest/analyzing-source-code/scanners/sonarscanner/
# Agrega el bin/ a tu PATH

# Mac
brew install sonar-scanner

# Linux
# Descarga y extrae de: https://docs.sonarqube.org/latest/analyzing-source-code/scanners/sonarscanner/
```

### 3. **Verificar instalaciones**
```bash
sonar-scanner --version
```

### 4. **Ejecutar tests generando reportes**
```bash
cd tu-proyecto
pytest --cov=app --cov-report=xml:coverage.xml --junit-xml=test-results.xml
```

### 5. **Ejecutar SonarQube Scanner**
```bash
sonar-scanner
```

### 6. **Ver resultados**
Abre: `http://localhost:9000`

Busca: **"cucei-foods-backend"** en el dashboard

## 📈 Métricas que Verás en SonarQube

| Métrica | Descripción | Tu Valor |
|---------|------------|----------|
| **Tests** | Total de tests | 21 tests ✅ |
| **Cobertura** | % de código cubierto | ~54% |
| **Auth Coverage** | Cobertura de auth.py | 100% ✅ |
| **Bugs** | Issues críticas | Detectadas automáticamente |
| **Vulnerabilidades** | Problemas de seguridad | Detectados automáticamente |
| **Code Smells** | Problemas de calidad | Detectados automáticamente |

## 🔄 Automatización: GitHub Actions (Opcional)

Si quieres que SonarQube se ejecute **automáticamente** en cada push:

### 1. **En GitHub: Settings > Secrets and variables > Actions**
Agrega:
- `SONAR_HOST_URL` = tu URL de SonarQube
- `SONAR_TOKEN` = tu token de autenticación

### 2. **El workflow se ejecutará automáticamente**
Cada vez que hagas push, GitHub Actions:
- Ejecutará todos los tests
- Generará reportes de cobertura
- Enviará reportes a SonarQube
- Mostrará análisis en PR

## ⚙️ Configuración: `sonar-project.properties`

Archivo creado en tu proyecto. Ahora SonarQube sabe:
```properties
- Dónde están los tests: tests/
- Dónde está el código: app/
- Dónde buscar cobertura: coverage.xml
- Dónde buscar resultados: test-results.xml
```

## 🔐 Usar Token para Remoto/CI/CD

Si tu SonarQube requiere autenticación:

```bash
# Opción 1: Parámetro en línea de comandos
sonar-scanner -Dsonar.login=tu-token-aqui

# Opción 2: Variable de entorno
export SONAR_TOKEN=tu-token-aqui
sonar-scanner

# Opción 3: En sonar-project.properties
sonar.login=tu-token-aqui
```

## 📚 Próximos Pasos

1. ✅ Tests creados y funcionando (21 tests)
2. ✅ Cobertura Configurada (coverage.xml generado)
3. ✅ SonarQube Configurado (sonar-project.properties)
4. ✅ Reportes Generados (coverage.xml, test-results.xml)
5. **Próximo:** Ejecutar `sonar-scanner` si tienes SonarQube instalado

## 🆘 Troubleshooting

### SonarQube no ve los tests
```bash
# 1. Verifica que los XML se generaron:
dir coverage.xml test-results.xml

# 2. Verifica pytest.ini tiene la config correcta:
cat pytest.ini

# 3. Genera reportes manualmente:
pytest --cov=app --cov-report=xml --junit-xml=test-results.xml
```

### SonarQube no detecta cobertura
```bash
# Asegúrate que está en el mismo directorio que sonar-project.properties:
pwd
ls coverage.xml
```

### Error de autenticación
```bash
# Valida tu token:
echo %SONAR_TOKEN%  (Windows)
echo $SONAR_TOKEN   (Linux/Mac)

# Prueba con token directo:
sonar-scanner -Dsonar.login=tu-token-valido
```

## 📝 Repositorio

Los siguientes archivos fueron creados/actualizados:

```
✨ Nuevo:
- sonar-project.properties
- requirements-dev.txt
- docs/SONARQUBE.md
- .github/workflows/sonarqube.yml
- run_tests.bat
- run_tests.sh
- tests/conftest.py (reconstruido)
- tests/test_auth.py (reorganizado)

📝 Actualizado:
- pytest.ini (agregadas opciones de reportes)
```

## 🎉 Resultado

Ahora tienes:
- ✅ 21 tests funcionando
- ✅ Cobertura de código (54% actual)
- ✅ Reportes en formato Cobertura + JUnit
- ✅ SonarQube correctamente configurado
- ✅ CI/CD automático opcional

**SonarQube ahora puede detectar y analizar tus tests automáticamente.**

---

Para más detalles, ver: [docs/SONARQUBE.md](../docs/SONARQUBE.md)
