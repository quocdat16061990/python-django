import os

os.makedirs('tasks/templates/tasks', exist_ok=True)

# ---- tasks/models.py ----
with open('tasks/models.py', 'w', encoding='utf-8') as f:
    f.write("""from django.db import models


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Thap'),
        ('medium', 'Trung binh'),
        ('high', 'Cao'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
""")

# ---- tasks/views.py ----
with open('tasks/views.py', 'w', encoding='utf-8') as f:
    f.write("""from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Task


def index(request):
    tasks = Task.objects.all()
    total = tasks.count()
    completed = tasks.filter(completed=True).count()
    return render(request, 'tasks/index.html', {
        'tasks': tasks,
        'total': total,
        'completed': completed,
        'pending': total - completed,
    })


@require_POST
def add_task(request):
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()
    priority = request.POST.get('priority', 'medium')
    if title:
        task = Task.objects.create(title=title, description=description, priority=priority)
        return JsonResponse({
            'success': True,
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'completed': task.completed,
            'created_at': task.created_at.strftime('%d/%m/%Y %H:%M'),
        })
    return JsonResponse({'success': False}, status=400)


@require_POST
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.completed = not task.completed
    task.save()
    return JsonResponse({'success': True, 'completed': task.completed})


@require_POST
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.delete()
    return JsonResponse({'success': True})
""")

# ---- tasks/urls.py ----
with open('tasks/urls.py', 'w', encoding='utf-8') as f:
    f.write("""from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add_task, name='add_task'),
    path('toggle/<int:task_id>/', views.toggle_task, name='toggle_task'),
    path('delete/<int:task_id>/', views.delete_task, name='delete_task'),
]
""")

# ---- mysite/urls.py ----
with open('mysite/urls.py', 'w', encoding='utf-8') as f:
    f.write("""from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tasks.urls')),
]
""")

# ---- mysite/settings.py ----
with open('mysite/settings.py', 'w', encoding='utf-8') as f:
    f.write("""from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-demo-key-12345'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tasks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
""")

print('Python files written OK')
