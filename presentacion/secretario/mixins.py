from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from presentacion.permisos import SecretaryRequiredMixin as BaseSecretaryRequiredMixin


class SecretariaOrAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        print("DEBUG ROLE:", user.role)
        print("DEBUG is_admin:", user.is_admin())
        print("DEBUG is_secretaria:", user.is_secretaria())
        return user.is_authenticated


class SecretarioRequiredMixin(BaseSecretaryRequiredMixin):
    pass
