import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class DashboardService {
  constructor(private readonly prisma: PrismaService) {}

  async getMetrics() {
    const today = new Date();
    const startOfDay = new Date(today);
    startOfDay.setHours(0, 0, 0, 0);
    const endOfDay = new Date(today);
    endOfDay.setHours(23, 59, 59, 999);

    const [
      aircraftAvailable,
      flightsToday,
      activeMissions,
      maintenanceAlerts,
      crewAvailability,
      utilization,
    ] = await Promise.all([
      this.prisma.aircraft.count({ where: { status: 'AVAILABLE' } }),
      this.prisma.flightLog.count({
        where: { flightDateTime: { gte: startOfDay, lte: endOfDay } },
      }),
      this.prisma.flightLog.count({
        where: {
          flightDateTime: { gte: startOfDay, lte: endOfDay },
          missionStatus: 'ACTIVE',
        },
      }),
      this.prisma.alert.count({ where: { isResolved: false } }),
      this.prisma.crew.count({ where: { isAvailable: true } }),
      this.prisma.flightLog.groupBy({
        by: ['aircraftId'],
        _sum: { flightHours: true },
        orderBy: { _sum: { flightHours: 'desc' } },
        take: 5,
      }),
    ]);

    const utilizationRows = await Promise.all(
      utilization.map(async (row) => {
        const aircraft = await this.prisma.aircraft.findUnique({
          where: { id: row.aircraftId },
          select: { tailNumber: true },
        });
        return {
          aircraft: aircraft?.tailNumber ?? `Aircraft-${row.aircraftId}`,
          hours: row._sum.flightHours ?? 0,
        };
      }),
    );

    return {
      aircraftAvailable,
      flightsToday,
      activeMissions,
      maintenanceAlerts,
      crewAvailability,
      aircraftUtilization: utilizationRows,
      updatedAt: new Date().toISOString(),
    };
  }
}
