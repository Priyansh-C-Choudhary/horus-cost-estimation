# Variables Configuration
# This file defines all the variables used across the Terraform configuration

# Project Information
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "webapp-infrastructure"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# AWS Region
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

# Network Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

variable "admin_cidr" {
  description = "CIDR block for admin access"
  type        = string
  default     = "10.0.0.0/8"  # Adjust this to your admin network
}

# EC2 Configuration
variable "frontend_instance_type" {
  description = "Instance type for frontend servers"
  type        = string
  default     = "t3.medium"
}

variable "backend_instance_type" {
  description = "Instance type for backend servers"
  type        = string
  default     = "t3.large"
}

variable "frontend_instance_count" {
  description = "Number of frontend instances"
  type        = number
  default     = 2
}

variable "backend_instance_count" {
  description = "Number of backend instances"
  type        = number
  default     = 2
}

variable "key_pair_name" {
  description = "Name of the AWS key pair for EC2 instances"
  type        = string
  default     = "webapp-keypair"
}

# RDS Configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_engine" {
  description = "Database engine"
  type        = string
  default     = "mysql"
}

variable "db_engine_version" {
  description = "Database engine version"
  type        = string
  default     = "8.0"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS instance (GB)"
  type        = number
  default     = 100
}

variable "db_storage_type" {
  description = "Storage type for RDS instance"
  type        = string
  default     = "gp3"
}

variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "webapp_db"
}

variable "db_username" {
  description =