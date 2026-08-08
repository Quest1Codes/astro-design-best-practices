# Network Isolation and VPC Peering (Hybrid)

AutoSys used OS-level TCP connectivity between the Event Server and agents — no cloud VPC model. On Astro, network topology is the primary physical isolation control and is the deciding factor for whether a **Standard Cluster** or a **Dedicated Cluster** is required.

## Cluster type decision

| Requirement | Standard Cluster (multi-tenant) | Dedicated Cluster (single-tenant) |
|---|---|---|
| Namespace-level isolation | ✓ | ✓ |
| VPC peering to private data | ✗ | ✓ |
| AWS PrivateLink | ✗ | ✓ |
| Transit Gateway / VPN | ✗ | ✓ |
| Private egress mode (no public internet) | ✗ | ✓ (AWS) |
| Remote Execution agents | ✗ | ✓ |
| Data residency / sovereignty | Limited | Full control |

For any AutoSys migration that involves connecting Airflow workers to on-premises databases, private cloud APIs, or VPC-resident services without public endpoints, a **Dedicated Cluster** is required.

## Private connectivity options (Dedicated Cluster only)

| Method | Use case |
|---|---|
| **VPC Peering / VNet Peering** | Most private connectivity use cases; recommended first choice |
| **AWS PrivateLink** | AWS services (S3, SQS, ECR) or connecting Remote Execution agents to Astro control plane without public internet exposure |
| **Transit Gateway** | Hub-and-spoke enterprise networking to connect Astro to multiple on-premises or multi-account VPCs |
| **VPN** | Site-to-site connectivity to corporate network |

## Remote Execution (Hybrid architecture)

For AutoSys estates where data must never leave the on-premises network:

```
Astro Control Plane (cloud — orchestration only)
  ↕ outbound-only connection
Remote Execution Agent (on-premises / private VPC)
  → runs Airflow task code on local infrastructure
  → accesses on-premises databases/APIs locally
```

Key properties:
- Agents communicate with the Astro control plane using **outbound-only** connections — no inbound firewall holes required
- Task code and data remain on the customer's infrastructure
- Secrets backend must be accessible from the agent's network

## Private egress mode (AWS Dedicated Cluster)

Disables all public internet egress from the Deployment — a "data loss protection" architecture. All outbound traffic must go through a configured VPC endpoint or peering connection.

## Deployment model (Axis A — H rating)

| Deployment model | Network design |
|---|---|
| **Astro Hosted (Standard)** | Namespace isolation only; public endpoint access; no private networking |
| **Astro Hosted (Dedicated)** | VPC peering, PrivateLink, private egress available |
| **Astro Hybrid / Remote Execution** | Agent on-premises; control plane cloud; outbound-only connectivity |

## Compliance callout (Axis E — H rating)

For data residency (EU GDPR, Australia Privacy Act) or ITAR/export control requirements:
- Use Dedicated Cluster in the required data-residency region
- Enable Private Egress Mode to prevent data exfiltration via public internet
- Use Remote Execution if processing must remain on-premises entirely

## Sources

[Network facts] Astronomer Docs — Dedicated clusters and networking: https://www.astronomer.io/docs/astro/create-dedicated-cluster (accessed 2026-08-08)
[Remote Execution] Astronomer Docs — Remote Execution: https://www.astronomer.io/docs/astro/remote-execution (accessed 2026-08-08)
[Private egress] Astronomer Docs — Private network egress: https://www.astronomer.io/docs/astro/private-network-egress (accessed 2026-08-08)
[PrivateLink] Astronomer Docs — AWS PrivateLink configuration (accessed 2026-08-08)
