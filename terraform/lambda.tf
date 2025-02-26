
            #####################################
            ### Resources for Lambda Function ###
            #####################################

# Archive a single file.
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/lambda_handler.py"
  output_path = "${path.module}/../packages/lambda_function.zip"
}


#Create Lambda function to handle fetching guardian articles
resource "aws_lambda_function" "guardian_lambda_function" {
  function_name = var.lambda_function_name
  role = aws_iam_role.guardian_lambda_role.arn
  filename = data.archive_file.lambda_zip.output_path
  handler = "guardian_articles_handler.${var.lambda_function_name}"
  runtime = "python3.12"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      SECRET_NAME = aws_secretsmanager_secret.guardian_api_key_secret.name
      SQS_QUEUE_URL = aws_sqs_queue.guardian_queue.url
    }
  }

  memory_size = var.memory_size
  timeout = var.timeout
}
