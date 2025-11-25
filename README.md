# Sistema Académico UNSA

Sistema de gestión académica desarrollado con Django siguiendo arquitectura DDD (Domain-Driven Design) con sistema completo de permisos por roles.

## 🚀 Instalación Rápida

### 1. Activar entorno virtual

```bash
# Si usas Poetry (recomendado)
poetry shell

# O si usas venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### 2. Configurar base de datos PostgreSQL

Asegúrate de tener PostgreSQL ejecutándose con:

- Base de datos: `modelsistak`
- Usuario: `postgres`
- Contraseña: `131070`
- Host: `localhost`
- Puerto: `5432`

### 3. Ejecutar script de configuración

```bash
python setup_sistema.py
```

### 4. Iniciar servidor

```bash
python manage.py runserver
```

### 5. Acceder al sistema

Abrir: http://127.0.0.1:8000

## 👤 Credenciales de Prueba

| Rol               | Email               | Contraseña    | Descripción                |
| ----------------- | ------------------- | ------------- | -------------------------- |
| **Administrador** | admin@unsa.edu.pe   | admin123      | Acceso completo al sistema |
| **Estudiante**    | sesteba@unsa.edu.pe | 20241234      | Portal estudiantil         |
| **Profesor**      | jperez@unsa.edu.pe  | profesor123   | Portal docente             |
| **Secretario**    | mgarcia@unsa.edu.pe | secretario123 | Portal secretarial         |

## 🎯 Funcionalidades por Rol

### 👤 Administrador

- **Dashboard**: Métricas del sistema, alertas, estadísticas
- **Gestión de usuarios**: Activar/desactivar cuentas, supervisar roles
- **Reportes globales**: Asistencia, notas, estadísticas por curso/docente/alumno
- **Recursos**: Estado de laboratorios, reservas automáticas
- **Configuración**: Parámetros técnicos del sistema

### 🎓 Estudiante

- **Dashboard personal**: Horario, avance de cursos, asistencia   
- **Laboratorios**: Matrícula/desmatrícula en laboratorios
- **Notas**: Consulta de calificaciones
- **Horarios**: Visualización de horario académico

### 👨‍🏫 Profesor

- **Dashboard docente**: Cursos asignados, horarios, asistencia propia
- **Gestión de notas**: Carga mediante Excel, reportes
- **Asistencia**: Registro de estudiantes, reportes
- **Reservas**: Solicitud de laboratorios y aulas
- **Sílabo**: Gestión de contenidos y avance

### 📋 Secretario

- **Dashboard académico**: Resumen del sistema educativo
- **Laboratorios**: Supervisión de inscripciones
- **Reportes académicos**: Generación de reportes consolidados

## 📁 Estructura del Proyecto

```
├── config/                     # Configuración Django
├── dominio/                   # Capa de dominio (DDD)
│   └── modelo/
│       └── admin_sistema/     # Modelos administrativos
├── presentacion/              # Capa de presentación
│   ├── administrador/         # Módulo administrativo
│   ├── estudiante/           # Módulo estudiantil
│   ├── profesor/             # Módulo docente
│   ├── secretario/           # Módulo secretarial
│   ├── login/                # Sistema de autenticación
│   └── templates/            # Templates por rol
├── repositorio/              # Capa de repositorio
│   └── postgres_repository/  # Modelos PostgreSQL
├── servicios/                # Capa de servicios
└── tests/                    # Pruebas unitarias
```

## 🛠️ Desarrollo

### Ejecutar Tests

```bash
python manage.py test
```

### Crear Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### Cargar Datos de Prueba

```bash
python create_test_users.py
```

## 📊 Sistema de Asignación Automática de Cursos

El sistema incluye una funcionalidad avanzada para asignar estudiantes a cursos automáticamente desde archivos Excel.

### 🚀 Uso Rápido

```bash
# Asignación básica (usa directorio EXELS por defecto)
python manage.py assign_courses

# Con directorio específico
python manage.py assign_courses --directory /path/to/excel

# Con logging detallado
python manage.py assign_courses --verbose --log-level DEBUG

# Ejecutar demostración completa
python demo_assign_courses.py
```

### 📁 Estructura de Archivos Requerida

```
EXELS/
├── bdtotall.xlsx              # Archivo principal con todos los estudiantes
├── alumnos_matematica.xlsx    # Estudiantes del curso de matemática
├── alumnos_fisica.xlsx        # Estudiantes del curso de física
└── alumnos_*.xlsx            # Más archivos de cursos
```

### ✨ Características

- **Lectura automática**: Procesa archivos Excel automáticamente
- **Extracción inteligente**: Extrae nombres de cursos desde nombres de archivos
- **Creación automática**: Crea cursos en base de datos si no existen
- **Prevención de duplicados**: Evita asignaciones duplicadas
- **Reportes detallados**: Genera reportes completos del proceso
- **Manejo de errores**: Continúa procesando aunque algunos archivos fallen
- **Verificación de resultados**: Incluye verificación en base de datos

### 📋 Parámetros del Comando

| Parámetro     | Descripción                   | Valor por defecto |
| ------------- | ----------------------------- | ----------------- |
| `--directory` | Directorio con archivos Excel | `EXELS`           |
| `--verbose`   | Mostrar información detallada | `False`           |
| `--log-level` | Nivel de logging              | `INFO`            |

### 🎯 Casos de Uso

- **Matrícula masiva**: Asignar cientos de estudiantes automáticamente
- **Actualización de cursos**: Procesar nuevas listas de estudiantes
- **Migración de datos**: Importar datos desde sistemas externos
- **Auditoría**: Verificar asignaciones existentes

## 🔧 Tecnologías

- **Backend**: Django 5.2.7, Python 3.12
- **Base de datos**: PostgreSQL
- **Frontend**: Tailwind CSS, HTML5
- **Autenticación**: Django Auth con roles personalizados
- **Arquitectura**: Domain-Driven Design (DDD)
- **Procesamiento Excel**: openpyxl, pandas


-----

# 📚 Guía 

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
