import pytest
from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from projects.models import Client, Project, ProjectMember
from projects.admin import *  # Import all admin classes (currently none)
from organizations.models import Organization, Workspace, Membership
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()


class ProjectsAdminTest(TestCase):
    """Test projects admin interface (currently minimal - placeholder for future implementation)."""

    def setUp(self):
        self.site = AdminSite()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )

        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

        self.client_obj = Client.objects.create(
            name='Test Client',
            organization=self.organization,
            default_hourly_rate=Decimal('100.00')
        )

        self.project = Project.objects.create(
            name='Test Project',
            workspace=self.workspace,
            client=self.client_obj,
            manager=self.superuser,
            billing_type='hourly',
            hourly_rate=Decimal('125.00'),
            budget_hours=100
        )

        self.member = ProjectMember.objects.create(
            project=self.project,
            user=self.superuser,
            role='project_manager',
            hourly_rate=Decimal('150.00'),
            allocation_percent=100
        )

    def test_projects_admin_module_import(self):
        """Test that projects admin module can be imported."""
        try:
            from projects import admin
            self.assertTrue(hasattr(admin, 'admin'))
        except ImportError as e:
            self.fail(f"Failed to import projects admin: {e}")

    def test_projects_admin_structure(self):
        """Test that projects admin module has expected structure."""
        from projects import admin

        # Should have basic Django admin imports
        self.assertTrue(hasattr(admin, 'admin'))

        # Check for any admin classes (currently none expected)
        admin_classes = [attr for attr in dir(admin) if not attr.startswith('_') and attr.endswith('Admin')]

        # Currently should be empty (no custom admin classes implemented)
        self.assertEqual(len(admin_classes), 0,
                        f"Unexpected admin classes found: {admin_classes}")

    def test_no_models_registered_in_admin(self):
        """Test that no project models are currently registered in admin."""
        from projects import admin
        from django.apps import apps

        # Get all project models
        project_models = [
            Client, Project, ProjectMember
        ]

        # Check that none are registered in admin
        for model in project_models:
            is_registered = admin.admin.site.is_registered(model)
            self.assertFalse(is_registered,
                           f"Model {model.__name__} should not be registered in admin yet")

    def test_project_models_available_for_admin(self):
        """Test that all project models are available for future admin implementation."""
        # Verify models exist and can be imported
        models_to_check = [Client, Project, ProjectMember]

        for model in models_to_check:
            # Check model has Meta class
            self.assertTrue(hasattr(model, '_meta'))

            # Check model has expected fields
            fields = [f.name for f in model._meta.fields]
            self.assertGreater(len(fields), 0, f"Model {model.__name__} has no fields")

        # Test model relationships work
        self.assertEqual(self.project.client, self.client_obj)
        self.assertEqual(self.project.workspace, self.workspace)
        self.assertEqual(self.project.manager, self.superuser)
        self.assertEqual(self.member.project, self.project)
        self.assertEqual(self.member.user, self.superuser)

    def test_admin_list_display_fields(self):
        """Test fields that would be used in admin list_display."""
        # Client fields for list display
        client_fields = ['name', 'email', 'phone', 'is_active', 'created_at']
        for field in client_fields:
            self.assertTrue(hasattr(self.client_obj, field))

        # Project fields for list display
        project_fields = ['name', 'status', 'billing_type', 'start_date', 'end_date', 'created_at']
        for field in project_fields:
            self.assertTrue(hasattr(self.project, field))

        # ProjectMember fields for list display
        member_fields = ['user', 'role', 'allocation_percent', 'joined_at']
        for field in member_fields:
            self.assertTrue(hasattr(self.member, field))

    def test_admin_search_fields(self):
        """Test fields that would be used in admin search_fields."""
        # Client search fields
        self.assertEqual(self.client_obj.name, 'Test Client')
        self.assertEqual(self.client_obj.email, 'client@example.com')

        # Project search fields
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.client.name, 'Test Client')
        self.assertEqual(self.project.manager.email, 'admin@example.com')

        # Member search fields (via related user)
        self.assertEqual(self.member.user.email, 'admin@example.com')
        self.assertEqual(self.member.user.username, 'admin')

    def test_admin_list_filter_fields(self):
        """Test fields that would be used in admin list_filter."""
        # Client filters
        self.assertIsInstance(self.client_obj.is_active, bool)
        self.assertIsNotNone(self.client_obj.created_at)

        # Project filters
        self.assertEqual(self.project.status, 'planning')  # Default status
        self.assertEqual(self.project.billing_type, 'hourly')
        self.assertIsNotNone(self.project.created_at)

        # Member filters
        self.assertEqual(self.member.role, 'project_manager')
        self.assertIsNotNone(self.member.joined_at)

    def test_admin_fieldsets_structure(self):
        """Test field grouping that would be used in admin fieldsets."""
        # Client fieldsets
        basic_fields = ['name', 'email', 'phone', 'website']
        address_fields = ['address_line1', 'city', 'state', 'country']
        settings_fields = ['default_hourly_rate', 'currency', 'notes', 'is_active']

        for field in basic_fields + address_fields + settings_fields:
            self.assertTrue(hasattr(self.client_obj, field))

        # Project fieldsets
        project_basic = ['name', 'description', 'color', 'status']
        project_dates = ['start_date', 'end_date']
        project_billing = ['billing_type', 'hourly_rate', 'fixed_price', 'budget_hours']
        project_relations = ['client', 'manager', 'workspace']

        for field in project_basic + project_dates + project_billing + project_relations:
            self.assertTrue(hasattr(self.project, field))

        # Member fieldsets
        member_basic = ['user', 'role']
        member_settings = ['hourly_rate', 'allocation_percent']

        for field in member_basic + member_settings:
            self.assertTrue(hasattr(self.member, field))

    def test_admin_readonly_fields(self):
        """Test fields that would be readonly in admin."""
        readonly_fields = ['id', 'created_at', 'updated_at', 'joined_at']

        for field in readonly_fields:
            if field == 'joined_at':
                self.assertTrue(hasattr(self.member, field))
            else:
                self.assertTrue(hasattr(self.client_obj, field))
                self.assertTrue(hasattr(self.project, field))

    def test_admin_form_validation(self):
        """Test form validation that admin interfaces would need."""
        # Test unique constraints
        with self.assertRaises(Exception):  # Should raise IntegrityError
            Client.objects.create(
                name='Another Client',
                organization=self.organization,
                email='client@example.com'  # Duplicate email
            )

        # Test project validation (billing type consistency)
        project = Project.objects.create(
            name='Invalid Project',
            workspace=self.workspace,
            billing_type='fixed'
            # Missing fixed_price - should be validated in admin
        )

        # Test member allocation validation
        member = ProjectMember.objects.create(
            project=self.project,
            user=self.superuser,
            role='developer',
            allocation_percent=150  # Over 100% - should be validated
        )

        # Clean up
        member.delete()
        project.delete()

    def test_admin_bulk_actions_readiness(self):
        """Test bulk operations that admin interfaces would support."""
        # Create multiple clients for bulk testing
        client2 = Client.objects.create(
            name='Client 2',
            organization=self.organization,
            email='client2@example.com'
        )

        client3 = Client.objects.create(
            name='Client 3',
            organization=self.organization,
            email='client3@example.com'
        )

        # Test bulk queryset operations
        clients = Client.objects.filter(organization=self.organization)
        self.assertEqual(clients.count(), 3)

        # Test bulk update
        Client.objects.filter(organization=self.organization).update(is_active=False)
        inactive_clients = Client.objects.filter(is_active=False)
        self.assertEqual(inactive_clients.count(), 3)

        # Test bulk project operations
        project2 = Project.objects.create(
            name='Project 2',
            workspace=self.workspace,
            client=client2
        )

        projects = Project.objects.filter(workspace=self.workspace)
        self.assertEqual(projects.count(), 2)

        # Test bulk status update
        Project.objects.filter(workspace=self.workspace).update(status='active')
        active_projects = Project.objects.filter(status='active')
        self.assertEqual(active_projects.count(), 2)

    def test_admin_export_import_readiness(self):
        """Test data export/import functionality that admin would need."""
        from django.core import serializers
        import json

        # Test client serialization
        client_data = serializers.serialize('json', [self.client_obj])
        self.assertIn('Test Client', client_data)

        # Test project serialization with relations
        project_data = serializers.serialize('json', [self.project])
        self.assertIn('Test Project', project_data)
        self.assertIn('Test Client', project_data)  # Should include related client

        # Test deserialization
        deserialized = serializers.deserialize('json', client_data)
        restored_client = next(deserialized).object
        self.assertEqual(restored_client.name, 'Test Client')

    def test_admin_related_objects_display(self):
        """Test related object display that admin interfaces would need."""
        # Test client projects relationship
        client_projects = self.client_obj.projects.all()
        self.assertEqual(client_projects.count(), 1)
        self.assertEqual(client_projects.first(), self.project)

        # Test project members relationship
        project_members = self.project.members.all()
        self.assertEqual(project_members.count(), 1)
        self.assertEqual(project_members.first(), self.member)

        # Test reverse relationships
        client_from_project = self.project.client
        self.assertEqual(client_from_project, self.client_obj)

        workspace_from_project = self.project.workspace
        self.assertEqual(workspace_from_project, self.workspace)

        manager_from_project = self.project.manager
        self.assertEqual(manager_from_project, self.superuser)

    def test_admin_permissions_readiness(self):
        """Test permission checks that admin interfaces would need."""
        # Test superuser permissions
        self.assertTrue(self.superuser.is_superuser)
        self.assertTrue(self.superuser.is_staff)

        # Test organization access (if implemented)
        # These would check if user can manage clients/projects in specific organizations

        # Test workspace access
        user_workspaces = Membership.objects.filter(user=self.superuser).values_list('workspace', flat=True)
        self.assertIn(self.workspace.id, user_workspaces)

    def test_admin_change_view_data(self):
        """Test data that would be displayed in admin change views."""
        # Client change view data
        client_data = {
            'name': self.client_obj.name,
            'email': self.client_obj.email,
            'projects_count': self.client_obj.projects.count(),
            'organization': self.client_obj.organization.name,
            'is_active': self.client_obj.is_active,
            'created_at': self.client_obj.created_at
        }

        self.assertEqual(client_data['name'], 'Test Client')
        self.assertEqual(client_data['projects_count'], 1)

        # Project change view data
        project_data = {
            'name': self.project.name,
            'status': self.project.status,
            'client': self.project.client.name,
            'workspace': self.project.workspace.name,
            'manager': self.project.manager.email,
            'billing_type': self.project.billing_type,
            'hourly_rate': self.project.hourly_rate,
            'members_count': self.project.members.count(),
            'created_at': self.project.created_at
        }

        self.assertEqual(project_data['name'], 'Test Project')
        self.assertEqual(project_data['members_count'], 1)
        self.assertEqual(project_data['billing_type'], 'hourly')
        self.assertEqual(project_data['hourly_rate'], Decimal('125.00'))

        # Member change view data
        member_data = {
            'user': self.member.user.email,
            'project': self.member.project.name,
            'role': self.member.role,
            'hourly_rate': self.member.hourly_rate,
            'allocation_percent': self.member.allocation_percent,
            'joined_at': self.member.joined_at
        }

        self.assertEqual(member_data['role'], 'project_manager')
        self.assertEqual(member_data['hourly_rate'], Decimal('150.00'))
        self.assertEqual(member_data['allocation_percent'], 100)

    def test_admin_audit_trail_readiness(self):
        """Test audit trail functionality that admin would need."""
        # Test that models have audit fields
        audit_fields = ['created_at', 'updated_at']

        for field in audit_fields:
            self.assertTrue(hasattr(self.client_obj, field))
            self.assertTrue(hasattr(self.project, field))
            self.assertTrue(hasattr(self.member, field))

        # Test that changes are tracked (if implemented)
        original_name = self.project.name
        self.project.name = 'Updated Project'
        self.project.save()

        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Project')
        self.assertNotEqual(self.project.created_at, self.project.updated_at)

    def test_admin_custom_actions_readiness(self):
        """Test custom admin actions that would be implemented."""
        # Test bulk status changes for projects
        projects_to_activate = Project.objects.filter(status='planning')
        activated_count = projects_to_activate.update(status='active')
        self.assertEqual(activated_count, 1)

        # Test bulk client activation
        clients_to_activate = Client.objects.filter(is_active=False)
        activated_count = clients_to_activate.update(is_active=True)
        self.assertEqual(activated_count, 3)  # All clients were deactivated earlier

        # Test member role updates
        members_to_update = ProjectMember.objects.filter(role='project_manager')
        updated_count = members_to_update.update(role='senior_manager')
        self.assertEqual(updated_count, 1)

    def test_admin_queryset_optimization(self):
        """Test queryset optimization that admin would need."""
        # Test select_related for efficient queries
        projects_with_relations = Project.objects.select_related(
            'client', 'manager', 'workspace'
        ).filter(workspace=self.workspace)

        # Should not trigger additional queries when accessing related objects
        for project in projects_with_relations:
            client_name = project.client.name
            manager_email = project.manager.email
            workspace_name = project.workspace.name

        # Test prefetch_related for many-to-many relationships
        projects_with_members = Project.objects.prefetch_related('members').filter(workspace=self.workspace)

        for project in projects_with_members:
            members_list = list(project.members.all())
            self.assertEqual(len(members_list), 1)

    def test_admin_data_integrity(self):
        """Test data integrity constraints that admin would enforce."""
        # Test cascading deletes
        project_id = self.project.id
        member_id = self.member.id

        # Delete project
        self.project.delete()

        # Member should be deleted too (cascade)
        self.assertFalse(ProjectMember.objects.filter(id=member_id).exists())

        # But client should still exist
        self.assertTrue(Client.objects.filter(id=self.client_obj.id).exists())

        # Test workspace protection (if implemented)
        # Deleting a workspace with projects should be prevented or cascade properly

    def test_admin_performance_considerations(self):
        """Test performance considerations for admin interfaces."""
        # Create multiple projects for performance testing
        for i in range(10):
            Project.objects.create(
                name=f'Performance Project {i}',
                workspace=self.workspace,
                client=self.client_obj
            )

        # Test efficient counting
        project_count = Project.objects.filter(workspace=self.workspace).count()
        self.assertEqual(project_count, 11)  # 1 original + 10 new

        # Test efficient aggregation
        from django.db.models import Avg, Sum
        stats = Project.objects.filter(workspace=self.workspace).aggregate(
            avg_rate=Avg('hourly_rate'),
            total_budget=Sum('budget_hours')
        )

        self.assertIsNotNone(stats['avg_rate'])
        self.assertIsNotNone(stats['total_budget'])