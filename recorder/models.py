from django.db import models
from django.core.validators import RegexValidator

class Speaker(models.Model):
    username = models.CharField(max_length=100, unique=True)
    speaker_number = models.IntegerField(unique=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username}(speaker{self.speaker_number})"

class AudioRecording(models.Model):
    username = models.CharField(max_length=100)
    clip_number = models.IntegerField()
    audio_file = models.FileField(upload_to='recordings/')
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField(default=5.0)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.username} - Clip {self.clip_number}"