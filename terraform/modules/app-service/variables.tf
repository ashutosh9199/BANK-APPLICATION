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

variable "app_service_plan_sku" {
  type = string
}

variable "app_service_python_version" {
  type = string
}

variable "app_service_integration_subnet_id" {
  type = string
}

variable "private_endpoint_subnet_id" {
  type = string
}

variable "app_service_private_dns_zone_id" {
  type = string
}

variable "database_host" {
  type = string
}

variable "database_name" {
  type = string
}

variable "database_url" {
  type      = string
  sensitive = true
}

variable "secret_app_settings" {
  type      = map(string)
  sensitive = true
  default   = {}
}

variable "key_vault_uri" {
  type = string
}

variable "service_bus_namespace" {
  type = string
}

variable "service_bus_queue" {
  type = string
}

variable "storage_account_name" {
  type = string
}

variable "storage_account_url" {
  type = string
}

variable "storage_container_name" {
  type = string
}

variable "tags" {
  type = map(string)
}
