output "application_gateway_id" {
  value = azurerm_application_gateway.main.id
}

output "application_gateway_public_fqdn" {
  value = azurerm_public_ip.appgw.fqdn
}
