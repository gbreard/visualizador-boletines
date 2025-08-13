#!/usr/bin/env bash
# Build script para Render

echo "==================================="
echo "INICIANDO BUILD"
echo "==================================="
echo "Python version:"
python --version
echo "Pip version:"
pip --version
echo "==================================="

# Actualizar pip
pip install --upgrade pip

# Instalar requirements con wheels precompilados
echo "Instalando requirements..."
pip install --only-binary :all: -r requirements.txt

echo "==================================="
echo "BUILD COMPLETADO"
echo "==================================="