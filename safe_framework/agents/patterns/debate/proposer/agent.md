# Debate Proposer

_Argues the affirmative or initial position, gathering supporting evidence._

## Overview

The Debate Proposer is the **proposer** role in the **debate** pattern. Two agents argue opposing positions; a judge synthesises the best answer — surfaces edge cases and reduces single-agent bias in risk or investment analysis.

## Pattern Diagram

```mermaid
flowchart LR
    classDef active fill:#0078D4,color:#fff,stroke:#005A9E
    Input([Topic]) --> Proposer
    Input --> Challenger
    Proposer --> Judge
    Challenger --> Judge
    Judge --> Output([Verdict])
    class Proposer active
```

## Contract Specification

### Inputs
**topic** (string, required): The topic or question to debate  
**context** (object, optional): Additional context  


### Outputs
**position** (string): The proposer's argued position  
**evidence** (array): Supporting evidence and sources  
**strength** (float): Self-assessed argument strength 0.0–1.0  


## Azure Tools

| Tool ID | Display Name | Service | Purpose in this role |
|---|---|---|---|
| `iq-foundry` | Foundry IQ | Indexed org knowledge via Azure AI Search | Retrieve internal evidence supporting position A |
| `iq-web` | Web IQ | Live public web and news via Bing grounding | Gather external evidence supporting position A |

## Use Cases

1. **Investment case for**
2. **Risk analysis — upside**
3. **Policy argument for**


## Limitations

- Both proposer and challenger are positionally biased by design — the judge must remain impartial
- Token usage is ~3× a single-agent analysis — reserve for high-stakes decisions

## Related Roles

- **Proposer** + **Challenger** → **Judge** is the argument → synthesis chain
- See also: `self-consistency` for N identical attempts rather than two opposing positions

---

**Status:** Production Ready  
**Version:** 1.0  
**Framework:** SAFE 1.0  
**Last Updated:** 2026-06-21
