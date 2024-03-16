from django.db import models
from django.db import models, transaction

# Create your models here.

def upload_to(instance, filename):
    return 'tasks/{filename}'.format(filename=filename)


STATUS_CHOICES = (
    ('Started', 'Started'),
    ('Finished', 'Finished')
)

class Tasks(models.Model):
    name =models.CharField(max_length = 100, unique= True)
    expires =models.DateTimeField(auto_now_add = True)
    created =models.DateTimeField()
    status =models.CharField(max_length = 100, default = "Started", choices = STATUS_CHOICES)
    contributors =models.TextField(max_length = 100)
    tasks_number = models.IntegerField()
    image = models.ImageField(upload_to=upload_to, default='/tasks/cover.jpg')

    def __str__(self):
        return self.name