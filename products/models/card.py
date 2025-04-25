from django.db import models

class Card(models.Model):
    user = models.ForeignKey(to='auth_user_app.CustomUser', on_delete=models.CASCADE)
    post = models.ForeignKey(to='product.Post', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    # status = models.BooleanField(default=False)
    date =  models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.post}"


class Like(models.Model):
    user = models.ForeignKey(to='auth_user_app.CustomUser', on_delete=models.CASCADE)
    post = models.ForeignKey(to='product.Post', on_delete=models.CASCADE)
    like = models.BooleanField(default=False)
    # status = models.BooleanField(default=False)
    dis = models.BooleanField(default=False)
    date =  models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.post}"