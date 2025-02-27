variable "region_name" {
    description = "The name of AWS Region where the project will be deployed"
    type = string
    default = "eu-west-2"
}


variable "s3_bucket_name" {
    type = string
    default = "guardian-articles-config-bucket"
    description = "Name of the S3 bucket"
}


variable "queue_name" {
    type = string
    default = "guardian_queue"
    description = "Name of the AWS SQS queue"
}


variable "queue_policy_name" {
    type = string
    default = "guardian_queue_policy"
    description = "Name of the guardian queue policy"
}


variable "terraform_s3_policy_name" {
    type = string
    default = "terraform_s3_policy"
    description = "Name of the terraform policy to interact with s3 bucket"
}


variable "secret_name" {
    type = string
    default = "guardian_api_key"
    description = "Name of the secret in the AWS Secret Manager"
}


variable "secrets_manager_policy" {
    type = string
    default = "secrets-manager-policy"
    description = "Name of the Secrets Manager Policy"
}


variable "guardian_api_key" {
    description = "Guardian API Key to the application from Github Secrets"
    type = string
    sensitive = true
}


variable "lambda_function_name" {
    type = string
    default = "lambda_handler"
    description = "Name of the Lambda funcation"
}


variable "lambda_role_name" {
    type = string
    default = "guardian_lambda_role"
    description = "Name of the lambda IAM role"
}


variable "lambda_policy_name" {
    type = string
    default = "guardian_lambda_policy"
    description = "Name of the lambda IAM policy"
}


variable "memory_size" {
    type = number
    default = 512
    description = "Memory size for the quardian lambda function"
}


variable "timeout" {
    type = number
    default = 30
    description = "Timeout for the gaurdian lambda function in seconds"
}


variable "message_retention_seconds" {
    type = number
    default = 259200
}

