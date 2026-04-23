Performance Overheads Introduced by Mesh (Athena Gateway)

- Factors: extra hop(s), TLS handshakes, policy evaluation, telemetry sampling.
- Estimation approach: per-request overhead model, empirical measurement via baseline tests.
- Mitigation: tune sampling rate, enable adaptive TLS caching, optimize path length.
