Migration Sidecar Injection Steps for Athena Gateway

- Step 0: Prepare namespace with Istio injection label and ensure Istio control plane readiness.
- Step 1: Identify services to migrate and mark them for injection.
- Step 2: Apply Deployment manifests with appropriate annotations if needed.
- Step 3: Validate sidecar proxies are injected in Pods and traffic passes through mesh.
- Step 4: Incrementally enable mesh-specific routing rules via VirtualService.
- Step 5: Monitor performance and rollback if regressions observed.
