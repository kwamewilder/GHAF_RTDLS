import { PrismaClient, Role, AircraftStatus, MissionStatus } from '@prisma/client';
import * as bcrypt from 'bcrypt';

const prisma = new PrismaClient();

async function upsertUser(username: string, role: Role) {
  const passwordHash = await bcrypt.hash('DemoPass123!', 10);
  return prisma.user.upsert({
    where: { username },
    create: {
      username,
      role,
      passwordHash,
      email: `${username}@gaf.local`,
      firstName: username.split('_')[0],
      lastName: 'Demo',
    },
    update: {
      role,
      passwordHash,
      isActive: true,
    },
  });
}

async function main() {
  const admin = await upsertUser('admin_demo', Role.ADMIN);
  const flightOps = await upsertUser('flight_ops_demo', Role.FLIGHT_OPS);
  await upsertUser('maintenance_demo', Role.MAINTENANCE);
  await upsertUser('commander_demo', Role.COMMANDER);
  await upsertUser('auditor_demo', Role.AUDITOR);

  const accra = await prisma.base.upsert({
    where: { name: 'Accra' },
    create: { name: 'Accra', location: 'Accra' },
    update: {},
  });
  const tamale = await prisma.base.upsert({
    where: { name: 'Tamale' },
    create: { name: 'Tamale', location: 'Tamale' },
    update: {},
  });
  const takoradi = await prisma.base.upsert({
    where: { name: 'Takoradi' },
    create: { name: 'Takoradi', location: 'Takoradi' },
    update: {},
  });

  const c295 = await prisma.aircraft.upsert({
    where: { tailNumber: 'GAF-101' },
    create: {
      tailNumber: 'GAF-101',
      model: 'C-295',
      maintenanceThresholdHours: 100,
      status: AircraftStatus.AVAILABLE,
      homeBaseId: accra.id,
    },
    update: {},
  });

  const crewA = await prisma.crew.create({
    data: { fullName: 'Crew Member A', rank: 'Sgt', role: 'Crew', isAvailable: true },
  }).catch(() => prisma.crew.findFirstOrThrow({ where: { fullName: 'Crew Member A' } }));

  await prisma.flightLog.create({
    data: {
      aircraftId: c295.id,
      pilotName: 'Wing Cdr Mensah',
      missionType: 'Recon',
      missionStatus: MissionStatus.COMPLETED,
      flightDateTime: new Date(),
      flightHours: 2.4,
      fuelUsed: 320,
      departureBaseId: accra.id,
      arrivalBaseId: tamale.id,
      remarks: 'Seeded mission',
      loggedById: flightOps.id,
      crewMembers: { connect: [{ id: crewA.id }] },
    },
  });

  await prisma.maintenanceLog.create({
    data: {
      aircraftId: c295.id,
      totalFlightHours: 120,
      lastMaintenanceDate: new Date('2026-01-20T00:00:00Z'),
      componentStatus: 'Engine check required',
      maintenanceNotes: 'Threshold crossed during seed',
      loggedById: admin.id,
    },
  });

  console.log('Seed complete. Demo password: DemoPass123!');
  console.log('Bases seeded: Accra, Tamale, Takoradi');
  console.log('Accounts: admin_demo, flight_ops_demo, maintenance_demo, commander_demo, auditor_demo');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
