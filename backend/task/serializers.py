from rest_framework import serializers
from .models import Tasks

class Taskapi(serializers.ModelSerializer):
    total_tasks = serializers.SerializerMethodField()

    class Meta:
        model = Tasks
        fields = ['id', 'name','created', 'expires', 'status', 'image', 'contributors', 'tasks_number', 'total_tasks']

    def get_total_tasks(self, obj):
        total_tasks_count = Tasks.objects.count()
        return total_tasks_count
    

