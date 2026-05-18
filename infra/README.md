# Azure AI Foundry Agent Service: Standard Agent Setup with Public Networking

## Required Permissions
1. To deploy this template and create a Standard Setup project you need the follow permissions:
    * **Foundry Account Owner**
    * **Role Based Access Administrator**

For more information on the setup process, [see the getting started documentation.](https://learn.microsoft.com/en-us/azure/ai-services/agents/environment-setup)

For more details on the standard agent setup, see the [standard agent setup concept page.](https://learn.microsoft.com/en-us/azure/ai-services/agents/concepts/standard-agent-setup)

## Steps

[![Deploy To Azure](https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/1-CONTRIBUTION-GUIDE/images/deploytoazure.svg?sanitize=true)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fazure-ai-foundry%2Ffoundry-samples%2Frefs%2Fheads%2Fmain%2Finfrastructure%2Finfrastructure-setup-bicep%2F41-standard-agent-setup%2Fazuredeploy.json)

### Deployment Context

| Setting          | Value                                  |
| ---------------- | -------------------------------------- |
| Subscription ID  | `b14476f5-89c5-4531-875e-afbdaa3a5ca1` |
| Subscription     | `MCAPS-Hybrid-REQ-54957-2023-alrui`    |
| Tenant ID        | `16b3c013-d300-468d-ac64-7eda0820b6d3` |
| Resource Group   | `ai-agents-st-jude-lunch-rg`           |
| Location         | `westus3`                              |

1. Set the active subscription:

```bash
    az account set --subscription b14476f5-89c5-4531-875e-afbdaa3a5ca1
```

2. Create the resource group:

```bash
    az group create --name ai-agents-st-jude-lunch-rg --location westus3
```

3. Deploy the template:

```bash
    az deployment group create \
      --resource-group ai-agents-st-jude-lunch-rg \
      --template-file main.bicep \
      --parameters azuredeploy.parameters.json
```

## Use exitsing resources

**Azure Cosmos DB for NoSQL**
- Your existing Azure Cosmos DB for NoSQL Account used in standard setup must have at least a total throughput limit of at least 3000 RU/s. Both Provisioned Thoughtput and Serverless are supported.
    - 3 containers will be provisioned in your existing Cosmos DB account and each need 1000 RU/s

> **⚠️ Important: Cosmos DB Connection Requirements**
>
> When creating the Cosmos DB connection (e.g., via REST API or ARM), ensure the following:
> - The `authType` **must** be set to `AAD`. This is the only supported authentication type for the Cosmos DB connection used by the Agent Service.
> - The `metadata` section **must** include the `ResourceId` property, set to the full Azure Resource ID of your Cosmos DB account. The Agent Service relies on this property to correctly identify and connect to your Cosmos DB resource. Omitting `ResourceId` from the metadata will cause the connection to fail.
>
> Example connection properties:
> ```json
> {
>   "category": "CosmosDB",
>   "authType": "AAD",
>   "metadata": {
>     "ApiType": "Azure",
>     "ResourceId": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.DocumentDB/databaseAccounts/{cosmosDbAccountName}",
>     "location": "{region}"
>   }
> }
> ```
