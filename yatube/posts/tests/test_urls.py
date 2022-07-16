from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адресов
        # Автор поста
        cls.author = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='HasNoName')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        # self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client_author = Client()
        # Авторизуем пользователя автора
        self.authorized_client_author.force_login(PostURLTests.author)
        # Создаем третий клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(PostURLTests.user)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/post_create.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)

    # Проверяем общедоступные страницы
    def test_guest_url_exists_at_desired_location(self):
        """Страницы , доступные любому пользователю."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
        }
        for address in templates_url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_authorized_url_exists_at_desired_location(self):
        """Страницы, доступные авторизованному пользователю."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
        }
        for address in templates_url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем доступность страниц для автора поста
    def test_author_url_exists_at_desired_location(self):
        """Страницы, доступные авторизованному пользователю."""
        templates_url_names = {
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/post_create.html',
        }
        for address in templates_url_names:
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем редиректы для неавторизованного пользователя
    def test_url_redirect_anonymous(self):
        """Страница перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{PostURLTests.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{PostURLTests.post.id}/edit/')

    # Проверяем редиректы для авторизованного пользователя
    def test_url_redirect_authorized(self):
        """Страница перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, f'/posts/{PostURLTests.post.id}/')
