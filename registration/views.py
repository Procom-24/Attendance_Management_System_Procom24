import pandas as pd
import qrcode
from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.core.mail import send_mail, EmailMessage
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from io import BytesIO
from django.http import JsonResponse
from .models import Participants,QRcode
import csv
from django.core.files.base import ContentFile
from .models import Participants



@api_view(['GET'])
def home(request):
    return render(request, 'home.html')
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
    
        return HttpResponse("Error loading participant data from database.")

@api_view(['GET'])
def send_qr(request, participant_id, qr_type):
    participants = Participants.objects.all()
    if participants is None:
        return HttpResponse("Error loading participant data. Please check the CSV file.")

    try:
        
        participant_id = int(participant_id)+1
    except ValueError:
        return HttpResponse("Invalid participant_id. Please provide a valid integer.")

    
    specified_person = participants.loc[participants['id'] == participant_id]

    if specified_person.empty:
        return HttpResponse(f"No participant found with the ID '{participant_id}'.")

    
    generate_qr(specified_person.iloc[0]['name'], specified_person.iloc[0]['email'], qr_type)

    return Response({'message': f"QR {qr_type} sent to participant with ID {participant_id}"}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def send_qr_all(request, qr_type):
    participants = Participants.objects.all()
    if participants is None:
        return HttpResponse("Error loading participant data. Please check the CSV file.")

    for _, participant in participants.iterrows():
        generate_qr(participant['name'], participant['email'], qr_type)

    return Response({'message': f"QR {qr_type} sent to all participants"}, status=status.HTTP_201_CREATED)

from django.core.files.base import ContentFile
from io import BytesIO

from django.core.files.base import ContentFile
from io import BytesIO

def generate_qr():
    participants = Participants.objects.all()
    for participant in participants:
        name = participant.firstname
        email = participant.email

    
        qr_data_qr1 = f"{name},{email},qr1"
        qr1 = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr1.add_data(qr_data_qr1)
        qr1.make(fit=True)
        img_qr1 = qr1.make_image(fill_color="black", back_color="white")

        
        qr_data_qr2 = f"{name},{email},qr2"
        qr2 = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr2.add_data(qr_data_qr2)
        qr2.make(fit=True)
        img_qr2 = qr2.make_image(fill_color="black", back_color="white")

        qr_code_data = QRcode.objects.create(
            DataQRcode1=qr_data_qr1,
            DataQRcode2=qr_data_qr2,
            Participants_participantID=participant,
        )

        
        img_buffer_qr1 = BytesIO()
        img_qr1.save(img_buffer_qr1, format='PNG')
        qr_code_data.image_qr1.save(f'qrcode_qr1_{qr_code_data.QRcodeId}.png', ContentFile(img_buffer_qr1.getvalue()), save=False)

        img_buffer_qr2 = BytesIO()
        img_qr2.save(img_buffer_qr2, format='PNG')
        qr_code_data.image_qr2.save(f'qrcode_qr2_{qr_code_data.QRcodeId}.png', ContentFile(img_buffer_qr2.getvalue()), save=False)

        # Save the model with the images
        qr_code_data.save()


    
    #img_path = f"{name}_qr{qr_type}.png"
    # img_path = f"qrcodes/{name}_qr{qr_type}.png"
    # img.save(img_path)

    # subject = f'QR Code {qr_type} for Event'
    # message = f'Please find your QR code {qr_type} attached.'
    # from_email = 'ayeshaitshad124@gmail.com'
    # to_email = email
    # email = EmailMessage(subject, message, from_email, [to_email])
    # email.attach_file(img_path)
    # email.send()



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

def save_to_database(data):
    for entry in data:
        if any(value is None or value == '' for value in entry.values()):
            continue
        participant=Participants.objects.create(**entry)
    generate_qr()
