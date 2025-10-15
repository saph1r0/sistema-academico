# Dev1 del Proyecto SISACAD


## 📦 Prerrequisitos

- Python 3.10+
- PostgreSQL 14+
- Poetry

---

### 1. Clonar el repositorio

```bash
git clone https://github.com/saph1r0/sistema-academico.git
cd sistema-academico
```

### 2. Instalar dependencias

```bash
poetry install
poetry shell
```

### 3. Configurar PostgreSQL

```sql
-- Conectarse a PostgreSQL
psql -U postgres

-- Crear base de datos
CREATE DATABASE sisacad_db;
CREATE USER sisacad_user WITH PASSWORD 'sisacad123';
GRANT ALL PRIVILEGES ON DATABASE sisacad_db TO sisacad_user;
```

### 4. Aplicar migraciones

```bash
python manage.py migrate
```

### 5. Cargar datos de prueba

```bash
python manage.py cargar_datos_iniciales --limpiar
```

---

## 🧪 Ejecutar Tests

```bash
# Todos los tests
pytest

# Solo tests de repositorio
pytest tests/repositorio/ -v

---

## 📁 Estructura (Actualizazvion y nuevos archivos)

```
sistema-academico/
├── dominio/
│   └── modelo/
│       ├── usuario/
│       │   ├── estudiante.py          # Entidad de dominio
│       │   └── iEstudianteRepository.py  # Interface (puerto)
│       └── inscripciones/
│           └── matricula.py           # Entidad de dominio
├── repositorio/
│   └── postgres_repository/
│       ├── models.py                  # Modelos Django ORM
│       ├── estudiantePostgresRepository.py  # Implementación
│       └── management/
│           └── commands/
│               └── cargar_datos_iniciales.py
├── tests/
│   └── repositorio/
│       └── test_estudiante_repository.py
└── fixtures/
    └── datos_iniciales.sql
```

---

**La base está lista. ¡A trabajar equipo! 💪**
