import pandas as pd
import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.core.mail import send_mail, EmailMessage
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from io import BytesIO
from django.conf import settings
from .models import Participants, QRcode, UserAccount, ParticipantCard
import csv
import base64
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate, login as django_login
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.files import File
from django.db.models import Q
from django.contrib.auth.hashers import check_password
import json
from django.utils import timezone
from rest_framework.renderers import JSONRenderer
from email.mime.image import MIMEImage
from django.core.exceptions import ObjectDoesNotExist


@api_view(['GET'])
def home(request):
    if 'user_id' in request.session:
        print(request.session['user_id'])
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
   

def participant_list(request):
    if 'user_id' in request.session:
        search_query = request.GET.get('search', '')
        page = request.GET.get('page', 1)

        print(request.user)


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
    else:
        return render(request, 'login.html')


def send_qr(request, participant_id, qr_type):
    try:
        participant = Participants.objects.get(participantID=participant_id)
    except ObjectDoesNotExist:
        return JsonResponse({"success": False, "message": f"Participant with ID PR-{participant_id} not found."})

    # Fetches the QR code related to the participant
    qrcode_instance = QRcode.objects.filter(Participants_participantID=participant_id).first()

    if not qrcode_instance:
        return JsonResponse({"success": False, "message": f"No QR code found for participant with ID PR-{participant_id}."})

    # Select the appropriate QR code image based on the qr_type.
    if qr_type == 1:
        qr_image = qrcode_instance.image_qr1
    elif qr_type == 2:
        qr_image = qrcode_instance.image_qr2
    else:
       # Handle other cases here
        qr_image = None  # or any other default value or error handling logic

    if not qr_image:
        return JsonResponse({"success": False, "message": f"No QR code image found for type {qr_type}."})

    # Path to the QR code image is fetched from the database. Actual image retrieval may depend on how the image is stored.

    # You need to set your actual subject, message, and SMTP details
    subject = f"Here's your QR {qr_type}"
    message = f"Dear Participant ,\n\nPlease find your QR code {qr_type} attached.\n\nBest regards,\nProcom 24"
    from_email = 'samaharizvi14@gmail.com'

    try:
        # Construct the email message
        email = EmailMessage(
            subject,
            message,
            from_email,
            [participant.email]
        )

        # Attach the QR code image
        with qr_image.open() as img:
            mime_image = MIMEImage(img.read())
            mime_image.add_header('Content-ID', f'<QR_Code_{qr_type}>')
            mime_image.add_header('Content-Disposition', f'attachment; filename="QR_Code_{qr_type}.png"')  # Adjust as needed
            email.attach(mime_image)

        # Send the email
        email.send()
        return JsonResponse({"success": True, "message": f"Email sent to participant with ID PR-{participant_id} with subject: '{subject}'"})
       
    except Exception as e:
        print(f"Error sending email to {participant.email}: {e}")
        return JsonResponse({"success": False, "message": f"Error sending email to participant with ID {participant_id} : {e}"})




@api_view(['POST'])
def send_qr_all(request, qr_type):
    participants = Participants.objects.all()

    if not participants:
        return JsonResponse({"success": False, "message": "Error loading participant data. Please check the database."})

    successful_deliveries = 0
    failed_deliveries = 0

    # You need to set your actual subject, message, and SMTP details
    subject = f"Here's your QR {qr_type}"
    message = f"Dear Participant,\n\nPlease find your QR code {qr_type} attached.\n\nBest regards,\nProcom 24"
    from_email = 'samaharizvi14@gmail.com'

    for participant in participants:
        # Fetches the QRcode related to the participant
        qrcode_instance = QRcode.objects.filter(Participants_participantID=participant.participantID).first()

        if qrcode_instance:
            # Select the appropriate QR code image based on the qr_type.
            qr_image = qrcode_instance.image_qr1 if qr_type == 1 else qrcode_instance.image_qr2

            try:
                # Construct the email message
                email = EmailMessage(
                    subject,
                    message,
                    from_email,
                    [participant.email]
                )

                # Attach the QR code image if it exists.
                if qr_image:
                    with qr_image.open() as img:
                        mime_image = MIMEImage(img.read())
                        mime_image.add_header('Content-ID', f'<QR_Code_{qr_type}>')
                        mime_image.add_header('Content-Disposition', f'attachment; filename="QR_Code_{qr_type}.png"')  # Adjust as needed
                        email.attach(mime_image)

                # Send the email
                email.send()
                successful_deliveries += 1

            except Exception as e:
                print(f"Error sending email to {participant.email}: {e}")
                failed_deliveries += 1

    if successful_deliveries == len(participants):
        return JsonResponse({"success": True, "message": f"Emails sent to all participants with subject: '{subject}'"})
    else:
        error_message = f"Error: Failed to send emails to some participants. {failed_deliveries} emails failed."
        return JsonResponse({"success": False, "message": error_message})

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
    
def save_to_database(data):
    for entry in data:
        # Check if the CNIC already exists in the database
        if 'cnic' in entry:
            existing_participant = Participants.objects.filter(cnic=entry['cnic']).first()
            if existing_participant:
                # If CNIC exists, skip uploading this row
                print(f"Multiple entry of participant with CNIC: {entry['cnic']}")

        if any(value is None or value == '' for value in entry.values()):
            continue

        participant = Participants.objects.create(**entry)

        data_qrcode1 = f"PR-{participant.participantID},{entry.get('firstname')},{entry.get('lastname')},{entry.get('contestname')},qr1"
        
        data_qrcode2 = f"PR-{participant.participantID},{entry.get('firstname')},{entry.get('lastname')},{entry.get('contestname')},qr2"

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
            print(f"Error saving images for participant PR-{participant.participantID}: {str(e)}")
    cleanup_photos()    
    
def process_csv(csv_file):
    data = []
    decoded_file = csv_file.read().decode('utf-8').splitlines()
    csv_reader = csv.DictReader(decoded_file)
    
    for row in csv_reader:
        row['firstname'] = row.pop('\ufefffirstname') 
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
   


# views.py
def manual_attendance(request, participant_id=None):  # Modify the view to accept the participant_id parameter
    try:
        if participant_id is not None:  # Check if participant_id is provided
            participant = Participants.objects.get(participantID=participant_id)
            participant.attendanceStatus = 'P'
            participant.save()
            return redirect('participant_list')
        else:
            return JsonResponse({'success': False, 'message': 'Participant ID not provided'})
    except Participants.DoesNotExist:
        return JsonResponse({'success': False, 'message': f'Participant PR-{participant_id} not found'})

    
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
                    qr_type = qr_data.split(',')[-1]  # Extract qr_type from qr_data
                    if qr_type == 'qr1':
                        # Check if a participant card already exists
                        existing_card = ParticipantCard.objects.filter(Participants_participantID=participant).exists()
                        if existing_card:
                            # If a card is already issued, send QR code 2 automatically
                            # qr2_sent_response = send_qr(request, participant.participantID, qr_type=2)
                            # qr2_sent_data = json.loads(qr2_sent_response.content)
                            # if qr2_sent_data.get('success'):
                            return JsonResponse({'message': f'Card already issued to participant: PR-{participant.participantID}. QR code already sent'})
                        else:
                            # Generate participant card
                            ParticipantCard.objects.create(issuedate=timezone.now(), validitystatus='Valid', Participants_participantID=participant)
                             # If a card is already issued, send QR code 2 automatically
                            qr2_sent_response = send_qr(request, participant.participantID, qr_type=2)
                            qr2_sent_data = json.loads(qr2_sent_response.content)
                            if qr2_sent_data.get('success'):
                                return JsonResponse({'message': f'Card issued to participant: PR-{participant.participantID}. QR code 2 sent.'})
                            else:
                                return JsonResponse({'message': f'Failed to send QR code 2 after issuing card to participant: PR-{participant.participantID}'})
                            return JsonResponse({'message': f'Card issued to participant: {participant.participantID}'})
                        
                    elif qr_type == 'qr2':
                        # Mark attendance
                        participant.attendanceStatus = 'P'
                        participant.save()
                        return JsonResponse({'message': f'Attendance marked for participant: PR-{participant.participantID}'})
                else:
                    return JsonResponse({'message': 'QR code not found'})
            except Exception as e:
                print(e)  # Print the actual exception for debugging purposes
                return JsonResponse({'message': 'Error occurred while processing the QR code'}, status=500)
        else:
            return JsonResponse({'message': 'No QR code data received'}, status=400)
    else:
        return HttpResponseBadRequest('Invalid request method')


def generate_csv(request):
    participants = Participants.objects.filter(
        attendanceStatus='P',
        participantcard__validitystatus='Valid'
    )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="procom_participants.csv"'

    # Define CSV headers
    fieldnames = ['First Name', 'Last Name', 'CNIC', 'Email', 'Phone', 'University Name', 'Contest Name']

    writer = csv.DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()

    for participant in participants:
        writer.writerow({
            'First Name': participant.firstname,
            'Last Name': participant.lastname,
            'CNIC': participant.cnic,
            'Email': participant.email,
            'Phone': participant.phonenumber,
            'University Name': participant.universityname,
            'Contest Name': participant.contestname,
        })

    return response
   
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