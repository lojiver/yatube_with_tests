from django.contrib.auth import get_user_model
from django.test import TestCase


from ..models import Group, Post


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост' * 3,
        )

    def test_models_have_correct_object_name(self):
        group = PostModelTest.group
        expected_object_name_group = group.title
        post = PostModelTest.post
        expected_object_name_post = post.text[:15]
        self.assertEqual(expected_object_name_group, str(group))
        self.assertEqual(expected_object_name_post, str(post))
