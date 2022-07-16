from django.test import TestCase, Client
from django.urls import reverse


from ..models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адресов
        # Автор поста
        cls.author = User.objects.create_user(username='auth')
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
        # Создаем клиент
        self.authorized_client_author = Client()
        # Авторизуем пользователя автора
        self.authorized_client_author.force_login(PostURLTests.author)

    # при отправке валидной формы со страницы создания поста
    # создаётся новая запись в базе данных;
    def test_new_record_is_in_data_base(self):
        form_data = {
            'group': PostURLTests.group.id,
            'text': 'Тестовый текст',
        }
        # Отправляем POST-запрос
        self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=False
        )
        count = Post.objects.all().count()
        self.assertEqual(count, 2)

    # при отправке валидной формы со страницы редактирования поста
    # происходит изменение поста с post_id в базе данных.
    def test_edit_record_is_in_data_base(self):
        form_data = {
            'group': PostURLTests.group.id,
            'text': 'Тестовый текст 2',
        }
        # Отправляем POST-запрос
        self.authorized_client_author.post(
            reverse('posts:post_edit', args=(1,)),
            data=form_data,
            follow=False
        )
        text = Post.objects.all()[0].text
        self.assertEqual(text, 'Тестовый текст 2')
