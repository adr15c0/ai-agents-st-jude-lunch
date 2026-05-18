"""End-to-end smoke test for Demo 2 \u2014 file-search RAG against the protocol doc."""
import asyncio
import glob
import os

from dotenv import load_dotenv

from agent_framework.foundry import FoundryChatClient
from azure.ai.agents.aio import AgentsClient
from azure.ai.agents.models import FilePurpose
from azure.identity.aio import AzureCliCredential


async def main():
    load_dotenv()
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    deployment = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]

    data_files = glob.glob("data/*")
    print("uploading:", data_files)

    async with AzureCliCredential() as credential:
        agents = AgentsClient(endpoint=endpoint, credential=credential)
        file_ids = []
        for path in data_files:
            f = await agents.files.upload_and_poll(file_path=path, purpose=FilePurpose.AGENTS)
            file_ids.append(f.id)
            print(f"  uploaded {path} -> {f.id}")

        vs = await agents.vector_stores.create_and_poll(
            file_ids=file_ids, name="ped-all-protocol-vs-smoke"
        )
        print("vector store:", vs.id)

        try:
            client = FoundryChatClient(
                project_endpoint=endpoint,
                model=deployment,
                credential=credential,
            )
            file_search = client.get_file_search_tool(vector_store_ids=[vs.id])
            agent = client.as_agent(
                name="ProtocolQASmoke",
                instructions=(
                    "Answer using ONLY the attached protocol document. "
                    "If not in the docs, say so and recommend consulting the PI."
                ),
                tools=[file_search],
            )

            print("\n=== Q1: primary objective ===")
            print(await agent.run("What is the primary objective of PED-ALL-2025-01?"))

            print("\n=== Q2: sample collection timepoints ===")
            print(await agent.run("At which time points do we collect bone marrow vs cfDNA?"))

            print("\n=== Q3: out of scope (should refuse) ===")
            print(await agent.run("What's the recommended dose of EX-1042 for adults with AML?"))
        finally:
            await agents.vector_stores.delete(vs.id)
            for fid in file_ids:
                await agents.files.delete(fid)
            await agents.close()
            print("\ncleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
