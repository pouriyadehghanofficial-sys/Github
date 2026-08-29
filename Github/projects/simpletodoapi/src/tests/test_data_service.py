import unittest
from src.data_service import DataService

class TestDataService(unittest.TestCase):
    def setUp(self):
        self.data_service = DataService()

    def test_create_data(self):
        data = {
            'user_id': 1,
            'data': 'testdata'
        }
        result = self.data_service.create_data(data)
        self.assertIsNotNone(result)

    def test_get_data(self):
        data = {
            'user_id': 1,
            'data': 'testdata'
        }
        self.data_service.create_data(data)
        result = self.data_service.get_data(1)
        self.assertIsNotNone(result)

    def test_update_data(self):
        data = {
            'user_id': 1,
            'data': 'testdata'
        }
        self.data_service.create_data(data)
        updated_data = {
            'user_id': 1,
            'data': 'updateddata'
        }
        result = self.data_service.update_data(1, updated_data)
        self.assertIsNotNone(result)

    def test_delete_data(self):
        data = {
            'user_id': 1,
            'data': 'testdata'
        }
        self.data_service.create_data(data)
        result = self.data_service.delete_data(1)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()