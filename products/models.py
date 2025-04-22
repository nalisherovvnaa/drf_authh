from django.db import models

# Create your models here.

class Car(models.Model):
    model = models.CharField(max_length=50)
    brand = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    date =  models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'car'
        verbose_name_plural = 'cars'

    def __str__(self):
        return f"{self.brand} ({self.model})"
    
