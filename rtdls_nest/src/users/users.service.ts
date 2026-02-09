import { Injectable, NotFoundException } from '@nestjs/common';
import { AuditAction, Role } from '@prisma/client';
import * as bcrypt from 'bcrypt';
import { AuditService } from '../audit/audit.service';
import { PrismaService } from '../prisma/prisma.service';
import { CreateUserDto } from './dto/create-user.dto';
import { UpdateUserDto } from './dto/update-user.dto';

@Injectable()
export class UsersService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly auditService: AuditService,
  ) {}

  findAll() {
    return this.prisma.user.findMany({
      select: {
        id: true,
        username: true,
        firstName: true,
        lastName: true,
        email: true,
        role: true,
        isActive: true,
        createdAt: true,
      },
      orderBy: { username: 'asc' },
    });
  }

  async findByUsername(username: string) {
    return this.prisma.user.findUnique({ where: { username } });
  }

  async create(actorUserId: number, dto: CreateUserDto, ipAddress?: string) {
    const passwordHash = await bcrypt.hash(dto.password, 10);
    const created = await this.prisma.user.create({
      data: {
        username: dto.username,
        passwordHash,
        firstName: dto.firstName,
        lastName: dto.lastName,
        email: dto.email,
        role: dto.role as Role,
      },
      select: {
        id: true,
        username: true,
        firstName: true,
        lastName: true,
        email: true,
        role: true,
        isActive: true,
      },
    });

    await this.auditService.log({
      userId: actorUserId,
      action: AuditAction.CREATE,
      entity: 'User',
      entityId: created.id,
      description: `Created user ${created.username}`,
      ipAddress,
    });

    return created;
  }

  async update(userId: number, actorUserId: number, dto: UpdateUserDto, ipAddress?: string) {
    const existing = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!existing) {
      throw new NotFoundException('User not found');
    }

    const data: Record<string, unknown> = {};
    if (dto.firstName !== undefined) data.firstName = dto.firstName;
    if (dto.lastName !== undefined) data.lastName = dto.lastName;
    if (dto.email !== undefined) data.email = dto.email;
    if (dto.role !== undefined) data.role = dto.role as Role;
    if (dto.isActive !== undefined) {
      data.isActive = dto.isActive;
    }
    if (dto.password) {
      data.passwordHash = await bcrypt.hash(dto.password, 10);
    }

    const updated = await this.prisma.user.update({
      where: { id: userId },
      data,
      select: {
        id: true,
        username: true,
        firstName: true,
        lastName: true,
        email: true,
        role: true,
        isActive: true,
      },
    });

    await this.auditService.log({
      userId: actorUserId,
      action: AuditAction.UPDATE,
      entity: 'User',
      entityId: userId,
      description: `Updated user ${updated.username}`,
      ipAddress,
    });

    if (dto.role && dto.role !== (existing.role as unknown as string)) {
      await this.auditService.log({
        userId: actorUserId,
        action: AuditAction.ROLE_CHANGE,
        entity: 'User',
        entityId: userId,
        description: `Role changed from ${existing.role} to ${dto.role}`,
        ipAddress,
      });
    }

    return updated;
  }
}
