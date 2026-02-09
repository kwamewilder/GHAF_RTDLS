import { Body, Controller, Get, Param, ParseIntPipe, Patch, Post, Req, UseGuards } from '@nestjs/common';
import { Roles } from '../common/decorators/roles.decorator';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { RolesGuard } from '../common/guards/roles.guard';
import { AppRole } from '../common/types/role.type';
import { CreateUserDto } from './dto/create-user.dto';
import { UpdateUserDto } from './dto/update-user.dto';
import { UsersService } from './users.service';

@Controller('users')
@UseGuards(JwtAuthGuard, RolesGuard)
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get()
  @Roles(AppRole.ADMIN)
  list() {
    return this.usersService.findAll();
  }

  @Post()
  @Roles(AppRole.ADMIN)
  create(@Body() dto: CreateUserDto, @Req() req: any) {
    return this.usersService.create(req.user.sub, dto, req.ip);
  }

  @Patch(':id')
  @Roles(AppRole.ADMIN)
  update(@Param('id', ParseIntPipe) id: number, @Body() dto: UpdateUserDto, @Req() req: any) {
    return this.usersService.update(id, req.user.sub, dto, req.ip);
  }
}
