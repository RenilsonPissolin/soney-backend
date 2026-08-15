"""
soney_bridge.py — Ponte entre o backend FastAPI e o agente Soney na Virtuals Protocol.

Usa o ACP CLI para interagir com o agente on-chain e o marketplace.
Também gerencia webhooks e comunicação com o agente via console.
"""

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("soney.bridge")

# Configurações do agente
AGENT_ID = os.getenv("SONEY_AGENT_ID", "acp-ba6dd7313b0ee18864d3")
VIRTUAL_AGENT_ID = int(os.getenv("SONEY_VIRTUAL_AGENT_ID", "133819"))
TOKEN_SYMBOL = os.getenv("SONEY_TOKEN_SYMBOL", "SONEY")
CHAIN_ID = int(os.getenv("CHAIN_ID", "8453"))  # Base Chain

# Caminho do ACP CLI
ACP_CLI = os.getenv("ACP_CLI_PATH", "acp")


def _run_acp(args: list[str]) -> dict:
    """
    Executa um comando do ACP CLI e retorna o JSON parseado.
    """
    cmd = [ACP_CLI] + args + ["--json"]
    logger.info(f"Executando ACP: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "IS_TESTNET": os.getenv("IS_TESTNET", "false")}
        )
        
        if result.returncode != 0:
            # Tenta parsear erro JSON do stderr
            try:
                err = json.loads(result.stderr)
                logger.error(f"ACP CLI erro: {err.get('error', result.stderr)}")
                return {"success": False, "error": err.get("error", result.stderr)}
            except json.JSONDecodeError:
                logger.error(f"ACP CLI erro bruto: {result.stderr}")
                return {"success": False, "error": result.stderr.strip()}
        
        # Parseia stdout
        try:
            data = json.loads(result.stdout)
            return {"success": True, "data": data}
        except json.JSONDecodeError:
            return {"success": True, "data": {"raw": result.stdout.strip()}}
            
    except subprocess.TimeoutExpired:
        logger.error("ACP CLI timeout (30s)")
        return {"success": False, "error": "Timeout"}
    except FileNotFoundError:
        logger.error(f"ACP CLI não encontrado em: {ACP_CLI}")
        return {"success": False, "error": "ACP CLI não instalado"}
    except Exception as e:
        logger.error(f"Erro inesperado no ACP CLI: {e}")
        return {"success": False, "error": str(e)}


async def get_agent_status() -> dict:
    """
    Verifica o status do agente Soney na Virtuals Protocol.
    """
    result = _run_acp(["agent", "whoami"])
    if result["success"]:
        data = result["data"]
        return {
            "online": True,
            "name": data.get("name", "Soney"),
            "wallet": data.get("walletAddress"),
            "solana_wallet": data.get("solWalletAddress"),
            "offerings": len(data.get("offerings", [])),
            "last_active": data.get("lastActiveAt"),
            "agent_id": data.get("id"),
            "virtual_agent_id": VIRTUAL_AGENT_ID,
            "token": TOKEN_SYMBOL,
            "chain_id": CHAIN_ID
        }
    return {
        "online": False,
        "error": result.get("error", "Unknown"),
        "agent_id": AGENT_ID,
        "virtual_agent_id": VIRTUAL_AGENT_ID
    }


async def get_wallet_balance() -> dict:
    """
    Consulta o saldo da wallet do agente.
    """
    result = _run_acp(["wallet", "balance", "--chain-id", str(CHAIN_ID)])
    if result["success"]:
        return {"success": True, "balance": result["data"]}
    return {"success": False, "error": result.get("error")}


async def generate_drama_script(theme: str, tone: str, episode: int) -> dict:
    """
    Contrata o próprio agente Soney (via offering) para gerar um roteiro de drama.
    
    Isso usa o marketplace ACP — o agente se auto-contrata ou 
    podemos chamar diretamente a offering.
    """
    logger.info(f"Solicitando roteiro: tema={theme}, tom={tone}, ep={episode}")
    
    # Aqui podemos usar o ACP marketplace para criar um job
    # ou chamar diretamente a offering do agente
    # Por enquanto, retornamos um placeholder
    
    return {
        "success": True,
        "message": "Roteiro solicitado com sucesso",
        "episode": episode,
        "theme": theme,
        "tone": tone,
        "status": "processing"
    }


async def sync_player_data(player_data: dict) -> dict:
    """
    Sincroniza dados de um jogador do Roblox com o ecossistema Soney.
    
    Args:
        player_data: {
            userId, userName, coinsEarned, reason, timestamp
        }
    """
    logger.info(f"Sincronizando jogador: {player_data.get('userName')} "
                f"({player_data.get('coinsEarned')} coins)")
    
    # Validação básica
    required = ["userId", "userName", "coinsEarned"]
    for field in required:
        if field not in player_data:
            return {"success": False, "error": f"Campo obrigatório: {field}"}
    
    # Aqui podemos:
    # 1. Salvar no banco (feito pelo database.py)
    # 2. Enviar notificação para o agente via ACP message
    # 3. Atualizar leaderboard on-chain se aplicável
    
    return {
        "success": True,
        "message": f"Jogador {player_data['userName']} sincronizado com sucesso",
        "coins": player_data.get("coinsEarned", 0),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


async def process_vote(user_id: str, episode_id: str, choice: str) -> dict:
    """
    Processa um voto do jogador em uma decisão do drama.
    """
    logger.info(f"Voto: user={user_id}, ep={episode_id}, choice={choice}")
    
    # Aqui podemos registrar o voto e usar o resultado
    # para influenciar o próximo episódio
    
    return {
        "success": True,
        "message": "Voto registrado com sucesso",
        "episode_id": episode_id,
        "choice": choice,
        "total_votes": 0  # Placeholder - viria do banco
    }


async def get_next_episode(user_id: str, last_episode: int = 0) -> dict:
    """
    Retorna o próximo episódio do drama para o jogador.
    Pode ser personalizado baseado nos votos anteriores.
    """
    next_ep = last_episode + 1
    
    # Placeholder - numa versão real, isso viria do agente
    # ou de um banco de episódios
    
    return {
        "success": True,
        "episode": {
            "id": f"ep-{next_ep}",
            "number": next_ep,
            "title": f"Episódio {next_ep}",
            "hook": "O que você faria se descobrisse o segredo...",
            "choices": [
                {"id": "A", "text": "Enfrentar a verdade"},
                {"id": "B", "text": "Fugir enquanto pode"}
            ]
        }
    }


async def process_purchase(user_id: str, product_id: str, amount: float) -> dict:
    """
    Processa uma compra feita no Roblox e registra no ecossistema Soney.
    """
    logger.info(f"Compra: user={user_id}, product={product_id}, amount={amount}")
    
    return {
        "success": True,
        "message": "Compra registrada com sucesso",
        "product_id": product_id,
        "amount": amount,
        "bonus_episodes": 1  # Bônus por comprar
    }