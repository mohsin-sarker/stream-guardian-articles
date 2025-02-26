 
        ##### IAM Role for Guardian Lambda Function #####

#### Create IAM role for lambda function ####
resource "aws_iam_role" "guardian_lambda_role" {
  name      = var.lambda_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}



        ##### Terraform and S3 Policy #######

### Create terraform IAM policy to put and read object from S3 bucket
resource "aws_iam_policy" "terraform_s3_policy" {
  name = "terraform_s3_policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
        ],
        Effect   = "Allow"
        Resource = "arn:aws:s3:::${var.s3_bucket_name}/*"
      },
    ]
  })
}


#### Attach terraform policy to the guardian iam role
resource "aws_iam_role_policy_attachment" "terraform_s3_policy_attachment" {
    role = aws_iam_role.guardian_lambda_role.name
    policy_arn = aws_iam_policy.terraform_s3_policy.arn
}



        ####### SQS Queue Policy ######

### Create IAM policy for SQS queue
resource "aws_iam_policy" "sqs_queue_policy" {
  name        = var.queue_policy_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "sqs:SendMessage",
        ]
        Effect   = "Allow"
        Resource = aws_sqs_queue.guardian_queue.arn
      },
    ]
  })
}

#### Attach policy to the guardian iam role
resource "aws_iam_role_policy_attachment" "sqs_policy_attachment" {
    role = aws_iam_role.guardian_lambda_role.name
    policy_arn = aws_iam_policy.sqs_queue_policy.arn
}




            ####### CloudWatch Policy ######

### Create IAM policy for cloudwatch
resource "aws_iam_policy" "lambda_cloudwatch_logs_policy" {
  name_prefix = "cw-policy-"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ],
        Effect   = "Allow"
        Resource = "arn:aws:logs:${var.region_name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${aws_lambda_function.guardian_lambda_function.function_name}:log-stream:*"
      },
    ]
  })
}



# Attaches cloudwatch policy to the Guardian Lambda IAM role
resource "aws_iam_role_policy_attachment" "lambda_cw_policy_attachment" {
  role       = aws_iam_role.guardian_lambda_role.name
  policy_arn = aws_iam_policy.lambda_cloudwatch_logs_policy.arn
}



##### Secrets Manager Policy to retrieve API Keys #####
resource "aws_iam_policy" "secrets_manager_policy" {
  name = var.secrets_manager_policy

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = aws_secretsmanager_secret.guardian_api_key_secret.arn
      }
    ]
  })
}

#### Attach Secrets Manager Policy to the Guardian Lambda IAM role ####
resource "aws_iam_role_policy_attachment" "secrets_manager_policy_attachment" {
  role       = aws_iam_role.guardian_lambda_role.name
  policy_arn = aws_iam_policy.secrets_manager_policy.arn
}