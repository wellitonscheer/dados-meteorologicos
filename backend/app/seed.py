from sqlalchemy.orm import Session

from .config import SEED_PASSWORD, SEED_USERNAME
from .models import User
from .security import hash_password, verify_password


def seed_default_user(db: Session) -> None:
    """Garante o usuário definido em SEED_USERNAME/SEED_PASSWORD.

    Cria se não existir; se já existir e a senha divergir da configurada,
    atualiza o hash (permite trocar a senha pelo .env sem resetar o banco).
    """
    existing = db.query(User).filter(User.username == SEED_USERNAME).first()
    if existing:
        if not verify_password(SEED_PASSWORD, existing.hashed_password):
            existing.hashed_password = hash_password(SEED_PASSWORD)
            db.commit()
            print(f"[seed] senha do usuário '{SEED_USERNAME}' atualizada")
        return
    user = User(
        username=SEED_USERNAME,
        hashed_password=hash_password(SEED_PASSWORD),
    )
    db.add(user)
    db.commit()
    print(f"[seed] usuário '{SEED_USERNAME}' criado")
