import { Body, Controller, Get, Post, Req, UseGuards } from '@nestjs/common';
import { Roles } from '../common/decorators/roles.decorator';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { RolesGuard } from '../common/guards/roles.guard';
import { AppRole } from '../common/types/role.type';
import { CreateAircraftDto } from './dto/create-aircraft.dto';
import { CreateBaseDto } from './dto/create-base.dto';
import { CreateCrewDto } from './dto/create-crew.dto';
import { CreateFlightLogDto } from './dto/create-flight-log.dto';
import { OperationsService } from './operations.service';

@Controller('operations')
@UseGuards(JwtAuthGuard, RolesGuard)
export class OperationsController {
  constructor(private readonly operationsService: OperationsService) {}

  @Get('bases')
  listBases() {
    return this.operationsService.listBases();
  }

  @Post('bases')
  @Roles(AppRole.ADMIN)
  createBase(@Body() dto: CreateBaseDto, @Req() req: any) {
    return this.operationsService.createBase(dto, req.user.sub, req.ip);
  }

  @Get('crew')
  listCrew() {
    return this.operationsService.listCrew();
  }

  @Post('crew')
  @Roles(AppRole.ADMIN)
  createCrew(@Body() dto: CreateCrewDto, @Req() req: any) {
    return this.operationsService.createCrew(dto, req.user.sub, req.ip);
  }

  @Get('aircraft')
  listAircraft() {
    return this.operationsService.listAircraft();
  }

  @Post('aircraft')
  @Roles(AppRole.ADMIN)
  createAircraft(@Body() dto: CreateAircraftDto, @Req() req: any) {
    return this.operationsService.createAircraft(dto, req.user.sub, req.ip);
  }

  @Get('flight-logs')
  listFlightLogs() {
    return this.operationsService.listFlightLogs();
  }

  @Post('flight-logs')
  @Roles(AppRole.ADMIN, AppRole.FLIGHT_OPS)
  createFlightLog(@Body() dto: CreateFlightLogDto, @Req() req: any) {
    return this.operationsService.createFlightLog(dto, req.user.sub, req.ip);
  }
}
