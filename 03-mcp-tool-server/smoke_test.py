"""End-to-end smoke test for Demo 3 \u2014 MCP stdio server + Foundry agent."""
import asyncio
import os
import sys

from dotenv import load_dotenv

from agent_framework import MCPStdioTool
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential


async def main():
    load_dotenv()
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    deployment = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]

    async with AzureCliCredential() as credential:
        client = FoundryChatClient(
            project_endpoint=endpoint,
            model=deployment,
            credential=credential,
        )

        mcp_tools = MCPStdioTool(
            name="pediatric-onc-research-tools",
            command=sys.executable,
            args=["mcp_server.py"],
        )

        agent = client.as_agent(
            name="OncoMCPSmoke",
            instructions=(
                "You are a pediatric oncology research assistant. Use the MCP tools "
                "to look up open clinical trials and annotate gene variants. Cite "
                "NCT IDs and variant pathogenicity verbatim."
            ),
            tools=[mcp_tools],
        )

        print("=== Q1: clinical trials ===")
        print(await agent.run("What open phase II trials do we have for relapsed B-ALL?"))

        print("\n=== Q2: variant annotation ===")
        print(await agent.run("How would you classify TP53 p.R175H, and what's the supporting evidence?"))

        print("\n=== Q3: composed (both tools) ===")
        print(await agent.run(
            "I have a relapsed B-ALL patient with a confirmed IKZF1 p.N159S variant. "
            "Annotate the variant and tell me which open trials they may be eligible for."
        ))


if __name__ == "__main__":
    asyncio.run(main())
