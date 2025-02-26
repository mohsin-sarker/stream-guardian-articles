import os
import requests
import json
import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from pprint import pprint


def lambda_handler(event, context):
    logger = logging.getLogger('guardian articles logger')
    logger.info('Guardian article has been invoked!')



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
    # 
    secret_name = os.environ.get('SECRET_NAME')
    guardian_api_key = get_guardian_api_key(secret_name)
    search_url = 'https://content.guardianapis.com/search'
    
    params = {
        "q": search_term,
        "from-date": date_from,
        "api-key": guardian_api_key,
        "page_size": 10
    }
    
    response = requests.get(search_url, params=params)
    response.raise_for_status()
    data = response.json()
    
    articles = [article for article in data['response']['results']]
    return articles



def send_to_sqs(articles):
    queue_url = os.environ.get('SQS_QUEUE_URL')
    sqs_client = boto3.client('sqs')
    
    for article in articles:
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(article)
        )
        print(response['MessageId'])

