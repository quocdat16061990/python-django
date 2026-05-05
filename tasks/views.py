from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Task
import requests


def dashboard(request):
    tasks = Task.objects.all()
    total = tasks.count()
    completed = tasks.filter(completed=True).count()
    pending = total - completed

    low_count = tasks.filter(priority='low').count()
    medium_count = tasks.filter(priority='medium').count()
    high_count = tasks.filter(priority='high').count()

    tasks_by_priority = [
        {'priority': 'Thấp', 'count': low_count, 'color': '#22c55e'},
        {'priority': 'Trung bình', 'count': medium_count, 'color': '#eab308'},
        {'priority': 'Cao', 'count': high_count, 'color': '#ef4444'},
    ]

    return render(request, 'tasks/dashboard.html', {
        'total_tasks': total,
        'completed_tasks': completed,
        'pending_tasks': pending,
        'tasks_by_priority': tasks_by_priority,
    })


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
@csrf_exempt
def register(request):
    """Xử lý đăng ký và gửi thông tin qua webhook"""
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()

    if not name or not email:
        return JsonResponse({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin!'}, status=400)

    # Webhook URL
    WEBHOOK_URL = "https://n8n.devoverflow.xyz/webhook/tranhuuquocdatcontract"

    # Tạo dữ liệu gửi đi
    payload = {
        "name": name,
        "email": email,
        "phone": phone or "Không có",
        "source": "Website Anh Lập Trình"
    }

    # Gửi đến webhook
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        print(f"Webhook Response: {response.status_code} - {response.text}")

        if response.status_code in [200, 201, 202]:
            return JsonResponse({
                'success': True,
                'message': 'Đăng ký thành công! Chúng tôi sẽ liên hệ sớm.'
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'Đăng ký thành công!'
            })
    except Exception as e:
        print(f"Error calling webhook: {e}")
        return JsonResponse({
            'success': True,
            'message': 'Đăng ký thành công!'
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
