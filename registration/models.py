from django.db import models

# Create your models here.

class Participants(models.Model):
    participantID = models.AutoField(primary_key=True)
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phonenumber = models.IntegerField()
    studentid = models.CharField(max_length=255)
    universityname = models.CharField(max_length=255)
    contestname = models.CharField(max_length=255)
    age = models.IntegerField()

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
    passwordhash = models.CharField(max_length=255)
    Participants_ParticipantID = models.ForeignKey(Participants, on_delete=models.CASCADE)

    def __str__(self):
        return f"User {self.username} - {self.Participants_ParticipantID}"

class QRcode(models.Model):
    QRcodeId = models.AutoField(primary_key=True)
    QRcodetype = models.CharField(max_length=255)
    OTP = models.CharField(max_length=255)
    confirmationstatus = models.CharField(max_length=255)
    Participants_participantID = models.ForeignKey(Participants, on_delete=models.CASCADE)

    def __str__(self):
        return f"QR Code {self.QRcodeId} - {self.Participants_participantID}"

class Attendence(models.Model):
    AttendenceID = models.AutoField(primary_key=True)
    eventdate = models.DateField()
    status = models.CharField(max_length=255)
    Participants_participantID = models.ForeignKey(Participants, on_delete=models.CASCADE)

    def __str__(self):
        return f"Attendance {self.AttendenceID} - {self.Participants_participantID}"

class Registrations(models.Model):
    RegistrationID = models.AutoField(primary_key=True)
    registrationdate = models.DateField()
    status = models.CharField(max_length=255)
    Participants_participantID = models.ForeignKey(Participants, on_delete=models.CASCADE)

    def __str__(self):
        return f"Registration {self.RegistrationID} - {self.Participants_participantID}"

class Certificates(models.Model):
    certificateID = models.CharField(primary_key=True, max_length=255)
    certificateText = models.CharField(max_length=255)
    issuedate = models.DateField()
    Participants_participantID = models.ForeignKey(Participants, on_delete=models.CASCADE)

    def __str__(self):
        return f"Certificate {self.certificateID} - {self.Participants_participantID}"
