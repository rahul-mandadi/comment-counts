# Infrastructure for the Phase 2 corpus run.
#
# Deliberately small. The project reads from a PUBLIC bucket (s3://mirrulations)
# that needs no credentials, so nothing here grants access to the source data.
# What it creates is somewhere to put the assembled corpus and the embeddings,
# and the one role Bedrock batch inference needs to read and write it.
#
# Everything is destroyable and rebuildable: `terraform destroy` leaves no
# orphaned state, which matters because the expensive resources in this project
# are jobs rather than servers, and a forgotten server is how a portfolio
# project turns into a bill.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  type        = string
  default     = "us-east-1"
  description = "Bedrock batch inference is not available in every region; us-east-1 is the safe default."
}

variable "bucket_name" {
  type        = string
  description = "Globally unique. Suggest comment-counts-<something-of-yours>."
}

variable "force_destroy" {
  type        = bool
  default     = true
  description = "true so `terraform destroy` actually works on a bucket holding objects. This is a research corpus that can be rebuilt from the public mirror, not a system of record."
}

resource "aws_s3_bucket" "corpus" {
  bucket        = var.bucket_name
  force_destroy = var.force_destroy
}

# The corpus is rebuildable from a public mirror, so versioning would pay to
# keep copies of something already free to re-fetch.
resource "aws_s3_bucket_public_access_block" "corpus" {
  bucket                  = aws_s3_bucket.corpus.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "corpus" {
  bucket = aws_s3_bucket.corpus.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Intermediates are large and regenerable. Expiring them stops the bill growing
# after the analysis is finished and the paper figures are saved.
resource "aws_s3_bucket_lifecycle_configuration" "corpus" {
  bucket = aws_s3_bucket.corpus.id

  rule {
    id     = "expire-intermediates"
    status = "Enabled"
    filter { prefix = "scratch/" }
    expiration { days = 30 }
  }

  rule {
    id     = "abort-incomplete-uploads"
    status = "Enabled"
    filter {}
    abort_incomplete_multipart_upload { days_after_initiation = 7 }
  }
}

# --- role for Bedrock batch inference -------------------------------------
data "aws_caller_identity" "me" {}

data "aws_iam_policy_document" "bedrock_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }
    # confused-deputy guards: this role may only be assumed on behalf of THIS
    # account, for a batch job in THIS account
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.me.account_id]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:bedrock:${var.region}:${data.aws_caller_identity.me.account_id}:model-invocation-job/*"]
    }
  }
}

data "aws_iam_policy_document" "bedrock_s3" {
  statement {
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.corpus.arn, "${aws_s3_bucket.corpus.arn}/*"]
  }
  statement {
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.corpus.arn}/*"]
  }
}

resource "aws_iam_role" "bedrock_batch" {
  name               = "${var.bucket_name}-bedrock-batch"
  assume_role_policy = data.aws_iam_policy_document.bedrock_assume.json
}

resource "aws_iam_role_policy" "bedrock_batch" {
  role   = aws_iam_role.bedrock_batch.id
  policy = data.aws_iam_policy_document.bedrock_s3.json
}

output "bucket" { value = aws_s3_bucket.corpus.id }
output "bedrock_role_arn" { value = aws_iam_role.bedrock_batch.arn }

output "next_steps" {
  value = <<-EOT
    export COMMENT_COUNTS_BUCKET=${aws_s3_bucket.corpus.id}
    export BEDROCK_BATCH_ROLE_ARN=${aws_iam_role.bedrock_batch.arn}

    Verified 2026-09-20: Titan Text Embeddings V2 and Cohere Embed V4 both
    invoke with no console model-access step on a new account. If a future
    model does need one it is Bedrock > Model access, and the failure mode is
    a bare AccessDenied that does not mention model access.

    REGION MATTERS. us-east-1 carries 15 embedding models; us-east-2 carries 2.
  EOT
}
