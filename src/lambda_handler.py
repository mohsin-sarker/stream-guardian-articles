import requests
import json
import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError


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
        dict: This function will return a dictionay of secret.
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

