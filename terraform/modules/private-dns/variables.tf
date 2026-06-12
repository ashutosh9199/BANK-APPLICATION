variable "name_prefix" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "virtual_network_id" {
  type = string
}

variable "postgresql_private_dns_zone_name" {
  type = string
}

variable "tags" {
  type = map(string)
}
