import os
import requests
import json
import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from pprint import pprint


# Intialise logging to log in info to cloudwatch
logger = logging.getLogger('Guardian_articles_lambda_logger')
logger.setLevel(logging.INFO)


# Get search_term and date_from from environment variables 
get_search_term = os.environ.get('machine learning')
date_from = os.environ.get('2025-01-31')

class GuardianAPIError(Exception):
    pass

class NoArticlesFoundError(Exception):
    pass


def lambda_handler(event, context):
    logger.info('Function has been invoked!')



def get_guardian_api_key(secret_name, region='eu-west-2'):
    """
    Fetch Guardian-API-Key from secret manager.

    Args:
        secret_name (str): The name of the secret.
        region (str, optional): This AWS region where the secret is stored. Defaults to 'eu-west-2'.
    
    Return:
        String: This function will return a secret value.
    """
    # Create a secret manager client
    client = boto3.client('secretsmanager', region_name=region)
    
    # Try to get secret object (JSON Object) from secret manager
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret_str = response['SecretString']
        
        try: 
            return json.loads(secret_str)
        
        except json.JSONDecodeError: 
            return secret_str

    # If secret not found or permission denied issues
    except ClientError:
        return f'There has been Client Error: ResourceNotFound'
    
    # If there is a AWS Credential issue
    except NoCredentialsError:
        return f'No credentials has been found.'
    
    # For all other exceptions
    except Exception as e:
        return f'There has been an unexpected error: {e}'



def extract_guardian_articles(search_term, date_from=None):
    """
    Retrieves articles from the Guardian API based on the search term and date.

    Args:
        search_term: The search term for articles.
        date_from: Optional start date for the search (YYYY-MM-DD).

    Returns:
        A list of dictionaries, where each dictionary represents an article.
        Returns an empty list if there's an issue with the API call.
    """
    # Search Term validation check
    if not isinstance(search_term, str) or not search_term.strip():
        error_message = 'Invalid search_term or it must not be empty!'
        logger.error(error_message)
        raise ValueError(error_message)

    # Retrieve secret name and check validation
    secret_name = os.environ.get('SECRET_NAME')
    
    if not secret_name:
        error_message = 'It must not be an empty secret name!'
        raise GuardianAPIError(error_message)

    # Get the API KEY and define API endpoint
    guardian_api_key = get_guardian_api_key(secret_name)
    if not guardian_api_key:
        error_message = 'Unable to fetch API KEY, check secret_name!'
        raise GuardianAPIError(error_message)
    
    search_url = 'https://content.guardianapis.com/search'

    params = {
        "q": search_term,
        "from-date": date_from,
        "api-key": guardian_api_key,
        "page_size": 10,
        "order-by": "newest"
    }
    
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'response' not in data or 'results' not in data['response']:
            error_message = 'Unexcepted API response'
            logger.error(error_message)
            raise GuardianAPIError(error_message)
        
        articles = [article for article in data['response']['results']]
        if not articles:
            error_message = f'No articles found with the Search Term: {search_term}'
            logger.warning(error_message)
            return []
            
        return articles
    
    except requests.exceptions.Timeout as Timeout_error:
        error_message = f'Raise Timeout Error: {Timeout_error}'
    
    except requests.exceptions.ConnectionError as conn_err:
        error_message = f'Connection Error: {conn_err}'
    
    except Exception as e:
        error_message = f'Exception: {e}'
        
    logger.error(error_message)
    raise GuardianAPIError(error_message)



def transform_articles(get_search_term):
    try:
        articles = extract_guardian_articles(get_search_term)
    except:
        error = 'Failed to fetch articles'
        logger.error(error)
        return []
    
    if not articles:
        warning = 'No articles have been found!'
        logger.warning(warning)
        return []
    
    filtered_articles = [
        {
            "webPublicationDate": article.get("webPublicationDate"),
            "webTitle": article.get("webTitle"),
            "webUrl": article.get("webUrl", "#")
        }
        for article in articles if article.get("webUrl")
    ]
    return filtered_articles



def send_to_sqs(articles):
    queue_url = os.environ.get('SQS_QUEUE_URL')
    sqs_client = boto3.client('sqs')
    
    for article in articles:
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(article)
        )
        print(response['MessageId'])


