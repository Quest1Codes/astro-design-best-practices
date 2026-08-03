# Networking

## The baseline: what reaches what today

Before changing anything, establish the current reachability map for each machine group: which databases, file shares, internal APIs, MQ endpoints, and (if relevant) mainframe-adjacent gateways does each machine reach, over which ports, and through which firewall rules. This is the baseline the new environment's network posture must reproduce (or deliberately change, with sign-off) — get it from the network team's existing rule documentation, not by guessing from job commands alone (a command might call a hostname without revealing the port or protocol).

## Astro Cloud (Hosted) network model

Hosted workers execute outside the customer's network and reach downstream systems over the public internet or through Astro's supported private-connectivity options. Practically, this means:

- Downstream systems that currently only accept connections from specific on-prem IP ranges need new firewall rules allow-listing Astro's egress ranges (or the specific private-connectivity mechanism in use) — get Astro's current documented egress ranges/connectivity options directly rather than assuming a fixed IP list stays valid; these are platform-maintained and can change.
- Systems with no path to be reached from outside the network at all (no route, policy forbids it) are a hard signal toward Hybrid for that machine group, not a Hosted-with-more-firewall-rules situation.

## Astro Hybrid network model

Hybrid workers run inside the customer's own network/VPC, so they inherit whatever network position that VPC already has — reachability to on-prem systems is typically unchanged from today, which is exactly why Hybrid is the right answer when the network boundary itself (not the software) is the constraint.

## Practical firewall change management

- Track firewall change requests **per machine group**, not per job — many jobs on one machine typically need the same network paths, and requesting them individually creates duplicate tickets and drift between what was requested and what was actually opened.
- Confirm each opened path with an actual connection test from the real target environment (a `nc`/`telnet`-equivalent check, or better, an actual Airflow Connection test) before marking a machine group's networking `complete` — a ticket marked "done" by the network team is not the same as a verified-working path.
- Keep a rollback-relevant note of what was opened where, in case a wave needs to roll back — reverting a DAG pause is easy; reverting a firewall change that other things now depend on is not, so avoid closing old on-prem paths until the new path has run clean for a full cycle.

## Common gap: transitive dependencies

A job's own command might only obviously touch one system, but its script may shell out to something else (a wrapped call to another internal service, a shared config file that itself references a different host). `agent_fleet_inventory.py`'s flags surface known patterns (FT partner machines, cross-machine conditions) but cannot read inside arbitrary scripts — read the actual job scripts for a machine group before finalizing its network plan, don't rely on the JIL-level view alone.
