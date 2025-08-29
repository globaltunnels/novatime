import os
import sys
import django
from django.conf import settings

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

# Common fixtures and configurations for tests
import pytest
from django.contrib.auth import get_user_model

@pytest.fixture
def user_model():
    return get_user_model()

@pytest.fixture
def test_user(db, user_model):
    return user_model.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )