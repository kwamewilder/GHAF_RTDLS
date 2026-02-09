import { IsBoolean, IsOptional, IsString } from 'class-validator';

export class CreateCrewDto {
  @IsString()
  fullName!: string;

  @IsString()
  rank!: string;

  @IsString()
  role!: string;

  @IsOptional()
  @IsBoolean()
  isAvailable?: boolean;
}
