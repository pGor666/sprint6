import random

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Post, Group, Comment, Follow

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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        for i in range(1, 12):
            cls.post = Post.objects.create(
                group=PostViewsTests.group,
                text='Тестовый текст',
                author=cls.author,
                image=uploaded,
            )

        cls.post_two = Post.objects.create(
            group=PostViewsTests.group_two,
            text='Тестовый текст 2',
            author=cls.author,)

        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Комментарий',
            author=cls.user
        )

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
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_group_0, 'Тестовая группа')
        self.assertEqual(post_author_0, 'auth')
        self.assertNotEqual(post_image_0, None)

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
            response.context['page_obj'].end_index() % per_page, 2)

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
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_group_0, 'Тестовая группа')
        self.assertEqual(post_author_0, 'auth')
        self.assertNotEqual(post_image_0, None)

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
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_group_0, 'Тестовая группа')
        self.assertEqual(post_author_0, 'auth')
        self.assertNotEqual(post_image_0, None)

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
        post_image_0 = post.image
        self.assertEqual(text, 'Тестовый текст')
        self.assertEqual(username, 'auth')
        self.assertNotEqual(post_image_0, None)

    # Проверяем поля формы создания поста
    def test_post_create_page_form(self):
        """Форма создания нового поста"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
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
            'image': forms.fields.ImageField,
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

    def test_add_comment_view(self):
        '''комментировать посты может только авторизованный пользователь'''
        url = reverse(
            "posts:add_comment", kwargs={"post_id": 1}
        )
        count_comments = Comment.objects.filter(post__pk=1).count()
        data = {"text": "Test comment"}
        response = self.authorized_client.post(
            url, data, follow=True
        )
        response_guest = self.guest_client.post(
            url, data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(
            response_guest,
            '/auth/login/?next=' + url,
        )
        self.assertEqual(
            Comment.objects.filter(post__pk=1).count(), count_comments + 1
        )

    def test_cache_is_working_on_index_page(self):
        """Кэш постов на инекс пейдж хранится 20 секунд"""
        response = self.guest_client.get(reverse("posts:index"))
        content_response_before = response.content
        Post.objects.create(
            group=PostViewsTests.group,
            text='Новый текст, после кэша',
            author=PostViewsTests.author
        )
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        content_response_after = response.content
        self.assertNotEqual(content_response_before,
                            content_response_after)   

    def test_login_user_follow(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей
        """
        followers_before = len(
            Follow.objects.all().filter(author_id=self.author.id))

        self.authorized_client.get(
            reverse('posts:profile_follow', args=[self.author]))
        followers_after = len(
            Follow.objects.all().filter(author_id=self.author.id))
        self.assertEqual(followers_after, followers_before + 1)

    def test_login_user_unfollow(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей, а также отписываться
        """
        followers_before = len(
            Follow.objects.all().filter(author_id=self.author.id))

        self.authorized_client.get(
            reverse('posts:profile_follow', args=[self.author]))
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=[self.author]))

        followers_after_unfollow = len(
            Follow.objects.all().filter(author_id=self.author.id))
        self.assertEqual(followers_after_unfollow, followers_before)

    def test_follow_index(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан на него
        """
        response = self.authorized_client.get(reverse('posts:follow_index'))

        self.authorized_client.get(
            reverse('posts:profile_follow', args=[self.author]))

        response_after_follow = self.authorized_client.get(
            reverse('posts:follow_index'))

        self.assertEqual(response.content, response_after_follow.content)                

   