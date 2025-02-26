import requests
import json
import boto3
import logging
from botocore import exceptions


def lambda_handler(event, response):
    logger = logging.getLogger('guardian articles logger:')
    logger.info('Guardian article has been invoked!')


def get_guardian_api_key(secret_name, region='eu-west-2'):
    """
    Fetch Guardian-API-Key from secret manager.

    Args:
        secret_name (str): The name of the secret.
        region (str, optional): This AWS region where the secret is stored. Defaults to 'eu-west-2'.
    
    Return:
        dict: This function will return a dictionay of secret.
    """
    # Create a secret manager client
    client = boto3.client('secretsmanager', region_name=region)
    
    # Try to get secret object (JSON Object) from secret manager
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return secret

    # If secret not found or permission denied issues
    except exceptions.ClientError:
        return f'There has been Client Error: ResourceNotFound'
    
    # If there is a AWS Credential issue
    except exceptions.NoCredentialsError:
        return f'No credentials has been found.'
    
    # For all other exceptions
    except Exception as e:
        return f'There has been an unexpected error: {e}'


print(get_guardian_api_key('guardian_api_key'))