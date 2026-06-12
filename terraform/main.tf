terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}

  subscription_id     = var.subscription_id
  storage_use_azuread = true
}

data "azurerm_client_config" "current" {}

locals {
  location       = var.location
  name_prefix    = lower("${var.project_name}-${var.environment}")
  compact_prefix = lower(substr(replace("${var.project_name}${var.environment}", "-", ""), 0, 12))
  unique_suffix  = lower(substr(replace(var.unique_suffix, "-", ""), 0, 8))
  tags           = merge(var.tags, { project = var.project_name, environment = var.environment })
  database_url   = "postgresql://${var.postgresql_administrator_login}:${urlencode(var.postgresql_administrator_password)}@${module.database.server_fqdn}:5432/${module.database.database_name}?sslmode=require"
}


module "resource_group" {
  source = "./modules/resource-group"

  name_prefix = local.name_prefix
  location    = local.location
  tags        = local.tags
}

module "network" {
  source = "./modules/network"

  name_prefix                         = local.name_prefix
  location                            = module.resource_group.location
  resource_group_name                 = module.resource_group.name
  vnet_address_space                  = var.vnet_address_space
  app_gateway_subnet_cidr             = var.app_gateway_subnet_cidr
  app_service_integration_subnet_cidr = var.app_service_integration_subnet_cidr
  database_subnet_cidr                = var.database_subnet_cidr
  private_endpoint_subnet_cidr        = var.private_endpoint_subnet_cidr
  tags                                = local.tags
}

module "private_dns" {
  source = "./modules/private-dns"

  name_prefix                      = local.name_prefix
  resource_group_name              = module.resource_group.name
  virtual_network_id               = module.network.virtual_network_id
  postgresql_private_dns_zone_name = var.postgresql_private_dns_zone_name
  tags                             = local.tags
}

module "monitoring" {
  source = "./modules/monitoring"

  name_prefix         = local.name_prefix
  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  log_retention_days  = var.log_retention_days
  tags                = local.tags
}

module "database" {
  source = "./modules/database"

  name_prefix                       = local.name_prefix
  unique_suffix                     = local.unique_suffix
  location                          = module.resource_group.location
  resource_group_name               = module.resource_group.name
  delegated_subnet_id               = module.network.database_subnet_id
  private_dns_zone_id               = module.private_dns.postgresql_zone_id
  postgresql_version                = var.postgresql_version
  postgresql_administrator_login    = var.postgresql_administrator_login
  postgresql_administrator_password = var.postgresql_administrator_password
  postgresql_database_name          = var.postgresql_database_name
  postgresql_sku_name               = var.postgresql_sku_name
  postgresql_storage_mb             = var.postgresql_storage_mb
  postgresql_backup_retention_days  = var.postgresql_backup_retention_days
  postgresql_zone                   = var.postgresql_zone
  tags                              = local.tags

  depends_on = [module.private_dns]
}

module "backend_services" {
  source = "./modules/backend-services"

  name_prefix                             = local.name_prefix
  compact_prefix                          = local.compact_prefix
  unique_suffix                           = local.unique_suffix
  location                                = module.resource_group.location
  resource_group_name                     = module.resource_group.name
  tenant_id                               = data.azurerm_client_config.current.tenant_id
  deployer_object_id                      = data.azurerm_client_config.current.object_id
  private_endpoint_subnet_id              = module.network.private_endpoint_subnet_id
  key_vault_private_dns_zone_id           = module.private_dns.key_vault_zone_id
  service_bus_private_dns_zone_id         = module.private_dns.service_bus_zone_id
  storage_blob_private_dns_zone_id        = module.private_dns.storage_blob_zone_id
  create_key_vault_secrets                = var.create_key_vault_secrets
  key_vault_public_network_access_enabled = var.key_vault_public_network_access_enabled
  postgresql_administrator_password       = var.postgresql_administrator_password
  servicebus_sku                          = var.servicebus_sku
  servicebus_capacity                     = var.servicebus_capacity
  servicebus_premium_messaging_partitions = var.servicebus_premium_messaging_partitions
  servicebus_queue_name                   = var.servicebus_queue_name
  storage_replication_type                = var.storage_replication_type
  tags                                    = local.tags

  depends_on = [module.private_dns]
}

resource "azurerm_key_vault_secret" "database_url" {
  count = var.create_key_vault_secrets ? 1 : 0

  name         = "database-url"
  value        = local.database_url
  key_vault_id = module.backend_services.key_vault_id

  depends_on = [module.backend_services]
}

resource "azurerm_key_vault_secret" "app_secret_key" {
  count = var.create_key_vault_secrets ? 1 : 0

  name         = "app-secret-key"
  value        = var.app_secret_key
  key_vault_id = module.backend_services.key_vault_id

  depends_on = [module.backend_services]
}

resource "azurerm_key_vault_secret" "app_refresh_secret_key" {
  count = var.create_key_vault_secrets ? 1 : 0

  name         = "app-refresh-secret-key"
  value        = var.app_refresh_secret_key
  key_vault_id = module.backend_services.key_vault_id

  depends_on = [module.backend_services]
}

module "app_service" {
  source = "./modules/app-service"

  name_prefix                       = local.name_prefix
  unique_suffix                     = local.unique_suffix
  location                          = module.resource_group.location
  resource_group_name               = module.resource_group.name
  app_service_plan_sku              = var.app_service_plan_sku
  app_service_python_version        = var.app_service_python_version
  app_service_integration_subnet_id = module.network.app_service_integration_subnet_id
  private_endpoint_subnet_id        = module.network.private_endpoint_subnet_id
  app_service_private_dns_zone_id   = module.private_dns.app_service_zone_id
  database_host                     = module.database.server_fqdn
  database_name                     = module.database.database_name
  database_url                      = local.database_url
  secret_app_settings = var.use_key_vault_secret_references && var.create_key_vault_secrets ? {
    DATABASE_URL       = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.database_url[0].versionless_id})"
    SECRET_KEY         = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.app_secret_key[0].versionless_id})"
    REFRESH_SECRET_KEY = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.app_refresh_secret_key[0].versionless_id})"
  } : {}
  key_vault_uri          = module.backend_services.key_vault_uri
  service_bus_namespace  = module.backend_services.servicebus_namespace_name
  service_bus_queue      = module.backend_services.servicebus_queue_name
  storage_account_name   = module.backend_services.storage_account_name
  storage_account_url    = module.backend_services.storage_account_blob_endpoint
  storage_container_name = module.backend_services.storage_container_name
  tags                   = local.tags

  depends_on = [
    module.network,
    module.private_dns,
    module.database,
    module.backend_services
  ]
}

module "app_identity_access" {
  source = "./modules/app-identity-access"

  app_service_principal_id = module.app_service.principal_id
  key_vault_id             = module.backend_services.key_vault_id
  servicebus_namespace_id  = module.backend_services.servicebus_namespace_id
  storage_account_id       = module.backend_services.storage_account_id
}

moved {
  from = module.edge
  to   = module.application_gateway
}

module "application_gateway" {
  source = "./modules/application-gateway"

  name_prefix                           = local.name_prefix
  unique_suffix                         = local.unique_suffix
  location                              = module.resource_group.location
  resource_group_name                   = module.resource_group.name
  app_gateway_subnet_id                 = module.network.app_gateway_subnet_id
  app_service_default_hostname          = module.app_service.default_hostname
  app_gateway_public_ip_dns_label       = var.app_gateway_public_ip_dns_label
  application_gateway_capacity          = var.application_gateway_capacity
  application_gateway_waf_mode          = var.application_gateway_waf_mode
  application_gateway_health_probe_path = var.application_gateway_health_probe_path
  tags                                  = local.tags

  depends_on = [module.app_service]
}

module "diagnostics" {
  source = "./modules/diagnostics"

  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id
  application_gateway_id     = module.application_gateway.application_gateway_id
  app_service_id             = module.app_service.app_service_id
  postgresql_server_id       = module.database.server_id
  storage_account_id         = module.backend_services.storage_account_id
  key_vault_id               = module.backend_services.key_vault_id
}
