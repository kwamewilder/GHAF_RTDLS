import {
  ConnectedSocket,
  OnGatewayConnection,
  OnGatewayInit,
  WebSocketGateway,
  WebSocketServer,
} from '@nestjs/websockets';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import { Server, Socket } from 'socket.io';
import { DashboardService } from './dashboard.service';

@WebSocketGateway({
  namespace: '/dashboard',
  cors: { origin: '*' },
})
export class DashboardGateway implements OnGatewayInit, OnGatewayConnection {
  @WebSocketServer()
  server!: Server;

  constructor(
    private readonly dashboardService: DashboardService,
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
  ) {}

  afterInit() {
    // no-op
  }

  async handleConnection(@ConnectedSocket() client: Socket) {
    const rawToken =
      (client.handshake.auth?.token as string | undefined) ||
      (client.handshake.headers.authorization as string | undefined)?.replace('Bearer ', '');

    if (!rawToken) {
      client.disconnect(true);
      return;
    }

    try {
      this.jwtService.verify(rawToken, {
        secret: this.configService.get<string>('JWT_SECRET', 'change_me_for_production'),
      });
    } catch {
      client.disconnect(true);
      return;
    }

    client.emit('dashboard.initial', await this.dashboardService.getMetrics());
  }

  async broadcastMetrics(event = 'dashboard.refresh', payload: Record<string, unknown> = {}) {
    const metrics = await this.dashboardService.getMetrics();
    this.server.emit(event, { metrics, payload });
  }
}
