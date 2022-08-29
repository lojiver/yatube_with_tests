from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group


User = get_user_model()


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.user = User.objects.create_user(username='HasNoName')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.user_author = User.objects.get(username='HasNoName')
        self.user_not_author = User.objects.create_user(username='NotAuthor')
        self.authorized_not_author = Client()
        self.authorized_not_author.force_login(self.user_not_author)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user_author)

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_urls_responses(self):
        urls = {
            'index': '/',
            'group_posts': '/group/test-slug/',
            'profile': '/profile/NotAuthor/',
            'post_detail': '/posts/1/',
            '404': '/unexisting_page/',
            'post_edit': '/posts/1/edit/',
            'post_create': '/create/',
            'add_comment': '/posts/1/comment/'
        }
        for name, address in urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                if name == '404':
                    self.assertEqual(response.status_code, 404)
                    self.assertTemplateUsed(response, 'core/404.html')
                elif name in ['post_edit', 'post_create', 'add_comment']:
                    self.assertRedirects(
                        response, f'/auth/login/?next={urls[name]}'
                    )
                else:
                    self.assertEqual(response.status_code, 200)

    def test_urls_authorised(self):
        urls = {
            '/posts/1/edit/': '/posts/1/',
            '/profile/NotAuthor/follow/': '/profile/NotAuthor/',
            '/profile/NotAuthor/unfollow/': '/profile/NotAuthor/',
        }
        for address, redirect in urls.items():
            with self.subTest(address=address, redirect=redirect):
                self.assertRedirects(
                    self.authorized_not_author.get(address),
                    redirect
                )

        for address in (
            '/create/',
            '/posts/1/comment/',
        ):
            with self.subTest(address=address):
                response = self.authorized_not_author.get(address)
                self.assertEqual(response.status_code, 200)

    def test_urls_author(self):
        response = self.authorized_author.get(
            '/posts/1/edit/'
        )
        self.assertEqual(response.status_code, 200)

    def test_urls_posts_correct_templates(self):
        template_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/comment/': 'posts/add_comment.html'
        }
        for address, template in template_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)
