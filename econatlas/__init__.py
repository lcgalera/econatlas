"""Nome antigo do pacote (até a v0.12). O código agora é `rotzx` (D35).

Mantido só para não quebrar comandos e scripts locais: `python -m econatlas …` e `import econatlas…`
continuam funcionando, redirecionados para `rotzx`. Use `python -m rotzx …` daqui em diante.
"""
import sys
import warnings

import rotzx

if sys.argv[:1] == ["-m"]:  # `python -m econatlas …`: o Python executa rotzx/__main__.py pelo __path__ redirecionado
    print("aviso: o comando agora é `python -m rotzx …`; `econatlas` continua funcionando por compatibilidade.", file=sys.stderr)
else:
    warnings.warn("o pacote 'econatlas' agora se chama 'rotzx'; use `import rotzx`", DeprecationWarning, stacklevel=2)
sys.modules[__name__] = rotzx
