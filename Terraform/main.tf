terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }

  required_version = ">= 1.2.0"
}

provider "aws" {
  region = var.aws_region
}

# ----------------------------------------------------
# EC2 Instances
# ----------------------------------------------------

resource "aws_instance" "web_server_1" {
  ami           = "ami-0c55b159cbfafe1f0" # Amazon Linux 2 AMI for us-west-2
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "WebApp-Server-1"
  }
}

resource "aws_instance" "web_server_2" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.small"
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  subnet_id     = aws_subnet.public[1].id

  tags = {
    Name = "WebApp-Server-2"
  }
}

resource "aws_instance" "web_server_3" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.medium"
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "WebApp-Server-3"
  }
}

# ----------------------------------------------------
# RDS Database Instance
# ----------------------------------------------------

resource "aws_db_instance" "main_db" {
  identifier           = "${var.project_name}-main-db"
  instance_class       = var.db_instance_class
  engine               = var.db_engine
  engine_version       = var.db_engine_version
  allocated_storage    = var.db_allocated_storage
  storage_type         = var.db_storage_type
  db_name              = var.db_name
  username             = var.db_username
  password             = var.db_password
  multi_az             = true
  db_subnet_group_name = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  skip_final_snapshot  = true
}

# ----------------------------------------------------
# Security Groups & DB Subnet Group
# ----------------------------------------------------

resource "aws_security_group" "web_sg" {
  name        = "${var.project_name}-web-sg"
  description = "Allow HTTP/S traffic to web servers"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP/S"
    from_port   = 80
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH from admin network"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-web-sg" }
}

resource "aws_security_group" "db_sg" {
  name        = "${var.project_name}-db-sg"
  description = "Allow traffic from web servers to DB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "MySQL from web servers"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.web_sg.id]
  }

  tags = { Name = "${var.project_name}-db-sg" }
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = [for s in aws_subnet.private : s.id]

  tags = { Name = "${var.project_name}-db-subnet-group" }
}