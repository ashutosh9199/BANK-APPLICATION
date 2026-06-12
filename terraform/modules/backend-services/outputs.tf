output "key_vault_id" {
  value = azurerm_key_vault.main.id
}

output "key_vault_uri" {
  value = azurerm_key_vault.main.vault_uri
}

output "servicebus_namespace_id" {
  value = azurerm_servicebus_namespace.main.id
}

output "servicebus_namespace_name" {
  value = azurerm_servicebus_namespace.main.name
}

output "servicebus_queue_name" {
  value = azurerm_servicebus_queue.main.name
}

output "storage_account_id" {
  value = azurerm_storage_account.main.id
}

output "storage_account_name" {
  value = azurerm_storage_account.main.name
}

output "storage_account_blob_endpoint" {
  value = azurerm_storage_account.main.primary_blob_endpoint
}

output "storage_container_name" {
  value = azurerm_storage_container.documents.name
}
