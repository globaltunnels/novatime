import os
import sys
import django
from django.conf import settings

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

def test_database_connection():
    """
    Test the database connection by performing a simple query
    """
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"Database connection successful!")
            print(f"PostgreSQL version: {version[0]}")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing database connection...")
    success = test_database_connection()
    if success:
        print("✅ Database connection test passed!")
    else:
        print("❌ Database connection test failed!")
        sys.exit(1)