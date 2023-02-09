#  Install the libraries:
from scrapingbee import ScrapingBeeClient
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

# This section scrapes the website and saves a screenshot locally

client = ScrapingBeeClient(api_key=("First-40-api_key" "Second-40-api_key"))

response = client.get(
    "https://www.google.com/",
    params={
        "screenshot_full_page": True,
    },
)
if response.ok:
    with open("./screenshot.png", "wb") as f:
        f.write(response.content)
# This section takes the screenshot and emails it

OneTimePW = "TBD!"


def send_mail(
    send_from,
    send_to,
    subject,
    message,
    files=[],
    server="localhost",
    port=25,
    username=[],
    password=OneTimePW,
    use_tls=True,
):
    """

    Args:
        send_from (str): Email_1
        send_to (list[str]): (Email_1, Email_2)
        subject (str): Today's Bids-proposals
        message (str): Please see attached for screenshot of today's Bids-proposals page
        files (list[str]): ./screenshot.png
        server (str): "server"
        port (int): 25
        username (str):
        password (str):
        use_tls (bool): False
    """
    msg = MIMEMultipart()
    msg["From"] = send_from
    msg["To"] = COMMASPACE.join(send_to)
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject

    msg.attach(MIMEText(message))

    for path in files:
        part = MIMEBase("application", "octet-stream")
        with open(path, "rb") as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition", "attachment; filename={}".format(Path(path).name)
        )
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if use_tls:
        smtp.starttls()
    smtp.login(username, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()
