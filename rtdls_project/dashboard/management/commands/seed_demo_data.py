from datetime import timedelta
import os
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from maintenance.models import MaintenanceLog
from operations.models import Aircraft, Base, Crew, FlightData, FlightLog, Pilot

User = get_user_model()

GHANAIAN_CREW_PROFILES = [
    ('Sgt Kwame Boadu', 'Sgt', 'Loadmaster'),
    ('Cpl Richmond Ofori', 'Cpl', 'Crew Chief'),
    ('Sgt Kojo Addae', 'Sgt', 'Avionics Technician'),
    ('Sgt Samuel Tetteh', 'Sgt', 'Flight Engineer'),
    ('Cpl Joseph Asante', 'Cpl', 'Communications Specialist'),
    ('Sgt Emmanuel Baah', 'Sgt', 'Crew'),
    ('Cpl Daniel Kwarteng', 'Cpl', 'Crew'),
]

GHANAIAN_PILOT_PROFILES = [
    ('Flt Lt Kofi Mensah', 'Flt Lt'),
    ('Sqn Ldr Kwabena Owusu', 'Sqn Ldr'),
    ('Wing Cdr Yaw Asiedu', 'Wing Cdr'),
    ('Flt Lt Nana Yeboah', 'Flt Lt'),
    ('Sqn Ldr Ebenezer Appiah', 'Sqn Ldr'),
    ('Wing Cdr Michael Osei', 'Wing Cdr'),
    ('Flt Lt Selorm Ahiable', 'Flt Lt'),
]


class Command(BaseCommand):
    help = 'Seeds demo data for thesis presentation.'

    def handle(self, *args, **options):
        allow_seed = os.getenv('ALLOW_DEMO_SEED', '').strip().lower() in {'1', 'true', 'yes', 'on'}
        if not allow_seed:
            raise CommandError('Demo seed is disabled. Set ALLOW_DEMO_SEED=True to run this command.')

        demo_password = os.getenv('DEMO_USER_PASSWORD', 'DemoPass123!')

        bases = {
            'Accra': Base.objects.get_or_create(name='Accra', defaults={'location': 'Accra'})[0],
            'Tamale': Base.objects.get_or_create(name='Tamale', defaults={'location': 'Tamale'})[0],
            'Takoradi': Base.objects.get_or_create(name='Takoradi', defaults={'location': 'Takoradi'})[0],
        }

        users = [
            ('admin_demo', 'admin'),
            ('flight_ops_demo', 'flight_ops'),
            ('maintenance_demo', 'maintenance'),
            ('commander_demo', 'commander'),
            ('auditor_demo', 'auditor'),
        ]

        created_users = {}
        for username, role in users:
            user, created = User.objects.get_or_create(username=username, defaults={'role': role, 'email': f'{username}@gaf.local'})
            if created:
                user.set_password(demo_password)
                user.save()
            created_users[role] = user

        crew_members = []
        for full_name, rank, role in GHANAIAN_CREW_PROFILES:
            crew, _ = Crew.objects.get_or_create(
                full_name=full_name,
                defaults={'rank': rank, 'role': role, 'is_available': True},
            )
            crew_members.append(crew)

        pilots = []
        for idx, (full_name, rank) in enumerate(GHANAIAN_PILOT_PROFILES, start=1):
            pilot, _ = Pilot.objects.get_or_create(
                full_name=full_name,
                defaults={
                    'rank': rank,
                    'contact_info': f'+233-0200-000{idx:02d}',
                    'is_active': True,
                },
            )
            pilots.append(pilot)

        aircraft_models = [('GAF-101', 'C-295'), ('GAF-102', 'CN-235'), ('GAF-103', 'L-39')]
        aircraft_list = []
        for tail, model in aircraft_models:
            aircraft, _ = Aircraft.objects.get_or_create(
                tail_number=tail,
                defaults={
                    'model': model,
                    'maintenance_threshold_hours': 100,
                    'home_base': random.choice(list(bases.values())),
                },
            )
            aircraft_list.append(aircraft)

        for aircraft in aircraft_list:
            for _ in range(3):
                dep, arr = random.sample(list(bases.values()), 2)
                pilot = random.choice(pilots)
                flight_hours = round(random.uniform(1.0, 4.5), 1)
                atd_time = timezone.now() - timedelta(hours=random.randint(1, 36))
                eta_time = atd_time + timedelta(hours=flight_hours)
                ata_time = eta_time if random.choice([True, False]) else None
                log = FlightLog.objects.create(
                    aircraft=aircraft,
                    pilot=pilot,
                    mission_type=random.choice(['Recon', 'Transport', 'Training']),
                    atd=atd_time,
                    eta=eta_time,
                    ata=ata_time,
                    flight_hours=flight_hours,
                    fuel_used=round(random.uniform(150, 500), 1),
                    departure_base=dep,
                    arrival_base=arr,
                    remarks='Auto-generated demo entry',
                    logged_by=created_users['flight_ops'],
                )
                log.crew_members.set(random.sample(crew_members, k=2))
                for _ in range(2):
                    FlightData.objects.create(
                        flight_log=log,
                        timestamp=log.atd + timedelta(minutes=random.randint(5, 50)),
                        altitude=round(random.uniform(1500, 12000), 1),
                        speed=round(random.uniform(180, 540), 1),
                        engine_temp=round(random.uniform(65, 110), 1),
                        fuel_level=round(random.uniform(10, 100), 1),
                        heading=round(random.uniform(0, 360), 1),
                    )

            MaintenanceLog.objects.get_or_create(
                aircraft=aircraft,
                total_flight_hours=round(random.uniform(80, 140), 1),
                last_maintenance_date=timezone.localdate() - timedelta(days=random.randint(1, 30)),
                component_status='Operational',
                maintenance_notes='Auto-generated demo maintenance log',
                logged_by=created_users['maintenance'],
            )

        self.stdout.write(self.style.SUCCESS('Demo data seeded.'))
        self.stdout.write(self.style.SUCCESS(f'Demo users password: {demo_password}'))
