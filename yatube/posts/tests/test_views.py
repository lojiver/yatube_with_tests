from http import HTTPStatus
import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Group, Follow, Comment
from ..forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='HasNoName')

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug1',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsPagesTest.user)

    def test_pages_uses_correct_template(self):
        template_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_list', kwargs={
                'slug': PostsPagesTest.group.slug
            })): 'posts/group_list.html',
            (reverse('posts:profile', kwargs={
                'username': PostsPagesTest.user.username
            })): 'posts/profile.html',
            (reverse('posts:post_detail', kwargs={
                'post_id': PostsPagesTest.post.id
            })): 'posts/post_detail.html',
            (reverse('posts:post_edit', kwargs={
                'post_id': PostsPagesTest.post.id
            })): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_context_contains_page_or_post(self, context, post=False):
        if post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
        self.assertEqual(post.author, PostsPagesTest.user)
        self.assertEqual(post.pub_date, PostsPagesTest.post.pub_date)
        self.assertEqual(post.text, PostsPagesTest.post.text)
        self.assertEqual(post.group, PostsPagesTest.post.group)
        self.assertEqual(post.image, PostsPagesTest.post.image)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.check_context_contains_page_or_post(response.context)

    def test_follow_page_correct_context(self):
        follower = User.objects.create_user(username='Follower')
        self.authorized_follower = Client()
        self.authorized_follower.force_login(follower)
        Follow.objects.create(
            user=follower, author=PostsPagesTest.user
        )
        response_follower = self.authorized_follower.get(
            reverse('posts:follow_index')
        )
        self.check_context_contains_page_or_post(response_follower.context)

    def test_group_list_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={
                'slug': PostsPagesTest.group.slug
            })
        )
        self.check_context_contains_page_or_post(response.context)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={
                'username': PostsPagesTest.user.username
            })
        )
        self.check_context_contains_page_or_post(response.context)
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], PostsPagesTest.user)

    def test_post_detail_page_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': PostsPagesTest.post.id
            })
        )
        self.check_context_contains_page_or_post(
            response.context, post=True
        )

    def test_post_create_and_post_edit_paged_correct_context(self):

        urls = (
            ('create', reverse('posts:post_create')),
            ('edit', reverse('posts:post_edit', kwargs={
                'post_id': PostsPagesTest.post.id
            }))
        )

        for name, url in urls:
            with self.subTest(name=name):
                is_edit_value = bool(name == 'edit')

                response = self.authorized_client.get(url)

                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)

                self.assertIn('is_edit', response.context)
                is_edit = response.context['is_edit']
                self.assertIsInstance(is_edit, bool)
                self.assertEqual(is_edit, is_edit_value)

    def test_post_exists_on_pages_and_not_exists_in_group(self):
        post = Post.objects.create(
            text='Создано внутри функции',
            author=User.objects.create_user(username='CheckCreate'),
            group=Group.objects.create(
                title='Группа проверки поста',
                slug='test-slug3',
                description='Описание группы проверки поста',
            )
        )
        template_pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug3'}),
            reverse('posts:profile', kwargs={'username': 'CheckCreate'}),
        ]

        for address in template_pages_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTrue(post in response.context['page_obj'])

        self.assertTrue(post not in (
            self.authorized_client.get(
                reverse('posts:group_list', kwargs={'slug': 'test-slug1'}),
            ).context['page_obj']
        ))

    def test_paginator_views(self):
        template_pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                'slug': PostsPagesTest.group.slug
            }),
            reverse('posts:profile', kwargs={
                'username': PostsPagesTest.user.username
            }),
        ]

        post_count = Post.objects.count()
        paginator_amount = 10
        second_page_amount = post_count + 3

        posts = [
            Post(
                text=f'text {num}', author=PostsPagesTest.user,
                group=PostsPagesTest.group
            ) for num in range(1, paginator_amount + second_page_amount)
        ]
        Post.objects.bulk_create(posts)
        pages = (
            (1, paginator_amount),
            (2, second_page_amount)
        )

        for address in template_pages_names:
            for page, count in pages:
                with self.subTest(address=address, page=page):
                    response = self.authorized_client.get(
                        address, {'page': page}
                    )
                    self.assertEqual(len(
                        response.context.get('page_obj').object_list
                    ), count)

    def test_authorized_user_can_publish_comment(self):
        post = PostsPagesTest.post
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}
            ),
            data={'text': 'hello'},
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()

        self.assertEqual(comment.text, 'hello')
        self.assertEqual(comment.post, post)
        self.assertEqual(comment.author, self.user)

    def test_unauthorized_user_cant_publish_comment(self):
        post = PostsPagesTest.post
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}
            ),
            data={'text': 'hello'},
            follow=True
        )

        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{post.id}/comment/'
        )

        self.assertEqual(Comment.objects.count(), 0)

    def test_img_in_html(self):
        template_pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                'slug': PostsPagesTest.group.slug
            }),
            reverse('posts:profile', kwargs={
                'username': PostsPagesTest.user.username
            }),
            reverse('posts:follow_index')
        ]

        for address in template_pages_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertContains(response, '<img')

    def test_index_cache(self):
        response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.filter(pk=1).delete()

        self.assertEqual(
            response.content,
            self.authorized_client.get(reverse('posts:index')).content
        )
        cache.clear()
        self.assertNotEqual(
            response.content,
            self.authorized_client.get(reverse('posts:index')).content
        )
