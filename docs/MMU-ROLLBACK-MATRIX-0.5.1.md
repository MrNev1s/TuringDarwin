# MMU rollback matrix — 0.5.1

| Forward step | Proposed inverse | Evidence required | Status |
|---|---|---|---|
| Allocate CPU model | Release CPU allocations | Leak/failure tests | Proven offline |
| Build tables | Discard byte images | Deterministic rebuild | Proven offline |
| Verify tables | Discard byte images | Independent walker | Proven offline |
| Allocate VRAM | Zero and release exact allocation | Allocator ownership and readback | Unproven |
| Write tables | Restore saved bytes or zero isolated allocation | Reliable VRAM read/write | Unproven |
| Write instance block | Restore saved instance bytes | Exact layout and readback | Unproven |
| Program PDB | Restore original PDB | Original-value capture and masked readback | Unproven |
| Invalidate TLB | Restore PDB and invalidate again | Bounded invalidate and timeout recovery | Unproven |
| Submit translation probe | Stop channel/engine and restore baseline | Isolated channel and fault capture | Blocked |

## Hardware eligibility rule

A device-writing step is ineligible until its inverse is independently proven.
The plan is therefore globally ineligible for hardware execution.

## Failure injection result

The offline simulator injects failure before each CPU-only phase and confirms
that rollback returns to the safe baseline. It intentionally refuses to model
unproven hardware inverses as successful.
