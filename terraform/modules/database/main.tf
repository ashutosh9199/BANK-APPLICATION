resource "azurerm_postgresql_flexible_server" "main" {
  name                          = "pg-${var.name_prefix}-${var.unique_suffix}"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  version                       = var.postgresql_version
  delegated_subnet_id           = var.delegated_subnet_id
  private_dns_zone_id           = var.private_dns_zone_id
  public_network_access_enabled = false
  administrator_login           = var.postgresql_administrator_login
  administrator_password        = var.postgresql_administrator_password
  sku_name                      = var.postgresql_sku_name
  storage_mb                    = var.postgresql_storage_mb
  backup_retention_days         = var.postgresql_backup_retention_days
  zone                          = var.postgresql_zone
  tags                          = var.tags
}

resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = var.postgresql_database_name
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}
