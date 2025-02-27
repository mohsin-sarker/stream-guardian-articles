import pytest
import boto3
import json
import os
import logging
from moto import mock_aws
from unittest.mock import patch, MagicMock
from src.lambda_handler import (
                                GuardianAPIError,
                                get_guardian_api_key,
                                extract_guardian_articles,
                                transform_articles
                            )



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


@pytest.fixture(scope='function')
def mock_guardian_articles():
    mock_data = {
        "response" : {
            "results" : [
                {
                    "id": "commentisfree/2025/feb/26/what-i-have-learned-in-my-filthy-bloody-sisyphean-quest-to-tame-my-garden",
                    "type": "article",
                    "sectionId": "commentisfree",
                    "sectionName": "Opinion",
                    "webPublicationDate": "2025-02-26T15:29:36Z",
                    "webTitle": "What I have learned in my filthy, bloody, sisyphean quest to tame my garden | Adrian Chiles",
                    "webUrl": "https://www.theguardian.com/commentisfree/2025/feb/26/what-i-have-learned-in-my-filthy-bloody-sisyphean-quest-to-tame-my-garden",
                    "apiUrl": "https://content.guardianapis.com/commentisfree/2025/feb/26/what-i-have-learned-in-my-filthy-bloody-sisyphean-quest-to-tame-my-garden",
                    "isHosted": False,
                    "pillarId": "pillar/opinion",
                    "pillarName": "Opinion"
                },
                {
                    "id": "fashion/2025/feb/26/my-big-red-carpet-makeover-what-i-learned-from-the-stylists-to-the-stars",
                    "type": "article",
                    "sectionId": "fashion",
                    "sectionName": "Fashion",
                    "webPublicationDate": "2025-02-26T05:00:03Z",
                    "webTitle": "My big red carpet makeover: what I learned from the stylists to the stars",
                    "webUrl": "https://www.theguardian.com/fashion/2025/feb/26/my-big-red-carpet-makeover-what-i-learned-from-the-stylists-to-the-stars",
                    "apiUrl": "https://content.guardianapis.com/fashion/2025/feb/26/my-big-red-carpet-makeover-what-i-learned-from-the-stylists-to-the-stars",
                    "isHosted": False,
                    "pillarId": "pillar/lifestyle",
                    "pillarName": "Lifestyle"
                }
            ]
        }
    }
    mock_response = MagicMock()
    mock_response.json.return_value = mock_data
    mock_response.status_code = 200
    
    return mock_response, mock_data['response']['results']


@pytest.fixture(scope='function')
def mock_empty_articles():
    mock_data = {
        "response" : {
            "results" : []
        }
    }
    mock_response = MagicMock()
    mock_response.json.return_value = mock_data
    mock_response.status_code = 200
    
    return mock_response, mock_data['response']['results']


@pytest.fixture(scope='function')
def mock_extracted_articles():
    mock_articles = [
        {
            "webPublicationDate": "2023-11-21T11:11:31Z",
            "webTitle": "Who said what: using machine learning to correctly attribute quotes",
            "webUrl": "https://www.theguardian.com/info/2023/nov/21/who-said-what-using-machine-learning"
        },
        {
            "webPublicationDate": "2023-11-21T11:11:31Zyziur1234",
            'webTitle': 'Machine Learning Breakthrough',
            'webUrl': 'https://example.com/article1'
        }
    ]
    return mock_articles


@pytest.fixture(scope='function')
def mock_empty_extracted_articles():
    return []


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
        
        
class TestExtractGuardianArticles:
    
    @pytest.mark.it('Test returns value error if there is empty search term or invalid type.')
    def test_extract_guardian_articles_return_value_error(self):
        search_term = ''
        with pytest.raises(ValueError, match='Invalid search_term or it must not be empty!'):
            extract_guardian_articles(search_term)

    
    @pytest.mark.it('Test returns customed API Error if invalid secret name.') 
    def test_extract_guardian_articles_return_invalid_or_empty_secret_name(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(GuardianAPIError, match='It must not be an empty secret name!'):
                extract_guardian_articles('machine learning')
    
    
    @pytest.mark.it('Test returns API Error with correct secret name but no API KEY.')
    def test_extract_guardian_articles_return_api_error_with_correct_secret_name_but_no_api_key(self):
        with patch.dict(os.environ, {'SECRET_NAME': 'mock_secret_name'}):
            with patch('src.lambda_handler.get_guardian_api_key', return_value=None):
                with pytest.raises(GuardianAPIError, match='Unable to fetch API KEY, check secret_name!'):
                    extract_guardian_articles('machine learning')
                    
                    
    @pytest.mark.it('Test fetches data with valid API KEY.')
    def test_extract_guardian_articles_fetches_data_with_valid_api_key(self, mock_guardian_articles):
        # unpack mock response and expected data
        mock_response, expected_data = mock_guardian_articles
        with patch.dict(os.environ, {'SECRET_NAME': 'mock_secret_name'}):
            with patch('src.lambda_handler.get_guardian_api_key', return_value='valid_api_key'):
                with patch('requests.get', return_value=mock_response):
                    result = extract_guardian_articles('machine learning')
                    assert result == expected_data
                    assert isinstance(result, list)
    
    
    
    @pytest.mark.it('Test fetches an empty article list with valid API KEY if there are no data.')
    def test_extract_guardian_articles_fetches_empty_article_list_with_valid_api_key(self, mock_empty_articles):
        # unpack mock response and expected data
        mock_response, expected_data = mock_empty_articles
        
        with patch.dict(os.environ, {'SECRET_NAME': 'mock_secret_name'}):
            with patch('src.lambda_handler.get_guardian_api_key', return_value='valid_api_key'):
                with patch('requests.get', return_value=mock_response):
                        result = extract_guardian_articles('machine learning')
                        assert result == expected_data
                        assert len(result) == 0
                        

class TestTransformArticlesData:
    
    @pytest.mark.it('Test transform_articles function returns mock articles')
    def test_transform_articles_return_mock_articles(self, mock_extracted_articles):
        with patch('src.lambda_handler.extract_guardian_articles', return_value=mock_extracted_articles) as mock_articles:
            result = transform_articles("machine learning")
            
            expected = [[key for key, value in article.items()] for article in result]

            mock_articles.assert_called_once()
            for article in result:
                for key in expected[0]:
                    assert key in article
            assert result == mock_extracted_articles
            
            

    @pytest.mark.it('Test transform_articles function returns an empty list.')
    def test_transform_articles_function_returns_an_empty_list(self, mock_empty_extracted_articles):
         with patch('src.lambda_handler.extract_guardian_articles', return_value=mock_empty_extracted_articles):
             result = transform_articles("machine learning")
             assert result == []
    
    
    @pytest.mark.it('Test transform_articles function returns articles with expected key-values.')
    def test_transform_articles_returns_articles_with_expected_key_value_pairs(self, mock_extracted_articles):
        with patch('src.lambda_handler.extract_guardian_articles', return_value=mock_extracted_articles):
            result = transform_articles("machine learning")
            expected_keys = ["webPublicationDate", "webTitle", "webUrl"]
            for article in result:
                for key in expected_keys:
                    assert key in article