# Design Document

## Overview

El submódulo administrador será implementado como una aplicación Django dentro de la capa de presentación, siguiendo la arquitectura DDD existente. El panel proporcionará una interfaz web responsive construida con Tailwind CSS que permite al administrador supervisar, auditar y configurar el sistema académico.

La solución se integrará con la estructura existente de Django, utilizando el template base_admin.html ya definido y extendiendo la funcionalidad con nuevas vistas, controladores y templates específicos para el rol de administrador.

## Architecture

### Architectural Pattern

- **Domain-Driven Design (DDD)**: Siguiendo la estructura existente con capas de dominio, servicios y presentación
- **Model-View-Controller (MVC)**: Implementado a través del patrón Django MVT (Model-View-Template)
- **Repository Pattern**: Utilizando los repositorios existentes para acceso a datos

### Layer Structure

```
presentacion/
├── administrador/                    # Nuevo submódulo
│   ├── __init__.py
│   ├── views.py                     # Controladores/Vistas
│   ├── urls.py                      # Rutas específicas del admin
│   ├── forms.py                     # Formularios de configuración
│   └── templates/administrador/     # Templates específicos
│       ├── dashboard.html
│       ├── usuarios/
│       ├── reportes/
│       ├── recursos/
│       └── configuracion/
├── templates/
│   └── base_admin.html             # Template base existente (actualizado)
└── static/administrador/           # Assets específicos
    ├── css/
    ├── js/
    └── images/
```

### Integration Points

- **Authentication**: Django's built-in auth system con roles personalizados
- **Database**: PostgreSQL existente a través de repositorios DDD
- **Services**: Integración con servicios existentes (ServicioUsuario, ServicioReportes, etc.)
- **Templates**: Extensión del base_admin.html existente

## Components and Interfaces

### 1. AdminDashboardView

**Responsabilidad**: Controlador principal del dashboard administrativo

```python
class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'administrador/dashboard.html'

    def test_func(self):
        return self.request.user.rol == 'admin'

    def get_context_data(self, **kwargs):
        # Métricas del sistema, alertas, estadísticas
```

**Interfaces**:

- `ServicioUsuario`: Para obtener estadísticas de usuarios
- `ServicioReportes`: Para métricas globales
- `ServicioReservas`: Para estado de laboratorios

### 2. AdminUsuariosView

**Responsabilidad**: Gestión y visualización de usuarios del sistema

```python
class AdminUsuariosView(AdminRequiredMixin, ListView):
    template_name = 'administrador/usuarios/lista.html'
    paginate_by = 20

    def get_queryset(self):
        # Filtrado por rol, estado, búsqueda

    def post(self, request, *args, **kwargs):
        # Activar/desactivar usuarios
```

### 3. AdminReportesView

**Responsabilidad**: Generación y descarga de reportes globales

```python
class AdminReportesView(AdminRequiredMixin, TemplateView):
    template_name = 'administrador/reportes/index.html'

    def post(self, request, *args, **kwargs):
        # Generar reportes PDF/Excel
```

### 4. AdminRecursosView

**Responsabilidad**: Consulta de laboratorios y reservas

```python
class AdminRecursosView(AdminRequiredMixin, TemplateView):
    template_name = 'administrador/recursos/index.html'

    def get_context_data(self, **kwargs):
        # Estado de laboratorios, reservas automáticas
```

### 5. AdminConfiguracionView

**Responsabilidad**: Configuración de parámetros del sistema

```python
class AdminConfiguracionView(AdminRequiredMixin, FormView):
    template_name = 'administrador/configuracion/index.html'
    form_class = ConfiguracionSistemaForm

    def form_valid(self, form):
        # Guardar configuración con validación
```

### 6. AdminRequiredMixin

**Responsabilidad**: Mixin para verificar permisos de administrador

```python
class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'rol') and self.request.user.rol == 'admin'

    def handle_no_permission(self):
        return redirect('login')
```

## Data Models

### Existing Models (Extended)

```python
# dominio/modelo/usuario/usuario.py (existente)
class Usuario:
    id: int
    correo_institucional: str
    nombre: str
    apellido: str
    rol: str  # 'admin', 'docente', 'estudiante', 'secretaria'
    activo: bool
    ultimo_acceso: datetime
```

### New Configuration Model

```python
# dominio/modelo/admin_sistema/configuracion_sistema.py
class ConfiguracionSistema:
    def __init__(self):
        self.id = None
        self.capacidad_maxima_laboratorio = 30
        self.tiempo_sesion_minutos = 120
        self.backup_automatico = True
        self.frecuencia_backup_horas = 24
        self.alertas_activas = True
        self.fecha_modificacion = None
        self.usuario_modificacion = None
```

### Dashboard Metrics Model

```python
# dominio/modelo/admin_sistema/metricas_sistema.py
class MetricasSistema:
    def __init__(self):
        self.total_usuarios_activos = 0
        self.total_cursos_activos = 0
        self.total_laboratorios = 0
        self.promedio_asistencia_global = 0.0
        self.promedio_notas_global = 0.0
        self.alertas_pendientes = []
        self.fecha_calculo = None
```

## Error Handling

### Exception Hierarchy

```python
class AdminPanelException(Exception):
    """Excepción base para el panel administrativo"""
    pass

class PermisosDenegadosException(AdminPanelException):
    """Usuario sin permisos de administrador"""
    pass

class ConfiguracionInvalidaException(AdminPanelException):
    """Parámetros de configuración inválidos"""
    pass

class ReporteGeneracionException(AdminPanelException):
    """Error en la generación de reportes"""
    pass
```

### Error Handling Strategy

1. **Authentication Errors**: Redirect to login with message
2. **Permission Errors**: Show 403 page with explanation
3. **Configuration Errors**: Form validation with specific field errors
4. **Report Generation Errors**: Toast notifications with retry option
5. **System Errors**: Graceful degradation with fallback data

### Logging Strategy

```python
import logging

logger = logging.getLogger('admin_panel')

# Configuración en settings.py
LOGGING = {
    'loggers': {
        'admin_panel': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

## Testing Strategy

### Unit Tests

```python
# tests/test_admin_views.py
class TestAdminDashboardView(TestCase):
    def setUp(self):
        self.admin_user = create_admin_user()
        self.client.force_login(self.admin_user)

    def test_dashboard_loads_metrics(self):
        # Test que el dashboard carga métricas correctamente

    def test_non_admin_access_denied(self):
        # Test que usuarios no admin son rechazados
```

### Integration Tests

```python
# tests/test_admin_integration.py
class TestAdminIntegration(TestCase):
    def test_user_activation_flow(self):
        # Test completo de activación de usuario

    def test_report_generation_flow(self):
        # Test completo de generación de reportes
```

### Frontend Tests

```javascript
// static/administrador/js/tests/dashboard.test.js
describe("Admin Dashboard", () => {
  test("should load metrics on page load", () => {
    // Test de carga de métricas via AJAX
  });

  test("should handle responsive sidebar toggle", () => {
    // Test de funcionalidad responsive
  });
});
```

### Performance Tests

```python
# tests/test_admin_performance.py
class TestAdminPerformance(TestCase):
    def test_dashboard_load_time(self):
        # Test que el dashboard carga en menos de 2 segundos

    def test_user_list_pagination(self):
        # Test de paginación con grandes volúmenes de datos
```

## UI/UX Design Specifications

### Design System

- **Typography**: Inter font family
- **Color Palette**:
  - Primary: #1E3A8A (blue-800)
  - Secondary: #3B82F6 (blue-500)
  - Background: #F9FAFB (gray-50)
  - Text: #1F2937 (gray-800)
- **Spacing**: Tailwind's spacing scale (4, 6, 8, 12, 16, 24px)
- **Border Radius**: Rounded corners (4px, 8px)

### Responsive Breakpoints

```css
/* Mobile First Approach */
sm: 640px   /* Tablet portrait */
md: 768px   /* Tablet landscape */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large desktop */
```

### Component Library

```html
<!-- Dashboard Card Component -->
<div class="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
  <div class="flex items-center justify-between">
    <div>
      <p class="text-sm font-medium text-gray-600">{{ title }}</p>
      <p class="text-2xl font-bold text-gray-900">{{ value }}</p>
    </div>
    <div class="p-3 bg-blue-50 rounded-full">
      <i data-lucide="{{ icon }}" class="w-6 h-6 text-blue-600"></i>
    </div>
  </div>
</div>
```

### Accessibility Features

- **ARIA Labels**: All interactive elements
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader**: Semantic HTML structure
- **Color Contrast**: WCAG AA compliance
- **Focus Indicators**: Visible focus states

## Security Considerations

### Authentication & Authorization

```python
# Decorador personalizado para vistas admin
@admin_required
def admin_view(request):
    # Solo usuarios con rol 'admin' pueden acceder
```

### CSRF Protection

- Django's built-in CSRF middleware
- CSRF tokens in all forms
- AJAX requests include CSRF headers

### Input Validation

```python
# forms.py
class ConfiguracionSistemaForm(forms.Form):
    capacidad_maxima = forms.IntegerField(
        min_value=1,
        max_value=100,
        validators=[validate_positive_integer]
    )
```

### Audit Trail

```python
# Registro de acciones administrativas
class AuditoriaAdmin:
    def registrar_accion(self, usuario, accion, detalles):
        # Log de todas las acciones administrativas
```

## Performance Optimizations

### Database Optimization

- **Query Optimization**: Select_related y prefetch_related
- **Pagination**: Limit queries to 20 items per page
- **Caching**: Redis cache for dashboard metrics
- **Indexing**: Database indexes on frequently queried fields

### Frontend Optimization

- **Lazy Loading**: Images and non-critical components
- **Code Splitting**: Separate JS bundles per section
- **Compression**: Gzip compression for static files
- **CDN**: Tailwind CSS from CDN

### Caching Strategy

```python
# Cache de métricas del dashboard (5 minutos)
@cache_page(300)
def dashboard_metrics_api(request):
    return JsonResponse(get_dashboard_metrics())
```

## Deployment Considerations

### Static Files

```python
# settings.py
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'presentacion' / 'static',
    BASE_DIR / 'presentacion' / 'administrador' / 'static',
]
```

### Environment Variables

```python
# Configuración sensible en variables de entorno
ADMIN_SESSION_TIMEOUT = os.getenv('ADMIN_SESSION_TIMEOUT', 3600)
MAX_REPORT_SIZE = os.getenv('MAX_REPORT_SIZE', 10485760)  # 10MB
```

### Monitoring

- **Health Checks**: Endpoint para verificar estado del sistema
- **Metrics Collection**: Prometheus/Grafana integration
- **Error Tracking**: Sentry integration for error monitoring
