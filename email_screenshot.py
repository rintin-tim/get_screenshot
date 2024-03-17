import smtplib
import email.message
import os

eml_from = os.getenv("2GO_SMTP_LOGIN", os.getenv("MG_SMTP_LOGIN"))
smtp_server = os.getenv("2GO_SMTP_SERVER", os.getenv("MG_SMTP_SERVER"))
smtp_login = os.getenv("2GO_SMTP_LOGIN", os.getenv("MG_SMTP_LOGIN"))
smtp_pw = os.getenv("2GO_SMTP_PW", os.getenv("MG_SMTP_PW"))


def send_screenshot_email(html, send_to: list=["fake@email.com"]):

    if send_to:
        try:
            msg = email.message.Message()
            msg['Subject'] = 'Your Screenshots Are Ready'

            msg['From'] = eml_from
            msg['To'] = ", ".join(send_to)  # cannot use list in body, convert list to a string

            msg.add_header('Content-Type', 'text/html')
            msg.set_payload(html)

            print("** THE SMTP SERVER IS {}".format(smtp_server))
            s = smtplib.SMTP(smtp_server, port=587)
            s.starttls()

            # Login Credentials for sending the mail
            s.login(user=smtp_login, password=smtp_pw)

            result = s.sendmail(msg['From'], send_to, msg.as_string())

            print("** email sent to: {}".format(msg['To']))
            return result
        except Exception as err:
            print("** error when sending email: {}".format(err))

    else:
        print("** no email address, so no email")


if __name__ == "__main__":
    html = "Test"
    send_screenshot_email(html)
