"""
Script one-time para crear labels de feedback en el repositorio GitHub.
Uso: python scripts/setup_feedback_labels.py
Requiere: GITHUB_FEEDBACK_TOKEN como variable de entorno.
"""

import os
import json
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError

REPO = "gbreard/visualizador-boletines"
API_URL = f"https://api.github.com/repos/{REPO}/labels"

LABELS = [
    {"name": "feedback", "color": "0075ca", "description": "Feedback de usuario del dashboard"},
    {"name": "calculo", "color": "d73a4a", "description": "Error de calculo reportado"},
    {"name": "datos", "color": "e4e669", "description": "Problema con datos"},
    {"name": "diseno", "color": "a2eeef", "description": "Mejora de diseno"},
    {"name": "otro", "color": "cfd3d7", "description": "Otro tipo de feedback"},
    {"name": "tab:resumen", "color": "bfdadc", "description": "Tab Resumen"},
    {"name": "tab:analisis", "color": "bfdadc", "description": "Tab Analisis"},
    {"name": "tab:remuneraciones", "color": "bfdadc", "description": "Tab Remuneraciones"},
    {"name": "tab:empresas", "color": "bfdadc", "description": "Tab Empresas"},
    {"name": "tab:flujos", "color": "bfdadc", "description": "Tab Flujos"},
    {"name": "tab:genero", "color": "bfdadc", "description": "Tab Genero"},
    {"name": "tab:comparaciones", "color": "bfdadc", "description": "Tab Comparaciones"},
    {"name": "tab:alertas", "color": "bfdadc", "description": "Tab Alertas"},
    {"name": "tab:datos", "color": "bfdadc", "description": "Tab Datos"},
]


def main():
    token = os.environ.get("GITHUB_FEEDBACK_TOKEN", "")
    if not token:
        print("ERROR: GITHUB_FEEDBACK_TOKEN no configurado.")
        sys.exit(1)

    for label in LABELS:
        payload = json.dumps(label).encode("utf-8")
        req = Request(API_URL, data=payload, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("Content-Type", "application/json")

        try:
            with urlopen(req, timeout=10) as resp:
                print(f"  Creado: {label['name']}")
        except HTTPError as e:
            if e.code == 422:
                print(f"  Ya existe: {label['name']}")
            else:
                body = e.read().decode("utf-8", errors="replace")[:100]
                print(f"  Error ({e.code}): {label['name']} - {body}")

    print("Done.")


if __name__ == "__main__":
    main()
