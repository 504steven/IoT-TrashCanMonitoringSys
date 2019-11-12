import smtplib

customerName = 'Ye Mei'
duration = '04/01/0219 - 05/01/2019'


def sendemail(msg):
    basicPlanEmailbody = msg

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login("kittymayor2@gmail.com", "mayorkitty")

        sent_from = "kittymayor2@gmail.com"
        to = ['111@sjsu.edu']
        subject = 'Park Trash Can Monitoring System Bill'
        emailbody = basicPlanEmailbody
        message = 'Subject: {}\n\n{}'.format(subject, emailbody)

        print("email to send:\n" + message)
        server.sendmail(sent_from,to, message)
        print("email is sent.")
        server.close()
    except:
        print('sth went wrong:')

