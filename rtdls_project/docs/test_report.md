# Test Report

## Scope
- Unit tests
- Integration tests
- Role-access tests
- Security access tests
- Report export tests

## Implemented Test Cases
1. `accounts/tests.py`
- Login audit log generated
- Logout audit log generated
- Role change audit log generated
- API login throttling enforced

2. `operations/tests.py`
- Flight Ops can create flight logs via API
- Auditor cannot create flight logs
- Flight Ops can create flight telemetry (`FlightData`) via API

3. `maintenance/tests.py`
- Predictive maintenance alert generated when threshold exceeded

4. `reports_app/tests.py`
- Daily report PDF generation
- Utilization report XLSX generation
- CSV export spreadsheet-formula sanitization

5. `dashboard/tests.py`
- Anonymous users redirected from dashboard
- Authenticated users can access dashboard

## Expected Outcome
- All tests should pass once dependencies are installed and migrations are applied.
