

-----

# 📚 Guía de Instalación y Arranque Rápido (`feature/erika3`)

## 1\. 📂 Clonación del Proyecto

```bash
git clone -b feature/erika3 https://github.com/saph1r0/sistema-academico.git
cd sistema-academico
```

-----

## 2\. ⚙️ Configuración de PostgreSQL y Entorno

### 2.1 Configuración de la Base de Datos

```bash
sudo -u postgres psql

# Dentro de psql, ejecute estos comandos:
CREATE DATABASE sisacad_db;
ALTER USER postgres WITH PASSWORD '123456';
\q
```

### 2.2 Instalación de Dependencias

```bash
# Instalación de dependencias Python (Poetry)
poetry install
source $(poetry env info --path)/bin/activate

# Instalación de herramientas de sistema (OCR y PDF)
sudo apt install tesseract-ocr poppler-utils
```

-----

## 3\. 💾 Migraciones y Creación de Usuarios

### 3.1 Aplicación de Migraciones

```bash
# Crea la carpeta 'logs' para evitar FileNotFoundError
mkdir logs

# Generar y Aplicar migraciones
python manage.py makemigrations
python manage.py migrate
```

### 3.2 Creación de Usuarios Iniciales

Cree las cuentas Admin y Secretaria manualmente en el shell de Django:

```bash
python manage.py shell
```

*Dentro del shell, pegue el siguiente script:*

```python
from repositorio.postgres_repository.models import User
from django.contrib.auth.hashers import make_password

# Crear Administrador
User.objects.create(institutional_email="admin@unsa.edu.pe", first_name="Admin", last_name="Sistema", role="admin", password=make_password("admin123"), is_active=True, is_superuser=True, is_staff=True)

# Crear Secretaria
User.objects.create(institutional_email="secretary@unsa.edu.pe", first_name="Secretaria", last_name="Sistema", role="secretary", password=make_password("secretary123"), is_active=True)

exit()
```

-----

## 4\. 🚀 Arranque y Prueba de Carga

### 4.1 Iniciar el Servidor

```bash
python manage.py runserver
```

### 4.2 Cargar los Documentos desde la Interfaz Web

Una vez que el servidor esté corriendo ([http://127.0.0.1:8000/](http://127.0.0.1:8000/)):

1.  Inicie sesión como **Secretaria**

      * **Correo:** `secretary@unsa.edu.pe`
      * **Contraseña:** `secretary123`

2.  En la página de carga de documentos, suba los archivos en este **orden obligatorio** :

      * **1°:** `docentes_450_2025.pdf` (Crea Cursos, Profesores y Período Académico)
      * **2°:** `HORARIOS-AULAS.pdf` (Asigna Horarios y Aulas a los Cursos)
      * **3°:** `alumnos_450_1703240_B_A (1).xlsx` (Crea Estudiantes y sus Matrículas)
