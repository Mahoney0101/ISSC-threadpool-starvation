provider "aws" {
  profile = "issc"
  region  = "eu-west-1"
}

variable "region" {
  default = "eu-west-1"
}

resource "tls_private_key" "issc_key" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "aws_key_pair" "issc_key" {
  key_name   = "issc"
  public_key = tls_private_key.issc_key.public_key_openssh
}

resource "local_file" "private_key" {
  content         = tls_private_key.issc_key.private_key_pem
  filename        = "${path.module}/issc.pem"
  file_permission = "0600"
}

resource "aws_security_group" "swarm_sg" {
  name        = "swarm_sg"
  description = "Allow SSH and Docker swarm communication"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 2377
    to_port     = 2377
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 7946
    to_port     = 7946
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 4789
    to_port     = 4789
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 7946
    to_port     = 7946
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 4789
    to_port     = 4789
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 9091
    to_port     = 9091
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 9093
    to_port     = 9093
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5001
    to_port     = 5001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}

data "aws_caller_identity" "current" {}

resource "aws_iam_instance_profile" "worker_profile" {
  name = "worker-instance-profile"
  role = aws_iam_role.worker_role.name
}


resource "aws_iam_role" "worker_role" {
  name = "worker-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "worker_policy" {
  name = "worker-policy"
  role = aws_iam_role.worker_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = "*"
      }
    ]
  })
}


resource "aws_instance" "worker" {
  ami                  = "ami-0d940f23d527c3ab1"
  instance_type        = "t2.micro"
  key_name             = aws_key_pair.issc_key.key_name
  security_groups      = [aws_security_group.swarm_sg.name]
  iam_instance_profile = aws_iam_instance_profile.worker_profile.name

  depends_on = [null_resource.wait_for_token] # Ensure join token has been added to parameter store before creating 

  user_data = <<-EOF
              #!/bin/bash
              apt update
              apt install -y docker.io 
              apt install -y awscli
              apt install -y pip

              JOIN_TOKEN=$(aws ssm get-parameter --name "swarm-join-token" --query "Parameter.Value" --output text --region ${var.region})
              MANAGER_IP=$(aws ssm get-parameter --name "manager-ip" --query "Parameter.Value" --output text --region ${var.region})
              docker swarm join --token $JOIN_TOKEN $MANAGER_IP:2377

              ufw allow 3000/tcp
              ufw allow 5000/tcp
              ufw allow 9090/tcp
              ufw allow 9091/tcp
              ufw allow 9093/tcp

              EOF

  tags = {
    Name = "swarm-worker"
  }
}


resource "null_resource" "wait_for_token" {

  provisioner "local-exec" {
    command = <<EOT
      echo "Waiting for swarm join token to be available..."
      while true; do
        TOKEN=$(aws ssm get-parameter --name "swarm-join-token" --query "Parameter.Value" --output text --region ${var.region} --profile issc 2>/tmp/ssm_error.log)
        if [ -n "$TOKEN" ]; then
          echo "Swarm join token is available: $TOKEN. Proceeding with worker creation."
          break
        fi
        echo "Join token not found yet. Retrying..."
        sleep 10
      done
    EOT
  }
}



output "ssh_command" {
  value = <<-EOT

    worker
    ssh -i "${path.module}/issc.pem" ubuntu@ec2-${replace(aws_instance.worker.public_ip, ".", "-")}.eu-west-1.compute.amazonaws.com

    curl -I http://${aws_instance.worker.public_ip}:4789

    prometheus 
      ${aws_instance.worker.public_ip}:9090
    
    pushgateway
      ${aws_instance.worker.public_ip}:9091
    
    alertmanager
      ${aws_instance.worker.public_ip}:9093

    webserver
      ${aws_instance.worker.public_ip}:5000/test-threadpool
  EOT
}
