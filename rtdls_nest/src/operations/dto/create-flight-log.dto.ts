import { MissionStatus } from '@prisma/client';
import { Type } from 'class-transformer';
import { IsArray, IsDateString, IsEnum, IsNumber, IsOptional, IsString, Min } from 'class-validator';

export class CreateFlightLogDto {
  @IsNumber()
  aircraftId!: number;

  @IsString()
  pilotName!: string;

  @IsOptional()
  @IsArray()
  @Type(() => Number)
  crewMemberIds?: number[];

  @IsString()
  missionType!: string;

  @IsOptional()
  @IsEnum(MissionStatus)
  missionStatus?: MissionStatus;

  @IsDateString()
  flightDateTime!: string;

  @IsNumber()
  @Min(0.1)
  flightHours!: number;

  @IsNumber()
  @Min(0)
  fuelUsed!: number;

  @IsNumber()
  departureBaseId!: number;

  @IsNumber()
  arrivalBaseId!: number;

  @IsOptional()
  @IsString()
  remarks?: string;
}
