# import random
# import datetime
# from django.core.management.base import BaseCommand
# from faker import Faker
# from registration.models import Participants, ParticipantCard, UserAccount, QRcode, Attendence, Registrations, Certificates

# fake = Faker()

# class Command(BaseCommand):
#     help = 'Generate and insert dummy data into the database'

#     def add_arguments(self, parser):
#         parser.add_argument('total', type=int, help='Indicates the number of dummy data records to be created')

#     def generate_student_id(self):
#         xx = str(random.randint(18, 23))
#         A = random.choice(['k', 'i', 'l', 'p', 'c'])
#         yyyy = str(random.randint(0, 9999)).zfill(4)  # Ensure yyyy is four digits with leading zeros if needed
#         return f'{xx}{A}-{yyyy}'

#     def handle(self, *args, **kwargs):
#         total = kwargs['total']

#         for _ in range(total):
#             participant = Participants.objects.create(
#                 firstname=fake.first_name(),
#                 lastname=fake.last_name(),
#                 email=fake.email(),
#                 phonenumber=int(''.join(filter(str.isdigit, fake.phone_number()))),
#                 studentid=self.generate_student_id(),
#                 universityname=fake.company(),
#                 contestname=fake.word(),
#                 age=random.randint(18, 30)
#             )

#             participant_card = ParticipantCard.objects.create(
#                 issuedate=fake.date_between(start_date='-30d', end_date='today'),
#                 validitystatus=random.choice(['Valid', 'Invalid']),
#                 Participants_participantID=participant
#             )

#             user_id_prefix = 'user'
#             user_id_random_part = ''.join(fake.random_letters(length=8))  # Join the list of characters into a string
#             user_id = f'{user_id_prefix}_{user_id_random_part}'

#             user_account = UserAccount.objects.create(
#                 username=fake.user_name(),
#                 passwordhash=fake.password(),
#                 Participants_ParticipantID=participant,
#                 userID=user_id
#             )

#             qrcode = QRcode.objects.create(
#                 QRcodetype=fake.word(),
#                 OTP=fake.uuid4(),
#                 confirmationstatus=random.choice(['Confirmed', 'Unconfirmed']),
#                 Participants_participantID=participant
#             )

#             attendance = Attendence.objects.create(
#                 eventdate=fake.date_between(start_date='-30d', end_date='today'),
#                 status=random.choice(['Present', 'Absent']),
#                 Participants_participantID=participant
#             )

#             registration = Registrations.objects.create(
#                 registrationdate=fake.date_between(start_date='-30d', end_date='today'),
#                 status=random.choice(['Approved', 'Pending', 'Rejected']),
#                 Participants_participantID=participant
#             )

#             certificate = Certificates.objects.create(
#                 certificateID=fake.uuid4(),
#                 certificateText=fake.text(),
#                 issuedate=fake.date_between(start_date='-30d', end_date='today'),
#                 Participants_participantID=participant
#             )

#         self.stdout.write(self.style.SUCCESS(f'Successfully created {total} dummy data records'))
