"""
database.py — Banco de dados SQLite para o backend Soney.

Armazena:
- Jogadores e seus progressos
- Episódios gerados
- Votos dos jogadores
- Transações de compra
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Caminho do banco
DB_PATH = os.getenv("SONEY_DB_PATH", str(Path(__file__).parent / "soney_data.db"))


def get_connection() -> sqlite3.Connection:
    """Retorna uma conexão com o banco SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Performance em concorrência
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Inicializa as tabelas do banco de dados."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.executescript("""
        -- Jogadores do Roblox
        CREATE TABLE IF NOT EXISTS players (
            user_id TEXT PRIMARY KEY,
            user_name TEXT NOT NULL,
            display_name TEXT,
            total_coins_earned INTEGER DEFAULT 0,
            total_coins_spent INTEGER DEFAULT 0,
            episodes_watched INTEGER DEFAULT 0,
            votes_cast INTEGER DEFAULT 0,
            first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        
        -- Transações de coins
        CREATE TABLE IF NOT EXISTS coin_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount INTEGER NOT NULL,
            reason TEXT NOT NULL,  -- 'purchase', 'earned', 'welcome_bonus', 'vote', 'watch'
            reference_id TEXT,      -- ID da compra no Roblox, se aplicável
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        );
        
        -- Episódios de drama
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            hook TEXT,
            content TEXT,           -- JSON com o roteiro completo
            choices TEXT,           -- JSON com as opções de voto
            votes_a INTEGER DEFAULT 0,
            votes_b INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            published_at TEXT
        );
        
        -- Votos dos jogadores
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            episode_id INTEGER NOT NULL,
            choice TEXT NOT NULL CHECK(choice IN ('A', 'B')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES players(user_id),
            FOREIGN KEY (episode_id) REFERENCES episodes(id),
            UNIQUE(user_id, episode_id)  -- Um voto por episódio por jogador
        );
        
        -- Compras (vindas do Roblox)
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            receipt_id TEXT UNIQUE,  -- ID único da transação no Roblox
            amount_coins INTEGER NOT NULL,
            amount_usd REAL,
            status TEXT NOT NULL DEFAULT 'completed',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        );
        
        -- Índices para performance
        CREATE INDEX IF NOT EXISTS idx_coin_tx_user ON coin_transactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_votes_episode ON votes(episode_id);
        CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);
        CREATE INDEX IF NOT EXISTS idx_players_last_seen ON players(last_seen_at);
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Banco de dados inicializado em: {DB_PATH}")


# --- Players ---

def upsert_player(user_id: str, user_name: str, display_name: Optional[str] = None) -> dict:
    """Cria ou atualiza um jogador."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    
    conn.execute("""
        INSERT INTO players (user_id, user_name, display_name, first_seen_at, last_seen_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            user_name = excluded.user_name,
            display_name = COALESCE(excluded.display_name, players.display_name),
            last_seen_at = excluded.last_seen_at
    """, (user_id, user_name, display_name, now, now))
    
    conn.commit()
    
    cursor = conn.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = dict(cursor.fetchone())
    conn.close()
    return row


def add_coins(user_id: str, amount: int, reason: str, reference_id: Optional[str] = None) -> dict:
    """Adiciona coins a um jogador e registra a transação."""
    conn = get_connection()
    
    # Registra transação
    conn.execute("""
        INSERT INTO coin_transactions (user_id, amount, reason, reference_id)
        VALUES (?, ?, ?, ?)
    """, (user_id, amount, reason, reference_id))
    
    # Atualiza saldo do jogador
    if reason == "purchase":
        conn.execute("""
            UPDATE players SET 
                total_coins_earned = total_coins_earned + ?,
                last_seen_at = datetime('now')
            WHERE user_id = ?
        """, (amount, user_id))
    else:
        conn.execute("""
            UPDATE players SET 
                total_coins_earned = total_coins_earned + ?,
                last_seen_at = datetime('now')
            WHERE user_id = ?
        """, (amount, user_id))
    
    conn.commit()
    
    cursor = conn.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = dict(cursor.fetchone())
    conn.close()
    return row


def get_player(user_id: str) -> Optional[dict]:
    """Retorna dados de um jogador."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# --- Episódios ---

def create_episode(episode_number: int, title: str, hook: str, 
                   content: dict, choices: list[dict]) -> dict:
    """Cria um novo episódio de drama."""
    conn = get_connection()
    
    conn.execute("""
        INSERT INTO episodes (episode_number, title, hook, content, choices)
        VALUES (?, ?, ?, ?, ?)
    """, (
        episode_number, title, hook,
        json.dumps(content), json.dumps(choices)
    ))
    
    conn.commit()
    cursor = conn.execute("SELECT * FROM episodes ORDER BY id DESC LIMIT 1")
    row = dict(cursor.fetchone())
    conn.close()
    return row


def get_episode(episode_id: int) -> Optional[dict]:
    """Retorna um episódio pelo ID."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        row = dict(row)
        row["content"] = json.loads(row["content"]) if row.get("content") else {}
        row["choices"] = json.loads(row["choices"]) if row.get("choices") else []
        return row
    return None


def get_latest_episode() -> Optional[dict]:
    """Retorna o episódio mais recente."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM episodes ORDER BY episode_number DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        row = dict(row)
        if row.get("content"):
            row["content"] = json.loads(row["content"])
        if row.get("choices"):
            row["choices"] = json.loads(row["choices"])
        return row
    return None


# --- Votos ---

def register_vote(user_id: str, episode_id: int, choice: str) -> dict:
    """Registra o voto de um jogador em um episódio."""
    conn = get_connection()
    
    try:
        conn.execute("""
            INSERT INTO votes (user_id, episode_id, choice)
            VALUES (?, ?, ?)
        """, (user_id, episode_id, choice))
        
        # Atualiza contagem no episódio
        if choice == "A":
            conn.execute("UPDATE episodes SET votes_a = votes_a + 1 WHERE id = ?", (episode_id,))
        else:
            conn.execute("UPDATE episodes SET votes_b = votes_b + 1 WHERE id = ?", (episode_id,))
        
        # Atualiza contagem de votos do jogador
        conn.execute("""
            UPDATE players SET votes_cast = votes_cast + 1, last_seen_at = datetime('now')
            WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
        
        cursor = conn.execute("SELECT * FROM votes WHERE user_id = ? AND episode_id = ?", 
                            (user_id, episode_id))
        row = dict(cursor.fetchone())
        conn.close()
        return row
        
    except sqlite3.IntegrityError:
        conn.close()
        return {"error": "Jogador já votou neste episódio"}


def get_episode_votes(episode_id: int) -> dict:
    """Retorna a contagem de votos de um episódio."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT votes_a, votes_b FROM episodes WHERE id = ?", (episode_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return {"votes_a": 0, "votes_b": 0}


# --- Compras ---

def register_purchase(user_id: str, product_id: str, receipt_id: str,
                      amount_coins: int, amount_usd: Optional[float] = None) -> dict:
    """Registra uma compra feita no Roblox."""
    conn = get_connection()
    
    try:
        conn.execute("""
            INSERT INTO purchases (user_id, product_id, receipt_id, amount_coins, amount_usd)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, product_id, receipt_id, amount_coins, amount_usd))
        
        # Atualiza coins do jogador
        conn.execute("""
            UPDATE players SET 
                total_coins_earned = total_coins_earned + ?,
                last_seen_at = datetime('now')
            WHERE user_id = ?
        """, (amount_coins, user_id))
        
        conn.commit()
        cursor = conn.execute("SELECT * FROM purchases ORDER BY id DESC LIMIT 1")
        row = dict(cursor.fetchone())
        conn.close()
        return row
        
    except sqlite3.IntegrityError:
        conn.close()
        return {"error": "Receipt ID duplicado — compra já processada"}


# --- Estatísticas ---

def get_stats() -> dict:
    """Retorna estatísticas gerais do ecossistema Soney."""
    conn = get_connection()
    
    cursor = conn.execute("SELECT COUNT(*) as total FROM players")
    total_players = cursor.fetchone()["total"]
    
    cursor = conn.execute("SELECT COALESCE(SUM(amount), 0) as total FROM coin_transactions WHERE reason != 'purchase'")
    total_coins_earned = cursor.fetchone()["total"]
    
    cursor = conn.execute("SELECT COALESCE(SUM(amount), 0) as total FROM coin_transactions WHERE reason = 'purchase'")
    total_coins_purchased = cursor.fetchone()["total"]
    
    cursor = conn.execute("SELECT COUNT(*) as total FROM votes")
    total_votes = cursor.fetchone()["total"]
    
    cursor = conn.execute("SELECT COUNT(*) as total FROM episodes")
    total_episodes = cursor.fetchone()["total"]
    
    cursor = conn.execute("SELECT COUNT(*) as total FROM purchases")
    total_purchases = cursor.fetchone()["total"]
    
    cursor = conn.execute("""
        SELECT COALESCE(SUM(amount_coins), 0) as total FROM purchases
    """)
    total_revenue_coins = cursor.fetchone()["total"]
    
    conn.close()
    
    return {
        "total_players": total_players,
        "total_coins_earned": total_coins_earned,
        "total_coins_purchased": total_coins_purchased,
        "total_votes": total_votes,
        "total_episodes": total_episodes,
        "total_purchases": total_purchases,
        "total_revenue_coins": total_revenue_coins
    }