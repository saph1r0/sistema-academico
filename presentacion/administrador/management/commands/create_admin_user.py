"""
Comando de gestión para crear usuarios administradores
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea un usuario administrador para el sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email del usuario administrador'
        )
        parser.add_argument(
            '--nombre',
            type=str,
            required=True,
            help='Nombre del usuario administrador'
        )
        parser.add_argument(
            '--apellido',
            type=str,
            required=True,
            help='Apellido del usuario administrador'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Contraseña del usuario (se solicitará si no se proporciona)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la creación incluso si el usuario ya existe'
        )

    def handle(self, *args, **options):
        email = options['email']
        nombre = options['nombre']
        apellido = options['apellido']
        password = options['password']
        force = options['force']

        # Verificar si el usuario ya existe
        if User.objects.filter(email=email).exists():
            if not force:
                raise CommandError(f'El usuario con email {email} ya existe. Use --force para sobrescribir.')
            else:
                # Eliminar usuario existente
                User.objects.filter(email=email).delete()
                self.stdout.write(
                    self.style.WARNING(f'Usuario existente {email} eliminado.')
                )

        # Solicitar contraseña si no se proporcionó
        if not password:
            import getpass
            password = getpass.getpass('Contraseña: ')
            password_confirm = getpass.getpass('Confirmar contraseña: ')
            
            if password != password_confirm:
                raise CommandError('Las contraseñas no coinciden.')

        try:
            # Crear usuario administrador
            user = User.objects.create_user(
                email=email,
                password=password,
                nombre=nombre,
                apellido=apellido,
                rol='admin'
            )
            
            # Asegurar que esté activo
            user.activar_usuario()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Usuario administrador creado exitosamente: {email}'
                )
            )
            
            # Mostrar información del usuario
            self.stdout.write(f'Nombre: {user.nombre} {user.apellido}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Rol: {user.get_rol_display()}')
            self.stdout.write(f'Activo: {user.activo}')
            
        except IntegrityError as e:
            raise CommandError(f'Error creando usuario: {e}')
        except Exception as e:
            raise CommandError(f'Error inesperado: {e}')