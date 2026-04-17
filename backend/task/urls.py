from django.urls import path
from .views import CreateTask,ListTasks,AIChatView,AITaskActionView,TaskDeleteView,TaskUpdateView, TaskSearchView, TaskFinish

urlpatterns = [
    path('create/', CreateTask.as_view(), name='tasks_create'),  
    path('delete/<str:name>/', TaskDeleteView.as_view(), name='tasks_delete'),  
    path('update/<str:name>/', TaskUpdateView.as_view(), name='tasks_update'),  
    path('finish-tasks/<str:name>/', TaskFinish.as_view(), name='tasks_finish'),  
    path('list/', ListTasks.as_view(), name='tasks_lists'),  
    path('search/', TaskSearchView.as_view(), name='tasks_search'),  
    path('ai-chat/', AIChatView.as_view(), name='tasks_ai_chat'),  
    path('ai-analyze/', AITaskActionView.as_view(), name='tasks_ai_analyze'),  
]