from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import Taskapi 
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Tasks
from django.db.models import Q
from django.db.models import F, Max, Count




# Create your views here.
class CreateTask(APIView):
    parser_classes= [MultiPartParser, FormParser]

    def post(self, request, format=None):
        highest_number = Tasks.objects.aggregate(max_tasks=Max('tasks_number'))
        if highest_number["max_tasks"] is None:
            highest_number = 1
        else:
            highest_number = highest_number["max_tasks"] + 1
        
        mutable_querydict = request.data.copy()
        mutable_querydict["tasks_number"] = highest_number

        print(mutable_querydict)
        serializer = Taskapi(data=mutable_querydict, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.error_messages)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskQuerysetMixin:
    def get_queryset(self):
        return Tasks.objects.all()


class ListTasks(TaskQuerysetMixin, generics.ListAPIView):
    serializer_class= Taskapi


class TaskDeleteView(TaskQuerysetMixin, generics.DestroyAPIView):
    serializer_class = Taskapi

    def delete(self, request, *args, **kwargs):
        name = self.kwargs.get('name')
        try:
            instance = self.get_queryset().get(name=name)
            deleted_number = instance.tasks_number
            self.perform_destroy(instance)
            remaining_books = Tasks.objects.filter(tasks_number__gt=deleted_number)
            remaining_books.update(tasks_number=F('tasks_number') - 1)

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Tasks.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        


class TaskUpdateView(TaskQuerysetMixin, generics.UpdateAPIView):
    serializer_class = Taskapi

    def update(self, request, *args, **kwargs):
        name = self.kwargs.get('name')  # Get the 'pk' captured from URL
        try:
            instance = self.get_queryset().get(name=name)
            print(instance, "first")
            serializer = self.get_serializer(instance, data=request.data, partial=True, context={'request':request})
            print(serializer.error_messages, "second")
            print(request.data, "third")
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Tasks.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)



class TaskSearchView(TaskQuerysetMixin,generics.ListAPIView):
    serializer_class = Taskapi

    def get_queryset(self):
        queryset = super().get_queryset()
        search_param = self.request.query_params.get('q', None)        
        print(search_param)

        if search_param:
                name_filter = Q(name__icontains=search_param)
                status_filter = Q(status__icontains=search_param)
                contributors_filter = Q(contributors__icontains=search_param)

                tasks_number_filter = Q()
                try:
                    search_param_as_number = int(search_param)
                    tasks_number_filter = Q(tasks_number=search_param_as_number)
                except ValueError:
                    pass 

                queryset = queryset.filter(
                    name_filter | status_filter | contributors_filter | tasks_number_filter
                )

            
        return queryset 

