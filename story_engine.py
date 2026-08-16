"""
story_engine.py — Motor de histórias ramificadas para o ecossistema Soney.

Gerencia uma árvore de episódios onde cada voto decide o próximo caminho.
A história "O Último Andar" se adapta às escolhas dos jogadores em tempo real.
"""

from typing import Optional

# ─── ÁRVORE DE EPISÓDIOS ────────────────────────────────────────
# Cada episódio tem: id, numero, titulo, hook, choices (A/B) e
# o próximo episódio para cada escolha (next_A, next_B)

STORY_TREE = {
    # ── EPISÓDIO 1 ──────────────────────────────────────────────
    "ep-1": {
        "number": 1,
        "title": "O Último Andar",
        "hook": "Ela aceitou o emprego dos sonhos. Mas o escritório no 13º andar guarda um segredo que ninguém nunca contou a ninguém...",
        "scene": "escritorio_vazio_noite",
        "characters": ["Clara", "Dr. Mendes"],
        "choices": [
            {"id": "A", "text": "Abrir a porta trancada 🔑"},
            {"id": "B", "text": "Fingir que não viu nada e ir embora 🚪"}
        ],
        "next_A": "ep-2a",
        "next_B": "ep-2b"
    },

    # ── EPISÓDIO 2A (escolheu ABRIR) ────────────────────────────
    "ep-2a": {
        "number": 2,
        "title": "O Segredo do 13º Andar",
        "hook": "Clara abriu a porta. O que ela viu lá dentro mudou tudo — arquivos, fotos, gravações. O Dr. Mendes sabe que ela sabe. E ela ouviu passos no corredor.",
        "scene": "sala_secreta",
        "characters": ["Clara", "Dr. Mendes", "Arquivo X"],
        "choices": [
            {"id": "A", "text": "Confrontar o Dr. Mendes com as provas 🎯"},
            {"id": "B", "text": "Copiar tudo e denunciar anonimamente 📱"}
        ],
        "next_A": "ep-3aa",
        "next_B": "ep-3ab"
    },

    # ── EPISÓDIO 2B (escolheu FINGIR) ───────────────────────────
    "ep-2b": {
        "number": 2,
        "title": "A Noite Inquieta",
        "hook": "Clara foi para casa, mas o rosto do Dr. Mendes não sai da cabeça dela. Ela viu algo estranho no olhar dele hoje. Algo que diz: 'eu sei que você viu'.",
        "scene": "apartamento_noite",
        "characters": ["Clara"],
        "choices": [
            {"id": "A", "text": "Voltar ao escritório agora mesmo 🔙"},
            {"id": "B", "text": "Ligar para a amiga jornalista 📞"}
        ],
        "next_A": "ep-3ba",
        "next_B": "ep-3bb"
    },

    # ── EPISÓDIO 3AA (abriu + confrontou) ───────────────────────
    "ep-3aa": {
        "number": 3,
        "title": "O Confronto",
        "hook": "Clara entrou na sala do Dr. Mendes com os arquivos na mão. 'Eu sei de tudo.' O silêncio que se seguiu foi mais alto que qualquer grito. Então ele sorriu.",
        "scene": "sala_diretor",
        "characters": ["Clara", "Dr. Mendes"],
        "choices": [
            {"id": "A", "text": "Gravar a conversa escondido 🎙️"},
            {"id": "B", "text": "Chamar a polícia na hora 🚔"}
        ],
        "next_A": "ep-4aaa",
        "next_B": "ep-4aab"
    },

    # ── EPISÓDIO 3AB (abriu + denunciou) ────────────────────────
    "ep-3ab": {
        "number": 3,
        "title": "A Denúncia Anônima",
        "hook": "Com os arquivos copiados no celular, Clara enviou tudo para o maior jornal da cidade. Agora não há como voltar atrás. Mas alguém está batendo na porta dela.",
        "scene": "apartamento_porta",
        "characters": ["Clara", "Desconhecido"],
        "choices": [
            {"id": "A", "text": "Atender a porta 🚪"},
            {"id": "B", "text": "Fugir pela janela de emergência 🪟"}
        ],
        "next_A": "ep-4aba",
        "next_B": "ep-4abb"
    },

    # ── EPISÓDIO 3BA (fingiu + voltou) ──────────────────────────
    "ep-3ba": {
        "number": 3,
        "title": "O Retorno",
        "hook": "Clara voltou ao escritório. O prédio está vazio — ou quase. Uma luz acesa no 13º andar. Ele ainda está lá. Ela precisa ver o que ele está fazendo.",
        "scene": "escritorio_noturno",
        "characters": ["Clara", "Dr. Mendes (ao fundo)"],
        "choices": [
            {"id": "A", "text": "Seguir o Dr. Mendes discretamente 👣"},
            {"id": "B", "text": "Invadir a sala dele enquanto está vazia 🚪"}
        ],
        "next_A": "ep-4baa",
        "next_B": "ep-4bab"
    },

    # ── EPISÓDIO 3BB (fingiu + ligou) ───────────────────────────
    "ep-3bb": {
        "number": 3,
        "title": "A Jornalista",
        "hook": "Lúcia, a amiga jornalista, atendeu no segundo toque. 'Clara? Você não vai acreditar no que eu descobri sobre o Dr. Mendes. Ele já fez isso antes.'",
        "scene": "ligacao_telefonica",
        "characters": ["Clara", "Lúcia (voz)"],
        "choices": [
            {"id": "A", "text": "Ir encontrar Lúcia agora mesmo 🤝"},
            {"id": "B", "text": "Pedir para ela investigar primeiro 🔍"}
        ],
        "next_A": "ep-4bba",
        "next_B": "ep-4bbb"
    },

    # ── EPISÓDIO 4 (finais) ─────────────────────────────────────
    "ep-4aaa": {
        "number": 4,
        "title": "A Gravação (Final A)",
        "hook": "Com tudo gravado no celular, Clara agora tem a confissão completa. O Dr. Mendes está algemado. Mas a verdade é mais sombria do que ela imaginava: não era só ele.",
        "scene": "delegacia",
        "characters": ["Clara", "Delegado", "Dr. Mendes"],
        "choices": [
            {"id": "A", "text": "Revelar tudo para a imprensa 📰"},
            {"id": "B", "text": "Usar isso para negociar uma promoção 💼"}
        ],
        "is_final": True,
        "final_title": "FINAL: A Verdade Vem à Tona"
    },
    "ep-4aab": {
        "number": 4,
        "title": "A Chegada da Polícia (Final B)",
        "hook": "A polícia chegou. Dr. Mendes tentou fugir, mas estava cercado. Clara assistiu de longe enquanto tudo desmoronava. Ela fez a escolha certa. Mas o preço... foi alto.",
        "scene": "escritorio_policia",
        "characters": ["Clara", "Polícia", "Dr. Mendes"],
        "choices": [],
        "is_final": True,
        "final_title": "FINAL: A Justiça Prevalece"
    },
    "ep-4aba": {
        "number": 4,
        "title": "O Visitante (Final C)",
        "hook": "Era Lúcia na porta. 'Clara, a história já está viralizando. Mas você precisa sumir por uns dias. O Dr. Mendes tem amigos poderosos.' Clara pegou a bolsa e saiu. A fuga começou.",
        "scene": "fuga_noturna",
        "characters": ["Clara", "Lúcia"],
        "choices": [],
        "is_final": True,
        "final_title": "FINAL: A Fuga"
    },
    "ep-4abb": {
        "number": 4,
        "title": "A Janela (Final D)",
        "hook": "Clara fugiu pela janela de emergência. Lá embaixo, no estacionamento, uma viatura preta esperava. Ela não sabia se era polícia ou eles. Correu para o beco escuro e não olhou para trás.",
        "scene": "beco_escuro",
        "characters": ["Clara"],
        "choices": [],
        "is_final": True,
        "final_title": "FINAL: Na Escuridão"
    },
    "ep-4baa": {
        "number": 4,
        "title": "A Sombra (Final E)",
        "hook": "Clara seguiu o Dr. Mendes até um depósito abandonado. O que ela viu lá dentro era maior do que imaginava — uma operação inteira. Agora ela tem as provas definitivas.",
        "scene": "deposito_abandonado",
        "characters": ["Clara", "Dr. Mendes"],
        "choices": [],
        "is_final": True,
        "final_title": "FINAL: A Prova Final"
    },
    "ep-4bab": {
        "number": 4,
        "title": "A Sala Vazia (Final F)",
        "hook": "Na sala do Dr. Mendes, Clara encontrou um computador aberto. Os arquivos estavam todos lá. Mas quando ouviu o elevador chegando, ela percebeu: agora era tarde demais para sair.",
        "scene": "sala_diretor_noite",
        "characters": ["Clara", "Dr. Mendes (chegando)"],
        "choices": [],
        "is_final": True,
        "final_title": "FINAL: Encurralada"
    },
    "ep-4bba": {
        "number": 4,
        "title": "O Encontro (Final G)",
        "hook": "Lúcia e Clara se encontraram no café da esquina. A jornalista tinha um dossiê completo. 'Isso é maior que o Dr. Mendes, Clara. Muito maior. Você está preparada?'",
        "scene": "cafe_noturno",
        "characters": ["Clara", "Lúcia"],
        "choices": [],
        "is_final": True,
        "final_title": "FINAL: A Aliança"
    },
    "ep-4bbb": {
        "number": 4,
        "title": "A Investigação (Final H)",
        "hook": "Lúcia investigou enquanto Clara esperava. Três dias depois, o telefone tocou. 'Clara... o Dr. Mendes desapareceu. E a polícia está procurando VOCÊ.'",
        "scene": "apartamento_tarde",
        "characters": ["Clara", "Lúcia (voz)"],
        "choices": [],
        "is_final": True,
        "final_title": "FINAL: O Suspeito"
    }
}


# ─── FUNÇÕES ────────────────────────────────────────────────────

def get_episode(episode_id: str) -> Optional[dict]:
    """Retorna um episódio pelo ID."""
    return STORY_TREE.get(episode_id)


def get_first_episode() -> dict:
    """Retorna o primeiro episódio da história."""
    return STORY_TREE["ep-1"]


def get_next_episode(current_episode_id: str, choice: str) -> Optional[dict]:
    """
    Retorna o próximo episódio baseado na escolha do jogador.
    
    Args:
        current_episode_id: ID do episódio atual (ex: "ep-1")
        choice: "A" ou "B"
    
    Returns:
        O próximo episódio ou None se for o final
    """
    episode = STORY_TREE.get(current_episode_id)
    if not episode:
        return None
    
    if choice == "A":
        next_id = episode.get("next_A")
    else:
        next_id = episode.get("next_B")
    
    if not next_id:
        return None
    
    return STORY_TREE.get(next_id)


def get_episode_by_number(number: int, path: str = "A") -> Optional[dict]:
    """
    Retorna um episódio pelo número e caminho.
    Útil para a API /episode/next.
    """
    # Mapeamento simples: número 1 = ep-1, números maiores seguem o caminho
    if number == 1:
        return STORY_TREE["ep-1"]
    if number == 2:
        return STORY_TREE.get(f"ep-2{path.lower()}")
    if number == 3:
        return STORY_TREE.get(f"ep-3{path.lower()}")
    if number == 4:
        return STORY_TREE.get(f"ep-4{path.lower()}")
    return None


def get_full_path(choices: list[str]) -> list[dict]:
    """
    Simula um caminho completo baseado em uma lista de escolhas.
    Ex: ["A", "B"] → ep-1 → ep-2a → ep-3ab
    """
    path = []
    current_id = "ep-1"
    
    for choice in choices:
        episode = STORY_TREE.get(current_id)
        if not episode:
            break
        path.append(episode)
        
        if choice == "A":
            current_id = episode.get("next_A")
        else:
            current_id = episode.get("next_B")
        
        if not current_id:
            break
    
    # Adiciona o último episódio
    last = STORY_TREE.get(current_id)
    if last:
        path.append(last)
    
    return path


def get_available_paths() -> list[dict]:
    """
    Retorna um resumo de todos os caminhos possíveis na história.
    """
    paths = []
    
    # Caminho A-A-A
    paths.append({"path": "A → A → A", "episodes": ["ep-1", "ep-2a", "ep-3aa", "ep-4aaa"], "final": "A Verdade Vem à Tona"})
    paths.append({"path": "A → A → B", "episodes": ["ep-1", "ep-2a", "ep-3aa", "ep-4aab"], "final": "A Justiça Prevalece"})
    paths.append({"path": "A → B → A", "episodes": ["ep-1", "ep-2a", "ep-3ab", "ep-4aba"], "final": "A Fuga"})
    paths.append({"path": "A → B → B", "episodes": ["ep-1", "ep-2a", "ep-3ab", "ep-4abb"], "final": "Na Escuridão"})
    paths.append({"path": "B → A → A", "episodes": ["ep-1", "ep-2b", "ep-3ba", "ep-4baa"], "final": "A Prova Final"})
    paths.append({"path": "B → A → B", "episodes": ["ep-1", "ep-2b", "ep-3ba", "ep-4bab"], "final": "Encurralada"})
    paths.append({"path": "B → B → A", "episodes": ["ep-1", "ep-2b", "ep-3bb", "ep-4bba"], "final": "A Aliança"})
    paths.append({"path": "B → B → B", "episodes": ["ep-1", "ep-2b", "ep-3bb", "ep-4bbb"], "final": "O Suspeito"})
    
    return paths


def get_stats() -> dict:
    """Estatísticas da história."""
    total = len(STORY_TREE)
    finais = sum(1 for ep in STORY_TREE.values() if ep.get("is_final"))
    return {
        "total_episodes": total,
        "finales": finais,
        "choices_per_episode": 8,
        "paths": 8
    }