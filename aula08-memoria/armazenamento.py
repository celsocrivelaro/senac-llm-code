# Aula 08 — A raiz de armazenamento das memórias.
#
# As três memórias compartilham uma raiz e adotam formas de armazenamento
# distintas dentro dela: banco vetorial para a episódica, arquivo JSON para a
# semântica, arquivo de texto para a procedural. A diferença de forma decorre
# da diferença de padrão de acesso de cada uma.
#
# A pasta é criada em tempo de execução e não é versionada: memória é estado,
# e estado de laboratório não pertence ao repositório.

from pathlib import Path

BASE = Path(__file__).parent / "memoria_db"
