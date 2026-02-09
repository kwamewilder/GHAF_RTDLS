import { Injectable, NotFoundException } from '@nestjs/common';
import { AlertSeverity, AuditAction } from '@prisma/client';
import { AuditService } from '../audit/audit.service';
import { DashboardGateway } from '../dashboard/dashboard.gateway';
import { PrismaService } from '../prisma/prisma.service';
import { CreateMaintenanceLogDto } from './dto/create-maintenance-log.dto';

@Injectable()
export class MaintenanceService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly auditService: AuditService,
    private readonly dashboardGateway: DashboardGateway,
  ) {}

  listLogs() {
    return this.prisma.maintenanceLog.findMany({
      include: {
        aircraft: true,
        loggedBy: { select: { id: true, username: true, role: true } },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  listAlerts() {
    return this.prisma.alert.findMany({
      include: { aircraft: true, maintenanceLog: true },
      orderBy: { createdAt: 'desc' },
    });
  }

  async createMaintenanceLog(dto: CreateMaintenanceLogDto, actorUserId: number, ipAddress?: string) {
    const aircraft = await this.prisma.aircraft.findUnique({ where: { id: dto.aircraftId } });
    if (!aircraft) {
      throw new NotFoundException('Aircraft not found');
    }

    const log = await this.prisma.maintenanceLog.create({
      data: {
        aircraftId: dto.aircraftId,
        totalFlightHours: dto.totalFlightHours,
        lastMaintenanceDate: new Date(dto.lastMaintenanceDate),
        componentStatus: dto.componentStatus,
        maintenanceNotes: dto.maintenanceNotes,
        loggedById: actorUserId,
      },
      include: { aircraft: true },
    });

    await this.auditService.log({
      userId: actorUserId,
      action: AuditAction.CREATE,
      entity: 'MaintenanceLog',
      entityId: log.id,
      description: `Created maintenance log for ${log.aircraft.tailNumber}`,
      ipAddress,
    });

    if (dto.totalFlightHours >= aircraft.maintenanceThresholdHours) {
      const alert = await this.prisma.alert.create({
        data: {
          aircraftId: aircraft.id,
          maintenanceLogId: log.id,
          title: 'Maintenance Threshold Reached',
          message: `Aircraft ${aircraft.tailNumber} recorded ${dto.totalFlightHours} hours (threshold ${aircraft.maintenanceThresholdHours}).`,
          severity: AlertSeverity.HIGH,
          recipientRole: 'MAINTENANCE',
        },
      });

      await this.auditService.log({
        userId: actorUserId,
        action: AuditAction.CREATE,
        entity: 'Alert',
        entityId: alert.id,
        description: `Predictive maintenance alert created for ${aircraft.tailNumber}`,
        ipAddress,
      });

      await this.dashboardGateway.broadcastMetrics('maintenance.alert', {
        alertId: alert.id,
      });
    }

    await this.dashboardGateway.broadcastMetrics('maintenance_log_created', {
      maintenanceLogId: log.id,
    });

    return log;
  }

  async resolveAlert(alertId: number, actorUserId: number, ipAddress?: string) {
    const alert = await this.prisma.alert.findUnique({ where: { id: alertId } });
    if (!alert) {
      throw new NotFoundException('Alert not found');
    }

    const updated = await this.prisma.alert.update({
      where: { id: alertId },
      data: { isResolved: true },
    });

    await this.auditService.log({
      userId: actorUserId,
      action: AuditAction.UPDATE,
      entity: 'Alert',
      entityId: alertId,
      description: 'Alert marked as resolved',
      ipAddress,
    });

    await this.dashboardGateway.broadcastMetrics('alert_resolved', { alertId });

    return updated;
  }
}
