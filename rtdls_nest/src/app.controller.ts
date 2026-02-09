import { Controller, Get } from '@nestjs/common';

@Controller()
export class AppController {
  @Get('health')
  health() {
    return {
      service: 'GAF RTDLS API',
      status: 'ok',
      timestamp: new Date().toISOString(),
    };
  }
}
