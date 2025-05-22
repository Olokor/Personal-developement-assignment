from django.db import models

# Create your models here.
class Note(models.Model):

    CATEGORIES = (
        ('BUSINESS', 'Business'),
        ('PERSONAL', 'Personal'),
        ('IMPORTANT', 'Important'),
    )
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    body = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORIES, default='PERSONAL')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.body[:50]
