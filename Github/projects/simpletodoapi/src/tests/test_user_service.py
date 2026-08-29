import unittest
from src.user_service import UserService

class TestUserService(unittest.TestCase):
    def setUp(self):
        self.user_service = UserService()

    def test_create_user(self):
        user_data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        result = self.user_service.create_user(user_data)
        self.assertIsNotNone(result)

    def test_get_user(self):
        user_data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        self.user_service.create_user(user_data)
        result = self.user_service.get_user('testuser')
        self.assertIsNotNone(result)

    def test_update_user(self):
        user_data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        self.user_service.create_user(user_data)
        updated_data = {
            'username': 'testuser',
            'password': 'newpassword'
        }
        result = self.user_service.update_user('testuser', updated_data)
        self.assertIsNotNone(result)

    def test_delete_user(self):
        user_data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        self.user_service.create_user(user_data)
        result = self.user_service.delete_user('testuser')
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()