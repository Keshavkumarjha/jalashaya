from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "jalashaya.accounts"
    verbose_name = _("accounts")

    def ready(self):
        """
        Override this method in subclasses to run code when Django starts.
        """
