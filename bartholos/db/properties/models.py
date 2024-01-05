from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from bartholos.db.idmapper.models import SharedMemoryModel


class Attribute(SharedMemoryModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    category = models.CharField(max_length=128, null=False, blank=True, default='')
    name = models.CharField(max_length=255, null=False, blank=False)
    value = models.JSONField(null=False, blank=False)

    class Meta:
        unique_together = (('content_type', 'object_id', 'category', 'name'),)

