from django.test import TestCase

# Create your tests here.
from datetime import date

from rest_framework.test import APITestCase
from rest_framework import status

from task.models import Tasks


class CreateTask(APITestCase):

    def test_create_task_successfully(self):
        payload = {
            "title": "Test task",
            "description": "Testing creation",
            "expires": "2026-06-01"
        }

        response = self.client.post(
            "/api/tasks/create/",
            payload,
            format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Tasks.objects.count(), 1)


    def test_invalid_expiry_date_returns_400(self):
        payload = {
            "title": "Bad task",
            "description": "Bad expiry",
            "expires": "01-06-2026"
        }

        response = self.client.post(
            "/api/tasks/create/",
            payload,
            format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expires", response.data)

    def test_first_task_number_starts_at_one(self):
        payload = {
            "title": "First task",
            "description": "Testing numbering",
            "expires": "2026-06-01"
        }

        response = self.client.post(
            "/api/tasks/create/",
            payload,
            format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        task = Tasks.objects.first()

        self.assertEqual(task.tasks_number, 1)

    def test_second_task_increments_task_number(self):
        Tasks.objects.create(
            title="Existing",
            tasks_number=1
        )

        payload = {
            "title": "New task",
            "description": "Testing increment",
            "expires": "2026-06-01"
        }

        response = self.client.post(
            "/api/tasks/create/",
            payload,
            format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        newest_task = Tasks.objects.order_by("-id").first()

        self.assertEqual(newest_task.tasks_number, 2)
