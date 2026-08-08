from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def assign_existing_chat_recipients(apps, schema_editor):
    ChatConversation = apps.get_model("chat", "ChatConversation")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))

    # Preserve the existing conversation by assigning it to Aryan Raina.
    recipient = User.objects.filter(
        email__iexact="aryanuavmarketplace@gmail.com"
    ).first()

    if recipient is None:
        raise RuntimeError(
            "Cannot migrate chat conversations: "
            "aryanuavmarketplace@gmail.com does not exist."
        )

    ChatConversation.objects.filter(recipient__isnull=True).update(
        recipient=recipient
    )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("employee", "0001_initial"),
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatconversation",
            name="recipient",
            field=models.ForeignKey(
                blank=True,
                help_text="Which HR contact this thread is with.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="chats_received",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Recipient",
            ),
        ),

        migrations.RunPython(
            assign_existing_chat_recipients,
            migrations.RunPython.noop,
        ),

        migrations.AlterField(
            model_name="chatconversation",
            name="recipient",
            field=models.ForeignKey(
                help_text="Which HR contact this thread is with.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="chats_received",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Recipient",
            ),
        ),

        migrations.AlterField(
            model_name="chatconversation",
            name="employee",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="hr_chats",
                to="employee.employee",
                verbose_name="Employee",
            ),
        ),

        migrations.AlterUniqueTogether(
            name="chatconversation",
            unique_together={("employee", "recipient")},
        ),
    ]