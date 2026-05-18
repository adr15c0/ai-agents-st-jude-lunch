"""
Minimal MCP tool server for the live demo.

Exposes two research-flavored tools the agent can call:
  - clinical_trials_search(condition, phase): (mocked) ClinicalTrials.gov-style
        lookup of open pediatric trials for a given condition.
  - variant_annotation(gene, variant):        (mocked) Annotation of a
        gene-level variant (pathogenicity, allele frequency, evidence).

Run stand-alone with:  python mcp_server.py
The agent notebook spawns this script as a subprocess over stdio.
"""

from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("pediatric-onc-research-tools")


@mcp.tool()
def clinical_trials_search(
    condition: str,
    phase: Optional[str] = None,
) -> list[dict]:
    """Search for (mocked) open pediatric clinical trials matching a condition.

    Args:
        condition: Disease or condition string, e.g. "relapsed B-ALL".
        phase: Optional phase filter, e.g. "II". Pass None for all phases.
    """
    catalog = [
        {
            "nct_id": "NCT09000001",
            "title": "Adaptive Salvage Therapy in Relapsed Pediatric B-ALL",
            "condition": "relapsed B-ALL",
            "phase": "II",
            "status": "Recruiting",
            "sites": ["Memphis, TN", "Seattle, WA"],
        },
        {
            "nct_id": "NCT09000002",
            "title": "CD19-CAR-T Re-infusion Strategies After Antigen Loss",
            "condition": "relapsed B-ALL",
            "phase": "I/II",
            "status": "Recruiting",
            "sites": ["Memphis, TN"],
        },
        {
            "nct_id": "NCT09000003",
            "title": "MYCN-Amplified Neuroblastoma: BET Inhibitor Combination",
            "condition": "high-risk neuroblastoma",
            "phase": "I",
            "status": "Recruiting",
            "sites": ["Memphis, TN", "Boston, MA"],
        },
        {
            "nct_id": "NCT09000004",
            "title": "Tumor Mutational Burden-Guided Immunotherapy in Pediatric Solid Tumors",
            "condition": "refractory solid tumors",
            "phase": "II",
            "status": "Recruiting",
            "sites": ["Memphis, TN"],
        },
    ]
    cond = condition.strip().lower()
    hits = [t for t in catalog if cond in t["condition"].lower()]
    if phase:
        hits = [t for t in hits if t["phase"].lower() == phase.strip().lower()]
    return hits


@mcp.tool()
def variant_annotation(gene: str, variant: str) -> dict:
    """Return (mocked) annotation for a gene-level variant.

    Args:
        gene: HGNC gene symbol, e.g. "TP53".
        variant: HGVS-style variant string, e.g. "p.R175H" or "c.524G>A".
    """
    catalog = {
        ("TP53", "p.R175H"): {
            "consequence": "missense_variant",
            "pathogenicity": "Pathogenic",
            "evidence": "Hotspot; loss of DNA-binding function; Li-Fraumeni-associated.",
            "gnomad_af": 0.0,
        },
        ("IKZF1", "p.N159S"): {
            "consequence": "missense_variant",
            "pathogenicity": "Likely pathogenic",
            "evidence": "Dominant-negative; recurrent in B-ALL; adverse prognostic marker.",
            "gnomad_af": 0.0,
        },
        ("MYCN", "amplification"): {
            "consequence": "copy_number_gain",
            "pathogenicity": "Pathogenic",
            "evidence": "Defines high-risk neuroblastoma; ≥10 copies typical threshold.",
            "gnomad_af": None,
        },
    }
    key = (gene.upper(), variant.strip())
    if key in catalog:
        return {"gene": key[0], "variant": key[1], **catalog[key]}
    return {
        "gene": gene.upper(),
        "variant": variant,
        "pathogenicity": "Unknown",
        "evidence": "No record in demo annotation catalog.",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
