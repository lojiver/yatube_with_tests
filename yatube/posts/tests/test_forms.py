from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import Client, TestCase, override_settings
from posts.forms import PostForm
from posts.models import Post, Group, Comment
from django.contrib.auth import get_user_model


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы')

        cls.form = PostForm

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.user = User.objects.create(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
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

        form_data = {
            'text': 'Тестовый текст',
            'group': PostsFormsTest.group.id,
            'image': uploaded
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': 'HasNoName'}
            )
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, PostsFormsTest.group)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_edit_post(self):

        post = Post.objects.create(
            text='test',
            author=self.user,
            group=PostsFormsTest.group
        )
        new_post_text = 'Тестовый текст редактированный'
        new_group = Group.objects.create(
            title='New Test group',
            slug='new-test-group',
            description='new test description'
        )

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data={'text': new_post_text, 'group': new_group.id},
            follow=True,
        )

        self.assertRedirects(
            response, reverse('posts:post_detail', kwargs={'post_id': 1})
        )

        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, 'Тестовый текст редактированный')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, new_group)

    def test_add_comment(self):
        post = Post.objects.create(
            text='test',
            author=self.user,
            group=PostsFormsTest.group
        )

        form_data = {
            'text': 'Тестовый текст комментария',
            'post': post,
            'author': self.user
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, 'Тестовый текст комментария')
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, post)
