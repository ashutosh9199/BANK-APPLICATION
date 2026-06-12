resource "azurerm_role_assignment" "app_key_vault_secrets_user" {
  scope                = var.key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = var.app_service_principal_id
}

resource "azurerm_role_assignment" "app_service_bus_data_owner" {
  scope                = var.servicebus_namespace_id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = var.app_service_principal_id
}

resource "azurerm_role_assignment" "app_storage_blob_data_contributor" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.app_service_principal_id
}
