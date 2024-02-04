import pandas as pd
import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
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
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

@api_view(['GET'])
def home(request):
    return render(request, 'home.html')

@api_view(['GET'])
def uploadPage(request):
    return render(request, 'uploadData.html')

# def participant_list(request):
#     try:
#         participants = Participants.objects.all()
#         context = {'participants': participants}
#         return render(request, 'participant_list.html', context)
#     except Exception as e:
#         print(f"Error loading participant data: {e}")
#         return HttpResponse("Error loading participant data from the database.")



# def participant_list(request):
#     participants = Participants.objects.all()  # Replace YourModel with the actual model name
#     paginator = Paginator(participants, 10)  # Show 10 participants per page

#     page = request.GET.get('page')
#     try:
#         participants = paginator.page(page)
#     except PageNotAnInteger:
#         participants = paginator.page(1)
#     except EmptyPage:
#         participants = paginator.page(paginator.num_pages)

#     return render(request, 'participant_list.html', {'participants': participants})



from django.db.models import Q

def participant_list(request):
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)

    if search_query:
        # Split the search query into individual terms
        search_terms = search_query.split()

        # Construct a Q object to search for first name or last name containing any of the search terms
        first_name_q = Q()
        last_name_q = Q()
        for term in search_terms:
            first_name_q |= Q(firstname__icontains=term)
            last_name_q |= Q(lastname__icontains=term)

        # Query participants with first name or last name matching any of the search terms
        participants = Participants.objects.filter(first_name_q | last_name_q)
    else:
        participants = Participants.objects.all()

    # Set up pagination
    paginator = Paginator(participants, 10)  # Show 10 participants per page
    try:
        participants = paginator.page(page)
    except PageNotAnInteger:
        participants = paginator.page(1)
    except EmptyPage:
        participants = paginator.page(paginator.num_pages)

    context = {'participants': participants, 'search_query': search_query}
    return render(request, 'participant_list.html', context)


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

@api_view(['POST'])
def update_attendance(request, unique_identifier):
    participant = get_object_or_404(Participants, unique_identifier=unique_identifier)
    participant.attendanceStatus = "P"
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
        Participants.objects.create(**entry)

    generate_qr()

# logic for login is incomplete
def login(request):
    if request.method == 'POST':
        # Retrieve email and password from form submission
        email = request.POST.get('user_email')
        password = request.POST.get('user_password')

        # Authenticate user
        user = authenticate(request, email=email, password=password)

        if user is not None:
            # If user is authenticated, login the user and redirect to a success page
            login(request, user)
            return redirect('participant_list.html')  # Replace 'success_page' with the URL name of your desired success page
        else:
            # If authentication fails, display an error message
            error_message = "Invalid email or password. Please try again."
            return render(request, 'login.html', {'error_message': error_message})

    # If request method is not POST, render the login page
    return render(request, 'login.html')

