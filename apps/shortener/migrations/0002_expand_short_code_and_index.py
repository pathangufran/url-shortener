from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("shortener", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="url",
            name="short_code",
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.RemoveIndex(model_name="url", name="urls_is_acti_ad181e_idx"),
        migrations.RemoveIndex(model_name="url", name="urls_created_71be6f_idx"),
        migrations.RemoveIndex(model_name="url", name="urls_expires_52ec95_idx"),
        migrations.AddIndex(
            model_name="url",
            index=models.Index(fields=["is_active", "expires_at"], name="urls_active_expiry_idx"),
        ),
        migrations.AddIndex(
            model_name="url",
            index=models.Index(fields=["user", "-created_at"], name="urls_user_created_idx"),
        ),
    ]
