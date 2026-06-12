# This module creates Application Gateway with WAF. It exposes 
# the public URL and forwards traffic to the App Service backend.
locals {
  appgw_backend_pool_name     = "appsvc-backend-pool"
  appgw_backend_settings_name = "appsvc-http-settings"
  appgw_frontend_port_name    = "http-frontend-port"
  appgw_frontend_ip_name      = "public-frontend-ip"
  appgw_listener_name         = "http-listener"
  appgw_probe_name            = "appsvc-health-probe"
  appgw_rule_name             = "appsvc-routing-rule"
}

# Application Gateway with WAF routes requests to the App Service private endpoint DNS name.
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

# HTTPS listener support requires a certificate source; no certificate resource was specified in the architecture.

# Azure Front Door forwards public traffic to the Application Gateway origin.
resource "azurerm_cdn_frontdoor_profile" "main" {
  count = var.create_front_door ? 1 : 0

  name                = "afd-${var.name_prefix}"
  resource_group_name = var.resource_group_name
  sku_name            = var.front_door_sku
  tags                = var.tags
}

resource "azurerm_cdn_frontdoor_endpoint" "main" {
  count = var.create_front_door ? 1 : 0

  name                     = "fde-${var.name_prefix}-${var.unique_suffix}"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main[0].id
  tags                     = var.tags
}

resource "azurerm_cdn_frontdoor_origin_group" "appgw" {
  count = var.create_front_door ? 1 : 0

  name                     = "og-appgw-${var.name_prefix}"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main[0].id
  session_affinity_enabled = false

  load_balancing {
    sample_size                 = 4
    successful_samples_required = 3
  }

  health_probe {
    interval_in_seconds = 100
    path                = var.front_door_health_probe_path
    protocol            = "Http"
    request_type        = "GET"
  }
}

resource "azurerm_cdn_frontdoor_origin" "appgw" {
  count = var.create_front_door ? 1 : 0

  name                           = "origin-appgw-${var.name_prefix}"
  cdn_frontdoor_origin_group_id  = azurerm_cdn_frontdoor_origin_group.appgw[0].id
  enabled                        = true
  host_name                      = azurerm_public_ip.appgw.fqdn
  origin_host_header             = azurerm_public_ip.appgw.fqdn
  certificate_name_check_enabled = false
  http_port                      = 80
  https_port                     = 443
  priority                       = 1
  weight                         = 1000

  depends_on = [azurerm_application_gateway.main]
}

resource "azurerm_cdn_frontdoor_route" "main" {
  count = var.create_front_door ? 1 : 0

  name                          = "route-appgw-${var.name_prefix}"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.main[0].id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.appgw[0].id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.appgw[0].id]
  supported_protocols           = ["Http", "Https"]
  patterns_to_match             = ["/*"]
  forwarding_protocol           = "HttpOnly"
  https_redirect_enabled        = true
  link_to_default_domain        = true
}
