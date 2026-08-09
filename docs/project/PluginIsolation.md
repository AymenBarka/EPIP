# Plugin Isolation

Each plugin receives a newly constructed immutable `PluginContext` containing:

- the immutable market context;
- an isolated structural copy of the registry;
- an isolated EventBus;
- the configured clock and identity generator.

Registry changes made through that context are discarded after execution. Events published by a
plugin are recorded locally and become visible on the Kernel EventBus only after the whole pipeline
commits. Temporary results from earlier plugins are never passed to later plugins.

Plugins must complete and join plugin-owned threads before returning. Effects performed directly
through external services are outside the local Kernel transaction.
