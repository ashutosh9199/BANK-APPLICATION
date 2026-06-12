locals {
  appgw_backend_pool_name     = "appsvc-backend-pool"
  appgw_backend_settings_name = "appsvc-http-settings"
  appgw_frontend_port_name    = "http-frontend-port"
  appgw_frontend_ip_name      = "public-frontend-ip"
  appgw_listener_name         = "http-listener"
  appgw_probe_name            = "appsvc-health-probe"
  appgw_rule_name             = "appsvc-routing-rule"
}

resource "azurerm_public_ip" "appgw" {
  name                = "pip-appgw-${var.name_prefix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  domain_name_label   = var.app_gateway_public_ip_dns_label
  tags                = var.tags
}

resource "azurerm_web_application_firewall_policy" "appgw" {
  name                = "waf-${var.name_prefix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  policy_settings {
    enabled = true
    mode    = var.application_gateway_waf_mode
  }

  managed_rules {
    managed_rule_set {
      type    = "OWASP"
      version = "3.2"
    }
  }
}

resource "azurerm_application_gateway" "main" {
  name                = "agw-${var.name_prefix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  firewall_policy_id  = azurerm_web_application_firewall_policy.appgw.id
  tags                = var.tags

  sku {
    name     = "WAF_v2"
    tier     = "WAF_v2"
    capacity = var.application_gateway_capacity
  }

  gateway_ip_configuration {
    name      = "gateway-ip-configuration"
    subnet_id = var.app_gateway_subnet_id
  }

  frontend_ip_configuration {
    name                 = local.appgw_frontend_ip_name
    public_ip_address_id = azurerm_public_ip.appgw.id
  }

  frontend_port {
    name = local.appgw_frontend_port_name
    port = 80
  }

  backend_address_pool {
    name  = local.appgw_backend_pool_name
    fqdns = [var.app_service_default_hostname]
  }

  probe {
    name                                      = local.appgw_probe_name
    protocol                                  = "Https"
    host                                      = var.app_service_default_hostname
    path                                      = var.application_gateway_health_probe_path
    interval                                  = 30
    timeout                                   = 30
    unhealthy_threshold                       = 3
    pick_host_name_from_backend_http_settings = false

    match {
      status_code = ["200-399"]
    }
  }

  backend_http_settings {
    name                                = local.appgw_backend_settings_name
    protocol                            = "Https"
    port                                = 443
    request_timeout                     = 30
    cookie_based_affinity               = "Disabled"
    host_name                           = var.app_service_default_hostname
    probe_name                          = local.appgw_probe_name
    pick_host_name_from_backend_address = false
  }

  http_listener {
    name                           = local.appgw_listener_name
    frontend_ip_configuration_name = local.appgw_frontend_ip_name
    frontend_port_name             = local.appgw_frontend_port_name
    protocol                       = "Http"
  }

  request_routing_rule {
    name                       = local.appgw_rule_name
    rule_type                  = "Basic"
    priority                   = 100
    http_listener_name         = local.appgw_listener_name
    backend_address_pool_name  = local.appgw_backend_pool_name
    backend_http_settings_name = local.appgw_backend_settings_name
  }

}
