resource "aws_instance" "core_ec2" {
  ami           = var.ami_id
  instance_type = var.instance_type
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.ec2_sg.id]

  root_block_device {
    volume_type = "gp3"
    volume_size = var.volume_size
    encrypted   = false
  }

  tags = {
    Name        = "ec2-server"
    Environment = var.environment
  }
}