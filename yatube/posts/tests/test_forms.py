import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='TitleTest',
            slug='test_slug',
            description='Тестовый description'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.test_image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.guest_client = Client()

    def test_post_create(self):
        """форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': self.test_image,
        }

        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=self.group,
                author=self.user,
            ).exists()
        )

    def test_edit_post(self):
        '''Тест редактировая поста'''
        post_edit = Post.objects.create(
            text='Текст для редактирования',
            author=self.user,
            group=self.group,
        )
        post_id = post_edit.id
        form_data = {
            'text': 'Текст поста для редактирование',
            'group': self.group.id,
        }

        response = self.author_client.post(
            reverse('posts:post_edit', args=[
                    post_edit.id]),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', args=[post_edit.id]))
        self.assertEqual(Post.objects.get(id=post_id).text, form_data['text'])

    def test_comment_create(self):
        '''Тест создания комментария'''
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Новый комментарий'
        }

        response = self.author_client.post(
            reverse(('posts:add_comment'),
                    kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True)

        self.assertRedirects(response, reverse((
            'posts:post_detail'), kwargs={'post_id': f'{self.post.id}'}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(Comment.objects.filter(text='Новый комментарий',
                                              ).exists())

    def test_add_comment_login_user(self):
        '''
        Проверка доступа не зарегистрированного
        пользователя к добавлению комментария
        '''

        response = self.guest_client.get(reverse('posts:add_comment',
                                                 kwargs={'post_id': '1'})
                                        )

        self.assertEqual(response.status_code, 302)
