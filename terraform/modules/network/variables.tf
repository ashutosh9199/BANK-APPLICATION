variable "name_prefix" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "vnet_address_space" {
  type = string
}

variable "app_gateway_subnet_cidr" {
  type = string
}

variable "app_service_integration_subnet_cidr" {
  type = string
}

variable "database_subnet_cidr" {
  type = string
}

variable "private_endpoint_subnet_cidr" {
  type = string
}

variable "tags" {
  type = map(string)
}
