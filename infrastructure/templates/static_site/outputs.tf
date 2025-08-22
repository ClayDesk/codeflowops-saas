# Static Site Template Outputs

output "website_url" {
  description = "Public URL of the deployed website"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_cloudfront_distribution.website.domain_name}"
}

output "cloudfront_url" {
  description = "CloudFront distribution URL"
  value       = "https://${aws_cloudfront_distribution.website.domain_name}"
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket hosting the website"
  value       = aws_s3_bucket.website.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.website.arn
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation)"
  value       = aws_cloudfront_distribution.website.id
}

output "cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.website.arn
}

output "deployment_role_arn" {
  description = "IAM role ARN for deployment automation"
  value       = aws_iam_role.deployment.arn
}

output "nameservers" {
  description = "Route53 nameservers (if custom domain is used)"
  value       = var.domain_name != "" ? aws_route53_zone.main[0].name_servers : []
}

output "certificate_arn" {
  description = "ACM certificate ARN (if custom domain is used)"
  value       = var.domain_name != "" ? aws_acm_certificate.cert[0].arn : null
}

# Deployment information
output "deployment_info" {
  description = "Comprehensive deployment information"
  value = {
    project_name     = var.project_name
    environment      = var.environment
    region          = var.aws_region
    website_url     = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_cloudfront_distribution.website.domain_name}"
    s3_bucket       = aws_s3_bucket.website.bucket
    cloudfront_id   = aws_cloudfront_distribution.website.id
    deployment_role = aws_iam_role.deployment.arn
    has_custom_domain = var.domain_name != ""
  }
}
