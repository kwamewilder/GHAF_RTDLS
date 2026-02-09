import { Controller, Get, Header, Query, Res, UseGuards } from '@nestjs/common';
import { Response } from 'express';
import { Roles } from '../common/decorators/roles.decorator';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { RolesGuard } from '../common/guards/roles.guard';
import { AppRole } from '../common/types/role.type';
import { ReportsService } from './reports.service';

@Controller('reports')
@UseGuards(JwtAuthGuard, RolesGuard)
export class ReportsController {
  constructor(private readonly reportsService: ReportsService) {}

  @Get('daily-flight')
  @Roles(AppRole.ADMIN, AppRole.FLIGHT_OPS, AppRole.COMMANDER, AppRole.AUDITOR)
  async dailyFlight(@Query('format') format = 'pdf', @Res() res: Response) {
    const data = await this.reportsService.dailyFlights();

    if (format === 'xlsx') {
      const buffer = await this.reportsService.buildXlsx(
        'Daily Flights',
        ['Aircraft', 'Pilot', 'Mission', 'DateTime', 'Hours', 'Fuel', 'Departure', 'Arrival', 'LoggedBy'],
        data.map((row) => [
          row.aircraft.tailNumber,
          row.pilotName,
          row.missionType,
          row.flightDateTime.toISOString(),
          row.flightHours,
          row.fuelUsed,
          row.departureBase.name,
          row.arrivalBase.name,
          row.loggedBy.username,
        ]),
      );
      res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      res.setHeader('Content-Disposition', 'attachment; filename="daily-flight-report.xlsx"');
      return res.send(buffer);
    }

    const pdf = await this.reportsService.buildPdf(
      'Daily Flight Report',
      data.map(
        (row) =>
          `${row.aircraft.tailNumber} | ${row.pilotName} | ${row.missionType} | ${row.flightHours}h | ${row.departureBase.name}->${row.arrivalBase.name}`,
      ),
    );
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'attachment; filename="daily-flight-report.pdf"');
    return res.send(pdf);
  }

  @Get('weekly-maintenance')
  @Roles(AppRole.ADMIN, AppRole.MAINTENANCE, AppRole.COMMANDER, AppRole.AUDITOR)
  async weeklyMaintenance(@Query('format') format = 'pdf', @Res() res: Response) {
    const data = await this.reportsService.weeklyMaintenance();

    if (format === 'xlsx') {
      const buffer = await this.reportsService.buildXlsx(
        'Weekly Maintenance',
        ['Aircraft', 'Total Hours', 'Last Maintenance', 'Status', 'Notes', 'LoggedBy'],
        data.map((row) => [
          row.aircraft.tailNumber,
          row.totalFlightHours,
          row.lastMaintenanceDate.toISOString().split('T')[0],
          row.componentStatus,
          row.maintenanceNotes ?? '',
          row.loggedBy.username,
        ]),
      );
      res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      res.setHeader('Content-Disposition', 'attachment; filename="weekly-maintenance-report.xlsx"');
      return res.send(buffer);
    }

    const pdf = await this.reportsService.buildPdf(
      'Weekly Maintenance Report',
      data.map(
        (row) =>
          `${row.aircraft.tailNumber} | ${row.totalFlightHours}h | ${row.componentStatus} | Last: ${row.lastMaintenanceDate.toISOString().split('T')[0]}`,
      ),
    );
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'attachment; filename="weekly-maintenance-report.pdf"');
    return res.send(pdf);
  }

  @Get('aircraft-utilization')
  @Roles(AppRole.ADMIN, AppRole.FLIGHT_OPS, AppRole.MAINTENANCE, AppRole.COMMANDER, AppRole.AUDITOR)
  @Header('Cache-Control', 'no-store')
  async aircraftUtilization(@Query('format') format = 'json', @Res() res: Response) {
    const data = await this.reportsService.utilization();

    if (format === 'xlsx') {
      const buffer = await this.reportsService.buildXlsx(
        'Utilization',
        ['Aircraft', 'Total Flight Hours', 'Total Fuel Used'],
        data.map((row) => [row.aircraft, row.totalFlightHours, row.totalFuelUsed]),
      );
      res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      res.setHeader('Content-Disposition', 'attachment; filename="aircraft-utilization-report.xlsx"');
      return res.send(buffer);
    }

    if (format === 'pdf') {
      const pdf = await this.reportsService.buildPdf(
        'Aircraft Utilization Report',
        data.map(
          (row) => `${row.aircraft} | Hours: ${row.totalFlightHours} | Fuel: ${row.totalFuelUsed}`,
        ),
      );
      res.setHeader('Content-Type', 'application/pdf');
      res.setHeader('Content-Disposition', 'attachment; filename="aircraft-utilization-report.pdf"');
      return res.send(pdf);
    }

    return res.json({ utilization: data });
  }
}
