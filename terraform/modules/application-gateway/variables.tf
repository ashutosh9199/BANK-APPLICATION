variable "name_prefix" {
  type = string
}

variable "unique_suffix" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "app_gateway_subnet_id" {
  type = string
}

variable "app_service_default_hostname" {
  type = string
}

variable "app_gateway_public_ip_dns_label" {
  type = string
}

variable "application_gateway_capacity" {
  type = number
}

variable "application_gateway_waf_mode" {
  type = string
}

variable "application_gateway_health_probe_path" {
  type = string
}

variable "tags" {
  type = map(string)
}
