import pandas as pd
import pandas as os
import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db.models import Q 
from django.core.mail import send_mail, EmailMessage
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from io import BytesIO
from django.conf.urls.static import static
from django.conf import settings
from .models import Participants, QRcode
import csv
from django.core.files.base import ContentFile
from django.core.files import File


@api_view(['GET'])
def home(request):
    return render(request, 'home.html')

def scan_qr(request):
    return render(request, 'scan_qr.html')

@api_view(['GET'])
def uploadPage(request):
    return render(request, 'uploadData.html')

def participant_list(request):
    try:
        participants = Participants.objects.all()
        context = {'participants': participants}
        return render(request, 'participant_list.html', context)
    except Exception as e:
        print(f"Error loading participant data: {e}")
        return HttpResponse("Error loading participant data from the database.")

@api_view(['GET'])
def send_qr(request, participant_id, qr_type):
    participants = Participants.objects.all()
    if participants is None:
        return HttpResponse("Error loading participant data. Please check the CSV file.")

    try:
        participant_id = int(participant_id) + 1
    except ValueError:
        return HttpResponse("Invalid participant_id. Please provide a valid integer.")

    specified_person = participants.filter(id=participant_id)

    if not specified_person.exists():
        return HttpResponse(f"No participant found with the ID '{participant_id}'.")

    generate_qr(specified_person[0].firstname, specified_person[0].email, qr_type)

    return Response({'message': f"QR {qr_type} sent to participant with ID {participant_id}"}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def send_qr_all(request, qr_type):
    participants = Participants.objects.all()
    if participants is None:
        return HttpResponse("Error loading participant data. Please check the CSV file.")

    for participant in participants:
        generate_qr(participant.firstname, participant.email, qr_type)

    return Response({'message': f"QR {qr_type} sent to all participants"}, status=status.HTTP_201_CREATED)

    

# csv file upload save data functionality
def upload_csv(request):
    if request.method == 'POST' and request.FILES['csv_file']:
        csv_file = request.FILES['csv_file']

        # Process the CSV file
        data = process_csv(csv_file)

        # Save data to the database
        save_to_database(data)
        return JsonResponse({'status': 'success'})

    return render(request, 'index.html')

def process_csv(csv_file):
    data = []
    decoded_file = csv_file.read().decode('utf-8').splitlines()
    csv_reader = csv.DictReader(decoded_file)

    for row in csv_reader:
        data.append(row)

    return data

def generate_qr_code(participant_id, data_qrcode1, data_qrcode2):
    qr1 = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr1.add_data(data_qrcode1)
    qr1.make(fit=True)
    img1 = qr1.make_image(fill_color="black", back_color="white")

    qr2 = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr2.add_data(data_qrcode2)
    qr2.make(fit=True)
    img2 = qr2.make_image(fill_color="black", back_color="white")

    buffer1 = BytesIO()
    img1.save(buffer1)
    buffer1.seek(0)

    buffer2 = BytesIO()
    img2.save(buffer2)
    buffer2.seek(0)

    return File(buffer1), File(buffer2)

def save_to_database(data):
    for entry in data:
        if any(value is None or value == '' for value in entry.values()):
            continue

        participant = Participants.objects.create(**entry)

        data_qrcode1 = f"{entry.get('firstname')},{participant.participantID},{entry.get('contestname')},qr1"
        data_qrcode2 = f"{entry.get('firstname')},{participant.participantID},{entry.get('contestname')},qr2"

        image_qr1, image_qr2 = generate_qr_code(
            participant.participantID, data_qrcode1, data_qrcode2
        )
        
        qr_code_instance = QRcode.objects.create(
            DataQRcode1=data_qrcode1,
            DataQRcode2=data_qrcode2,
            Participants_participantID=participant
        )

        try:
            qr_code_instance.image_qr1.save(f"qrcode_{participant.participantID}_1.png", image_qr1, save=True)
            qr_code_instance.image_qr2.save(f"qrcode_{participant.participantID}_2.png", image_qr2, save=True)
        except Exception as e:
            print(f"Error saving images for participant {participant.participantID}: {str(e)}")
    cleanup_photos()

def cleanup_photos():
    try:
        photos_folder = os.path.join(settings.MEDIA_ROOT, 'qrcodes')
        all_files = set(os.listdir(photos_folder))

        for file_to_remove in all_files:
            file_path = os.path.join(photos_folder, file_to_remove)
            os.remove(file_path)
            print(f'Removed file: {file_path}')

        print('Cleanup process completed successfully!')

    except Exception as e:
        print(f'An error occurred during cleanup: {str(e)}')
        

def mark_attendance(request):
    if request.method == 'POST':
        qr_data = request.POST.get('qrData', '')
        try:
            qr_code = QRCode.objects.get(Q(DataQRcode1=qr_data) | Q(DataQRcode2=qr_data))
            participant = qr_code.Participants_participantID
            participant.attendanceStatus = 'P'
            participant.save()

            return JsonResponse({'message': f'Attendance marked for participant: {participant.participantID}'})
        except QRCode.DoesNotExist:
            return JsonResponse({'message': 'QR code not found'})
    else:
        return JsonResponse({'message': 'Invalid request method'})