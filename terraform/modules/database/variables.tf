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

variable "delegated_subnet_id" {
  type = string
}

variable "private_dns_zone_id" {
  type = string
}

variable "postgresql_version" {
  type = string
}

variable "postgresql_administrator_login" {
  type = string
}

variable "postgresql_administrator_password" {
  type      = string
  sensitive = true
}

variable "postgresql_database_name" {
  type = string
}

variable "postgresql_sku_name" {
  type = string
}

variable "postgresql_storage_mb" {
  type = number
}

variable "postgresql_backup_retention_days" {
  type = number
}

variable "postgresql_zone" {
  type = string
}

variable "tags" {
  type = map(string)
}
