from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Котики',
            slug='cat',
            description='Группа о котиках',
            id='1'
        )
        cls.author = User.objects.create_user(
            username='AuthorForPosts'
        )
        cls.post = Post.objects.create(
            group=PostURLTests.group,
            text="Тестовый текст",
            author=User.objects.get(username='AuthorForPosts')
        )
        cls.index = '/'
        cls.group_list = '/group/cat/'
        cls.create = '/create/'
        cls.profile = '/profile/AuthorForPosts/'
        cls.detail = '/posts/1/'

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        template_url_names = {
            'posts/index.html': self.index,
            'posts/group_list.html': self.group_list,
            'posts/create_post.html': self.create,
            'posts/post_detail.html': self.detail,
            'posts/profile.html': self.profile,
        }
        for template, reverse_name in template_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_url_exists_at_desired_location(self):

        response = self.guest_client.get(self.index)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_list_url_exists_at_desired_location(self):

        response = self.guest_client.get(self.group_list)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_exists_at_desired_location(self):

        response = self.guest_client.get(self.profile)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail_exists_at_desired_location(self):

        response = self.guest_client.get(self.detail)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_exists_at_desired_location(self):

        response = self.authorized_client.get(self.create)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_redirect_anonymous_on_admin_login(self):

        response = self.guest_client.get(self.create, follow=True)

        redirect = reverse('login') + '?next=' + self.create

        self.assertRedirects(response, redirect)

    def test_page_404(self):

        response = self.guest_client.get('/page/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_page_500(self):

        response = self.guest_client.get('500/')

        self.assertEqual(response.status_code, 404)

    def test_500_page(self):
        """ Проверка ошибки 500 """
        self.client.raise_request_exception = False
        response = self.client.get(reverse('posts:500'))
        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, 'core/500.html')
