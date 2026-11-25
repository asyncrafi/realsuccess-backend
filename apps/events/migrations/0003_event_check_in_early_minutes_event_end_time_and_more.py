import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0002_event_price_event_qr_registration_token_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="check_in_early_minutes",
            field=models.PositiveIntegerField(default=30),
        ),
        migrations.AddField(
            model_name="event",
            name="end_time",
            field=models.TimeField(default=datetime.time(17, 0)),
        ),
        migrations.AddField(
            model_name="event",
            name="start_time",
            field=models.TimeField(default=datetime.time(9, 0)),
        ),
        migrations.AlterField(
            model_name="event",
            name="days_duration",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
