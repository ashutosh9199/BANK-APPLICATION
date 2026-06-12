
resource "azurerm_service_plan" "app" {
  name                = "asp-${var.name_prefix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  sku_name            = var.app_service_plan_sku
  tags                = var.tags
}

resource "azurerm_linux_web_app" "app" {
  name                                           = "app-${var.name_prefix}-${var.unique_suffix}"
  location                                       = var.location
  resource_group_name                            = var.resource_group_name
  service_plan_id                                = azurerm_service_plan.app.id
  https_only                                     = true
  public_network_access_enabled                  = false
  ftp_publish_basic_authentication_enabled       = false
  webdeploy_publish_basic_authentication_enabled = false
  virtual_network_subnet_id                      = var.app_service_integration_subnet_id
  tags                                           = var.tags

  identity {
    type = "SystemAssigned"
  }

  site_config {
    always_on              = true
    app_command_line       = "gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app"
    ftps_state             = "Disabled"
    minimum_tls_version    = "1.2"
    vnet_route_all_enabled = true

    application_stack {
      python_version = var.app_service_python_version
    }
  }

  app_settings = merge({
    SCM_DO_BUILD_DURING_DEPLOYMENT = "true"
    WEBSITES_PORT                  = "8000"
    DATABASE_URL                   = var.database_url
    DATABASE_HOST                  = var.database_host
    DATABASE_NAME                  = var.database_name
    KEY_VAULT_URI                  = var.key_vault_uri
    SERVICE_BUS_NAMESPACE          = var.service_bus_namespace
    SERVICE_BUS_QUEUE              = var.service_bus_queue
    STORAGE_ACCOUNT_NAME           = var.storage_account_name
    AZURE_STORAGE_ACCOUNT_NAME     = var.storage_account_name
    AZURE_STORAGE_ACCOUNT_URL      = var.storage_account_url
    AZURE_STORAGE_BLOB_ENDPOINT    = var.storage_account_url
    AZURE_STORAGE_CONTAINER_NAME   = var.storage_container_name
    AZURE_CONTAINER_NAME           = var.storage_container_name
    REQUIRE_AZURE_STORAGE          = "true"
  }, var.secret_app_settings)
}

resource "azurerm_private_endpoint" "app_service" {
  name                = "pe-app-${var.name_prefix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-app-${var.name_prefix}"
    private_connection_resource_id = azurerm_linux_web_app.app.id
    subresource_names              = ["sites"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "pdzg-app-service"
    private_dns_zone_ids = [var.app_service_private_dns_zone_id]
  }
}
