#!/bin/bash
# Script para ejecutar tests con pytest en Linux/Mac
# Genera reportes de cobertura en formato compatible con SonarQube

case "${1:-}" in
    "coverage")
        echo "Ejecutando tests con reporte de cobertura..."
        pytest --cov=app --cov-report=html --cov-report=xml
        echo "Abre htmlcov/index.html para ver el reporte"
        ;;
    "sonar")
        echo "Ejecutando tests y preparando para SonarQube..."
        pytest --cov=app --cov-report=xml:coverage.xml --junit-xml=test-results.xml
        echo "Tests completados. Ejecuta: sonar-scanner"
        ;;
    "auth")
        echo "Ejecutando tests de autenticación..."
        pytest tests/test_auth.py -v
        ;;
    "quick")
        echo "Ejecutando tests rápidamente..."
        pytest -q
        ;;
    "help")
        echo "Uso: ./run_tests.sh [opcion]"
        echo ""
        echo "Opciones:"
        echo "  (vacio)    - Ejecuta todos los tests con cobertura"
        echo "  coverage   - Ejecuta tests y genera reporte HTML"
        echo "  sonar      - Prepara reportes para SonarQube"
        echo "  auth       - Ejecuta solo tests de autenticación"
        echo "  quick      - Ejecuta tests rápidamente sin cobertura"
        echo "  help       - Muestra esta ayuda"
        ;;
    "")
        echo "Ejecutando todos los tests con cobertura..."
        pytest --cov=app --cov-report=xml --cov-report=html --junit-xml=test-results.xml
        ;;
    *)
        pytest "$@"
        ;;
esac
