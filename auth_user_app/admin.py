from django.contrib import admin
from django.contrib.auth.models import Group
from .models import CustomUser

# Register your models here.

admin.site.register(CustomUser)
admin.site.unregister(Group)
