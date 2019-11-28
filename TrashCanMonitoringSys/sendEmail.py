import smtplib

duration = '10/13/0219 - 11/13/2019'

def sendemail(msg):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login("email_acc", "pswd")    # gmail need to go to account, set up in security to turn on Less secure app access

        sent_from = "kittymayor2@gmail.com"
        to = ['kittymayor2@gmail.com']   #['ruizhe.song@sjsu.edu@sjsu.edu']
        sub = 'Bill of Trash Can Monitoring System'
        message = 'Subject: {}\n\n{}'.format(sub, msg)

        server.sendmail(sent_from,to, message)
        server.close()
        print("email is sent successfully..")
    except:
        print('sending email failed:')

