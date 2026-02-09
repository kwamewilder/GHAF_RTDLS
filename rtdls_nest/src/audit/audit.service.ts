import { Injectable } from '@nestjs/common';
import { AuditAction } from '@prisma/client';
import { createHash } from 'crypto';
import { PrismaService } from '../prisma/prisma.service';

export interface AuditPayload {
  userId?: number;
  action: AuditAction;
  entity: string;
  entityId?: number;
  description: string;
  ipAddress?: string;
}

@Injectable()
export class AuditService {
  constructor(private readonly prisma: PrismaService) {}

  list(limit = 200) {
    return this.prisma.auditLog.findMany({
      take: limit,
      include: {
        user: {
          select: {
            id: true,
            username: true,
            role: true,
          },
        },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  async log(payload: AuditPayload) {
    const previous = await this.prisma.auditLog.findFirst({
      orderBy: { id: 'desc' },
      select: { checksum: true },
    });

    const previousChecksum = previous?.checksum ?? 'GENESIS';
    const raw = [
      payload.action,
      payload.entity,
      String(payload.entityId ?? ''),
      String(payload.userId ?? ''),
      payload.description,
      previousChecksum,
    ].join('|');

    const checksum = createHash('sha256').update(raw).digest('hex');

    return this.prisma.auditLog.create({
      data: {
        userId: payload.userId,
        action: payload.action,
        entity: payload.entity,
        entityId: payload.entityId,
        description: payload.description,
        ipAddress: payload.ipAddress,
        previousChecksum,
        checksum,
      },
    });
  }
}
