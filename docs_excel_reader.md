# ExcelReader Service Documentation

## Overview

El servicio `ExcelReader` es responsable de leer y procesar archivos Excel para el sistema de asignación automática de cursos. Maneja dos tipos principales de archivos:

1. **bdtotall.xlsx**: Archivo principal con información completa de todos los estudiantes
2. **alumnos\_\*.xlsx**: Archivos específicos de cursos que contienen códigos de estudiantes

## Features

### ✅ Validación Robusta de Archivos

- Verificación de existencia de archivos
- Validación de formato (solo .xlsx y .xls)
- Detección de archivos vacíos o corruptos
- Manejo de errores de acceso a archivos

### ✅ Lectura de Datos de Estudiantes

- Extracción de información completa desde bdtotall.xlsx
- Mapeo de columnas específicas (CUI, nombres, apellidos, email)
- Normalización de datos (códigos de estudiante, emails)
- Detección y reporte de duplicados

### ✅ Lectura de Archivos de Cursos

- Búsqueda automática de códigos de estudiante en archivos alumnos\_\*.xlsx
- Filtrado inteligente de códigos válidos (8 dígitos)
- Manejo de diferentes formatos de datos

### ✅ Manejo de Errores y Advertencias

- Sistema de logging detallado
- Reporte de advertencias sin detener el procesamiento
- Manejo graceful de errores de celdas individuales

## API Reference

### Classes

#### `StudentData`

```python
@dataclass
class StudentData:
    email: str
    first_name: str
    last_name: str
    student_code: str
    full_name: str  # Auto-generado
```

#### `ExcelReadResult`

```python
@dataclass
class ExcelReadResult:
    success: bool
    data: Optional[Dict] = None
    error_message: str = ""
    warnings: List[str] = None
```

#### `ExcelReader`

##### Methods

**`read_students_file(file_path: str) -> ExcelReadResult`**

- Lee el archivo bdtotall.xlsx
- Retorna diccionario {student_code: StudentData}
- Estructura esperada del archivo:
  - Fila 2: Encabezados
  - Columna B (2): CUI (código de estudiante)
  - Columna D (4): Apellido paterno
  - Columna E (5): Apellido materno
  - Columna F (6): Nombres
  - Columna G (7): Correo electrónico

**`read_course_file(file_path: str) -> ExcelReadResult`**

- Lee archivos alumnos\_\*.xlsx
- Retorna lista de códigos de estudiantes
- Busca códigos de 8 dígitos en todo el archivo

**`get_file_info(file_path: str) -> Dict`**

- Obtiene información básica del archivo Excel
- Retorna metadatos como hojas, dimensiones, etc.

## Usage Examples

### Lectura de Archivo Principal

```python
from servicios.servicioExcelReader import ExcelReader

reader = ExcelReader()
result = reader.read_students_file("EXELS/bdtotall.xlsx")

if result.success:
    students = result.data
    print(f"Estudiantes cargados: {len(students)}")

    for code, student in students.items():
        print(f"{code}: {student.full_name} ({student.email})")

    if result.warnings:
        print(f"Advertencias: {len(result.warnings)}")
else:
    print(f"Error: {result.error_message}")
```

### Lectura de Archivo de Curso

```python
result = reader.read_course_file("EXELS/alumnos_mac(1).xlsx")

if result.success:
    student_codes = result.data
    print(f"Códigos encontrados: {len(student_codes)}")
    print(f"Primeros códigos: {student_codes[:5]}")
else:
    print(f"Error: {result.error_message}")
```

### Validación de Archivos

```python
validation = reader._validate_file("path/to/file.xlsx")
if validation.success:
    print("Archivo válido")
else:
    print(f"Error de validación: {validation.error_message}")
```

## File Structure Requirements

### bdtotall.xlsx

```
Fila 1: [Título o vacío]
Fila 2: [ID, CUI, INICIO, APELLIDO PATERNO, APELLIDO MATERNO, NOMBRES, CORREO, ...]
Fila 3+: [Datos de estudiantes]
```

### alumnos\_\*.xlsx

- Puede tener cualquier estructura
- Debe contener códigos de estudiante de 8 dígitos
- Los códigos pueden estar en cualquier posición del archivo

## Error Handling

### Tipos de Errores Manejados

1. **Archivo no encontrado**: Retorna error, no continúa
2. **Archivo corrupto**: Retorna error, no continúa
3. **Datos faltantes**: Genera advertencia, continúa procesamiento
4. **Códigos duplicados**: Genera advertencia, omite duplicado
5. **Celdas con errores**: Ignora celda, continúa

### Logging

- **INFO**: Progreso normal del procesamiento
- **WARNING**: Datos faltantes, duplicados, archivos omitidos
- **ERROR**: Errores críticos que impiden el procesamiento

## Testing

El servicio incluye tests unitarios completos:

```bash
python -m unittest tests.test_excel_reader -v
```

### Test Coverage

- ✅ Creación de objetos de datos
- ✅ Validación de archivos (existentes, inexistentes, corruptos)
- ✅ Lectura exitosa de archivos
- ✅ Manejo de datos faltantes
- ✅ Obtención de valores de celdas
- ✅ Información de archivos

## Performance Considerations

- **Memoria**: Carga archivos completos en memoria
- **Velocidad**: Optimizado para archivos de hasta ~1000 estudiantes
- **Robustez**: Manejo graceful de errores sin detener procesamiento

## Dependencies

- `openpyxl`: Lectura de archivos Excel
- `logging`: Sistema de logging
- `dataclasses`: Estructuras de datos
- `typing`: Type hints

## Integration Notes

Este servicio está diseñado para integrarse con:

- `CourseAssignmentService`: Servicio principal de asignación
- `CourseMapper`: Mapeo de nombres de cursos
- `AssignmentProcessor`: Procesamiento de asignaciones

## Limitations

1. Solo soporta formatos .xlsx y .xls
2. Estructura fija esperada para bdtotall.xlsx
3. Códigos de estudiante deben ser exactamente 8 dígitos
4. No maneja archivos extremadamente grandes (>10MB)

## Future Enhancements

- [ ] Soporte para archivos CSV
- [ ] Configuración flexible de columnas
- [ ] Procesamiento streaming para archivos grandes
- [ ] Cache de archivos procesados
- [ ] Validación de formato de emails
