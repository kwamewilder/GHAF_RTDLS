import { AircraftStatus } from '@prisma/client';
import { IsEnum, IsNumber, IsOptional, IsString, Min } from 'class-validator';

export class CreateAircraftDto {
  @IsString()
  tailNumber!: string;

  @IsString()
  model!: string;

  @IsOptional()
  @IsNumber()
  @Min(1)
  maintenanceThresholdHours?: number;

  @IsOptional()
  @IsEnum(AircraftStatus)
  status?: AircraftStatus;

  @IsNumber()
  homeBaseId!: number;
}
