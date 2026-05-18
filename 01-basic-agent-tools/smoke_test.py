"""End-to-end smoke test for Demo 1 — exercises the same code the notebook runs."""
import asyncio
import os
from typing import Annotated

from dotenv import load_dotenv
from pydantic import Field

from agent_framework.foundry import FoundryChatClient
from agent_framework import AgentSession
from azure.identity.aio import AzureCliCredential


def pubmed_search(
    query: Annotated[str, Field(description="PubMed query.")],
    max_results: Annotated[int, Field(description="Max results.")] = 3,
) -> list[dict]:
    return [
        {"pmid": "39812345", "year": 2025, "title": f"Single-cell atlas of {query}"},
        {"pmid": "39798765", "year": 2024, "title": f"CRISPR screen in {query}"},
        {"pmid": "39654321", "year": 2024, "title": f"Outcomes after targeted therapy in {query}"},
    ][:max_results]


def gene_lookup(symbol: Annotated[str, Field(description="HGNC gene symbol.")]) -> dict:
    catalog = {
        "TP53":  {"chromosome": "17p13.1", "function": "Tumor suppressor.",
                  "disease_associations": ["Li-Fraumeni", "many cancers"]},
        "IKZF1": {"chromosome": "7p12.2",  "function": "Lymphoid TF.",
                  "disease_associations": ["B-ALL (poor prognosis when deleted)"]},
    }
    return catalog.get(symbol.upper(), {"error": f"No record for {symbol}."})


async def main():
    load_dotenv()
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    deployment = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    print(f"endpoint = {endpoint}")
    print(f"model    = {deployment}\n")

    async with AzureCliCredential() as credential:
        client = FoundryChatClient(
            project_endpoint=endpoint,
            model=deployment,
            credential=credential,
        )
        agent = client.as_agent(
            name="SmokeTestAgent",
            instructions=(
                "You are a research assistant. Use the tools for facts; "
                "cite PMIDs when referencing papers."
            ),
            tools=[pubmed_search, gene_lookup],
        )

        print("=== Turn 1: requires both tools ===")
        r1 = await agent.run(
            "Give me a brief on TP53 (one line of function, one line on diseases) "
            "and one recent paper on TP53 in pediatric ALL relapse."
        )
        print(r1)

        print("\n=== Turn 2: multi-turn session ===")
        session = AgentSession()
        r2 = await agent.run("I'm reviewing high-risk B-ALL cases.", session=session)
        print("A:", r2)
        r3 = await agent.run(
            "Which gene is most associated with poor prognosis there?",
            session=session,
        )
        print("A:", r3)


if __name__ == "__main__":
    asyncio.run(main())
