# Streaming Data Project: Guardian Articles to Message Broker (AWS SQS) 

An application to retrieve real-time articles from the Guardian API and Publish it to AWS Simple Queue Service (SQS) to be consumed for analysis purpose. The project is deploying using a streaming pipeline. The infrastructure is deployed usin Terraform and CI/CD pipeline is set up for automated deployment.

## Project Features

    - Fetch Guardian Articles from the Guardian API.
    - Publish Messages to an AWS SQS Service.
    - Extracting articles using AWS Lambda and send to AWS SQS.
    - Infrastructure as Code (IaC) for the project using Terraform.
    - CI/CD pipeline for automated deployment.
    - Store Terraform State Management to S3 bucket to update deployement.
    - AWS Secrets Manager to store secret and Github Action Environment Variabels.

## Prerequisites

Before runing the project, you mush ensure to have the following installed:

    - Python latest
    - Terraform
    - AWS Cli
        with all required IAM Permission
    - Git init
    - Guardian API Key ( Store in Github Secret )
    - AWS Credentials ( Store in Github Secret )

## Project Structure
    
This the local structrue before push it to Github:

    |--- STREAM-GUARDIAN-ARTICLES
    |    |--- .github/workflows
    |    |      |---build.yml
    |    |
    |    |--- .venv
    |    |--- packages
    |    |--- src
    |    |    |--- lambda_handler.py
    |    |    |--- requirements.txt
    |    |
    |    |--- terraform
    |    |    |--- iam.tf
    |    |    |--- lambda.tf
    |    |    |--- main.tf
    |    |    |--- outputs.tf
    |    |    |--- variables.tf
    |    |
    |    |--- tests
    |    |    |--- test_lambda_handler.py
    |    |
    |    |--- .gitignore
    |    |--- Makefile
    |    |--- README.md
    |    |--- requirements.txt
        


## Intruction to Deploy the Project

### Clone Repository

    - "git clone https://github.com/mohsin-sarker/stream-guardian-articles.git"
    - cd stream-guardian-articles

### Virtual Environment

Make sure you're going to create virtual environment and activae to start working.

### Add a Package Directory for Lambda

In the project directory, create a empty package folder where Lambda function will be copied and dependencies will be installed by CI/CD pipeline for automated deployment

    - mkdir packages

### Configurations

Ensure AWS Credentials and Guardian API Key are properly configured in Github Secrets:

    - GUARDIAN_API_KEY
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_REGION
    - SAFETY_API_KEY (This is new Safety requirement for Safety Run. Need to register for free to get the KEY.)

For local using: 
    run in terminal
    - aws configure


### Terraform State Management

Before deployment, ensure you will have a AWS S3 bucket with a unique bucket name. Change Backend Bucket name ["guardian-articles-config-bucket"] in main.tf so terraform state management will be stored and update during deployment.

### Lambda Environment Variables

Before or After deployment, a defualt searh term as "machine learning" is created during deployment. Check terraform variables to replace ["search_teram] variable. Or It can be changed after demployment from Lambda Configuration (Environment Variables).

### Push it Github for Automated Demployment

The Github action is set up to:
    - Deploy Terraform whenever pushing to main
    - Deploy updated Lambda Function when functionality changed

push it to Github:
    - git add .
    - git commit -m "commit message"
    - git push origin main


## Test Deployment

To trigger the Lambda Function from terminal:
    - aws lambda invoke --function-name <your-lambda-function-name> response.json
    - cat response.json

## Destroy AWS Resources (Manually) to Cleanup

To cleanup AWS Resources, run:
    - terraform destroy (It may ask to provide GUARDIAN_API_KEY to continue cleaning process)
    Or
    - terraform destory -auto-approve
