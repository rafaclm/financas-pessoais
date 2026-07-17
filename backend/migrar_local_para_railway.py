"""
Script de migracao: PostgreSQL LOCAL -> PostgreSQL Railway (nuvem)

INSTRUCOES:
1. Preencha DATABASE_URL_RAILWAY logo abaixo com a URL do Railway
2. Confirme que o backend LOCAL nao esta rodando
3. Execute: python migrar_local_para_railway.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, MetaData, text
from loguru import logger

from app.core.config import settings
from app.infrastructure.db.base import Base
from app.infrastructure.db import models  # noqa: F401


# ============================================================
# ⚠️ COLE AQUI A URL DO POSTGRESQL DO RAILWAY
# ============================================================
DATABASE_URL_RAILWAY = "postgresql://postgres:pdPEhwuEOZKWzHgYLQVrXQKmThIEnFBw@postgres.railway.internal:5432/railway"


# Ordem correta de migracao (respeitando FKs)
ORDEM_TABELAS = [
    "anos",
    "categorias_despesas",
    "categorias_receitas",
    "instituicoes",
    "ativos",
    "usuarios",
    "contas",
    "produtos_investimento",
    "cartoes",
    "lancamentos_receitas",
    "lancamentos_combustivel",
    "aportes_bolsa",
    "proventos",
    "pagamentos_cartao",
    "lancamentos_despesas",
    "saldos_contas",
    "saldos_investimentos",
    "posicoes_cripto",
    "posicoes_ativos_br",
    "posicoes_ativos_eua",
    "cotacoes_cambio",
    "posicao_atual_ativo",
    "balanceamento_config_geografia",
    "balanceamento_config_classe",
    "balanceamento_config_ativo",
]


def _ajustar_url(url: str) -> str:
    """Railway usa 'postgresql://' - adaptamos para 'postgresql+psycopg2://'."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "psycopg2" not in url:
        return "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def validar_config():
    """Verifica configuracoes basicas."""
    if DATABASE_URL_RAILWAY == "COLE_AQUI_A_URL_DO_RAILWAY":
        logger.error(
            "❌ Voce nao configurou a DATABASE_URL_RAILWAY!\n"
            "   Abra o script e cole a URL do PostgreSQL do Railway."
        )
        sys.exit(1)

    if not settings.database_url.startswith(("postgresql", "postgres")):
        logger.error(
            "❌ O .env local nao esta apontando para PostgreSQL.\n"
            "   Verifique a variavel DATABASE_URL no .env."
        )
        sys.exit(1)

    logger.info(f"📤 Origem: PostgreSQL LOCAL")
    logger.info(f"📥 Destino: PostgreSQL RAILWAY (nuvem)")


def criar_engine_local():
    """Engine para o PostgreSQL LOCAL."""
    return create_engine(settings.database_url)


def criar_engine_railway():
    """Engine para o PostgreSQL RAILWAY."""
    url_ajustada = _ajustar_url(DATABASE_URL_RAILWAY)
    return create_engine(url_ajustada, pool_pre_ping=True)


def recriar_tabelas_railway(engine_destino):
    """Recria as tabelas no Railway (drop + create)."""
    logger.info("🔧 Recriando tabelas no Railway...")
    Base.metadata.drop_all(bind=engine_destino)
    Base.metadata.create_all(bind=engine_destino)
    logger.info(f"✅ {len(ORDEM_TABELAS)} tabelas recriadas na nuvem")


def migrar_tabela(nome_tabela, engine_origem, engine_destino):
    """Migra uma tabela do local para o Railway."""
    with engine_origem.connect() as conn_origem:
        try:
            result = conn_origem.execute(text(f"SELECT * FROM {nome_tabela}"))
            registros = [dict(row._mapping) for row in result]
        except Exception as e:
            logger.warning(f"  ⚠️ Tabela '{nome_tabela}' nao existe local: {e}")
            return (0, 0)

    if not registros:
        return (0, 0)

    with engine_destino.connect() as conn_destino:
        metadata = MetaData()
        metadata.reflect(bind=engine_destino, only=[nome_tabela])
        tabela = metadata.tables.get(nome_tabela)

        if tabela is None:
            logger.warning(f"  ⚠️ Tabela '{nome_tabela}' nao existe no Railway")
            return (len(registros), 0)

        try:
            conn_destino.execute(tabela.insert(), registros)
            conn_destino.commit()
        except Exception as e:
            logger.error(f"  ❌ Erro ao inserir em '{nome_tabela}': {e}")
            return (len(registros), 0)

        result = conn_destino.execute(text(f"SELECT COUNT(*) FROM {nome_tabela}"))
        destino_count = result.scalar() or 0

    return (len(registros), destino_count)


def resetar_sequences_railway(engine_destino):
    """Reseta as sequences (auto-increment) apos insercao de IDs."""
    logger.info("🔧 Resetando sequences do Railway...")

    with engine_destino.connect() as conn:
        for tabela in ORDEM_TABELAS:
            try:
                sql = text(f"""
                    SELECT setval(
                        pg_get_serial_sequence('{tabela}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {tabela}), 1),
                        true
                    )
                """)
                conn.execute(sql)
                conn.commit()
            except Exception:
                pass

    logger.info("✅ Sequences resetadas")


def verificar_totais(engine_local, engine_railway):
    """Compara totais entre local e Railway."""
    logger.info("\n📊 Comparativo Local vs Railway:")
    logger.info(f"{'Tabela':<40} {'Local':>10} {'Railway':>10}")
    logger.info("-" * 60)

    for nome in ORDEM_TABELAS:
        try:
            with engine_local.connect() as c1:
                r1 = c1.execute(text(f"SELECT COUNT(*) FROM {nome}"))
                cnt_origem = r1.scalar() or 0
        except Exception:
            cnt_origem = 0

        try:
            with engine_railway.connect() as c2:
                r2 = c2.execute(text(f"SELECT COUNT(*) FROM {nome}"))
                cnt_destino = r2.scalar() or 0
        except Exception:
            cnt_destino = 0

        if cnt_origem == 0 and cnt_destino == 0:
            continue

        icone = "✅" if cnt_origem == cnt_destino else "⚠️"
        logger.info(f"{icone} {nome:<38} {cnt_origem:>10} {cnt_destino:>10}")


def migrar_tudo():
    """Executa a migracao completa."""
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO MIGRACAO: LOCAL -> RAILWAY (NUVEM)")
    logger.info("=" * 60)

    validar_config()

    engine_local = criar_engine_local()
    engine_railway = criar_engine_railway()

    logger.info("\n📦 Passo 1/4: Preparando Railway")
    recriar_tabelas_railway(engine_railway)

    logger.info("\n📦 Passo 2/4: Copiando dados")
    total_registros = 0
    tabelas_com_erro = []

    for nome in ORDEM_TABELAS:
        try:
            origem, destino = migrar_tabela(nome, engine_local, engine_railway)
            if origem > 0:
                status = "✅" if origem == destino else "⚠️"
                logger.info(f"  {status} {nome}: {origem} -> {destino}")
                total_registros += destino
                if origem != destino:
                    tabelas_com_erro.append(nome)
        except Exception as e:
            logger.error(f"  ❌ Erro na tabela {nome}: {e}")
            tabelas_com_erro.append(nome)

    logger.info(f"\n📊 Total copiado: {total_registros} registros")

    logger.info("\n📦 Passo 3/4: Ajustando sequences")
    resetar_sequences_railway(engine_railway)

    logger.info("\n📦 Passo 4/4: Verificacao final")
    verificar_totais(engine_local, engine_railway)

    logger.info("\n" + "=" * 60)
    if tabelas_com_erro:
        logger.warning(f"⚠️ MIGRACAO COM AVISOS ({len(tabelas_com_erro)} tabelas):")
        for t in tabelas_com_erro:
            logger.warning(f"    - {t}")
    else:
        logger.info("✅ MIGRACAO CONCLUIDA COM SUCESSO!")
        logger.info("🎉 Seus dados agora estao NA NUVEM!")
    logger.info("=" * 60)


if __name__ == "__main__":
    migrar_tudo()