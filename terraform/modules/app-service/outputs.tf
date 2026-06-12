output "app_service_id" {
  value = azurerm_linux_web_app.app.id
}

output "name" {
  value = azurerm_linux_web_app.app.name
}

output "default_hostname" {
  value = azurerm_linux_web_app.app.default_hostname
}

output "principal_id" {
  value = azurerm_linux_web_app.app.identity[0].principal_id
}
