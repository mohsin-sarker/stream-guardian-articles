import os
import requests
import json
import boto3
import logging
import datetime
from bs4 import BeautifulSoup
from pprint import pprint
from botocore.exceptions import (
                                    ClientError,
                                    NoCredentialsError
                                )


# Intialise logging to log in info to cloudwatch
logger = logging.getLogger('Guardian_articles_lambda_logger')
logger.setLevel(logging.INFO)

 
# Get SEARCH_TERM and DATE_FROM (optional) from environment variables
# SEARCH_TERM is set to Lambda Environment Variable by terraform
get_search_term = os.environ.get('SEARCH_TERM')
date_from = os.environ.get('DATE_FROM')

class GuardianAPIError(Exception):
    pass

class NoArticlesFoundError(Exception):
    pass


def lambda_handler(event, context):
    """
    Function will retrieve all content returned by the API and post up to the ten most recent 
    items in JSON format onto the message broker with the ID "guardian_content". 
    """
    logger.info('Function has been invoked!')
    logger.info('Fetching Guardian Contents from Guardina API.....')
    
    bucket_name = 'guardian-articles-config-bucket'
    
    if not api_request_count(bucket_name):
        return {
            "status_code": 429,
            "message": "API Request calls has been reached for Today.",
            'success': False
        }
    
    articles = processed_guardian_articles(get_search_term)
    
    if not articles:
        warning = 'No articles found or unable to fetched !'
        logger.warning(warning)
        raise NoArticlesFoundError(warning)
    
    logger.info(f'Publishing {len(articles)} articles to SQS......')
    messageId = send_to_sqs(articles)
    return {
        'status_code': 200,
        'message': f'Successfylly processed and sent {len(articles)} articles to SQS.',
        'success': True
    }



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
    # Terraform should create SECRET_NAME environment variable
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



def processed_guardian_articles(get_search_term, date_from=None):
    """
    Get extracted data based on get_search_term and process them to publish on message queue.
    Get also content preview and add to publish contents.

    Args:
        get_search_term (str): search term should be a string.

    Returns:
        A list of Dictionary after processing raw data. Empty list if no articles.
    """
    try:
        articles = extract_guardian_articles(get_search_term, date_from=date_from)
    except:
        error = 'Failed to fetch articles'
        logger.error(error)
        return []
    
    if not articles:
        warning = 'No articles have been found!'
        logger.warning(warning)
        return []

    filtered_articles = []
    
    for article in articles:
        webUrl = article.get("webUrl")
        if not webUrl:
            continue
        
        try:
            content_preview = get_content_preview(webUrl)
            
        except Exception as e:
            warning = f'Failed to fetch content preview from the url {webUrl}: {e}'
            logger.warning(warning)
            content_preview = 'Content preview is not avaiable.'
        
        filtered_articles.append({
            "webPublicationDate": article.get("webPublicationDate"),
            "webTitle": article.get("webTitle"),
            "webUrl": webUrl,
            "content_preview": content_preview
        })
            
    return filtered_articles



def send_to_sqs(articles):
    """
        The function will accept a list of articles and publish it to AWS SQS.
        The SQS service deployment will be automated by Terraform and hold messages for 3 days.
        Once SQS will be deployed, QueueURL will be set on lambda environment variable.

    Args:
        articles (list): The articles should a list of dictionary
    """
    # Retrieve sqs_queue_url from lambda environment
    queue_url = os.environ.get('SQS_QUEUE_URL')
    
    if not queue_url or queue_url.strip() == "":
        error = 'SQS URL may not be set in environment or not availabe.'
        logger.error(error)
        raise ValueError(error)
    
    # Create a SQS Client to send message
    sqs_client = boto3.client('sqs')
    
    # check if there are valid list of articles or not empty
    if not articles or not isinstance(articles, list):
        error = 'Articles must be a list of dictionaries and must not be empty!'
        logger.error(error)
        raise NoArticlesFoundError(error)
    
    for article in articles:
        try:
            response = sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(article)
            )
            logger.info(f"Message sent to SQS. MessageId : {response['MessageId']}")
        
        except Exception as e:
            error = f'Exception: {e}'
            logger.exception(error)
            raise



def api_request_count(bucket_name):
    """
    Get and Update API Request Data in S3 bucket:
        - Get API Request Data from S3 bucket
        - Check whether it's today if not reset the tracking data
        - Return False if api request is reached
        - Allow more API request if not more than 50
    
    Returns:
        Boolean: Function returns True if API Call limit less than 50 for a day.
    """
    
    s3_client = boto3.client('s3')
    bucket_name = bucket_name
    file_name = 'api_request_tracker.json'
    today = str(datetime.date.today())
    
    try:
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=file_name
        )
        tracking_data = json.loads(response['Body'].read().decode('utf-8'))
        
    except s3_client.exceptions.NoSuchKey:
        tracking_data = {
            "date": str(today),
            "count": 0
        }
    
    # Check and reset tracking data if not today
    if tracking_data['date'] != today:
        # reset tracking date
        tracking_data = {
            "date": today,
            "count": 0
        }
    
    # Check API Request limit
    if tracking_data['count'] >= 50:
        warning = 'API request limit has reached!'
        logger.warning(warning)
        return False
    
    tracking_data['count'] += 1
    s3_client.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=json.dumps(tracking_data)
    )
    return True



def get_content_preview(url, max_length=1000):
    """
    The function will get a url to scrap its data from the web using the URL.
    The first 1000 characters will be stored.

    Args:
        url (str): Name of the URL to scrap data from the site.
        max_length (int, optional): Store content preview upto 1000 characters.
    """
    
    try:
        # Adding headers to mimic the real browser
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        contents = soup.find_all('p')
        content_preview = " ".join([content.get_text(strip=True) for content in contents])
        
        logger.info(f'Successfully pulled content data from the {url}')
        
        return content_preview[:max_length] if content_preview else 'No content is avaiable!'
    
    except requests.exceptions.RequestException as e:
        error = f'Exception: Error has been occurred to pull content from {url}: {e}'
        logger.error(error)
        return f'Content fetching error: {e}'


pprint(processed_guardian_articles('machine learning'))