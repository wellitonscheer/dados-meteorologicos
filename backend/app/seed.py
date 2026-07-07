from sqlalchemy.orm import Session

from .config import SEED_PASSWORD, SEED_USERNAME
from .models import User
from .security import hash_password


def seed_default_user(db: Session) -> None:
    """Cria o usuário padrão (admin/admin) se ainda não existir."""
    existing = db.query(User).filter(User.username == SEED_USERNAME).first()
    if existing:
        return
    user = User(
        username=SEED_USERNAME,
        hashed_password=hash_password(SEED_PASSWORD),
    )
    db.add(user)
    db.commit()
    print(f"[seed] usuário '{SEED_USERNAME}' criado")
