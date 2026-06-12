output "virtual_network_id" {
  value = azurerm_virtual_network.main.id
}

output "app_gateway_subnet_id" {
  value = azurerm_subnet.appgw.id
}

output "app_service_integration_subnet_id" {
  value = azurerm_subnet.app_service_integration.id
}

output "database_subnet_id" {
  value = azurerm_subnet.database.id
}

output "private_endpoint_subnet_id" {
  value = azurerm_subnet.private_endpoints.id
}
