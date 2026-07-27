from __future__ import annotations

import logging
import sys

from radar_vagas.db import conectar, criar_schema, inserir_vagas
from radar_vagas.fetch import coletar_tudo
from radar_vagas.filtro import aplicar_filtros


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    vagas, erros = coletar_tudo()
    aprovadas, geo_por_id = aplicar_filtros(vagas)

    con = conectar("vagas.db")
    criar_schema(con)
    novas = inserir_vagas(con, aprovadas, geo_por_id)

    print()
    print(f"coletadas    {len(vagas)}")
    print(f"aprovadas    {len(aprovadas)}")
    print(f"novas no db  {novas}")

    por_fonte: dict[str, list[int]] = {}
    for v in vagas:
        por_fonte.setdefault(v.fonte, [0, 0])[0] += 1
    for v in aprovadas:
        por_fonte.setdefault(v.fonte, [0, 0])[1] += 1

    print()
    print(f"{'fonte':<12} {'coletadas':>10} {'aprovadas':>10}")
    for fonte, (total, ok) in sorted(por_fonte.items(), key=lambda kv: -kv[1][1]):
        print(f"{fonte:<12} {total:>10} {ok:>10}")

    if erros:
        print("\nfontes com erro:")
        for e in erros:
            print(f"  {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
