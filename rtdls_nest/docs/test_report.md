# Test Report Plan

## Completed technical validation
- TypeScript static check (`npm run lint`)
- Endpoint smoke tests (recommended via Postman/curl)

## Required test coverage for thesis defense
1. Unit tests
- AuthService credential validation
- Maintenance predictive-alert threshold logic
- Dashboard metrics aggregation

2. Integration tests
- Login -> create flight log -> dashboard metrics update
- Maintenance log creation -> alert creation
- Role-guarded endpoint access matrix

3. Security tests
- JWT required for protected routes
- Role mismatch returns 403
- Invalid payload blocked by validation pipe

4. UAT scripts
- Flight Ops daily log workflow
- Maintenance alert workflow
- Commander reporting workflow
- Auditor read-only workflow
