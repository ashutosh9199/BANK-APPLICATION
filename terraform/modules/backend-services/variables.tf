variable "name_prefix" {
  type = string
}

variable "compact_prefix" {
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

variable "tenant_id" {
  type = string
}

variable "deployer_object_id" {
  type = string
}

variable "private_endpoint_subnet_id" {
  type = string
}

variable "key_vault_private_dns_zone_id" {
  type = string
}

variable "service_bus_private_dns_zone_id" {
  type = string
}

variable "storage_blob_private_dns_zone_id" {
  type = string
}

variable "postgresql_administrator_password" {
  type      = string
  sensitive = true
}

variable "create_key_vault_secrets" {
  type = bool
}

variable "key_vault_public_network_access_enabled" {
  type = bool
}

variable "servicebus_sku" {
  type = string
}

variable "servicebus_capacity" {
  type = number
}

variable "servicebus_premium_messaging_partitions" {
  type = number
}

variable "servicebus_queue_name" {
  type = string
}

variable "storage_replication_type" {
  type = string
}

variable "tags" {
  type = map(string)
}
