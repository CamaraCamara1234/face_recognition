from django.db import models

class User(models.Model):
    pid = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255)
    email = models.EmailField()
    given_name = models.CharField(max_length=255, blank=True, null=True)
    family_name = models.CharField(max_length=255, blank=True, null=True)
    photo_path = models.CharField(max_length=255, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.username