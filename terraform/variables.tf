variable "subscription_id" {
  description = "Azure subscription ID used by the AzureRM provider."
  type        = string
}

variable "project_name" {
  description = "Short project name used in resource naming."
  type        = string
  default     = "banking"
}

variable "environment" {
  description = "Environment name used in resource naming."
  type        = string
  default     = "dev"
}

variable "unique_suffix" {
  description = "Short lowercase suffix for globally unique Azure resource names."
  type        = string
}

variable "location" {
  description = "Azure region for all regional resources."
  type        = string
  default     = "Central India"
}

variable "tags" {
  description = "Common tags applied to supported resources."
  type        = map(string)
  default     = {}
}

variable "vnet_address_space" {
  description = "Virtual Network address space."
  type        = string
  default     = "10.0.0.0/16"
}

variable "app_gateway_subnet_cidr" {
  description = "Dedicated Application Gateway subnet CIDR."
  type        = string
  default     = "10.0.1.0/24"
}

variable "app_service_integration_subnet_cidr" {
  description = "App Service VNet Integration subnet CIDR. The architecture did not specify this CIDR, so it is configurable."
  type        = string
}

variable "database_subnet_cidr" {
  description = "PostgreSQL Flexible Server private access subnet CIDR."
  type        = string
  default     = "10.0.3.0/24"
}

variable "private_endpoint_subnet_cidr" {
  description = "Private Endpoint subnet CIDR."
  type        = string
  default     = "10.0.4.0/24"
}

variable "log_retention_days" {
  description = "Log Analytics retention in days."
  type        = number
  default     = 30
}

variable "app_service_plan_sku" {
  description = "Linux App Service Plan SKU."
  type        = string
  default     = "S1"
}

variable "app_service_python_version" {
  description = "Python runtime version for the Linux App Service."
  type        = string
  default     = "3.12"
}

variable "app_gateway_public_ip_dns_label" {
  description = "Globally unique DNS label for the Application Gateway public IP."
  type        = string
}

variable "application_gateway_capacity" {
  description = "Application Gateway WAF_v2 instance capacity."
  type        = number
  default     = 1
}

variable "application_gateway_waf_mode" {
  description = "Application Gateway WAF mode."
  type        = string
  default     = "Prevention"
}

variable "application_gateway_health_probe_path" {
  description = "Application Gateway health probe path for the App Service backend."
  type        = string
  default     = "/"
}

variable "postgresql_private_dns_zone_name" {
  description = "Private DNS zone name for PostgreSQL Flexible Server private access."
  type        = string
  default     = "private.postgres.database.azure.com"
}

variable "postgresql_version" {
  description = "PostgreSQL Flexible Server version."
  type        = string
  default     = "16"
}

variable "postgresql_administrator_login" {
  description = "PostgreSQL administrator login name."
  type        = string
  default     = "pgadminuser"
}

variable "postgresql_administrator_password" {
  description = "PostgreSQL administrator password. Supply through tfvars, environment variable, or CI secret variable."
  type        = string
  sensitive   = true
}

variable "app_secret_key" {
  description = "Application JWT secret key. Supply through a local untracked tfvars file or CI/CD secret variable."
  type        = string
  sensitive   = true
}

variable "app_refresh_secret_key" {
  description = "Application refresh-token JWT secret key. Supply through a local untracked tfvars file or CI/CD secret variable."
  type        = string
  sensitive   = true
}

variable "postgresql_database_name" {
  description = "Application database name."
  type        = string
  default     = "bankingdb"
}

variable "postgresql_sku_name" {
  description = "PostgreSQL Flexible Server SKU."
  type        = string
  default     = "B_Standard_B1ms"
}

variable "postgresql_storage_mb" {
  description = "PostgreSQL storage size in MB."
  type        = number
  default     = 32768
}

variable "postgresql_backup_retention_days" {
  description = "PostgreSQL backup retention in days."
  type        = number
  default     = 7
}

variable "postgresql_zone" {
  description = "Availability zone for PostgreSQL Flexible Server."
  type        = string
  default     = "1"
}

variable "servicebus_sku" {
  description = "Service Bus namespace SKU. Private endpoints require a SKU that supports private networking."
  type        = string
  default     = "Premium"
}

variable "servicebus_capacity" {
  description = "Service Bus Premium messaging unit capacity. Premium supports 1, 2, 4, 8, or 16."
  type        = number
  default     = 1
}

variable "servicebus_premium_messaging_partitions" {
  description = "Service Bus Premium messaging partitions. Premium supports 1, 2, or 4."
  type        = number
  default     = 1
}

variable "servicebus_queue_name" {
  description = "Service Bus queue name."
  type        = string
  default     = "banking-events"
}

variable "storage_replication_type" {
  description = "Storage account replication type."
  type        = string
  default     = "LRS"
}

variable "create_key_vault_secrets" {
  description = "Create Key Vault secrets with Terraform. Keep false when applying from a public machine because Key Vault public network access is disabled."
  type        = bool
  default     = false
}

variable "key_vault_public_network_access_enabled" {
  description = "Temporarily enable public network access to Key Vault so Terraform can seed secrets from a local machine. Disable again after secrets are created."
  type        = bool
  default     = false
}

variable "use_key_vault_secret_references" {
  description = "Use Key Vault references in App Service settings for application secrets."
  type        = bool
  default     = false
}
