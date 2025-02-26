import pytest
import boto3
import json
import os
from moto import mock_aws
from unittest.mock import Mock, patch
from src.lambda_handler import get_guardian_api_key



@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"
    

@pytest.fixture(scope='function')
def sm_client(aws_credentials):
    """
    Return a Secret Manager Client as sm_client
    """
    with mock_aws():
        yield boto3.client('secretsmanager', region_name='eu-west-2')
        

@pytest.fixture(scope='function')
def create_secret(sm_client):
    """
    This function will create secret using sm_client

    Args:
        sm_client: uses sm_client to create a test secret
    """
    secret_name = 'GuardianAPIKey'
    secret_value = {'GUARDIAN_API_KEY': '93b56eed745en5-5851-4501-a953jd50'}
    
    sm_client.create_secret(
        Name=secret_name,
        SecretString=json.dumps(secret_value)
    )
    return secret_name


class TestSecretsManager:
    
    @pytest.mark.it('Funtion will return secret value from AWS Secret Manager')
    def test_get_guardian_api_key_from_secret_manager(self, create_secret):
        """Test function retrieve secret from AWS Secret Manager successfully"""
        # Arrange
        secret_name = create_secret
        
        # Act
        result = get_guardian_api_key(secret_name)
        
        # Assert
        assert result is not None
        assert result['GUARDIAN_API_KEY'] == '93b56eed745en5-5851-4501-a953jd50'
     
        
    @pytest.mark.it('Function will return ClientError')
    def test_get_guardian_api_key_returns_secret_not_found(self, create_secret):
        """Test function retrieve no secret found in Secret Manager"""
        # Arrange
        secret_name = 'Another_GuardianAPIKey'
        
        # Act
        result = get_guardian_api_key(secret_name)
        
        # Assert
        assert result == 'There has been Client Error: ResourceNotFound'