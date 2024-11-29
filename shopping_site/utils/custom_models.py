from django.db import models

class TimestampedModel(models.Model):
    """
    Abstract model that adds `created_at` and `updated_at` fields.
    This model should be inherited by other models that require these fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
