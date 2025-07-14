import pytest
import pickle
import zlib
from unittest.mock import Mock, patch, MagicMock
from src.memory.redis import store_messages_in_redis, read_messages_from_redis, redis_client


class TestRedisOperations:
    
    @patch('src.memory.redis.redis_client')
    def test_store_messages_in_redis_default_ttl(self, mock_redis):
        """Test storing messages with default TTL"""
        message = {"user": "test", "content": "hello"}
        key = "test_key"
        
        store_messages_in_redis(key, message)
        
        expected_key = f"msg_{key}"
        serialized_data = pickle.dumps(message)
        compressed_data = zlib.compress(serialized_data)
        
        mock_redis.setex.assert_called_once_with(expected_key, 43200, compressed_data)
    
    @patch('src.memory.redis.redis_client')
    def test_store_messages_in_redis_custom_ttl(self, mock_redis):
        """Test storing messages with custom TTL"""
        message = {"user": "test", "content": "hello"}
        key = "test_key"
        custom_ttl = 3600
        
        store_messages_in_redis(key, message, custom_ttl)
        
        expected_key = f"msg_{key}"
        serialized_data = pickle.dumps(message)
        compressed_data = zlib.compress(serialized_data)
        
        mock_redis.setex.assert_called_once_with(expected_key, custom_ttl, compressed_data)
    
    @patch('src.memory.redis.redis_client')
    def test_read_messages_from_redis_key_exists(self, mock_redis):
        """Test reading messages when key exists"""
        message = {"user": "test", "content": "hello"}
        key = "test_key"
        
        serialized_data = pickle.dumps(message)
        compressed_data = zlib.compress(serialized_data)
        mock_redis.get.return_value = compressed_data
        
        result = read_messages_from_redis(key)
        
        expected_key = f"msg_{key}"
        mock_redis.get.assert_called_once_with(expected_key)
        assert result == message
    
    @patch('src.memory.redis.redis_client')
    def test_read_messages_from_redis_key_not_exists(self, mock_redis):
        """Test reading messages when key doesn't exist"""
        key = "nonexistent_key"
        mock_redis.get.return_value = None
        
        result = read_messages_from_redis(key)
        
        expected_key = f"msg_{key}"
        mock_redis.get.assert_called_once_with(expected_key)
        assert result == []
    
    @patch('src.memory.redis.redis_client')
    def test_store_and_read_complex_message(self, mock_redis):
        """Test storing and reading complex nested message"""
        complex_message = {
            "session_id": "123",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "metadata": {"timestamp": "2024-01-01", "user_id": 456}
        }
        key = "complex_key"
        
        # Test store
        store_messages_in_redis(key, complex_message)
        
        expected_key = f"msg_{key}"
        serialized_data = pickle.dumps(complex_message)
        compressed_data = zlib.compress(serialized_data)
        mock_redis.setex.assert_called_once_with(expected_key, 43200, compressed_data)
        
        # Test read
        mock_redis.get.return_value = compressed_data
        result = read_messages_from_redis(key)
        
        assert result == complex_message
    
    @patch('src.memory.redis.redis_client')
    def test_store_empty_message(self, mock_redis):
        """Test storing empty message"""
        message = {}
        key = "empty_key"
        
        store_messages_in_redis(key, message)
        
        expected_key = f"msg_{key}"
        serialized_data = pickle.dumps(message)
        compressed_data = zlib.compress(serialized_data)
        
        mock_redis.setex.assert_called_once_with(expected_key, 43200, compressed_data)
    
    @patch('src.memory.redis.redis_client')
    def test_store_list_message(self, mock_redis):
        """Test storing list as message"""
        message = ["item1", "item2", "item3"]
        key = "list_key"
        
        store_messages_in_redis(key, message)
        
        expected_key = f"msg_{key}"
        serialized_data = pickle.dumps(message)
        compressed_data = zlib.compress(serialized_data)
        
        mock_redis.setex.assert_called_once_with(expected_key, 43200, compressed_data)