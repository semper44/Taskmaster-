from rest_framework import serializers
from .models import Tasks

class Taskapi(serializers.ModelSerializer):
    total_tasks = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Tasks
        fields = ['id', 'name', 'image_url', 'created', 'expires', 'status', 'image', 'contributors', 'tasks_number', 'total_tasks']
        extra_kwargs = {
            'name': {'required': False},
            'expires': {'required': False},
            'contributors': {'required': False},
            'image': {'required': False},
        }
        # when is extra_kwargs and when is it needed, what is representation and what are the methods i can use or overide in serializers

    def validate(self, data):
        errors = {}

        if not data.get('name'):
            errors['name'] = "The 'name' field cannot be empty. Please provide a valid value."
        
        if not data.get('expires'):
            errors['expires'] = "The 'expires' field cannot be empty. Please provide a valid value."
        
        if not data.get('contributors'):
            errors['contributors'] = "The 'contributors' field cannot be empty. Please provide a valid value."

        if not data.get('image'):
            errors['image'] = "The 'image' field cannot be empty. Please uplaod an image."

        if errors:
            raise serializers.ValidationError(errors)
        
        return data

    def get_total_tasks(self, obj):
        total_tasks_count = Tasks.objects.count()
        return total_tasks_count

    def get_image_url(self, obj):
        if obj.image:
            public_id = obj.image.public_id
            cloudinary_url = f'http://res.cloudinary.com/dboagqxsq/image/upload/{public_id}'
            return cloudinary_url
        return None


    
    

