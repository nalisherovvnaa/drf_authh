from django.contrib import admin
from .models import Car
from product.models.products import Post, Category

# Register your models here.

admin.site.register(Post)
admin.site.register(Category)