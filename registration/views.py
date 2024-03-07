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


# def send_qr(request, participant_id, qr_type):
#     try:
#         participant = Participants.objects.get(participantID=participant_id)
#     except ObjectDoesNotExist:
#         return JsonResponse({"success": False, "message": f"Participant with ID PR-{participant_id} not found."})

#     # Fetches the QR code related to the participant
#     qrcode_instance = QRcode.objects.filter(Participants_participantID=participant_id).first()

#     if not qrcode_instance:
#         return JsonResponse({"success": False, "message": f"No QR code found for participant with ID PR-{participant_id}."})

#     # Select the appropriate QR code image based on the qr_type.
#     if qr_type == 1:
#         qr_image = qrcode_instance.image_qr1
#     elif qr_type == 2:
#         qr_image = qrcode_instance.image_qr2
#     else:
#        # Handle other cases here
#         qr_image = None  # or any other default value or error handling logic

#     if not qr_image:
#         return JsonResponse({"success": False, "message": f"No QR code image found for type {qr_type}."})

#     # Path to the QR code image is fetched from the database. Actual image retrieval may depend on how the image is stored.

#     # You need to set your actual subject, message, and SMTP details
#     subject = f"QR {qr_type} for competition {participant.contestname}"
#     message = """
#     Subject: Important Instructions for Team Leads - Participant Cards Collection

#     Dear Team Leader,

#     We hope this email finds you well and excited for the upcoming event, PROCOM'24. As team leads, it is essential for you to follow certain procedures to ensure smooth registration and participation for your team.

#     Attached to this email, you will find unique QR codes assigned specifically to your team. These QR codes will serve as the key to collect participant cards for your team members.

#     Here are the steps you need to follow:

#     1. *QR Code Collection:* Please ensure that only the designated team lead retrieves the QR codes attached to this email. If your team is participating in multiple competitions, you will receive multiple QR codes, one for each competition.

#     2. *Registration Desk:* Upon arrival at the entrance gate, the team lead must present all the QR codes associated with your team at the registration desk. Our staff will scan each QR code to verify their participation in the respective competitions.

#     3. *Participant Cards:* Once all QR codes are successfully scanned, participant cards will be provided to your team members. It is crucial that the entire team is present at the registration desk during this process.

#     Additionally, please ensure that your team arrives at least 30 minutes prior to their competition time. Procom will not be held responsible for any inconvenience caused due to teams arriving with insufficient time.

#     Please note the following:

#     - *Responsibility:* Failure to present all QR codes at the registration desk will result in the inability to collect participant cards. Procom24 will not be held responsible for any inconvenience caused due to non-compliance with this procedure.

#     - *Team Presence:*  The presence of the entire team at the registration desk is mandatory for the collection of participant cards. Individual team members will not be able to collect their cards separately. If any of your members are absent, rest of the team must be present with their team lead during entry. No additional team members can enter afterwards; only one entry per team is allowed.

#     We appreciate your cooperation in following these instructions to ensure a seamless experience for everyone involved. If you have any questions or require further assistance, please do not hesitate to contact us.

#     Best regards,
#     PROCOM'24 Organizing Team
#     """
#     from_email = 'procom@nu.edu.pk'

#     try:
#         # Construct the email message
#         email = EmailMessage(
#             subject,
#             message,
#             from_email,
#             [participant.email]
#         )

#         # Attach the QR code image
#         with qr_image.open() as img:
#             mime_image = MIMEImage(img.read())
#             mime_image.add_header('Content-ID', f'<QR_Code_{qr_type}>')
#             mime_image.add_header('Content-Disposition', f'attachment; filename="QR_Code_{qr_type}.png"')  # Adjust as needed
#             email.attach(mime_image)

#         # Send the email
#         email.send()
#         return JsonResponse({"success": True, "message": f"Email sent to participant with ID PR-{participant_id} with subject: '{subject}'"})
       
#     except Exception as e:
#         print(f"Error sending email to {participant.email}: {e}")
#         return JsonResponse({"success": False, "message": f"Error sending email to participant with ID {participant_id} : {e}"})


from django.template.loader import render_to_string
from django.http import JsonResponse

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
        subject='Important Instructions for Team Leads - Participant Cards Collection'
        email_message_path = 'email_message1.txt'
    elif qr_type == 2:
        qr_image = qrcode_instance.image_qr2
        subject='QR Code for Attendance'
        email_message_path = 'email_message2.txt'
    else:
       # Handle other cases here
        qr_image = None  # or any other default value or error handling logic

    if not qr_image:
        return JsonResponse({"success": False, "message": f"No QR code image found for type {qr_type}."})

    # Read the email message content from the respective file
    email_message = render_to_string(email_message_path)

    # You need to set your actual subject and SMTP details
    subject = subject
    from_email = 'procom@nu.edu.pk'

    try:
        # Construct the email message
        email = EmailMessage(
            subject,
            email_message,  # Use the content from the respective file
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

        # Return JSON response with success message
        response_data = {"success": True, "message": f"Email sent to participant with ID PR-{participant_id} with subject: '{subject}'"}
        # Pass response data to JavaScript function to show it in a popup
        return JsonResponse(response_data)

    except Exception as e:
        error_message = f"Error sending email to {participant.email}: {e}"
        # Return JSON response with error message
        response_data = {"success": False, "message": error_message}
        # Pass response data to JavaScript function to show it in a popup
        return JsonResponse(response_data)




@api_view(['POST'])
def send_qr_all(request, qr_type):
    participants = Participants.objects.all()

    if not participants:
        return JsonResponse({"success": False, "message": "Error loading participant data. Please check the database."})

    successful_deliveries = 0
    failed_deliveries = 0

    for participant in participants:
        # Fetches the QRcode related to the participant
        qrcode_instance = QRcode.objects.filter(Participants_participantID=participant.participantID).first()
        if qrcode_instance:
            # Select the appropriate QR code image based on the qr_type.
            qr_image = qrcode_instance.image_qr1 if qr_type == 1 else qrcode_instance.image_qr2
            if qr_type == 1:
                subject='Important Instructions for Team Leads - Participant Cards Collection'
            elif qr_type == 2:
                subject='QR Code for Attendance'
            try:
                # Construct the email message
                email_message_path = f'email_message{qr_type}.txt'
                email_message = render_to_string(email_message_path)

                subject = subject
                from_email = 'procom@nu.edu.pk'

                email = EmailMessage(
                    subject,
                    email_message,
                    from_email,
                    [participant.email]
                )

                # Attach the QR code image if it exists.
                if qr_image:
                    with qr_image.open() as img:
                        mime_image = MIMEImage(img.read())
                        mime_image.add_header('Content-ID', f'<QR_Code_{qr_type}>')
                        mime_image.add_header('Content-Disposition', f'attachment; filename="QR_Code_{qr_type}.png"')
                        email.attach(mime_image)

                # Send the email
                email.send()
                successful_deliveries += 1

            except Exception as e:
                print(f"Error sending email to {participant.email}: {e}")
                failed_deliveries += 1

    if successful_deliveries == len(participants):
        return JsonResponse({"success": True, "message": f"Emails sent to all participants with subject: 'QR {qr_type}'"})
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

        if any(value is None for value in entry.values()):
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
        # participantcard__validitystatus='Valid'
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