from django.urls import path
from .views import CreateTask,ListTasks,TaskDeleteView,TaskUpdateView, TaskSearchView, TaskFinish

urlpatterns = [
    path('create/', CreateTask.as_view(), name='tasks_create'),  
    path('delete/<str:name>/', TaskDeleteView.as_view(), name='tasks_delete'),  
    path('update/<str:name>/', TaskUpdateView.as_view(), name='tasks_update'),  
    path('finish-tasks/<str:name>/', TaskFinish.as_view(), name='tasks_finish'),  
    path('list/', ListTasks.as_view(), name='tasks_lists'),  
    path('search/', TaskSearchView.as_view(), name='tasks_search'),  
]