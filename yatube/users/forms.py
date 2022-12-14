from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class CreationForm(UserCreationForm):
    """
    Класс формы регистации.
    """
    class Meta(UserCreationForm.Meta):
        """
        Настройка формы.
        """
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
