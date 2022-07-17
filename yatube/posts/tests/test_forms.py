from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()


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

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_post_create(self):
        """форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
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
