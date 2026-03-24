@echo off
REM Script para ejecutar tests con pytest en Windows
REM Genera reportes de cobertura en formato compatible con SonarQube

if "%1%"=="" (
    echo Ejecutando todos los tests con cobertura...
    pytest --cov=app --cov-report=xml --cov-report=html --junit-xml=test-results.xml
) else if "%1%"=="coverage" (
    echo Ejecutando tests con reporte de cobertura...
    pytest --cov=app --cov-report=html --cov-report=xml
    echo Abre htmlcov/index.html para ver el reporte
) else if "%1%"=="sonar" (
    echo Ejecutando tests y preparando para SonarQube...
    pytest --cov=app --cov-report=xml:coverage.xml --junit-xml=test-results.xml
    echo Tests completados. Ejecuta: sonar-scanner
) else if "%1%"=="auth" (
    echo Ejecutando tests de autenticación...
    pytest tests/test_auth.py -v
) else if "%1%"=="quick" (
    echo Ejecutando tests sin cobertura...
    pytest -q
) else if "%1%"=="help" (
    echo Uso: run_tests.bat [opcion]
    echo.
    echo Opciones:
    echo   (vacio)    - Ejecuta todos los tests con cobertura
    echo   coverage   - Ejecuta tests y genera reporte HTML
    echo   sonar      - Prepara reportes para SonarQube
    echo   auth       - Ejecuta solo tests de autenticación
    echo   quick      - Ejecuta tests rápidamente sin cobertura
    echo   help       - Muestra esta ayuda
) else (
    echo pytest %*
    pytest %*
)
