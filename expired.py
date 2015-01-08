import os
import ldap
import datetime
import getpass
import smtplib
import jinja2
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEImage import MIMEImage

# LDAP Variables
server = 'IPA.local'
username = 'uid=YOUR_USERNAME,cn=users,cn=accounts,dc=linux, dc=dhnet, dc=ufl, dc=edu'
password = 'PASSWORD'
base = 'cn=users,cn=accounts,dc=linux, dc=dhnet, dc=ufl, dc=edu'
retrieve_Attributes = ['uid','krbPasswordExpiration','mail','nsaccountlock']
filter_Attributes = '(objectClass=*)'

# MAIL Variables
mail_From = 'MAIL@TEST.LOCAL'
mail_FromAdmin = 'MAIL@TEST.LOCAL'
mail_Admin = 'ADMIN@TEST.LOCAL'
mail_Server = 'mail.test.local'
email_ExpiredTemplate = 'expired_email.html'
email_AdminTemplate = 'admin_email.html'
email_TemplateDir = os.path.dirname(os.path.realpath(__file__))
email_Img = os.path.dirname(os.path.realpath(__file__)) + '/ipa_instruct.gif'

# IPA Server URL
ipa_Url = 'https://ipa.local/ipa/ui'

# Lists
users_Disabled = []
users_Expired = []
users_MissingEmails = []

# Bind to the LDAP server
ldap_Instance = ldap.initialize('ldap://' + server)
ldap_Instance.simple_bind_s(username, password)

# Perform LDAP search
search_Results = ldap_Instance.search(base, ldap.SCOPE_SUBTREE, filter_Attributes, retrieve_Attributes)
# Gather the search results
# The 1 below instructs the result function to return ALL results
search_ResultType, search_ResultData = ldap_Instance.result(search_Results, 1)

def send_ExpiredEmail(email, name, days):
    # Setup JINJA2
    template_loader = jinja2.FileSystemLoader( searchpath=email_TemplateDir )
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template(email_ExpiredTemplate)
    template_vars = { 'days': days,
                      'user': name,
                      'ipa_url': ipa_Url,
                    }
    output = template.render( template_vars )
    
    msg = MIMEMultipart()
    msg['Subject'] = 'IPA Password Expiring'
    msg['From'] = mail_From
    msg['To'] = email
    msg_Html = MIMEText(output, 'html')
    msg.attach(msg_Html)

    # Add the image
    fp = open(email_Img, 'rb')
    msg_Image = MIMEImage(fp.read())
    fp.close()
    msg_Image.add_header('Content-ID', '<image1>')
    msg.attach(msg_Image)


    mailer = smtplib.SMTP(mail_Server)
    mailer.sendmail(mail_From, email, msg.as_string())
    mailer.quit()

def send_AdminEmail(users_MissingEmails, users_Expired, users_Disabled):
    # Setup JINJA2
    template_loader = jinja2.FileSystemLoader( searchpath=email_TemplateDir )
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template(email_AdminTemplate)
    template_vars = { 'users_disabled': users_Disabled,
                      'users_expired': users_Expired,
                      'users_missingEmails': users_MissingEmails,
                    }
    output = template.render( template_vars )
    
    msg = MIMEText(output, 'html')
    msg['Subject'] = 'IPA Admin Report'
    msg['From'] = mail_FromAdmin
    msg['To'] = mail_Admin

    mailer = smtplib.SMTP(mail_Server)
    mailer.sendmail(mail_From, mail_Admin, msg.as_string())
    mailer.quit()


for search_Data in search_ResultData:

    # Check for certain values. If they don't exist, continue
    if search_Data[1].has_key('uid'):
        uid = str(search_Data[1]['uid']).replace("['","").replace("']","")
    else:
        print('No UID')
	continue

    if search_Data[1].has_key('mail'):
        email = str(search_Data[1]['mail']).replace("['","").replace("']","")
    else:
        print(uid + ' doesnt have an email address')
        users_MissingEmails.append([uid, 'BLANK'])
        print('----------------')
        continue
    
    # Check for DISABLED accounts
    # A nsaccountlock of TRUE == Disabled
    if search_Data[1].has_key('nsaccountlock'):
	nsaccountlock = str(search_Data[1]['nsaccountlock']).replace("['","").replace("']","")
        if 'true' in nsaccountlock.lower():
            print('User ' + uid + ' is disabled')
	    print('----------------')
            users_Disabled.append(uid)
      	    continue

    # Calculate whether the password is expired or expiring
    # We will email on LESS THAN 8 days until EXPIRED
    # Once expired, the users name will be added to the expired_users list
    # The expired_users list will be sent to the administrator
    today = datetime.datetime.today()
    ldap_Expired = str(search_Data[1]['krbPasswordExpiration']).replace("['","").replace("']","")
    ldap_Expired = datetime.datetime.strptime(ldap_Expired,'%Y%m%d%H%M%SZ')
    days_Left = ldap_Expired - today
    
    if days_Left.days < 8:
        if days_Left.days <= 0:
            print('User: ' + uid)
            print('Expired: ' + str(ldap_Expired))
            print('----------------')
            users_Expired.append([uid, days_Left.days])
            continue
        else:
            print('User: ' + uid)
            print('Email: ' + email)
            print('Going To Expire - EMAILS OUTGOING')
            print('----------------')
	    send_ExpiredEmail(email, uid, days_Left.days)

send_AdminEmail(users_MissingEmails, users_Expired, users_Disabled)
