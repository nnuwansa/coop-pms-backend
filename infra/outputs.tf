output "public_ip" {
  value = aws_instance.core_ec2.public_ip
}

output "fastapi_alb_url" {
  description = "URL to access FastAPI application via ALB"
  value       = "http://${aws_lb.core_alb.dns_name}"
}