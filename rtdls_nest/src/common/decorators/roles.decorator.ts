import { SetMetadata } from '@nestjs/common';
import { AppRole } from '../types/role.type';

export const ROLES_KEY = 'roles';
export const Roles = (...roles: AppRole[]) => SetMetadata(ROLES_KEY, roles);
