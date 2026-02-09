import { Controller, Get, Query, UseGuards } from '@nestjs/common';
import { Roles } from '../common/decorators/roles.decorator';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { RolesGuard } from '../common/guards/roles.guard';
import { AppRole } from '../common/types/role.type';
import { AuditService } from './audit.service';

@Controller('audit-logs')
@UseGuards(JwtAuthGuard, RolesGuard)
export class AuditController {
  constructor(private readonly auditService: AuditService) {}

  @Get()
  @Roles(AppRole.ADMIN, AppRole.AUDITOR, AppRole.COMMANDER)
  list(@Query('limit') limit = '200') {
    const parsedLimit = Math.max(1, Math.min(1000, Number(limit) || 200));
    return this.auditService.list(parsedLimit);
  }
}
