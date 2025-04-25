from django.db import models

# Create your models here.
class Ctegory(models.Model):
    name = models.CharField(max_length=20)


    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Category'

class Car(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey(to='auth_user_app.CustomUser', on_delete=models.CASCADE)
    model = models.CharField(max_length=50)
    brand = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    date =  models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digit=10, decimal_places=2)
    price_type = models.CharField(max_length=20)
    image = model.ImageField(upload_to ='images/', blank=True, null=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'car'
        verbose_name_plural = 'cars'

    def __str__(self):
        return f"{self.brand} ({self.model})"
    
