from django.test import TestCase, Client
from django.urls import reverse
from .models import Task


class TaskModelTest(TestCase):
    def setUp(self):
        self.task = Task.objects.create(
            title="Test task",
            description="Test description",
            priority="high",
        )

    def test_task_creation(self):
        self.assertEqual(self.task.title, "Test task")
        self.assertEqual(self.task.priority, "high")
        self.assertFalse(self.task.completed)

    def test_task_default_priority(self):
        task = Task.objects.create(title="Default priority")
        self.assertEqual(task.priority, "medium")

    def test_task_str(self):
        self.assertEqual(str(self.task), "Test task")


class TaskViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.task = Task.objects.create(
            title="Test task",
            description="Test description",
            priority="low",
        )

    def test_index_view(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DevOverflow")
        self.assertTemplateUsed(response, "tasks/index.html")

    def test_add_task(self):
        response = self.client.post(reverse("add_task"), {
            "title": "New task",
            "description": "New description",
            "priority": "high",
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["title"], "New task")

    def test_add_task_missing_title(self):
        response = self.client.post(reverse("add_task"), {"title": ""})
        self.assertEqual(response.status_code, 400)

    def test_toggle_task(self):
        response = self.client.post(reverse("toggle_task", args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["completed"])

        # Toggle back
        response = self.client.post(reverse("toggle_task", args=[self.task.id]))
        self.assertFalse(response.json()["completed"])

    def test_delete_task(self):
        response = self.client.post(reverse("delete_task", args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(Task.objects.count(), 0)


class DashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        Task.objects.create(title="Task 1", priority="high")
        Task.objects.create(title="Task 2", priority="medium")
        Task.objects.create(title="Task 3", priority="low", completed=True)

    def test_dashboard_view(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Task Dashboard")
        self.assertContains(response, "Tổng số")
        self.assertContains(response, "Đã hoàn thành")
        self.assertContains(response, "Đang chờ")
