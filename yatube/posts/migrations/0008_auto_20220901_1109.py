# Generated by Django 2.2.16 on 2022-09-01 07:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20220827_1216'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ('-created',), 'verbose_name': ('Комментарий',), 'verbose_name_plural': 'Комментарии'},
        ),
        migrations.AddField(
            model_name='post',
            name='title',
            field=models.CharField(default='Заметка Льва Толстого <built-in function id>', help_text='Введите название поста', max_length=200, verbose_name='Название поста'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='follow',
            name='author',
            field=models.ForeignKey(help_text='Выберите автора, на которого хотите подписаться', on_delete=django.db.models.deletion.CASCADE, related_name='following', to=settings.AUTH_USER_MODEL, verbose_name='Подписка'),
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='unique_author_user_following'),
        ),
    ]