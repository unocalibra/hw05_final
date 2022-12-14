from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self):
        """URL используют соответствующий шаблон."""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')
