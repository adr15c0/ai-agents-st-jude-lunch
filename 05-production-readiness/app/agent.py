"""Agent factory \u2014 builds the literature-triage agent from Demo 1."""
from __future__ import annotations

import os
from typing import Annotated

from agent_framework.foundry import FoundryChatClient
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


def build_agent_client() -> tuple[FoundryChatClient, DefaultAzureCredential]:
    """Return a connected FoundryChatClient and the credential to close on shutdown.

    Uses DefaultAzureCredential so the same code runs locally (via `az login`)
    and in the Container App (via its system-assigned managed identity).
    """
    credential = DefaultAzureCredential()
    client = FoundryChatClient(
        project_endpoint=PROJECT_ENDPOINT,
        model=MODEL_DEPLOYMENT,
        credential=credential,
    )
    return client, credential


def create_agent(client: FoundryChatClient):
    return client.as_agent(
        name="LiteratureTriageAgent",
        instructions=(
            "You are a research assistant helping pediatric oncology investigators "
            "triage literature and gene-level evidence. Use the available tools "
            "instead of relying on memory. Cite PMIDs when referencing papers."
        ),
        tools=[pubmed_search, gene_lookup],
    )
