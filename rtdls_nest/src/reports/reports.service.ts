import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import PDFDocument = require('pdfkit');
import ExcelJS from 'exceljs';

@Injectable()
export class ReportsService {
  constructor(private readonly prisma: PrismaService) {}

  async dailyFlights() {
    const today = new Date();
    const start = new Date(today);
    start.setHours(0, 0, 0, 0);
    const end = new Date(today);
    end.setHours(23, 59, 59, 999);

    return this.prisma.flightLog.findMany({
      where: { flightDateTime: { gte: start, lte: end } },
      include: { aircraft: true, departureBase: true, arrivalBase: true, loggedBy: true },
      orderBy: { flightDateTime: 'desc' },
    });
  }

  async weeklyMaintenance() {
    const end = new Date();
    const start = new Date(end);
    start.setDate(start.getDate() - 7);

    return this.prisma.maintenanceLog.findMany({
      where: { createdAt: { gte: start, lte: end } },
      include: { aircraft: true, loggedBy: true },
      orderBy: { createdAt: 'desc' },
    });
  }

  async utilization() {
    const grouped = await this.prisma.flightLog.groupBy({
      by: ['aircraftId'],
      _sum: { flightHours: true, fuelUsed: true },
      orderBy: { _sum: { flightHours: 'desc' } },
    });

    return Promise.all(
      grouped.map(async (row) => {
        const aircraft = await this.prisma.aircraft.findUnique({ where: { id: row.aircraftId } });
        return {
          aircraft: aircraft?.tailNumber ?? `Aircraft-${row.aircraftId}`,
          totalFlightHours: row._sum.flightHours ?? 0,
          totalFuelUsed: row._sum.fuelUsed ?? 0,
        };
      }),
    );
  }

  buildPdf(title: string, lines: string[]): Promise<Buffer> {
    return new Promise((resolve) => {
      const doc = new PDFDocument({ margin: 40 });
      const chunks: Buffer[] = [];
      doc.on('data', (chunk) => chunks.push(chunk));
      doc.on('end', () => resolve(Buffer.concat(chunks)));

      doc.fontSize(16).text(title);
      doc.moveDown();
      doc.fontSize(10);
      for (const line of lines) {
        doc.text(line);
      }

      if (!lines.length) {
        doc.text('No records for selected period.');
      }

      doc.end();
    });
  }

  async buildXlsx(sheetName: string, headers: string[], rows: (string | number)[][]): Promise<Buffer> {
    const wb = new ExcelJS.Workbook();
    const ws = wb.addWorksheet(sheetName);
    ws.addRow(headers);
    for (const row of rows) {
      ws.addRow(row);
    }
    const arrayBuffer = await wb.xlsx.writeBuffer();
    return Buffer.from(arrayBuffer as ArrayBuffer);
  }
}
