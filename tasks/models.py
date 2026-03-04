from django.db import models


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Thap'),
        ('medium', 'Trung binh'),
        ('high', 'Cao'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
