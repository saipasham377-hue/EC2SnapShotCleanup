variable "aws_region" {
  description = "The AWS region to deploy the resources in."
  type        = string
}

variable "project_name" {
  description = "The name of the project."
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., dev, staging, prod)."
  type        = string
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC."
  type        = string
}

variable "public_subnet_cidr" {
  description = "The CIDR block for the public subnet."
  type        = string
}

variable "private_subnet_cidr" {
  description = "The CIDR block for the private subnet."
  type        = string
}

variable "snapshot_age_days" {
  description = "The age of snapshots to retain in days."
  type        = number
}

variable "log_retention_days" {
  description = "The retention period for logs in days."
  type        = number
}

variable "schedule_expression" {
  description = "The schedule expression for snapshot cleanup."
  type        = string
}