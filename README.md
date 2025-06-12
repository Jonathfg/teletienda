# Tienda Online API & Front

Una aplicación para una **tienda online** con:

- **Backend** en FastAPI + SQLModel + PostgreSQL/SQLite + Redis  
- **Frontend** ligero en Streamlit  
- **Productos** consumidos en tiempo real desde DummyJSON  
- **Pedidos** almacenados localmente y enriquecidos con datos externos  
- **Autenticación** JWT (access + refresh + revocación)  
- **Exportación** de pedidos a CSV, Excel y PDF  
- **Docker & Docker Compose** para orquestación

---

## 📂 Estructura del proyecto

```text
.
├── app/
│   ├── main.py            # Arranque de FastAPI, startup events
│   ├── database.py        # Configuración de SQLModel / DB
│   ├── models.py          # Tablas: User, Order, OrderItem
│   ├── schemas.py         # Pydantic schemas
│   ├── auth.py            # Lógica JWT, dependencias
│   ├── utils.py           # Fetch DummyJSON, export CSV/Excel/PDF
│   ├── crud_users.py      # CRUD usuarios
│   ├── crud_orders.py     # CRUD pedidos + enriquecimiento
│   └── routers/           # APIRouters por funcionalidad
│       ├── auth.py
│       ├── users.py
│       ├── products.py
│       ├── orders.py
│       └── exports.py
├── streamlit_app.py       # Frontend en Streamlit
├── Dockerfile             # Imagen de la API
├── docker-compose.yml     # Servicios: api, redis, db
└── README.md              # Esta documentación

-------------------

🚀 Cómo arrancar la aplicación
🖥️ local

# 1. Crea y activa entorno virtual
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.\.venv\Scripts\activate

# 2. Instala dependencias
pip install -r requirements.txt

# 3. Arranca la API
uvicorn app.main:app --reload --port 8000

# 4. Swagger / OpenAPI disponible en:
http://localhost:8000/docs

-------------------

🌐Frontend con Streamlit

# Ejecuta Streamlit
streamlit run streamlit_app.py
