import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from timesheets.models import Timesheet, TimesheetEntry
from projects.models import Project

User = get_user_model()


class TimesheetViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.timesheet = Timesheet.objects.create(
            user=self.user,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=6),
            status='draft'
        )
        
    def test_get_timesheets_list(self):
        url = reverse('timesheet-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
    def test_get_timesheet_detail(self):
        url = reverse('timesheet-detail', kwargs={'pk': self.timesheet.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.timesheet.pk)
        
    def test_create_timesheet(self):
        url = reverse('timesheet-list')
        start_date = timezone.now().date() + timezone.timedelta(days=7)
        end_date = start_date + timezone.timedelta(days=6)
        
        data = {
            'start_date': start_date,
            'end_date': end_date,
            'status': 'draft'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Timesheet.objects.count(), 2)
        self.assertEqual(response.data['user'], self.user.id)


class ProjectViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.project = Project.objects.create(
            name='Test Project',
            slug='test-project',
            description='A test project',
            owner=self.user
        )
        
    def test_get_projects_list(self):
        url = reverse('project-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
    def test_get_project_detail(self):
        url = reverse('project-detail', kwargs={'pk': self.project.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.project.pk)
        
    def test_create_project(self):
        url = reverse('project-list')
        data = {
            'name': 'New Project',
            'slug': 'new-project',
            'description': 'A new test project',
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 2)
        self.assertEqual(response.data['owner'], self.user.id)