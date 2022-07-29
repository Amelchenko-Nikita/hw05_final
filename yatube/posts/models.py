from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
    text = models.TextField(verbose_name='texts')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='pub_dates')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='authors'
        )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True, null=True, 
        verbose_name='groups'
        )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
        )
    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
        )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
        )
    text = models.TextField()
    created = models.DateTimeField('date published', auto_now_add=True)

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
        )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
        )
    class Meta:
        constraints = (models.UniqueConstraint(fields=('user', 'author'),
                                               name='Пара уникальных значений'),
                       )
