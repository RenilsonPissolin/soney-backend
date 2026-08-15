# 🎬 Soney Backend

**Backend do ecossistema Soney** — Ponte entre Roblox e o agente Soney na Virtuals Protocol.

## 🚀 Rotas da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Informações da API |
| `GET` | `/health` | Health check |
| `GET` | `/agent/status` | Status do agente Soney (Virtuals) |
| `POST` | `/sync` | Sincronizar jogador do Roblox |
| `GET` | `/player/{user_id}` | Dados de um jogador |
| `GET` | `/episode/latest` | Último episódio do drama |
| `GET` | `/episode/next/{user_id}` | Próximo episódio personalizado |
| `POST` | `/episode` | Criar novo episódio |
| `POST` | `/vote` | Registrar voto do jogador |
| `POST` | `/purchase` | Processar compra do Roblox |
| `POST` | `/drama/generate` | Gerar roteiro de drama via agente |
| `GET` | `/stats` | Estatísticas do ecossistema |
| `POST` | `/roblox/webhook` | Webhook genérico do Roblox |

## 📦 Deploy no Render

1. Crie o repositório no GitHub
2. Conecte no [Render](https://dashboard.render.com) → New → Blueprint
3. Aponte para `render.yaml`

## 🛠️ Tecnologias

- **FastAPI** — Servidor web
- **SQLite** — Banco de dados local
- **ACP CLI** — Comunicação com Virtuals Protocol
- **Docker** — Containerização

---

<p align="center">🎬 Feito com ❤️ por Soney AI</p>