Architecture Explanation

This architecture is for a secure Azure App Service based application inside a VNet with private access to backend services.

The user request flow is:

User → Microsoft Entra ID → Azure Front Door → Application Gateway with WAF → Listener → Rule → App Service

After the request reaches the App Service, the application privately connects to backend Azure services through Private Endpoints.

Main Components
1. Resource Group

All resources will be created inside one Resource Group.

Region:

Central India

Terraform should create:

azurerm_resource_group
2. Virtual Network

The main VNet is:

VNet: 10.0.0.0/16

This VNet contains multiple subnets.

Terraform should create:

azurerm_virtual_network
Subnet Plan
1. Application Gateway Subnet
Subnet Name: application-gateway-subnet
CIDR: 10.0.1.0/24

This subnet contains:

Application Gateway
WAF
Listener
Routing Rule

Important Terraform point:

Application Gateway must have its own dedicated subnet.

2. VNet Integration Subnet
Subnet Name: appservice-vnet-integration-subnet
Purpose: Outbound access from App Service into VNet

This subnet is delegated to:

Microsoft.Web/serverFarms

This allows App Service to connect privately to:

Key Vault
PostgreSQL
Service Bus
AI Service
Storage Account

Terraform needs subnet delegation:

Microsoft.Web/serverFarms
3. Database Subnet
Subnet Name: database-subnet
CIDR: 10.0.3.0/24

This subnet is for:

Azure PostgreSQL Flexible Server

It should be private, not publicly accessible.

Terraform should create:

azurerm_postgresql_flexible_server
azurerm_postgresql_flexible_server_database
4. Private Endpoint Subnet
Subnet Name: private-endpoint-subnet
CIDR: 10.0.4.0/24

This subnet contains Private Endpoints for:

Key Vault
App Service
Service Bus
PostgreSQL
AI Service
Storage Account

Terraform should create:

azurerm_private_endpoint
azurerm_private_dns_zone
azurerm_private_dns_zone_virtual_network_link
Application Layer
App Service

App Service hosts your application.

It should have:

Public access disabled
Private Endpoint enabled
VNet Integration enabled
Managed Identity enabled

Terraform resources:

azurerm_service_plan
azurerm_linux_web_app / azurerm_windows_web_app
azurerm_private_endpoint
azurerm_app_service_virtual_network_swift_connection
Security Layer
Microsoft Entra ID

Entra ID is used for authentication.

Users authenticate first through Entra ID before accessing the application.

Terraform can configure App Service authentication using:

auth_settings_v2
Application Gateway + WAF

Application Gateway receives traffic from Front Door and forwards it to App Service.

It includes:

Frontend IP
Backend pool
HTTP/HTTPS listener
Routing rule
WAF policy

Terraform resources:

azurerm_application_gateway
azurerm_web_application_firewall_policy
Key Vault

Key Vault stores secrets such as:

Database connection string
Storage keys
Service Bus connection string
API keys

App Service should access Key Vault using Managed Identity.

Terraform resources:

azurerm_key_vault
azurerm_key_vault_secret
azurerm_role_assignment
azurerm_private_endpoint
Backend Services
PostgreSQL

Used as the application database.

Should be private and connected through:

Private access / Private Endpoint

Public access should be disabled.

Service Bus

Used for message-based communication.

Example use:

Failed job message
Success/failure notification
Background processing

App Service connects to Service Bus privately.

Storage Account

Used for file or document storage.

Should have:

Public network access disabled
Private Endpoint enabled
AI Service

Used for AI features such as:

OCR
prediction
document verification
chatbot
intelligent analysis

The app connects to AI Service through Private Endpoint.

NAT Gateway

NAT Gateway is used for controlled outbound internet access from the VNet.

It should be attached to the subnet that needs outbound internet, mainly:

App Service VNet Integration Subnet

Terraform resources:

azurerm_nat_gateway
azurerm_public_ip
azurerm_subnet_nat_gateway_association
Terraform Implementation Plan
Phase 1: Base Infrastructure

Create:

Resource Group
Virtual Network
Subnets
NSGs if required
NAT Gateway
Phase 2: Security and Identity

Create:

Key Vault
Managed Identity for App Service
Role assignments
Entra ID authentication for App Service
Phase 3: Application Gateway

Create:

Public IP for Application Gateway
Application Gateway
WAF Policy
Listener
Backend Pool
Routing Rule
Health Probe
Phase 4: App Service

Create:

App Service Plan
App Service
VNet Integration
Private Endpoint for App Service
App settings
Managed Identity
Phase 5: Backend Services

Create:

PostgreSQL Flexible Server
Storage Account
Service Bus Namespace + Queue
Azure AI Service
Phase 6: Private Endpoints and DNS

Create private endpoints for:

App Service
Key Vault
PostgreSQL
Storage Account
Service Bus
AI Service

Create private DNS zones and link them to VNet.

Phase 7: Monitoring

Add:

Log Analytics Workspace
Application Gateway diagnostics
App Service logs
Storage logs
PostgreSQL logs
Final Request Flow
User
 ↓
Microsoft Entra ID Authentication
 ↓
Azure Front Door
 ↓
Application Gateway
 ↓
WAF
 ↓
Listener
 ↓
Routing Rule
 ↓
App Service Private Endpoint
 ↓
App Service
 ↓
Private access to Key Vault / PostgreSQL / Service Bus / AI Service / Storage

This is the correct implementation order before writing Terraform.

