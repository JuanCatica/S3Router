# --------------------------------------------
# VARS
# --------------------------------------------
variable "topic_arn" {}
variable "bucket_name" {}

# --------------------------------------------
# S3
# --------------------------------------------

resource "aws_s3_bucket" "bucket" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.bucket.id

  topic {
    topic_arn     = var.topic_arn
    events        = ["s3:ObjectCreated:*"]
  }
}

# --------------------------------------------
# PROVIDER
# --------------------------------------------
terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "5.7.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}