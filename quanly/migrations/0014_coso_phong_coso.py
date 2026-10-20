from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('quanly', '0013_nguoithue_tai_khoan'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoSo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ten_co_so', models.CharField(max_length=100, unique=True)),
                ('dia_chi', models.CharField(blank=True, max_length=255)),
                ('mo_ta', models.TextField(blank=True)),
                ('ngay_tao', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Cơ sở',
                'verbose_name_plural': 'Cơ sở',
                'ordering': ('ten_co_so',),
            },
        ),
        migrations.AddField(
            model_name='phong',
            name='co_so',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='phong', to='quanly.coso'),
        ),
    ]
