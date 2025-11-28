from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# CREATE CONNECTION STRING
DB_URL = (
    f"mysql+pymysql://{settings.DB_USERNAME}:"
    f"{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:"
    f"{settings.DB_PORT}/"
    f"{settings.DB_NAME}"
)

print("🔌 Conectando a:", DB_URL)


engine = create_engine(DB_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency for routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
