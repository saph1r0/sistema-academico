
## 🧱 1. Crear la base de datos en PostgreSQL
```bash
sudo -u postgres psql
CREATE DATABASE modelsistak;
\q
```

---

## 🧩 2. Instalar dependencias del proyecto
```bash
poetry install
source $(poetry env info --path)/bin/activate
```

---

## 📂 3. Crear carpeta para logs
```bash
mkdir logs
```

---

## 📦 4. Instalar dependencias adicionales
```bash
pip install xlrd --break-system-packages
pip install django
pip install PyPDF2
pip install pdfplumber
pip install pdf2image
pip install pytesseract
pip install pillow
```

---

## ⚙️ 5. Instalar herramientas del sistema
```bash
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-spa
sudo apt install poppler-utils
```

---

## 🗃️ 6. Aplicar migraciones
```bash
python manage.py migrate
```

---

## 👤 7. Crear usuario secretario
Ejecuta el shell interactivo de Django:
```bash
python manage.py shell
```

Dentro del shell, ejecuta lo siguiente:
```python
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

User.objects.create(
    institutional_email="secretary@unsa.edu.pe",
    first_name="Secretaria",
    last_name="Sistema",
    role="secretary",
    password=make_password("secretary123"),
    is_active=True
)
exit()
```

---

## 🌐 8. Ejecutar el servidor
```bash
python manage.py runserver
```

Abre el navegador y entra a:  
👉 [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 📑 9. Cargar los documentos desde la interfaz web
Una vez que el servidor esté corriendo:

1. Inicia sesión como **Secretaria**  
   - **Correo:** `secretary@unsa.edu.pe`  
   - **Contraseña:** `secretary123`

2. En la página de carga de documentos, sube los archivos en este orden:
   - `docentes_450_2025.pdf`
   - `HORARIOS-AULAS.pdf`
   - `alumnos_450_1703240_B_A (1).xlsx`
