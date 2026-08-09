# Runtime Memory Policies

The effective default for every component is its Programme C contract.
Documented Unbounded and Manual policies preserve historical behaviour.
Bounded FIFO, LRU, Fixed Size, Ring Buffer, Time Window, or Disabled policies
activate only through an explicit matching contract.

Runtime adoption never uses GC timing, system time, object addresses, random
values, or unordered hash traversal. Immutable registry records state the
adoption mode and confirm preservation of defaults.
