from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """
    Настойка статитчного класса "Об авторе".
    """
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """
    Настойка статитчного класса "О технолигии".
    """
    template_name = 'about/tech.html'
