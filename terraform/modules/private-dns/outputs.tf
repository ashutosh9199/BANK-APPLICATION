output "app_service_zone_id" {
  value = azurerm_private_dns_zone.app_service.id
}

output "key_vault_zone_id" {
  value = azurerm_private_dns_zone.key_vault.id
}

output "postgresql_zone_id" {
  value = azurerm_private_dns_zone.postgresql.id
}

output "service_bus_zone_id" {
  value = azurerm_private_dns_zone.service_bus.id
}

output "storage_blob_zone_id" {
  value = azurerm_private_dns_zone.storage_blob.id
}
