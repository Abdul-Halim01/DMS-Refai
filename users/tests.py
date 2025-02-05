from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

class UserTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        
        # Create a superuser
        self.admin_user = self.User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create a regular user
        self.regular_user = self.User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )
        
        # Create a staff user with permissions
        self.staff_user = self.User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )

        """Test user creation and attri
    def test_user_creation(self):butes"""
        user = self.User.objects.get(username='user')
        self.assertEqual(user.email, 'user@example.com')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        
        admin = self.User.objects.get(username='admin')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_users_list_view(self):
        """Test user list view access permissions"""
        # Test unauthenticated access
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test regular user access
        self.client.login(username='user', password='userpass123')
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Test admin access
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_detail_view(self):
        """Test user detail view access"""
        user_id = self.regular_user.id
        
        # Test own profile access
        self.client.login(username='user', password='userpass123')
        response = self.client.get(reverse('user_detail', kwargs={'pk': user_id}))
        self.assertEqual(response.status_code, 200)
        
        # Test accessing other's profile
        other_user_id = self.staff_user.id
        response = self.client.get(reverse('user_detail', kwargs={'pk': other_user_id}))
        self.assertEqual(response.status_code, 403)

    def test_user_update(self):
        """Test user update functionality"""
        self.client.login(username='user', password='userpass123')
        user_id = self.regular_user.id
        
        update_data = {
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'User'
        }
        
        response = self.client.post(
            reverse('user_update', kwargs={'pk': user_id}),
            update_data
        )
        
        updated_user = self.User.objects.get(id=user_id)
        self.assertEqual(updated_user.email, 'updated@example.com')
        self.assertEqual(updated_user.first_name, 'Updated')

    def test_user_delete(self):
        """Test user deletion"""
        self.client.login(username='admin', password='adminpass123')
        user_to_delete = self.User.objects.create_user(
            username='delete_me',
            email='delete@example.com',
            password='deletepass123'
        )
        
        response = self.client.post(reverse('user_delete', kwargs={'pk': user_to_delete.id}))
        self.assertEqual(response.status_code, 302)  # Redirect after deletion
        
        # Verify user is deleted
        with self.assertRaises(self.User.DoesNotExist):
            self.User.objects.get(username='delete_me')

    def test_password_change(self):
        """Test password change functionality"""
        self.client.login(username='user', password='userpass123')
        
        password_change_data = {
            'old_password': 'userpass123',
            'new_password1': 'newuserpass123',
            'new_password2': 'newuserpass123'
        }
        
        response = self.client.post(
            reverse('change_password', kwargs={'user_id': self.regular_user.id}),
            password_change_data
        )
        
        # Verify can login with new password
        self.client.logout()
        login_successful = self.client.login(
            username='user',
            password='newuserpass123'
        )
        self.assertTrue(login_successful)

    def test_staff_permissions(self):
        """Test staff user permissions"""
        content_type = ContentType.objects.get_for_model(self.User)
        view_permission = Permission.objects.get(
            content_type=content_type,
            codename='view_user'
        )
        self.staff_user.user_permissions.add(view_permission)
        
        self.client.login(username='staff', password='staffpass123')
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_search(self):
        """Test user search functionality"""
        self.client.login(username='admin', password='adminpass123')
        
        # Create test users
        self.User.objects.create_user(username='test1', email='test1@example.com')
        self.User.objects.create_user(username='test2', email='test2@example.com')
        
        response = self.client.get(f"{reverse('user_list')}?search=test1")
        self.assertContains(response, 'test1@example.com')
        self.assertNotContains(response, 'test2@example.com')
