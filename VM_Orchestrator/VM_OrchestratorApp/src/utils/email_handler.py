# pylint: disable=import-error
from VM_OrchestratorApp import settings

from django.core.mail import EmailMessage
from datetime import datetime
import json
import os

def send_email_with_attachment(file_dir, email_to, message, title):
	if not settings['EMAIL']['HOST_USER']:
		print("Couldn't seend email, email user not configurated")
		return
	email = EmailMessage(title, message, settings['EMAIL']['HOST_USER'], [email_to])
	email.attach_file(file_dir)
	email.send()
	print("An email has been send succesfully at:"+str(datetime.now()) + ' to ' + str(email_to))

def send_email_message_only(email_to, message, title):
	if not settings['EMAIL']['HOST_USER']:
		print("Couldn't seend email, email user not configurated")
		return
	email = EmailMessage(title, message, settings['EMAIL']['HOST_USER'], [email_to])
	email.send()
	print("An email has been send succesfully at:"+str(datetime.now()) + ' to ' + str(email_to))

def send_notification_email(findings,email_to):
	if not settings['EMAIL']['HOST_USER']:
		print("Couldn't seend email, email user not configurated")
		return