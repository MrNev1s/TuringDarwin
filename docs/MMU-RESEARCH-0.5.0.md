# TuringProbe 0.5.0 — TU116 MMU research stage

## Status

**OFFLINE MODEL IMPLEMENTED. NO NEW HARDWARE REGISTER ACCESS.**

Version 0.5.0 is deliberately an offline research release. It preserves the
already verified PCI, identity, PTOP and FB-capacity paths, but adds no MMIO
register to the whitelist and adds no new boot argument.

The test EFI must remain in `-tdprobe` mode. Do not use `-tdmmio-read`,
`-tdtop-read` or `-tdfb-read` again for this stage.

## Important correction to 0.4.0 metadata

Version 0.4.0 published `TPMMUSourceDefaultBigPageKiB = 16`. That value was
incorrect: the Nouveau value `16` is a **page shift**, not a size in KiB.

- shift 12 = `1 << 12` bytes = 4 KiB;
- shift 16 = `1 << 16` bytes = 64 KiB.

The hardware FB-capacity result is unaffected. No MMU register was read and no
page table was created in 0.4.0. The bug existed only in source-labelled
telemetry/documentation. Version 0.5.0 corrects the future property to 64 KiB
and publishes both shift and byte-derived sizes to make this class of error
harder to repeat.

## Confirmed architecture facts

### TU116 dispatch

Nouveau routes TU116 through the TU102 MMU/VMM implementations. The static
`tu102_mmu` profile specifies:

- 47-bit DMA-address capability;
- GF100 MMU class;
- GF100 memory-object class;
- GP100 VMM class;
- a 16-entry kind map;
- invalid kind `0x07`;
- system-memory kinds enabled.

`dma_bits = 47` is a physical/DMA limit. It must not be described as the
virtual-address width.

### Page sizes and virtual-address hierarchy

The TU102 VMM page list includes shifts 21, 16 and 12. NVIDIA UVM independently
reports the same 2 MiB, 64 KiB and 4 KiB page sizes, a five-depth tree for
4/64 KiB mappings, and a four-depth tree for 2 MiB mappings. Nouveau's descriptor arrays
make their meaning explicit:

#### 4 KiB path

```text
VA[48:47] root        2 bits
VA[46:38] PD2         9 bits
VA[37:29] PD1         9 bits
VA[28:21] PD0         8 bits
VA[20:12] small PTE   9 bits
VA[11:0]  offset     12 bits
```

Total: `2 + 9 + 9 + 8 + 9 + 12 = 49` virtual-address bits.

#### 64 KiB path

```text
VA[48:47] root        2 bits
VA[46:38] PD2         9 bits
VA[37:29] PD1         9 bits
VA[28:21] PD0         8 bits
VA[20:16] large PTE   5 bits
VA[15:0]  offset     16 bits
```

Total: `2 + 9 + 9 + 8 + 5 + 16 = 49` virtual-address bits.

#### 2 MiB path

```text
VA[48:47] root        2 bits
VA[46:38] PD2         9 bits
VA[37:29] PD1         9 bits
VA[28:21] PD0 leaf    8 bits
VA[20:0]  offset     21 bits
```

Total: `2 + 9 + 9 + 8 + 21 = 49` virtual-address bits. The 2 MiB PTE occupies
the low 64-bit half of the 16-byte PD0 entry; the high half remains zero.

The 49-bit result is a direct arithmetic inference from the published Nouveau
descriptors, not a value read from hardware.

### Table geometry

| Table | Index bits | Entry bytes | Logical entries | Logical bytes | Coverage per entry/table |
|---|---:|---:|---:|---:|---:|
| Small PTE table | 9 | 8 | 512 | 4096 | 4 KiB / 2 MiB |
| PD0 direct leaf | 8 | 16 | 256 | 4096 | 2 MiB / 512 MiB |
| Large PTE table | 5 | 8 | 32 | 256 | 64 KiB / 2 MiB |
| PD0 | 8 | 16 | 256 | 4096 | 2 MiB / 512 MiB |
| PD1 | 9 | 8 | 512 | 4096 | 512 MiB / 256 GiB |
| PD2 | 9 | 8 | 512 | 4096 | 256 GiB / 128 TiB |
| Root | 2 | 8 | 4 | 32 logical, 4 KiB allocation alignment | 128 TiB / 512 TiB |

The 16-byte PD0 entry contains two 64-bit pointers. The low half points to
the large-page (LPT) table and the high half points to the small-page (SPT)
table. Both leaf formats cover the
same 2 MiB virtual region.

## PTE model

Nouveau constructs a GP100/TU102 PTE as:

```text
(physical_address >> 4) | attributes
```

Confirmed attribute construction:

| Field | Bits | Meaning |
|---|---:|---|
| VALID | 0 | entry valid |
| APERTURE | 2:1 | VRAM/system target |
| VOL | 3 | volatile/system-coherent semantics |
| PRIV | 5 | privileged access |
| RO | 6 | read-only |
| ATOMIC_DISABLE | 7 | disable atomic access in PFN path |
| COMPTAGLINE | starts at 36 | compression metadata on Turing |
| KIND | 63:56 | memory kind |

The model now distinguishes a logical kind index from the hardware kind bits.
Nouveau validates the 0..15 logical index against `tu102_mmu_kind`; without an
authorised GSP/PMU compression path, compressed logical kinds are replaced by
their uncompressed mapped hardware kind. Entries mapping to invalid kind
`0x07` are rejected.

Compression is deliberately fail-closed: any non-zero COMPTAGLINE request is
rejected. A future first mapping must be uncompressed. The exact initial kind
selection remains an explicit open decision: Nouveau defaults to logical kind
0, while NVIDIA UVM uses its generic-memory hardware kind. No hardware mapping
will be proposed until that difference is resolved.

## PDE model

Nouveau's GP100/TU102 PDE helper uses:

- entry size 8 bytes at higher levels;
- a 16-byte paired entry at PD0;
- page-table address encoded as `table_address >> 4`;
- aperture code 1 for VRAM;
- aperture code 2 plus VOL for coherent system memory;
- aperture code 3 for non-coherent system memory.

The root/PDB instance word additionally selects VER2 and a 64 KiB large-page
mode. Modelling that word offline is allowed; writing it to an instance block
is not authorised.

## Why a read-only MMU-register probe is not being created

The source audit did not identify a useful static MMU capability register that
is both necessary and clearly side-effect-free. The obvious TU102 MMU block is
operational:

- `0xB830A0` and `0xB830A4` receive a PDB address;
- writing bit 31 at `0xB830B0` triggers invalidation;
- the driver then polls bit 31 at `0xB830B0` for completion.

Fault-buffer registers are queue state, not immutable capability data. BAR1/2
PDB registers program address translation windows. Reading those blocks would
not materially improve the offline format model and would weaken the safety
boundary.

Therefore the current hardware whitelist for new MMU registers is:

```text
EMPTY
```

This is a positive research result: the next useful milestone is not another
register dump. It is a verified software page-table builder.

## Faster development method

The project now separates work into three parallel tracks:

1. **Format track** — page geometry, PTE/PDE/PDB encoders and decoders.
2. **Safety track** — exclusion matrix for operational MMU/BAR/fault registers.
3. **Execution track** — future memory allocation, BAR mapping and engine
   submission, kept blocked until the first two tracks provide test vectors.

The offline model runs tens of thousands of deterministic randomized vectors
in seconds. That replaces repeated risky boots while detecting alignment,
field-width and hierarchy errors much earlier.

## NVIDIA UVM cross-check

NVIDIA's current open UVM Turing MMU implementation independently confirms:

- VA bits `48:47`, `46:38`, `37:29`, `28:21`, then `20:16` or `20:12`;
- `num_va_bits = 49`;
- 4 KiB, 64 KiB and 2 MiB page sizes;
- 16-byte dual PD0 entries with big/64 KiB in the low half and small/4 KiB in
  the high half;
- 8-byte entries elsewhere;
- the PTE fields VALID, APERTURE, VOL, PRIVILEGE, READ_ONLY, ATOMIC_DISABLE and
  KIND used by the model.

This is a genuine independent cross-check, not a hardware acceptance test.

## Implemented offline tests

`tools/test-mmu-model.py` verifies:

- exact 4 KiB, 64 KiB and 2 MiB geometry;
- 49-bit VA split/compose round trips;
- 60,000 randomized VA vectors;
- 60,000 randomized PTE/PDE vectors;
- aperture and attribute encoding;
- 128-bit PD0 pair layout;
- VER2/64 KiB instance-word bits;
- rejection of invalid kinds;
- rejection of misalignment and out-of-range addresses;
- logical-kind fallback and fail-closed compression policy;
- zero device access.

`tools/test-page-table-image.py` additionally verifies 30,000 complete
byte-exact build/walk round trips across 4 KiB, 64 KiB and 2 MiB mappings,
including PD0 half ordering and malformed-image rejection.

## Proof boundary

This stage proves a coherent software interpretation of publicly available
TU102/TU116 page-table formats. It does not prove:

- that a page table created by TuringDarwin is accepted by the GPU;
- that VRAM can be allocated or CPU-mapped;
- that BAR1/BAR2 can be safely programmed;
- that TLB invalidation works;
- that faults can be handled;
- that Copy Engine or any other engine can submit commands.

## Next gate

The source cross-check and byte-exact RAM image generator are now complete.
Before any hardware write is even proposed:

1. add fixed golden vectors independently transcribed from NVIDIA UVM headers;
2. model multi-page ranges, mixed 4 KiB/64 KiB regions and 2 MiB promotion;
3. implement overlap, aliasing and permission-conflict detection;
4. model a CPU-only VRAM allocator without touching BAR1/BAR2;
5. write a future transaction/state-machine document for instance block, BAR
   windows and TLB invalidation, with rollback and bounded timeout rules;
6. obtain a separate explicit design approval before creating any write code.

No MMIO write or new hardware offset is authorised by this document.
