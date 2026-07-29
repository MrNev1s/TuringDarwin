# TU102 MMU register exclusion decision

## Decision

No new MMU register is admitted to the read-only TuringProbe whitelist at this
stage.

## Rationale

The registers found in the TU102 VMM and BAR paths are commands, queue state,
PDB selectors, fault-buffer controls or busy indicators. They are not required
to derive the page-table format, which is already available from source.

The machine-readable matrix is:

```text
research/mmu-register-exclusion-matrix.csv
```

A register can move from REJECT only after all of the following are proven:

1. exact function and field definition from at least two independent primary
   source paths where available;
2. no write-to-trigger, clear-on-read, read-to-pop, acknowledge or selector
   behaviour;
3. no prerequisite firmware, BAR window, page directory or fault buffer;
4. a concrete question whose answer cannot be obtained offline;
5. bounded one-shot access with before/after PCI and Bus Master invariants;
6. source, binary and real-hardware compatibility gates.

None of the current candidates satisfies all six conditions.
