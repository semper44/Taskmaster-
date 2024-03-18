from rest_framework import serializers
from .models import Tasks

class Taskapi(serializers.ModelSerializer):
    total_tasks = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Tasks
        fields = ['id', 'name','image_url','created', 'expires', 'status', 'image', 'contributors', 'tasks_number', 'total_tasks']

    def get_total_tasks(self, obj):
        total_tasks_count = Tasks.objects.count()
        return total_tasks_count
    
    def get_image_url(self, obj):
        # Assuming obj.pics is a Cloudinary resource
        if obj.image:
            # Extract the Cloudinary public ID
            public_id = obj.image.public_id
            # Construct the full Cloudinary image URL
            cloudinary_url = f'http://res.cloudinary.com/dboagqxsq/image/upload/{public_id}'
            return cloudinary_url
        return None  
    
    
    

