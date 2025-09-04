from django.db import models


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField('is_deleted', default=False, editable=False)

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        super(SoftDeleteMixin, self).save()

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def get_queryset_with_deleted(self):
        return super().get_queryset()

    class Meta:
        abstract = True


class PreventUpdateMixin(models.Model):
    def save(self, *args, **kwargs):
        if self.pk:
            raise NotImplementedError('Update not allowed')
        else:
            super().save(*args, **kwargs)

    class Meta:
        abstract = True


class PreventDeleteMixin(models.Model):
    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        raise Exception(f"Deletion of {self._meta.model.__name__} object is not allowed.")


class VersionMixin(models.Model):
    version = models.IntegerField(default=1)

    class Meta:
        abstract = True
