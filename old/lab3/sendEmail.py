import smtplib

customerName = 'Ye Mei'
#totalRequestCount = 100
#totalResponseCount = 150
duration = '04/01/0219 - 05/01/2019'


def sendemail(balance, totalRequestCount, totalResponseCount, isPremium):
    basicPlanEmailbody = """Dear Customer %s,
    Your Park Trash Can Monitoring System Bill is here.
    Bill summary for account ending in: 640 for %s
    Total amount due: $%f
    Your payment due date: May 04, 2019

    """ %(customerName, duration, balance)
    
    premiumPlanEmailbody = """Premuim usage information: total request count: %d, total response count: %d.
    In the premium plan,
    remote repair/maintenance is executed based on analysis of data reported by the devices""" %(totalRequestCount, totalResponseCount)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login("kittymayor2@gmail.com", "mayorkitty")

        sent_from = "kittymayor2@gmail.com"
        to = ['ye.mei@sjsu.edu']
        subject = 'Park Trash Can IoT System Bill'
        emailbody = basicPlanEmailbody
        if isPremium:
            emailbody += premiumPlanEmailbody
    
        message = 'Subject: {}\n\n{}'.format(subject, emailbody)

        print("email to send:\n" + message)
        server.sendmail(sent_from,to, message)
        print("email is sent.")
        server.close()
    except:
        print('sth went wrong:')

