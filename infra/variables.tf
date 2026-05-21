variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "ami_id" {
  description = "Ubuntu AMI"
  type        = string
  default     = "ami-02c7683e4ca3ebf58" # Amazon Machine Image ID
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "key_name" {
  description = "Name of the AWS key pair"
  type        = string
  default     = "test1_key" # refers to an existing AWS EC2 key pair
}

variable "ssh_cidr_blocks" {
  description = "CIDR blocks for SSH access"
  type = list(string)
  default = ["0.0.0.0/0"]  # Change this to your IP for better security
}

variable "volume_size" {
  description = "Size of the root volume in GB"
  type        = number
  default     = 20
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "health_check_path_fe" {
  description = "Health check path for the target group"
  type        = string
  default     = "/"
}

variable "health_check_path_be" {
  description = "Health check path for the target group"
  type        = string
  default     = "/"
}