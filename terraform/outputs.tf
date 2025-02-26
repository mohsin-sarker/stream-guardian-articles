output "sqs_queue_url" {
    value = aws_sqs_queue.guardian_queue.url
    description = "The output of SQS queue URL"
}