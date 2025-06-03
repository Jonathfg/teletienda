# app/main.py

import os
import uvicorn
import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from sqlmodel import Session, select, text  # IMPORTA text para ejecutar SQL crudo
from sqlalchemy.exc import ProgrammingError

from app.database import create_db_and_tables, engine
from app.models import User, Role
from app.auth import get_password_hash

# Constantes para el usuario admin por defecto
DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
DEFAULT_ADMIN_FULLNAME = os.getenv("DEFAULT_ADMIN_FULLNAME", "Administrador")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

app = FastAPI(title="Tienda Online API", version="1.0.0")

# ------------------ Configuración de Logging ------------------
LOG_FILE = os.getenv("LOG_FILE", "tienda_online.log")
logger = logging.getLogger("tienda_online")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=3)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


@app.on_event("startup")
def on_startup():
    """
    1. AÑADE 'cliente' al ENUM 'role' si aún no existe.
    2. Crea las tablas (si no existen).
    3. Inserta un usuario admin por defecto si no existe ninguno.
    """
    # --------------------------------------------------------------
    # 1. AÑADIR 'cliente' AL ENUM role (si ya existe el tipo)
    # --------------------------------------------------------------
    try:
        with engine.connect() as conn:
            # Este bloque PL/pgSQL comprueba si el enum 'role' ya tiene la etiqueta 'cliente';
            # si no la tiene, la añade. Posible error si el tipo no existe, por eso except ProgrammingError.
            conn.execute(
                text(
                    """
                    DO $$
                    BEGIN
                      IF EXISTS (
                        SELECT 1
                          FROM pg_type t
                          JOIN pg_enum e ON t.oid = e.enumtypid
                         WHERE t.typname = 'role'
                           AND e.enumlabel = 'cliente'
                      ) THEN
                        -- Ya existe 'cliente', no hacemos nada
                        RAISE NOTICE 'Enum superado: cliente ya existe';
                      ELSE
                        -- Si el tipo role existe, lo alteramos para añadir cliente
                        ALTER TYPE role ADD VALUE 'cliente';
                      END IF;
                    EXCEPTION WHEN undefined_object THEN
                      -- Si llegamos aquí es porque el tipo role NO existe todavía; lo ignoramos:
                      RAISE NOTICE 'Tipo role no existe: se creará más adelante';
                    END;
                    $$;
                    """
                )
            )
            conn.commit()
    except ProgrammingError:
        # Si hubo algún problema (por ejemplo, el tipo role no existe), lo ignoramos; 
        # más adelante create_db_and_tables() lo creará correctamente.
        pass

    # --------------------------------------------------------------
    # 2. CREAR TABLAS (enum role se crea si no existe)
    # --------------------------------------------------------------
    create_db_and_tables()
    logger.info("Tablas de la base de datos creadas (si no existían).")

    # --------------------------------------------------------------
    # 3. COMPROBAR Y CREAR USUARIO ADMIN POR DEFECTO
    # --------------------------------------------------------------
    with Session(engine) as session:
        statement = select(User).where(User.role == Role.admin)
        admin_exists = session.exec(statement).first()
        if not admin_exists:
            hashed_pwd = get_password_hash(DEFAULT_ADMIN_PASSWORD)
            new_admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                email=DEFAULT_ADMIN_EMAIL,
                full_name=DEFAULT_ADMIN_FULLNAME,
                hashed_password=hashed_pwd,
                role=Role.admin,
            )
            session.add(new_admin)
            session.commit()
            logger.info(
                f"Usuario ADMIN creado: "
                f"username='{DEFAULT_ADMIN_USERNAME}' "
                f"password='{DEFAULT_ADMIN_PASSWORD}'"
            )
        else:
            logger.info("Ya existe al menos un usuario con rol ADMIN. No se crea ninguno nuevo.")


# ------------------ CORS ------------------
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ Inclusión de Routers ------------------
from app.routers import users, auth, orders, products, exports

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(exports.router)

# ------------------ Ruta Raíz ------------------
@app.get("/")
def read_root():
    return {"message": "Bienvenidos a la Tienda Online API"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)