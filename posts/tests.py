from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
import tempfile
import os

User = get_user_model()


class AuthAndFileTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.test_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='TestPass123!'
        )
        self.token = Token.objects.create(user=self.user)

    # РЕГИСТРАЦИЯ

    def test_registration_success(self):
        """Успешная регистрация"""
        response = self.client.post(reverse('register'), data=self.test_user_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('token', response.json())

    def test_registration_empty_data(self):
        """Пустые данные"""
        response = self.client.post(reverse('register'), data={}, format='json')
        self.assertIn(response.status_code, [400, 422])

    def test_registration_weak_password(self):
        """Слабый пароль"""
        data = self.test_user_data.copy()
        data['password'] = '123'
        data['password2'] = '123'
        response = self.client.post(reverse('register'), data=data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_registration_duplicate_email(self):
        """Дубликат email"""
        self.client.post(reverse('register'), data=self.test_user_data, format='json')
        response = self.client.post(reverse('register'), data=self.test_user_data, format='json')
        self.assertEqual(response.status_code, 400)

    # 2. АУТЕНТИФИКАЦИЯ

    def test_login_success(self):
        """Успешный вход"""
        response = self.client.post(reverse('login'), data={
            'username': 'existinguser',
            'password': 'TestPass123!'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json())
        self.token_key = response.json()['token']

    def test_login_wrong_password(self):
        """Неверный пароль"""
        response = self.client.post(reverse('login'), data={
            'username': 'existinguser',
            'password': 'wrongpassword'
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_login_nonexistent_user(self):
        """Несуществующий пользователь"""
        response = self.client.post(reverse('login'), data={
            'username': 'nouser',
            'password': 'TestPass123!'
        }, format='json')
        self.assertEqual(response.status_code, 400)

    #3. ВЫХОД (LOGOUT)

    def test_logout_success(self):
        """Успешный выход"""
        response = self.client.post(reverse('logout'), HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.assertEqual(response.status_code, 200)

    def test_logout_invalid_token(self):
        """Невалидный токен"""
        response = self.client.post(reverse('logout'), HTTP_AUTHORIZATION='Token invalid_token')
        self.assertEqual(response.status_code, 401)

    #4. ЗАГРУЗКА ФАЙЛОВ

    def test_file_upload_no_auth(self):
        """Без авторизации"""
        test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        test_file.write(b'Test image content')
        test_file.close()

        with open(test_file.name, 'rb') as f:
            response = self.client.post(
                reverse('post-list-create'),
                {
                    'title': 'Test Post',
                    'content': 'Test content',
                    'image': f
                },
                format='multipart'
            )

        os.unlink(test_file.name)
        self.assertEqual(response.status_code, 401)

    def test_file_upload_invalid_type(self):
        """Запрещённый тип файла (.exe)"""
        # 🔹 Создаём файл с расширением .exe (не изображение)
        test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exe')
        test_file.write(b'MZ' + b'\x00' * 100)  # Сигнатура EXE файла
        test_file.close()

        with open(test_file.name, 'rb') as f:
            response = self.client.post(
                reverse('post-list-create'),
                {
                    'title': 'Test Post',
                    'content': 'Test content',
                    'image': f
                },
                HTTP_AUTHORIZATION=f'Token {self.token.key}',
                format='multipart'
            )

        os.unlink(test_file.name)
        self.assertIn(response.status_code, [400, 415])

    # 5. ПРОСМОТР ФАЙЛОВ (Постов)

    def test_view_files_success(self):
        """Успешный просмотр постов с файлами"""
        response = self.client.get(
            reverse('post-list-create'),
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertIsInstance(data['results'], list)

    def test_view_files_no_auth(self):
        """Без авторизации"""
        response = self.client.get(reverse('post-list-create'))
        self.assertEqual(response.status_code, 401)