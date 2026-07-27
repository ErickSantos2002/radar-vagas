from __future__ import annotations

import os
from pathlib import Path

# Onde o banco vive. Fora do git (ver .gitignore).
CAMINHO_DB = Path(os.environ.get("RADAR_DB", "vagas.db"))

# Destino dos relatórios semanais, em ordem de precedência:
#   1. $RADAR_RELATORIOS
#   2. o vault do Obsidian, se existir nesta máquina — os relatórios ficam ao
#      lado da meta que servem, e o vault está fora do repositório
#   3. ./relatorios (gitignored), para quem clonar o projeto
_VAULT = Path.home() / "Documentos/Obsidian Vault/Erick/Metas & Sonhos"


def _destino_padrao() -> Path:
    if env := os.environ.get("RADAR_RELATORIOS"):
        return Path(env)
    if _VAULT.is_dir():
        return _VAULT / "Radar de Vagas"
    return Path("relatorios")


PASTA_RELATORIOS = _destino_padrao()
