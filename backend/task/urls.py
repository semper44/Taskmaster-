from django.urls import path
from .views import CreateTask,ListTasks,TaskDeleteView,TaskUpdateView, TaskSearchView

urlpatterns = [
    path('create/', CreateTask.as_view(), name='tasks_create'),  
    path('delete/<str:name>/', TaskDeleteView.as_view(), name='tasks_delete'),  
    path('update/<str:name>/', TaskUpdateView.as_view(), name='tasks_update'),  
    path('list/', ListTasks.as_view(), name='tasks_lists'),  
    path('search/', TaskSearchView.as_view(), name='tasks_search'),  
]