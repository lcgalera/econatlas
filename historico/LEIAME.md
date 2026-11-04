# Histórico do radar de oportunidades (SIGET)

Gerado por `econatlas siget-atualizar` + `econatlas siget-historico-exportar` (toda segunda-feira, pelo workflow `radar-siget.yml`).

| Arquivo | Conteúdo | Regra |
|---|---|---|
| `siget_coletas.csv` | uma linha por coleta que trouxe arquivos diferentes, com os nomes (prefixo SHA-256) dos arquivos da ANEEL | só acréscimos |
| `siget_eventos.csv` | o que mudou em cada empreendimento entre uma coleta e a anterior: `novo`, `saiu_da_fonte` ou `mudou` (campo, antes, depois) | só acréscimos |
| `siget_estado.csv` | os campos acompanhados de cada empreendimento na última coleta, para comparar com a próxima | regravado a cada coleta (derivado) |

A exportação falha se uma linha antiga de `siget_coletas.csv` ou `siget_eventos.csv` divergir do banco. O histórico do git mostra quando cada linha entrou.
Isso torna o histórico auditável, mas não impossível de reescrever por quem controla o repositório (D27).

Contém dados da ANEEL (SIGET, Portal de Dados Abertos), disponibilizados sob a licença ODbL. Esta é uma base derivada, sob a mesma licença.
