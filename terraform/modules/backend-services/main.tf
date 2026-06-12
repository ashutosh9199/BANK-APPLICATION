resource "azurerm_key_vault" "main" {
  name                          = "kv-${var.compact_prefix}-${var.unique_suffix}"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  tenant_id                     = var.tenant_id
  sku_name                      = "standard"
  rbac_authorization_enabled    = true
  public_network_access_enabled = var.key_vault_public_network_access_enabled
  purge_protection_enabled      = true
  soft_delete_retention_days    = 7
  tags                          = var.tags
}

resource "azurerm_private_endpoint" "key_vault" {
  name                = "pe-kv-${var.name_prefix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-kv-${var.name_prefix}"
    private_connection_resource_id = azurerm_key_vault.main.id
    subresource_names              = ["vault"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "pdzg-key-vault"
    private_dns_zone_ids = [var.key_vault_private_dns_zone_id]
  }
}

resource "azurerm_role_assignment" "deployer_key_vault_secrets_officer" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = var.deployer_object_id
}

resource "azurerm_key_vault_secret" "postgresql_admin_password" {
  count = var.create_key_vault_secrets ? 1 : 0

  name         = "postgresql-admin-password"
  value        = var.postgresql_administrator_password
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [
    azurerm_role_assignment.deployer_key_vault_secrets_officer,
    azurerm_private_endpoint.key_vault
  ]
}


resource "azurerm_servicebus_namespace" "main" {
  name                          = "sb-${var.name_prefix}-${var.unique_suffix}"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  sku                           = var.servicebus_sku
  capacity                      = var.servicebus_capacity
  premium_messaging_partitions  = var.servicebus_premium_messaging_partitions
  public_network_access_enabled = false
  minimum_tls_version           = "1.2"
  tags                          = var.tags
}

resource "azurerm_servicebus_queue" "main" {
  name         = var.servicebus_queue_name
  namespace_id = azurerm_servicebus_namespace.main.id
}

resource "azurerm_private_endpoint" "service_bus" {
  name                = "pe-sb-${var.name_prefix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-sb-${var.name_prefix}"
    private_connection_resource_id = azurerm_servicebus_namespace.main.id
    subresource_names              = ["namespace"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "pdzg-service-bus"
    private_dns_zone_ids = [var.service_bus_private_dns_zone_id]
  }
}


resource "azurerm_storage_account" "main" {
  name                            = "st${var.compact_prefix}${var.unique_suffix}"
  location                        = var.location
  resource_group_name             = var.resource_group_name
  account_tier                    = "Standard"
  account_replication_type        = var.storage_replication_type
  public_network_access_enabled   = false
  shared_access_key_enabled       = false
  allow_nested_items_to_be_public = false
  min_tls_version                 = "TLS1_2"
  tags                            = var.tags
}

resource "azurerm_storage_container" "documents" {
  name                  = "documents"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_role_assignment" "deployer_storage_blob_data_reader" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = var.deployer_object_id
}

resource "azurerm_private_endpoint" "storage_blob" {
  name                = "pe-blob-${var.name_prefix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-blob-${var.name_prefix}"
    private_connection_resource_id = azurerm_storage_account.main.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "pdzg-storage-blob"
    private_dns_zone_ids = [var.storage_blob_private_dns_zone_id]
  }
}

