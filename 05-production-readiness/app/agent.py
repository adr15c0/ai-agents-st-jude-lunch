"""Agent factory — builds the literature-triage agent from Demo 1.

Kept in its own module so the FastAPI app and any tests can import it.
"""
from __future__ import annotations

import os
from typing import Annotated

from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential
from pydantic import Field

PROJECT_ENDPOINT = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
MODEL_DEPLOYMENT = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]


def pubmed_search(
    query: Annotated[str, Field(description="Free-text PubMed query.")],
    max_results: Annotated[int, Field(description="Max results.")] = 3,
) -> list[dict]:
    """Mocked PubMed search. Replace with real Entrez/E-utilities call."""
    return [
        {"pmid": "39812345", "year": 2025, "title": f"Single-cell atlas of {query}"},
        {"pmid": "39798765", "year": 2024, "title": f"CRISPR screen in {query}"},
        {"pmid": "39654321", "year": 2024, "title": f"Outcomes after targeted therapy in {query}"},
    ][:max_results]


def gene_lookup(symbol: Annotated[str, Field(description="HGNC gene symbol.")]) -> dict:
    """Mocked gene lookup. Replace with MyGene.info or an internal KB."""
    catalog = {
        "TP53":  {"chromosome": "17p13.1", "function": "Tumor suppressor."},
        "IKZF1": {"chromosome": "7p12.2",  "function": "Lymphoid TF; B-ALL prognostic marker."},
        "MYCN":  {"chromosome": "2p24.3",  "function": "Proto-oncogene; high-risk neuroblastoma."},
    }
    return catalog.get(symbol.upper(), {"error": f"No record for {symbol}."})


def build_agent_client() -> tuple[AzureAIAgentClient, DefaultAzureCredential]:
    """Return a connected AzureAIAgentClient and the credential to close on shutdown.

    Uses DefaultAzureCredential so the same code runs locally (via `az login`)
    and in the Container App (via its system-assigned managed identity).
    """
    credential = DefaultAzureCredential()
    client = AzureAIAgentClient(
        project_endpoint=PROJECT_ENDPOINT,
        model_deployment_name=MODEL_DEPLOYMENT,
        async_credential=credential,
    )
    return client, credential


def create_agent(client: AzureAIAgentClient):
    return client.create_agent(
        name="LiteratureTriageAgent",
        instructions=(
            "You are a research assistant helping pediatric oncology investigators "
            "triage literature and gene-level evidence. Use the available tools "
            "instead of relying on memory. Cite PMIDs when referencing papers."
        ),
        tools=[pubmed_search, gene_lookup],
    )
