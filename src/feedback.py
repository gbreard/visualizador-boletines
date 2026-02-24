"""
Cliente GitHub API para crear issues de feedback sobre graficos.
"""

import os
import json
import logging
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)

REPO = "gbreard/visualizador-boletines"
API_URL = f"https://api.github.com/repos/{REPO}/issues"


def create_feedback_issue(graph_id, graph_label, tab, category, description, context):
    """
    Crea un GitHub Issue con el feedback del usuario.

    Returns:
        dict con 'success' (bool), 'url' (str o None), 'error' (str o None)
    """
    token = os.environ.get("GITHUB_FEEDBACK_TOKEN", "")
    if not token:
        return {
            "success": False,
            "url": None,
            "error": "Token de GitHub no configurado. Contacte al administrador.",
        }

    tab_clean = tab.replace("tab-", "") if tab else "general"
    title = f"[Feedback][{tab_clean}] {graph_label} - {category}"

    # Armar body markdown con tabla de contexto
    ctx_rows = ""
    if isinstance(context, dict):
        for k, v in context.items():
            if v is not None and v != "" and v != []:
                ctx_rows += f"| {k} | {v} |\n"

    body = f"""## Feedback de usuario

**Categoria:** {category}
**Grafico:** {graph_label} (`{graph_id}`)
**Tab:** {tab_clean}

### Descripcion
{description}

### Contexto capturado
| Campo | Valor |
|-------|-------|
{ctx_rows}
---
_Generado automaticamente desde el dashboard._
"""

    labels = ["feedback", category, f"tab:{tab_clean}"]

    payload = json.dumps({
        "title": title,
        "body": body,
        "labels": labels,
    }).encode("utf-8")

    req = Request(API_URL, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")

    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "success": True,
                "url": data.get("html_url", ""),
                "error": None,
            }
    except HTTPError as e:
        body_err = e.read().decode("utf-8", errors="replace")[:200]
        logger.error("GitHub API error %s: %s", e.code, body_err)
        return {
            "success": False,
            "url": None,
            "error": f"Error GitHub API ({e.code}). Verifique el token.",
        }
    except (URLError, OSError) as e:
        logger.error("Network error creating issue: %s", e)
        return {
            "success": False,
            "url": None,
            "error": "Error de conexion. Intente nuevamente.",
        }
