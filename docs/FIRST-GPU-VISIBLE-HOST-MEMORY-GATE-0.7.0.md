# First GPU-visible host-memory gate after 0.7.0

This document is a boundary, not an authorisation.

Even after the host physical-segment test passes, the physical address must not
be given to TU116 until all of the following exist:

1. exact page-table allocation ownership and cleanup;
2. byte-exact PTE/PDE image generated from the observed host physical address;
3. a separately allocated instance/PDB block;
4. source-backed BAR1/BAR2 and TLB-invalidation register sequence;
5. bounded timeouts for every status poll;
6. pre-recorded original register state and an inverse rollback sequence;
7. a way to prove no existing firmware or GOP context is overwritten;
8. stable-EFI recovery and one-attempt policy.

The 0.7.0 mode performs none of these operations and therefore cannot expose
host memory to the GPU.
