import smtplib

customerName = 'Ye Mei'
duration = '04/01/0219 - 05/01/2019'


def sendemail(msg):


    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login("kittymayor2@gmail.com", "mayorkitty")

        sent_from = "kittymayor2@gmail.com"
        to = ['ruizhe.song@sjsu.edu@sjsu.edu']
        sub = 'Bill of Trash Can Monitoring System'
        message = 'Subject: {}\n\n{}'.format(sub, msg)

        server.sendmail(sent_from,to, message)
        server.close()
        print("email is sent successfully..")
    except:
        print('sending email failed:')

