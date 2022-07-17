
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post, User

User = get_user_model()


class StaticURLTests(TestCase):
    '''Класс для тестирования View'''
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
            id='1',
        )
        cls.another_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
        )
        cls.index = reverse('posts:index')
        cls.group_list = reverse('posts:group_list',
                                 kwargs={'slug': 'test-slug'})
        cls.another_group_list = reverse('posts:group_list',
                                         kwargs={'slug': 'test-slug-2'})
        cls.create = reverse('posts:post_create')
        cls.profile = reverse('posts:profile',
                              kwargs={'username': 'auth'})
        cls.detail = reverse('posts:post_detail',
                             kwargs={'post_id': '1'})

    def setUp(self):
        self.guest_client = Client()
        self.guest = User.objects.create_user(username='bot')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.guest)
        self.user = User.objects.get(username='auth')
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        '''Тест шаблонов'''

        templates_pages_names = {
            self.index: 'posts/index.html',
            self.group_list: 'posts/group_list.html',
            self.profile: 'posts/profile.html',
            self.detail: 'posts/post_detail.html',
            self.create: 'posts/create_post.html',
            reverse('posts:500'): 'core/500.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)

                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        '''Шаблон главной страницы'''
        response = self.authorized_client.get(self.index)

        object = response.context['page_obj'][0]

        self.assertEqual(object, self.post)

    def test_group_pages_show_correct_context(self):
        """Шаблон группы"""

        response = self.authorized_client.get(self.group_list)

        test_group_title = response.context.get('group').title

        test_group = response.context.get('group').description

        self.assertEqual(test_group_title, 'Тестовая группа')

        self.assertEqual(test_group, self.group.description)

    def test_post_another_group(self):
        """Пост не попал в другую группу"""

        response = self.authorized_client.get(self.group_list)

        object = response.context["page_obj"][0]

        post_text = object.text

        self.assertTrue(post_text, 'Тестовая запись для создания поста')

    def test_profile_page_show_correct_context(self):
        '''Тест профиля'''
        response = (self.authorized_client.
                    get(self.profile))

        test_author = response.context.get('author')

        self.assertEqual(test_author, self.post.author)

    def test_post_detail_show_correct_context(self):
        '''Тест страницы поста'''
        response = (self.authorized_client.
                    get(self.detail))

        test_posts = response.context.get('post')

        self.assertEqual(test_posts, self.post)

    def test_post_create_show_correct_context(self):
        '''Тест создания поста'''
        response = (self.authorized_client.
                    get(self.create))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_fields, expected)

    def test_additional_verification_when_creating_a_post(self):
        '''Тест дополнительная проверка поста'''
        project_pages = [
            self.index,
            self.group_list,
            self.profile,
        ]

        for address in project_pages:
            with self.subTest(adress=address):
                response = self.author_client.get(address)
                self.assertEqual(
                    response.context.get('page_obj')[0], self.post
                )

    def test_the_post_was_not_included_in_the_group(self):
        '''Тест пост не попал в другую группу'''
        response = self.authorized_client.get(self.another_group_list)

        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    '''Класс для тестирования пагинатора'''
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.index = reverse('posts:index')
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for post in range(13):
            Post.objects.create(
                author=cls.user,
                text=f'{post} тестовый текст',
                group=cls.group,
            )

    def setUp(self):
        self.client = Client()

    def test_first_page_contains_ten_records(self):
        '''Тест первой страницы'''
        response = self.client.get(self.index)

        self.assertEqual(
            len(
                response.context['page_obj']
            ),
            settings.POSTS_PER_PAGE
        )

    def test_second_page_contains_three_records(self):
        '''Тест второй страницы'''
        response = self.client.get(self.index + '?page=2')

        self.assertEqual(
            len(
                response.context['page_obj']
            ),
            3
        )


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='test_name'),
            text='Тестовая запись для создания поста')

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='bot')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Тест кэширования страницы index.html"""
        first_state = self.authorized_client.get(reverse('posts:index'))
        post_1 = Post.objects.get(pk=1)
        post_1.text = 'Измененный текст'
        post_1.save()
        second_state = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_state.content, second_state.content)
        cache.clear()
        third_state = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_state.content, third_state.content)


class FollowTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись для тестирования ленты'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_subscription_feed(self):
        """запись появляется в ленте подписчиков"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        post_text_0 = response.context["page"][0].text
        self.assertEqual(post_text_0, 'Тестовая запись для тестирования ленты')
        # в качестве неподписанного пользователя проверяем собственную ленту
        response = self.client_auth_following.get('/follow/')
        self.assertNotContains(response,
                               'Тестовая запись для тестирования ленты')

    def test_follow(self):
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.client_auth_follower.get(reverse('posts:profile_unfollow',
                                      kwargs={'username':
                                              self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)
