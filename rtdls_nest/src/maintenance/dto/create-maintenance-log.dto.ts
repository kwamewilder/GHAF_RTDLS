import { IsDateString, IsNumber, IsOptional, IsString, Min } from 'class-validator';

export class CreateMaintenanceLogDto {
  @IsNumber()
  aircraftId!: number;

  @IsNumber()
  @Min(0)
  totalFlightHours!: number;

  @IsDateString()
  lastMaintenanceDate!: string;

  @IsString()
  componentStatus!: string;

  @IsOptional()
  @IsString()
  maintenanceNotes?: string;
}
