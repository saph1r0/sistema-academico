"""
Comando Django para cargar datos iniciales de prueba
CORREGIDO: Estudiantes inician DESACTIVADOS y correo auto-generado
"""
from django.core.management.base import BaseCommand
from django.db import connection

from dominio.modelo.usuario.estudiante import Estudiante
from repositorio.postgres_repository.estudiantePostgresRepository import EstudiantePostgresRepository


class Command(BaseCommand):
    help = 'Carga datos iniciales de prueba en la base de datos (estudiantes DESACTIVADOS)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Limpia todos los datos antes de cargar',
        )

    def handle(self, *args, **options):
        repo = EstudiantePostgresRepository()
        
        if options['limpiar']:
            self.stdout.write(self.style.WARNING('Limpiando datos existentes...'))
            with connection.cursor() as cursor:
                cursor.execute('TRUNCATE TABLE estudiantes CASCADE;')
                cursor.execute('TRUNCATE TABLE matriculas CASCADE;')
            self.stdout.write(self.style.SUCCESS('✓ Datos limpiados'))
        
        # Datos de estudiantes basados en la imagen del Excel
        # Formato: (codigo, apellidos, nombres)
        estudiantes_datos = [
            ('20233590', 'ABENSUR ROMERO', 'DIEGO DANIEL'),
            ('20232284', 'ALCAZAR MEDINA', 'DIOGO ANDRAÃ‰'),
            ('20230573', 'ALVA CORNEJO', 'JOSE JAVIER'),
            ('20213145', 'CACSIRE SANCHEZ', 'JHOSEP ANGEL'),
            ('20231537', 'CALCINA MUCHICA', 'SERGIO ELISEO'),
            ('20233598', 'CALIZAYA QUISPE', 'JOSE LUIS'),
            ('20222178', 'CAÃÂAPATA VARGAS', 'ALEX ENRIQUE'),
            ('20222145', 'CARDENAS VILLAGOMEZ', 'PIERO ADRIANO'),
            ('20222179', 'CAYMA LMIR', 'JOSE RODRIGO'),
            ('20233582', 'CASTELO CHOQUE', 'JOAQUIN ANDREAÃ‰'),
            ('20221737', 'CHAVEZ MEDINA', 'FERNANDO JESUS'),
            ('20230579', 'COLOMA VIURA', 'RIKI SANTHER'),
        ]
        
        estudiantes = []
        self.stdout.write('\nCreando estudiantes...')
        
        for codigo, apellidos, nombres in estudiantes_datos:
            # NO generamos correo aquí, la entidad lo hace automáticamente
            estudiante = Estudiante(
                codigo=codigo,
                apellidos=apellidos,
                nombres=nombres
                # El correo se genera en __post_init__ de Estudiante
                # El estado por defecto es DESACTIVADO
            )
            estudiantes.append(estudiante)
            
            # Mostrar info del estudiante creado
            self.stdout.write(
                f"  - {codigo}: {estudiante.nombre_completo()} "
                f"→ {estudiante.correo_institucional} [{estudiante.estado}]"
            )
        
        try:
            cantidad = repo.guardar_lista(estudiantes)
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Se cargaron {cantidad} estudiantes correctamente')
            )
            
            # Mostrar resumen por estado
            total_desactivados = repo.contar_por_estado("DESACTIVADO")
            total_activos = repo.contar_por_estado("ACTIVO")
            
            self.stdout.write('\n' + '='*60)
            self.stdout.write('RESUMEN:')
            self.stdout.write(f'  - Total estudiantes DESACTIVADOS: {total_desactivados}')
            self.stdout.write(f'  - Total estudiantes ACTIVOS: {total_activos}')
            self.stdout.write('='*60)
            
            # Nota importante
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠ IMPORTANTE: Todos los estudiantes inician DESACTIVADOS.\n'
                    '  Se activarán cuando ingresen por primera vez al sistema.\n'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n✗ Error al cargar datos: {str(e)}')
            )