import { IsString } from 'class-validator';

export class CreateBaseDto {
  @IsString()
  name!: string;

  @IsString()
  location!: string;
}
