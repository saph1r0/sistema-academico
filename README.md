# Sistema de Gestión Académica - UNSA

Sistema integral de gestión académica para la Escuela Profesional de Ciencia de la Computación de la Universidad Nacional de San Agustín de Arequipa.

Dashboard Profesor
<img width="1364" height="629" alt="image" src="https://github.com/user-attachments/assets/9f5ad634-76ba-4a10-8ac4-40ebecb84465" />


## 📋 Descripción

Sistema web completo que digitaliza y automatiza los procesos académicos universitarios, incluyendo gestión de matrículas, notas, asistencia, sílabos y acreditación de exámenes. Implementado con Django siguiendo arquitectura DDD (Domain-Driven Design).

## 🎯 Características Principales

### 👨‍🏫 Módulo Docente

- **Dashboard Interactivo**: Vista general de cursos asignados, estudiantes y estadísticas
- **Gestión de Notas**: Subida masiva mediante Excel, registro manual, cálculo automático de estadísticas
- **Registro de Asistencia**: Sistema simplificado (Presente/Falta) con registro automático del docente
- **Horarios Visuales**: Calendario interactivo con clases y laboratorios

![Mi Horario](image_4.png)

- **Sílabos Inteligentes**: Subida de temas con cálculo automático de avance semanal
  <img width="1366" height="569" alt="image" src="https://github.com/user-attachments/assets/8366ec34-ef99-4de5-ab80-45690785e72f" />
  <img width="1356" height="687" alt="image" src="https://github.com/user-attachments/assets/8aa4c274-c512-4f4f-93b1-3f7cb3649dfc" />


- **Acreditación de Exámenes**: Sistema para subir 2 archivos por parcial (mejor y peor nota)

![Acreditación Exámenes]
<img width="1362" height="678" alt="image" src="https://github.com/user-attachments/assets/308b519d-6634-4bf8-ba16-b824c8b933c5" />
<img width="1361" height="591" alt="image" src="https://github.com/user-attachments/assets/c2bc6410-4322-4b28-aded-47310c0930c4" />
<img width="1030" height="584" alt="image" src="https://github.com/user-attachments/assets/2b9e6297-6560-4465-84f6-ed284bd417cc" />


- **Reportes Exportables**: Generación de reportes en PDF y Excel

![Generación Reportes]

<img width="757" height="801" alt="image" src="https://github.com/user-attachments/assets/d1182c54-d3e1-4b1d-a4f7-f17d0829b51b" />
<img width="710" height="847" alt="image" src="https://github.com/user-attachments/assets/ed8c727b-adac-42e9-91bc-1c5d535e88a2" />
<img width="1600" height="869" alt="image" src="https://github.com/user-attachments/assets/6addb203-fde0-4287-ba9b-322f09821b6f" />

- **Gestion de notas por fases **: Las notas se suben deacuerdo a als fases correspondientes en un formato excel determinado y se generan estadisticas en tiempo real 
  <img width="1363" height="614" alt="image" src="https://github.com/user-attachments/assets/82496cb7-aace-49ff-889e-79471f8ca7a5" />
- **Toma de asistencia dinamica**: El docente tomara asistencia a los estudiantes
  <img width="1364" height="606" alt="image" src="https://github.com/user-attachments/assets/2fb72db3-7a93-4b05-818b-b8b89d5e12b4" />


### 👨‍🎓 Módulo Estudiante

![Portal Estudiante](image_10.png)

- **Consulta de Notas**: Visualización de calificaciones por fase y promedio acumulado
  <img width="1360" height="673" alt="image" src="https://github.com/user-attachments/assets/0998c303-c47d-4305-a745-756f691c5783" />

- **Mis Asistencias**: Dashboard con porcentaje de asistencia por curso
  <img width="1365" height="583" alt="image" src="https://github.com/user-attachments/assets/1be671c0-3d98-4611-b585-37ff49309902" />


![Mis Asistencias](image_11.png)

- **Avance de Sílabo**: Seguimiento del progreso del curso
  <img width="1352" height="583" alt="image" src="https://github.com/user-attachments/assets/f06d7057-fc20-4239-846c-e6ab0d0ad75b" />

- **Matrícula de Laboratorios**: Gestión autónoma dentro del período habilitado

![Laboratorios](image_9.png)

- **Horario Personalizado**: Vista calendario con todas las clases matriculadas
- **Constancia de Matrícula**: Descarga en PDF para trámites

  

### 👩‍💼 Módulo Secretaría

![Portal Secretaría](image_6.png)

- **Gestión de Usuarios**: Activación/desactivación, reset de contraseñas
- **Carga Masiva de Matrículas**: Importación desde archivos Excel de SISACAD
- **Supervisión de Acreditaciones**: Visualización y descarga de todos los exámenes acreditados
- **Reportes Globales**: Estadísticas de todos los cursos, profesores y estudiantes
- **Gestión de Laboratorios**: Asignación de capacidades y profesores
- **Monitoreo de Asistencia**: Control de asistencia docente automática por IP

## 🏗️ Arquitectura

### Stack Tecnológico

- **Backend**: Django 5.0+ con Python 3.11+
- **Base de Datos**: PostgreSQL 15+
- **Frontend**: HTML5, Tailwind CSS 3.0, JavaScript (Vanilla)
- **Gráficos**: Chart.js, Lucide Icons
- **Procesamiento**: Pandas, OpenPyXL (Excel)
- **PDFs**: ReportLab, WeasyPrint

### Estructura del Proyecto

```
proyecto/
├── repositorio/
│   └── postgres_repository/
│       └── models.py              # Modelos ORM
├── servicios/
│   ├── servicioNotas.py           # Lógica de notas
│   ├── servicioAsistencia.py      # Lógica de asistencia
│   ├── servicioSilabo.py          # Gestión de sílabos
│   └── servicioAcreditacionExamenes.py  # Acreditación
├── profesor/
│   ├── views.py                   # Vistas del módulo
│   ├── forms.py                   # Formularios
│   ├── urls.py                    # Rutas
│   └── templates/                 # Templates
├── estudiante/
│   ├── views.py
│   ├── urls.py
│   └── templates/
├── secretario/
│   ├── views.py
│   ├── urls.py
│   └── templates/
└── media/
    └── exam_accreditations/       # Archivos de exámenes
```

## 📊 Módulos Implementados

### 1. Gestión de Usuarios (RF01-RF07)
- ✅ Autenticación por correo institucional
- ✅ Roles: Estudiante, Docente, Secretaría, Admin
- ✅ Permisos diferenciados por rol

### 2. Matrícula (RF08-RF19)
- ✅ Carga masiva desde Excel
- ✅ Gestión de laboratorios con capacidad
- ✅ Validación de horarios sin cruces
- ✅ Período de matrícula configurable
- ✅ Visualización de horarios gráfica
- ✅ Constancia de matrícula en PDF

### 3. Asistencia (RF20-RF23)
- ✅ Registro docente (Presente/Falta)
- ✅ Registro automático de asistencia del profesor
- ✅ Cálculo de porcentajes
- ✅ Reportes por curso

### 4. Gestión de Notas (RF24-RF28)
- ✅ Subida manual y masiva (Excel)
- ✅ Cálculo automático de estadísticas
- ✅ Visualización con gráficos
- ✅ Consulta para estudiantes
- ✅ Acreditación de 3 parciales (2 archivos c/u)

### 5. Sílabos (RF29-RF32)
- ✅ Subida de temas por unidades
- ✅ Cálculo automático de avance semanal
- ✅ Pronóstico de cumplimiento
- ✅ Visualización para estudiantes

### 6. Reportes (RF33-RF37)
- ✅ Reportes por docente
- ✅ Reportes globales para secretaría
- ✅ Exportación en PDF y Excel
- ✅ Estadísticas visuales con gráficos

### 7. Administración (RF38-RF41)
- ✅ Configuración de períodos académicos
- ✅ Fechas límite configurables
- ✅ Supervisión global

### 8. Reservas (RF8.1-RF8.5)
- ✅ Consulta de disponibilidad
- ✅ Gestión de solicitudes
- ✅ Prevención de conflictos
- ✅ Notificaciones de resultado

## 🚀 Instalación

### Requisitos Previos

```bash
Python 3.11+
PostgreSQL 15+
pip
virtualenv (recomendado)
```

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <url-repositorio>
cd sistema-academico
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar base de datos**

Crear base de datos PostgreSQL:
```sql
CREATE DATABASE sistema_academico;
CREATE USER admin WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE sistema_academico TO admin;
```

Configurar en `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sistema_academico',
        'USER': 'admin',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

5. **Aplicar migraciones**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Crear superusuario**
```bash
python manage.py createsuperuser
```

7. **Configurar archivos media**
```bash
mkdir -p media/exam_accreditations
chmod 755 media/
```

8. **Ejecutar servidor**
```bash
python manage.py runserver
```

Acceder a: `http://127.0.0.1:8000`

## 📝 Uso del Sistema

### Roles y Accesos

#### Profesor
- **URL**: `/profesor/`
- **Funciones**:
  - Subir notas por Excel o manual
  - Registrar asistencia de estudiantes
  - Gestionar sílabo y avance
  - Acreditar exámenes (2 archivos por parcial)
  - Ver reportes de sus cursos
  - Consultar horario
  - Reservar ambientes

#### Estudiante
- **URL**: `/estudiante/`
- **Funciones**:
  - Consultar notas y promedio
  - Ver asistencia por curso
  - Matricularse en laboratorios
  - Consultar horario
  - Ver avance de sílabo

#### Secretaría
- **URL**: `/secretario/`
- **Funciones**:
  - Cargar matrículas masivas
  - Gestionar usuarios
  - Ver acreditaciones de exámenes
  - Generar reportes globales
  - Supervisar asistencia docente
  - Gestionar laboratorios

### Acreditación de Exámenes

El sistema requiere que cada docente suba **2 archivos por parcial** (mejor y peor nota):

- **Parcial 1**: 2 archivos (mejor nota + peor nota)
- **Parcial 2**: 2 archivos (mejor nota + peor nota)
- **Parcial 3**: 2 archivos (mejor nota + peor nota)
- **Total**: 6 archivos por curso

**Formatos aceptados**: PDF o PNG (máx 10MB)

Las estadísticas (nota máxima, mínima, promedio) se calculan **automáticamente** desde las notas registradas en `PhaseGrade`.

## 🔒 Seguridad

- ✅ Autenticación por correo institucional
- ✅ Permisos por rol (RBAC)
- ✅ Validación de archivos (tipo, tamaño)
- ✅ CSRF protection
- ✅ SQL injection protection (ORM)
- ✅ Validación de IP para asistencia docente

## 📊 Base de Datos

### Modelos Principales

- **User**: Usuarios del sistema (estudiantes, docentes, secretaría)
- **Student**: Información de estudiantes
- **Teacher**: Información de docentes
- **Course**: Cursos académicos
- **CourseGroup**: Grupos/secciones de cursos
- **Laboratory**: Laboratorios
- **Enrollment**: Matrículas
- **PhaseGrade**: Notas por fase (Primera, Segunda, Tercera)
- **SimpleAttendanceRecord**: Asistencia de estudiantes
- **TeacherAttendance**: Asistencia automática de docentes
- **ExamAccreditation**: Acreditación de exámenes
- **Syllabus**: Sílabos de cursos
