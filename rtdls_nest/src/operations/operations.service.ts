import { BadRequestException, Injectable } from '@nestjs/common';
import { AircraftStatus, AuditAction, MissionStatus } from '@prisma/client';
import { AuditService } from '../audit/audit.service';
import { DashboardGateway } from '../dashboard/dashboard.gateway';
import { PrismaService } from '../prisma/prisma.service';
import { CreateAircraftDto } from './dto/create-aircraft.dto';
import { CreateBaseDto } from './dto/create-base.dto';
import { CreateCrewDto } from './dto/create-crew.dto';
import { CreateFlightLogDto } from './dto/create-flight-log.dto';

@Injectable()
export class OperationsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly auditService: AuditService,
    private readonly dashboardGateway: DashboardGateway,
  ) {}

  listBases() {
    return this.prisma.base.findMany({ orderBy: { name: 'asc' } });
  }

  async createBase(dto: CreateBaseDto, actorUserId: number, ipAddress?: string) {
    const created = await this.prisma.base.create({ data: dto });
    await this.auditService.log({
      userId: actorUserId,
      action: AuditAction.CREATE,
      entity: 'Base',
      entityId: created.id,
      description: `Created base ${created.name}`,
      ipAddress,
    });
    return created;
  }

  listCrew() {
    return this.prisma.crew.findMany({ orderBy: { fullName: 'asc' } });
  }

  async createCrew(dto: CreateCrewDto, actorUserId: number, ipAddress?: string) {
    const created = await this.prisma.crew.create({
      data: {
        fullName: dto.fullName,
        rank: dto.rank,
        role: dto.role,
        isAvailable: dto.isAvailable ?? true,
      },
    });
    await this.auditService.log({
      userId: actorUserId,
      action: AuditAction.CREATE,
      entity: 'Crew',
      entityId: created.id,
      description: `Created crew ${created.fullName}`,
      ipAddress,
    });
    return created;
  }

  listAircraft() {
    return this.prisma.aircraft.findMany({
      include: { homeBase: true },
      orderBy: { tailNumber: 'asc' },
    });
  }

  async createAircraft(dto: CreateAircraftDto, actorUserId: number, ipAddress?: string) {
    const created = await this.prisma.aircraft.create({
      data: {
        tailNumber: dto.tailNumber,
        model: dto.model,
        maintenanceThresholdHours: dto.maintenanceThresholdHours ?? 100,
        status: dto.status ?? AircraftStatus.AVAILABLE,
        homeBaseId: dto.homeBaseId,
      },
      include: { homeBase: true },
    });
    await this.auditService.log({
      userId: actorUserId,
      action: AuditAction.CREATE,
      entity: 'Aircraft',
      entityId: created.id,
      description: `Created aircraft ${created.tailNumber}`,
      ipAddress,
    });
    await this.dashboardGateway.broadcastMetrics('aircraft_created');
    return created;
  }

  listFlightLogs() {
    return this.prisma.flightLog.findMany({
      include: {
        aircraft: true,
        departureBase: true,
        arrivalBase: true,
        crewMembers: true,
        loggedBy: {
          select: { id: true, username: true, role: true },
        },
      },
      orderBy: { flightDateTime: 'desc' },
    });
  }

  async createFlightLog(dto: CreateFlightLogDto, actorUserId: number, ipAddress?: string) {
    if (dto.departureBaseId === dto.arrivalBaseId) {
      throw new BadRequestException('Departure and arrival bases must be different.');
    }

    const created = await this.prisma.flightLog.create({
      data: {
        aircraftId: dto.aircraftId,
        pilotName: dto.pilotName,
        missionType: dto.missionType,
        missionStatus: dto.missionStatus ?? MissionStatus.COMPLETED,
        flightDateTime: new Date(dto.flightDateTime),
        flightHours: dto.flightHours,
        fuelUsed: dto.fuelUsed,
        departureBaseId: dto.departureBaseId,
        arrivalBaseId: dto.arrivalBaseId,
        remarks: dto.remarks,
        loggedById: actorUserId,
        crewMembers: dto.crewMemberIds?.length
          ? {
              connect: dto.crewMemberIds.map((id) => ({ id })),
            }
          : undefined,
      },
      include: {
        aircraft: true,
        departureBase: true,
        arrivalBase: true,
        crewMembers: true,
        loggedBy: { select: { id: true, username: true, role: true } },
      },
    });

    await this.auditService.log({
      userId: actorUserId,
      action: AuditAction.CREATE,
      entity: 'FlightLog',
      entityId: created.id,
      description: `Created flight log for ${created.aircraft.tailNumber}`,
      ipAddress,
    });

    await this.dashboardGateway.broadcastMetrics('flight_log_created', {
      flightLogId: created.id,
    });

    return created;
  }
}
