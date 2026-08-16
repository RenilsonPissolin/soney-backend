"""
main.py — Servidor FastAPI do ecossistema Soney.

Pontes entre Roblox e o agente Soney na Virtuals Protocol.
Rotas para sync, compras, votos, episódios e estatísticas.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Módulos internos
from database import init_db, get_stats as db_get_stats
from database import (
    upsert_player, add_coins, get_player, get_latest_episode,
    register_vote, register_purchase, get_episode_votes, create_episode
)
from soney_bridge import (
    get_agent_status, sync_player_data, process_vote,
    get_next_episode, process_purchase, generate_drama_script
)
from story_engine import (
    STORY_TREE, get_episode, get_first_episode, get_next_episode as story_next,
    get_available_paths, get_stats as story_stats
)

# ─── Configuração ────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("soney.api")

API_KEY = os.getenv("SONEY_API_KEY", "soney-dev-key-2026")
ENABLE_AUTH = os.getenv("SONEY_ENABLE_AUTH", "false").lower() == "true"


# ─── Modelos Pydantic ────────────────────────────────────────────

class SyncRequest(BaseModel):
    userId: int
    userName: str
    displayName: Optional[str] = None
    coinsEarned: int = 0
    reason: str = "earned"
    referenceId: Optional[str] = None
    timestamp: Optional[str] = None


class VoteRequest(BaseModel):
    userId: int
    userName: str
    episodeId: int
    choice: str = Field(..., pattern="^[AB]$")


class PurchaseRequest(BaseModel):
    userId: int
    userName: str
    productId: str
    receiptId: str
    amountCoins: int
    amountUsd: Optional[float] = None


class EpisodeRequest(BaseModel):
    episodeNumber: int
    title: str
    hook: str
    content: dict = {}
    choices: list[dict] = []


class DramaRequest(BaseModel):
    theme: str
    tone: str = "drama"
    episode: int = 1
    userId: Optional[int] = None


# ─── Autenticação ────────────────────────────────────────────────

async def verify_api_key(request: Request):
    """Verifica a API key nos headers, se a autenticação estiver ativa."""
    if not ENABLE_AUTH:
        return True
    
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    return True


# ─── Lifecycle ───────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa o banco de dados ao iniciar o servidor."""
    logger.info("🎬 Inicializando servidor Soney...")
    init_db()
    logger.info("✅ Banco de dados pronto!")
    yield
    logger.info("👋 Servidor Soney finalizado.")


# ─── App FastAPI ─────────────────────────────────────────────────

app = FastAPI(
    title="Soney API",
    description="Backend do ecossistema Soney — ponte Roblox ↔ Virtuals Protocol",
    version="1.0.0",
    lifespan=lifespan
)

# CORS — permite requisições do Roblox e de qualquer origem em dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Rotas ───────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Raiz — informações básicas da API."""
    return {
        "service": "Soney API",
        "version": "1.0.0",
        "status": "online",
        "agent": "Virtuals Protocol / ACP",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check para monitoramento."""
    agent = await get_agent_status()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_online": agent.get("online", False)
    }


# ─── Agente ──────────────────────────────────────────────────────

@app.get("/agent/status")
async def agent_status():
    """Status do agente Soney na Virtuals Protocol."""
    status = await get_agent_status()
    return status


# ─── Jogadores ────────────────────────────────────────────────────

@app.post("/sync")
async def sync_player(req: SyncRequest):
    """
    Sincroniza dados de um jogador do Roblox.
    Chamado quando um jogador ganha coins, assiste episódio, etc.
    """
    # Upsert no banco
    player = upsert_player(
        user_id=str(req.userId),
        user_name=req.userName,
        display_name=req.displayName
    )
    
    # Se tiver coins, registra transação
    if req.coinsEarned > 0:
        add_coins(
            user_id=str(req.userId),
            amount=req.coinsEarned,
            reason=req.reason,
            reference_id=req.referenceId
        )
        # Recarrega dados atualizados
        player = get_player(str(req.userId)) or player
    
    # Notifica o agente (assíncrono, não bloqueia)
    bridge_result = await sync_player_data({
        "userId": req.userId,
        "userName": req.userName,
        "coinsEarned": req.coinsEarned,
        "reason": req.reason,
        "timestamp": req.timestamp or datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "player": {
            "user_id": str(req.userId),
            "user_name": req.userName,
            "total_coins": player.get("total_coins_earned", 0),
            "episodes_watched": player.get("episodes_watched", 0),
            "votes_cast": player.get("votes_cast", 0)
        },
        "bridge_sync": bridge_result.get("success", False)
    }


@app.get("/player/{user_id}")
async def get_player_info(user_id: str):
    """Retorna informações de um jogador."""
    player = get_player(user_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    return player


# ─── Episódios ───────────────────────────────────────────────────

@app.get("/episode/latest")
async def latest_episode():
    """Retorna o episódio mais recente da história ramificada."""
    episode = get_first_episode()
    if not episode:
        return {"episode": {"id": "ep-1", "number": 1, "title": "Carregando...", "hook": "Aguarde...", "choices": []}}
    return {"episode": episode}


@app.get("/episode/next/{user_id}")
async def next_episode(user_id: str, last_episode: int = 0, last_choice: str = "A"):
    """
    Retorna o próximo episódio baseado na escolha anterior.
    Usa a árvore de histórias ramificadas.
    """
    episode = get_first_episode()
    
    if last_episode == 1:
        episode = story_next("ep-1", last_choice)
    elif last_episode == 2:
        # Determina qual ep-2 baseado no caminho
        episode = story_next(f"ep-2{last_choice.lower()}", last_choice)
    elif last_episode == 3:
        episode = story_next(f"ep-3{last_choice.lower()}", last_choice)
    
    if not episode:
        return {"episode": None, "message": "História concluída!", "is_final": True}
    
    return {"episode": episode, "is_final": episode.get("is_final", False)}


# ─── Rotas da História Ramificada ────────────────────────────────

@app.get("/story/episode/{episode_id}")
async def story_get_episode(episode_id: str):
    """Retorna um episódio específico da árvore de histórias."""
    episode = get_episode(episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episódio não encontrado")
    return {"episode": episode}


@app.get("/story/paths")
async def story_paths():
    """Retorna todos os caminhos possíveis na história."""
    paths = get_available_paths()
    return {"paths": paths, "total": len(paths)}


@app.get("/story/stats")
async def story_statistics():
    """Estatísticas da história ramificada."""
    stats = story_stats()
    return stats


@app.post("/story/advance")
async def story_advance(data: dict):
    """
    Avança a história baseado no voto do jogador.
    Recebe: { "episode_id": "ep-1", "choice": "A" }
    Retorna: o próximo episódio
    """
    episode_id = data.get("episode_id", "ep-1")
    choice = data.get("choice", "A")
    
    next_ep = story_next(episode_id, choice)
    if not next_ep:
        return {"episode": None, "message": "Fim da história!", "is_final": True}
    
    return {"episode": next_ep, "is_final": next_ep.get("is_final", False)}


@app.post("/episode")
async def create_new_episode(req: EpisodeRequest):
    """Cria um novo episódio (endpoint administrativo)."""
    episode = create_episode(
        episode_number=req.episodeNumber,
        title=req.title,
        hook=req.hook,
        content=req.content,
        choices=req.choices
    )
    return {"success": True, "episode": episode}


# ─── Votos ───────────────────────────────────────────────────────

@app.post("/vote")
async def submit_vote(req: VoteRequest):
    """
    Registra o voto de um jogador em uma decisão do drama.
    """
    # Garante que o jogador existe
    upsert_player(user_id=str(req.userId), user_name=req.userName)
    
    # Registra o voto
    result = register_vote(
        user_id=str(req.userId),
        episode_id=req.episodeId,
        choice=req.choice
    )
    
    if "error" in result:
        raise HTTPException(status_code=409, detail=result["error"])
    
    # Notifica o agente
    await process_vote(str(req.userId), str(req.episodeId), req.choice)
    
    # Retorna resultado atualizado
    votes = get_episode_votes(req.episodeId)
    total = votes["votes_a"] + votes["votes_b"]
    percentage_a = round((votes["votes_a"] / total * 100), 1) if total > 0 else 0
    percentage_b = round((votes["votes_b"] / total * 100), 1) if total > 0 else 0
    
    return {
        "success": True,
        "vote": {
            "user_id": str(req.userId),
            "episode_id": req.episodeId,
            "choice": req.choice
        },
        "results": {
            "total_votes": total,
            "option_a": votes["votes_a"],
            "option_b": votes["votes_b"],
            "percentage_a": percentage_a,
            "percentage_b": percentage_b
        }
    }


# ─── Compras ─────────────────────────────────────────────────────

@app.post("/purchase")
async def process_purchase_route(req: PurchaseRequest):
    """
    Processa uma compra feita no Roblox.
    O receiptId garante que não haja duplicatas.
    """
    # Garante que o jogador existe
    upsert_player(user_id=str(req.userId), user_name=req.userName)
    
    # Registra a compra
    result = register_purchase(
        user_id=str(req.userId),
        product_id=req.productId,
        receipt_id=req.receiptId,
        amount_coins=req.amountCoins,
        amount_usd=req.amountUsd
    )
    
    if "error" in result:
        # Receipt duplicado = compra já processada, não é erro fatal
        return {
            "success": True,
            "message": "Compra já foi processada anteriormente",
            "duplicate": True
        }
    
    # Notifica o agente
    await process_purchase(str(req.userId), req.productId, req.amountCoins)
    
    return {
        "success": True,
        "message": "Compra processada com sucesso!",
        "purchase": result,
        "bonus": {
            "exclusive_episodes": 1,
            "bonus_coins": req.amountCoins
        }
    }


# ─── Drama (geração de roteiros) ────────────────────────────────

@app.post("/drama/generate")
async def generate_drama(req: DramaRequest):
    """
    Solicita a geração de um novo roteiro de drama.
    Usa a offering do agente Soney na Virtuals Protocol.
    """
    result = await generate_drama_script(
        theme=req.theme,
        tone=req.tone,
        episode=req.episode
    )
    return result


# ─── Estatísticas ────────────────────────────────────────────────

@app.get("/stats")
async def stats():
    """Estatísticas do ecossistema Soney."""
    return db_get_stats()


# ─── Webhook para Roblox (resposta formatada) ────────────────────

@app.post("/roblox/webhook")
async def roblox_webhook(request: Request):
    """
    Webhook genérico para o Roblox.
    Aceita qualquer payload e distribui para a rota correta.
    """
    body = await request.json()
    action = body.get("action", "sync")
    
    if action == "sync":
        return await sync_player(SyncRequest(**body.get("data", {})))
    elif action == "vote":
        return await submit_vote(VoteRequest(**body.get("data", {})))
    elif action == "purchase":
        return await process_purchase_route(PurchaseRequest(**body.get("data", {})))
    else:
        raise HTTPException(status_code=400, detail=f"Ação desconhecida: {action}")


# ─── Ponto de entrada ────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🎬 Soney API rodando em http://{host}:{port}")
    print(f"📚 Documentação: http://{host}:{port}/docs")
    print(f"🏥 Health check: http://{host}:{port}/health")
    
    uvicorn.run("main:app", host=host, port=port, reload=True)