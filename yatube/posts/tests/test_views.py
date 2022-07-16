import random

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Post, Group

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адресов
        # Автор поста
        cls.author = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_two = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        for i in range(1, 12):
            cls.post = Post.objects.create(
                group=PostViewsTests.group,
                text='Тестовый текст',
                author=cls.author,
            )

        cls.post_two = Post.objects.create(
            group=PostViewsTests.group_two,
            text='Тестовый текст 2',
            author=cls.author,)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        # self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client_author = Client()
        # Авторизуем пользователя автора
        self.authorized_client_author.force_login(PostViewsTests.author)
        # Создаем третий клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(PostViewsTests.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': PostViewsTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostViewsTests.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostViewsTests.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_create'
            ): 'posts/post_create.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostViewsTests.post.id}
            ): 'posts/post_create.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверяем, что словарь context страницы /index
    # в первом элементе списка post_list содержит ожидаемые значения
    def test_index_page_show_correct_context(self):
        """Список постов"""
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context.get('page_obj')[0]
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        post_author_0 = first_object.author.username
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_group_0, 'Тестовая группа')
        self.assertEqual(post_author_0, 'auth')

    # Тестируем паджинатор
    def test_first_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse('posts:index'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(response.context['page_obj'].end_index(), 10)

    def test_second_page_contains_two_records(self):
        # Проверка: на второй странице должно быть два поста.
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        per_page = response.context['paginator'].per_page
        self.assertEqual(
            response.context['page_obj'].end_index() % per_page, 2
            )

    # Проверяем, что словарь context страницы /group
    # в первом элементе списка post_list содержит ожидаемые значения
    def test_group_page_show_correct_context(self):
        """Список постов, отфильтрованных по группе"""
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        response = self.authorized_client.get(
            reverse('posts:group_posts', args=[self.group.slug]))
        first_object = response.context.get('page_obj')[0]
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        post_author_0 = first_object.author.username
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_group_0, 'Тестовая группа')
        self.assertEqual(post_author_0, 'auth')

    # Проверяем, что словарь context страницы /profile
    # в первом элементе списка post_list содержит ожидаемые значения
    def test_profile_page_show_correct_context(self):
        """Список постов, отфильтрованных по пользователю"""
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        response = self.authorized_client.get(
            reverse('posts:profile', args=[self.author.username]))
        first_object = response.context.get('page_obj')[0]
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        post_author_0 = first_object.author.username
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_group_0, 'Тестовая группа')
        self.assertEqual(post_author_0, 'auth')

    # Проверяем, что словарь context страницы /post_detail
    # содержит ожидаемые значения
    def test_post_detail_page_show_correct_context(self):
        """Один пост, отфильтрованный по id"""
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        list_id = Post.objects.filter(author=self.author).values_list(
            'id', flat=True)
        url = reverse('posts:post_detail', args=[random.choice(list_id)])
        response = self.authorized_client.get(url)
        post = response.context['post']
        username = post.author.username
        text = post.text
        self.assertEqual(text, 'Тестовый текст')
        self.assertEqual(username, 'auth')

    # Проверяем поля формы создания поста
    def test_post_create_page_form(self):
        """Форма создания нового поста"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context['form'].fields[value]
                self.assertIsInstance(form_fields, expected)

    def test_context_in_post_edit(self):
        """
        Проверка содержимого словаря context
        для /<username>/<post_id>/edit/
        """
        list_id = Post.objects.filter(author=self.author).values_list(
            'id', flat=True)
        url = reverse('posts:post_edit', args=[random.choice(list_id)])
        response = self.authorized_client_author.get(url)
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context['form'].fields[value]
                self.assertIsInstance(form_fields, expected)

    # При создании поста указать группу,
    # то этот пост появляется на главной странице сайта
    def test_new_post_at_index_page(self):
        url = reverse('posts:index')
        response = self.authorized_client_author.get(url)
        page_obj = response.context.get('page_obj')
        post = Post.objects.all()[0]
        self.assertIn(post, page_obj)

    # При создании поста указать группу,
    # то этот пост появляется на странице выбранной группы
    def test_new_post_at_chosen_group(self):
        url = reverse('posts:group_posts', args=[self.group.slug])
        response = self.authorized_client_author.get(url)
        page_obj = response.context.get('page_obj')
        post = Post.objects.all()[0]
        self.assertIn(post, page_obj)

    # При создании поста указать группу,
    # то этот пост появляется в профайле пользователя.
    def test_new_post_at_profile(self):
        url = reverse('posts:profile', args=[self.author])
        response = self.authorized_client_author.get(url)
        page_obj = response.context.get('page_obj')
        post = Post.objects.all()[0]
        self.assertIn(post, page_obj)

    # При создании поста указать группу,
    # то этот пост не появляется в другой группе.
    def test_new_post_not_in_wrong_group(self):
        url = reverse('posts:group_posts', args=[self.group_two.slug])
        response = self.authorized_client_author.get(url)
        page_obj = response.context.get('page_obj')
        post = Post.objects.all()[0]
        self.assertNotIn(post, page_obj)


fruits = ["apple", "banana", "cherry"]

x = fruits.count("cherry")

print(x)