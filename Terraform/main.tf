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
  region  = "us-west-2"
}

resource "aws_instance" "app_server1" {
  ami           = "ami-04999cd8f2624f834"
  instance_type = "t2.micro"

  tags = {
    Name = "ExampleAppServerInstance1"
  }
}

resource "aws_instance" "app_server2" {
  ami           = "ami-077d884fe0477d60d"
  instance_type = "t3.micro"

  tags = {
    Name = "ExampleAppServerInstance2"
  }
}

resource "aws_instance" "app_server3" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3a.small"

  tags = {
    Name = "ExampleAppServerInstance3"
  }
}

resource "aws_instance" "app_server4" {
  ami           = "ami-0e472ba40eb589f49"
  instance_type = "t2.small"

  tags = {
    Name = "ExampleAppServerInstance4"
  }
}

resource "aws_instance" "app_server5" {
  ami           = "ami-052c08d70def0ac62"
  instance_type = "t3.medium"

  tags = {
    Name = "ExampleAppServerInstance5"
  }
}

resource "aws_instance" "app_server6" {
  ami           = "ami-0aef57767f5404a3c"
  instance_type = "t2.medium"

  tags = {
    Name = "ExampleAppServerInstance6"
  }
}

resource "aws_db_instance" "example" {
  instance_class = "db.t3.micro"
  engine         = "mysql"
  multi_az       = true
}