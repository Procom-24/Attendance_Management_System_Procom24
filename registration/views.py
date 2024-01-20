import pandas as pd
import qrcode
from django.shortcuts import render
from django.http import HttpResponse
from django.core.mail import send_mail, EmailMessage
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from registration.models import Participants


def load_participant_data():

    csv_path = 'participants_data.csv'
    
    try:
        participants = pd.read_csv(csv_path)

        
        return participants
    except FileNotFoundError:
    
        return None


participants = load_participant_data()

@api_view(['GET'])
def home(request):
    return render(request, 'home.html')

@api_view(['GET'])
def participant_list(request):
    global participants
    if participants is None:
        return HttpResponse("Error loading participant data. Please check the CSV file.")

    return render(request, 'participant_list.html', {'participants': participants.to_dict(orient='records')})

@api_view(['GET'])
def send_qr(request, participant_id, qr_type):
    global participants
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
    global participants
    if participants is None:
        return HttpResponse("Error loading participant data. Please check the CSV file.")

    for _, participant in participants.iterrows():
        generate_qr(participant['name'], participant['email'], qr_type)

    return Response({'message': f"QR {qr_type} sent to all participants"}, status=status.HTTP_201_CREATED)


def update_attendance(request, unique_identifier):
    participant = get_object_or_404(Participants, unique_identifier=unique_identifier)
    participant.attendanceStatus = "Present"
    participant.save()

    return JsonResponse({'status': 'success', 'message': f'{participant.firstname} marked as present.'})


def generate_qr(name, email, qr_type):
    data = f"Participant: {name}, Email: {email}, QR Type: {qr_type}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    
    #img_path = f"{name}_qr{qr_type}.png"
    img_path = f"qrcodes/{name}_qr{qr_type}.png"
    img.save(img_path)

    subject = f'QR Code {qr_type} for Event'
    message = f'Please find your QR code {qr_type} attached.'
    from_email = 'ayeshaitshad124@gmail.com'
    to_email = email
    email = EmailMessage(subject, message, from_email, [to_email])
    email.attach_file(img_path)
    email.send()
