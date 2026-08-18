# Vertical Overlay: Government / Public Sector (FedRAMP / Data Residency)

Government and public sector deployments impose the strictest requirements around data sovereignty, security posture, and sometimes network isolation. This file covers the architectural choices for deploying Airflow on Astro within these constraints.

## FedRAMP

> **NEEDS_EXEC_CHECK**: FedRAMP Authorization status for Astronomer Astro must be verified directly against the [Astronomer Trust Center](https://trust.astronomer.io/) or the official FedRAMP Marketplace at the time of procurement. Authorization status changes and should not be assumed from any documentation including this file.

**Current Guidance**: If FedRAMP authorization is required, the recommended path is **Astro Private Cloud** (self-hosted) deployed within a FedRAMP-authorized cloud infrastructure (e.g., AWS GovCloud, Azure Government). Astronomer Private Cloud gives the customer full infrastructure control, which is a prerequisite for FedRAMP compliance operations regardless of Astronomer's own authorization status [B1].

## Data Residency

For government agencies with explicit data residency mandates (e.g., data must not leave a specific country or region):

| Architecture | Data Residency Guarantee | Notes |
|---|---|---|
| **Astro Cloud (Dedicated Cluster)** | Region-locked (single-cloud, single-region deployment) | Control Plane is Astronomer-hosted; customer must verify the control plane's region against data residency mandate [B1]. |
| **Astro Private Cloud** | Full — all infrastructure runs in your own environment | Strongest data residency guarantee; data never leaves your network [B1]. |
| **Remote Execution** | Task execution plane stays in your perimeter | Outbound-only connections to the Astronomer Orchestration Plane; raw data never transits to Astronomer's infrastructure [B1]. |

## Recommended Architecture for Government Workloads

For most government agency use-cases:
1. **Deploy Astro Private Cloud** within your existing FedRAMP-authorized cloud environment (GovCloud or equivalent).
2. Use **Terraform** (Astro Terraform Provider) to manage infrastructure-as-code, enabling consistent security posture across agency clusters and simplifying FedRAMP continuous monitoring (ConMon) requirements [B2].
3. Enforce **network isolation**: air-gapped installation support is available for Astro Private Cloud for environments with no outbound internet connectivity [B1].
4. Enable **SSO/IdP integration** with your agency's identity provider (e.g., PIV/CAC card authentication via a SAML bridge) [B1].

## Certifications Held by Astronomer

Astronomer maintains SOC 2 Type II, HIPAA, PCI-DSS, and GDPR certifications [B1]. Government customers should request the current certification list and any Authority to Operate (ATO) documentation directly from Astronomer's sales or security team.

## Sources

[B1] Astronomer Docs & Trust Center — Deployment models (Private Cloud, Remote Execution, Dedicated Cluster), data residency capabilities, and certifications (accessed 2026-08-10)
[B2] Astronomer Docs — Terraform Provider for infrastructure-as-code management (accessed 2026-08-10)
