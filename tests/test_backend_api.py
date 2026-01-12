"""
Backend API Tests for Telegram Signal Monitor
Tests: Authentication, Health, Stats, Session, Channels, Signals endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://signal-watch-2.preview.emergentagent.com')

# Test credentials from requirements
ADMIN_USERNAME = "aliziyad"
ADMIN_PASSWORD = "tM23v8Mr!@#"


class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_check_returns_200(self):
        """Test health endpoint returns 200 and correct structure"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_login_with_valid_credentials(self):
        """Test login with correct admin credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "token" in data
        assert len(data["token"]) > 0
        assert data["username"] == ADMIN_USERNAME
        assert "expires_in" in data
        assert data["expires_in"] == 86400  # 24 hours in seconds
    
    def test_login_with_invalid_credentials(self):
        """Test login with wrong credentials returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "wronguser", "password": "wrongpass"}
        )
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Invalid credentials"
    
    def test_login_with_wrong_password(self):
        """Test login with correct username but wrong password"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": ADMIN_USERNAME, "password": "wrongpassword"}
        )
        assert response.status_code == 401
    
    def test_login_with_empty_credentials(self):
        """Test login with empty credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "", "password": ""}
        )
        assert response.status_code == 401
    
    def test_verify_token_valid(self):
        """Test token verification with valid token"""
        # First login to get token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        token = login_response.json()["token"]
        
        # Verify token
        response = requests.post(
            f"{BASE_URL}/api/auth/verify",
            params={"token": token}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] == True
        assert data["username"] == ADMIN_USERNAME
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/verify",
            params={"token": "invalid-token-here"}
        )
        assert response.status_code == 401


class TestStatsEndpoint:
    """Dashboard statistics endpoint tests"""
    
    def test_get_stats_returns_200(self):
        """Test stats endpoint returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        # Verify all required fields exist
        assert "total_signals" in data
        assert "sent_signals" in data
        assert "pending_signals" in data
        assert "failed_signals" in data
        assert "active_channels" in data
        assert "total_channels" in data
        assert "signals_today" in data
        assert "success_rate" in data
        assert "is_monitoring" in data
        assert "session_connected" in data
        
        # Verify data types
        assert isinstance(data["total_signals"], int)
        assert isinstance(data["sent_signals"], int)
        assert isinstance(data["pending_signals"], int)
        assert isinstance(data["failed_signals"], int)
        assert isinstance(data["active_channels"], int)
        assert isinstance(data["total_channels"], int)
        assert isinstance(data["signals_today"], int)
        assert isinstance(data["success_rate"], (int, float))
        assert isinstance(data["is_monitoring"], bool)
        assert isinstance(data["session_connected"], bool)


class TestSessionEndpoints:
    """Telegram session endpoint tests"""
    
    def test_get_session_status(self):
        """Test session status endpoint"""
        response = requests.get(f"{BASE_URL}/api/session/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "is_connected" in data
        assert isinstance(data["is_connected"], bool)


class TestChannelsEndpoints:
    """Channels endpoint tests"""
    
    def test_get_monitored_channels(self):
        """Test get monitored channels endpoint"""
        response = requests.get(f"{BASE_URL}/api/channels")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # If there are channels, verify structure
        if len(data) > 0:
            channel = data[0]
            assert "channel_id" in channel
            assert "channel_name" in channel
            assert "is_active" in channel


class TestSignalsEndpoints:
    """Signals endpoint tests"""
    
    def test_get_signals_with_pagination(self):
        """Test signals endpoint with pagination"""
        response = requests.get(f"{BASE_URL}/api/signals?page=1&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "signals" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data
        
        assert isinstance(data["signals"], list)
        assert data["page"] == 1
        assert data["limit"] == 10
    
    def test_get_signals_with_status_filter(self):
        """Test signals endpoint with status filter"""
        response = requests.get(f"{BASE_URL}/api/signals?status=sent")
        assert response.status_code == 200
        
        data = response.json()
        assert "signals" in data


class TestMonitoringEndpoints:
    """Monitoring endpoint tests"""
    
    def test_get_monitoring_status(self):
        """Test monitoring status endpoint"""
        response = requests.get(f"{BASE_URL}/api/monitoring/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "is_monitoring" in data
        assert "is_connected" in data
        assert "monitored_channels" in data
        
        assert isinstance(data["is_monitoring"], bool)
        assert isinstance(data["is_connected"], bool)
        assert isinstance(data["monitored_channels"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
