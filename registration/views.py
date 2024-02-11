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
from .models import Participants, QRcode, UserAccount
import csv
import base64
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate, login as django_login
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.files import File
from django.db.models import Q
from django.contrib.auth.hashers import check_password
import json


@api_view(['GET'])
def home(request):
    if 'user_id' in request.session:
        return render(request, 'home.html')
    else:
        return render(request, 'login.html')

def scan_qr(request):
    return render(request, 'scan_qr.html')

@api_view(['GET'])
def uploadPage(request):
    if 'user_id' in request.session:
        user_id = request.session['user_id']

        if user_id == 'admin':
            return render(request, 'uploadData.html')
        else:
            return render(request, 'forbidden.html')
    else:
        return render(request, 'login.html')
   
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
    if not participants:
        return HttpResponse("Error loading participant data. Please check the database.")

    email_from = "samaharizvi14@gmail.com"
    subject = "Your QR Code"
    successful_deliveries = 0

    for participant in participants:
        qr_image = None
        if qr_type == '1':
            qr_image = participant.qrcode.image_qr1.read() if participant.qrcode else None
        elif qr_type == '2':
            qr_image = participant.qrcode.image_qr2.read() if participant.qrcode else None
       
        if qr_image:
            recipient_email = participant.email
            if qr_type == '1':
                QT = "QR Code 1"
            elif qr_type == '2':
                QT = "QR Code 2"
            message = f"Please find your {QT} attached below."
           
            qr_image_base64 = base64.b64encode(qr_image).decode('utf-8')
            sent = send_mail(subject, message, email_from, [recipient_email], fail_silently=False, html_message=f'<img src="data:image/png;base64,{qr_image_base64}">')
            successful_deliveries += sent

    if successful_deliveries == len(participants):
        return HttpResponse(f"QR {qr_type} sent to all participants")
    else:
        return HttpResponse(f"Error: Failed to send QR {qr_type} to some participants")

# @api_view(['POST'])
# def update_attendance(request, unique_identifier):
#     participant = get_object_or_404(Participants, unique_identifier=unique_identifier)
#     participant.attendanceStatus = "P"
#     participant.save()

#     return JsonResponse({'status': 'success', 'message': f'{participant.firstname} marked as present.'})

# def generate_qr(name, email, qr_type):
#     data = f"Participant: {name}, Email: {email}, QR Type: {qr_type}"
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=4,
#     )
#     qr.add_data(data)
#     qr.make(fit=True)
#     img = qr.make_image(fill_color="black", back_color="white")

   
#     #img_path = f"{name}_qr{qr_type}.png"
#     img_path = f"qrcodes/{name}_qr{qr_type}.png"
#     img.save(img_path)

#     subject = f'QR Code {qr_type} for Event'
#     message = f'Please find your QR code {qr_type} attached.'
#     from_email = 'samaharizvi14@gmail.com'
#     to_email = email
#     email = EmailMessage(subject, message, from_email, [to_email])
#     email.attach_file(img_path)
#     email.send()

# csv file upload save data functionality
def upload_csv(request):
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        if user_id == 'admin':
            if request.method == 'POST' and request.FILES['csv_file']:
                csv_file = request.FILES['csv_file']

                # Process the CSV file
                data = process_csv(csv_file)

                # Save data to the database
                save_to_database(data)
                return JsonResponse({'status': 'success'})

            return render(request, 'home.html')
        else:
            return render(request, 'forbidden.html')
    else:
        return render(request, 'login.html')

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

# def save_to_database(data):
#     for entry in data:
#         if any(value is None or value == '' for value in entry.values()):
#             continue
#         Participants.objects.create(**entry)

#     generate_qr()

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
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
   
        qr_data = body_data.get('qrData', '')

        print("Received QR Data:", qr_data)  

        if qr_data:
            try:
                qr_code = QRcode.objects.filter(Q(DataQRcode1=qr_data) | Q(DataQRcode2=qr_data)).first()
                if qr_code:
                    participant = qr_code.Participants_participantID
                    participant.attendanceStatus = 'P'
                    participant.save()
                    return JsonResponse({'message': f'Attendance marked for participant: {participant.participantID}'})
                else:
                    return JsonResponse({'message': 'QR code not found'})
            except Exception as e:
                print(e)  # Print the actual exception for debugging purposes
                return JsonResponse({'message': 'Error occurred while processing the QR code'})
        else:
            return JsonResponse({'message': 'No QR code data received'})
    else:
        return JsonResponse({'message': 'Invalid request method'})

       
       
# def mark_attendance(request):
#     if request.method == 'POST':
#         qr_data = request.POST.get('qrData', '')
#         print("Received QR Data:", qr_data)  # Check if the data is received properly
#         try:
#             qr_code = QRCode.objects.get(Q(DataQRcode1=qr_data) | Q(DataQRcode2=qr_data))
#             participant = qr_code.Participants_participantID
#             participant.attendanceStatus = 'P'
#             participant.save()

#             return JsonResponse({'message': f'Attendance marked for participant: {participant.participantID}'})
#         except QRCode.DoesNotExist:
#             return JsonResponse({'message': 'QR code not found'})
#     else:
#         return JsonResponse({'message': 'Invalid request method'})
 

#hardcoded login for login admin and user
# def login_view(request):
#     if request.method == 'POST':
#         admin_name = 'admin'
#         admin_pass ='admin123'
#         hardcoded_username = 'user'
#         hardcoded_password = 'pass'

#         username = request.POST.get('user_email')
#         password = request.POST.get('user_password')

#         if (username == hardcoded_username and password == hardcoded_password) | (username == admin_name and password == admin_pass):
#             # # Dummy authentication for testing
#             # user = authenticate(username=username, password=password)
#             # if user is not None:
#             # django_login(request, user)
#             return redirect('/home/')
#         else:
#             return render(request, 'login.html', {'error_message': 'Invalid credentials'})
#         # else:
#         #     return render(request, 'login.html', {'error_message': 'Invalid credentials'})

#     return render(request, 'login.html')
   
# logic for login_view takes details from userAccount
def login_view(request):
    if 'user_id' in request.session:
        return render(request, 'home.html')
    if request.method == 'POST':
        # Retrieve email and password from form submission
        usernames = request.POST.get('user_name')
        password = request.POST.get('user_password')

        # Authenticate user
        try:
            user = UserAccount.objects.get(username = usernames , passwordhash=password)
        except UserAccount.DoesNotExist:
            user = None

        if user is not None:
            # If user is authenticated, set session and redirect to a success page
            request.session['user_id'] = user.userID

            return redirect('/home/')
        else:
            # If authentication fails, display an error message
            error_message = "Invalid email or password. Please try again."
            return render(request, 'login.html', {'error_message': error_message})

    # If request method is not POST, render the login page
    return render(request, 'login.html')


def logout(request):
    if 'user_id' in request.session:
        del request.session['user_id']
    return redirect('/home/')