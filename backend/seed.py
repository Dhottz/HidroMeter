"""Popula um cenário de demonstração para a Entrega 1:
1 condomínio, 3 blocos, algumas unidades com hidrômetro cada, 1 usuário
síndico (administra o condomínio) e 2 usuários morador (cada um vinculado a
uma unidade distinta). Rodar com: python seed.py
"""

from app.database import SessionLocal
from app.models import Bloco, Condominio, Hidrometro, Papel, Unidade, Usuario, UsuarioCondominio, UsuarioUnidade
from app.security import hash_senha

SENHA_DEMO = "senha123"


def main():
    db = SessionLocal()
    try:
        print("Limpando dados existentes...")
        for modelo in [UsuarioUnidade, UsuarioCondominio, Hidrometro, Unidade, Bloco, Usuario, Condominio]:
            db.query(modelo).delete()
        db.commit()

        condominio = Condominio(nome="Residencial Águas Claras", endereco="Rua das Palmeiras, 100")
        db.add(condominio)
        db.flush()

        unidades_criadas = []
        for nome_bloco in ["Bloco A", "Bloco B", "Bloco C"]:
            bloco = Bloco(nome=nome_bloco, condominio_id=condominio.id)
            db.add(bloco)
            db.flush()

            for i in range(1, 4):
                numero = f"{nome_bloco[-1]}{i:02d}"  # ex: A01, A02...
                unidade = Unidade(numero=numero, bloco_id=bloco.id)
                db.add(unidade)
                db.flush()
                db.add(Hidrometro(unidade_id=unidade.id, numero_serie=f"HID-{numero}", litros_por_pulso=1))
                unidades_criadas.append(unidade)

        senha_hash = hash_senha(SENHA_DEMO)

        sindico = Usuario(nome="Síndico Demo", email="sindico@hidrometer.com", senha_hash=senha_hash, papel=Papel.sindico)
        db.add(sindico)
        db.flush()
        db.add(UsuarioCondominio(usuario_id=sindico.id, condominio_id=condominio.id))

        morador1 = Usuario(nome="Morador Demo 1", email="morador1@hidrometer.com", senha_hash=senha_hash, papel=Papel.morador)
        db.add(morador1)
        db.flush()
        db.add(UsuarioUnidade(usuario_id=morador1.id, unidade_id=unidades_criadas[0].id))

        morador2 = Usuario(nome="Morador Demo 2", email="morador2@hidrometer.com", senha_hash=senha_hash, papel=Papel.morador)
        db.add(morador2)
        db.flush()
        db.add(UsuarioUnidade(usuario_id=morador2.id, unidade_id=unidades_criadas[3].id))

        db.commit()

        print(f"\nSeed concluído. Credenciais de demonstração (senha para todos: {SENHA_DEMO}):")
        print(f"- Síndico:  {sindico.email} (vê todo o condomínio \"{condominio.nome}\")")
        print(f"- Morador:  {morador1.email} (vê apenas a unidade {unidades_criadas[0].numero})")
        print(f"- Morador:  {morador2.email} (vê apenas a unidade {unidades_criadas[3].numero})")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
