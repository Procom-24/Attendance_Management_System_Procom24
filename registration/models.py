from django.db import models

class Participants(models.Model):
    participantID = models.AutoField(primary_key=True)
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    cnic = models.CharField(max_length=13, default='')  # CNIC field added
    email = models.EmailField()
    phonenumber = models.CharField(max_length=20)
    universityname = models.CharField(max_length=255)
    contestname = models.CharField(max_length=255)
    attendanceStatus = models.CharField(max_length=255, default='A')

    def __str__(self):
        return f"{self.firstname} {self.lastname}"

class ParticipantCard(models.Model):
    cardID = models.AutoField(primary_key=True)
    issuedate = models.DateField()
    validitystatus = models.CharField(max_length=255)
    Participants_participantID = models.ForeignKey(Participants, on_delete=models.CASCADE)

    def __str__(self):
        return f"Card {self.cardID} - {self.Participants_participantID}"

class UserAccount(models.Model):
    userID = models.CharField(primary_key=True, max_length=255)
    username = models.CharField(max_length=255)
    email = models.EmailField(null=True)
    passwordhash = models.CharField(max_length=255)
    
    def __str__(self):
        return f"User {self.username}"

class QRcode(models.Model):
    QRcodeId = models.AutoField(primary_key=True)
    DataQRcode1 = models.CharField(max_length=255)
    DataQRcode2 = models.CharField(max_length=255)
    image_qr1 = models.ImageField(upload_to='qrcodes/', null=True, blank=True)
    image_qr2 = models.ImageField(upload_to='qrcodes/', null=True, blank=True)

    # OTP = models.CharField(max_length=255)
    # confirmationstatus = models.CharField(max_length=255)
    Participants_participantID = models.ForeignKey(Participants, on_delete=models.CASCADE)

    def __str__(self):
        return f"QR Code {self.QRcodeId} - {self.Participants_participantID}"

class Certificates(models.Model):
    certificateID = models.CharField(primary_key=True, max_length=255)
    certificateText = models.CharField(max_length=255)
    issuedate = models.DateField()
    Participants_participantID = models.ForeignKey(Participants, on_delete=models.CASCADE)

    def __str__(self):
        return f"Certificate {self.certificateID} - {self.Participants_participantID}"
