import { Body, Controller, Get, Param, ParseIntPipe, Patch, Post, Req, UseGuards } from '@nestjs/common';
import { Roles } from '../common/decorators/roles.decorator';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { RolesGuard } from '../common/guards/roles.guard';
import { AppRole } from '../common/types/role.type';
import { CreateMaintenanceLogDto } from './dto/create-maintenance-log.dto';
import { MaintenanceService } from './maintenance.service';

@Controller('maintenance')
@UseGuards(JwtAuthGuard, RolesGuard)
export class MaintenanceController {
  constructor(private readonly maintenanceService: MaintenanceService) {}

  @Get('logs')
  listLogs() {
    return this.maintenanceService.listLogs();
  }

  @Post('logs')
  @Roles(AppRole.ADMIN, AppRole.MAINTENANCE)
  createLog(@Body() dto: CreateMaintenanceLogDto, @Req() req: any) {
    return this.maintenanceService.createMaintenanceLog(dto, req.user.sub, req.ip);
  }

  @Get('alerts')
  listAlerts() {
    return this.maintenanceService.listAlerts();
  }

  @Patch('alerts/:id/resolve')
  @Roles(AppRole.ADMIN, AppRole.MAINTENANCE)
  resolveAlert(@Param('id', ParseIntPipe) id: number, @Req() req: any) {
    return this.maintenanceService.resolveAlert(id, req.user.sub, req.ip);
  }
}
