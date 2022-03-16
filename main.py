import requests
import logging
import smtplib
import configparser
import time

from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ------------------------------------------------------------------
#   Logging Setup
# ------------------------------------------------------------------

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%m-%y %H:%M:%S')

file_handler = logging.FileHandler("settings/logs.log", encoding='utf8')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

# ------------------------------------------------------------------

config = configparser.RawConfigParser()
configFilePath = r"settings/config.txt"
config.read(configFilePath, encoding="utf-8")


def main():
    while(True):
        # Creating a connction with the daft.ie website and adding headers
        headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0"}

        response = requests.get(config.get("CONFIG", "WEBSITE_URL"), headers=headers)
        webpage = response.content

        # Parsing the webpage with Beautiful Soup
        soup = BeautifulSoup(webpage, "html.parser")

        vests = parse_webpage(soup)

        if len(vests) != 0:
            msg = "New gaff(s) found: " + str(vests)
            send_email(vests)
        else:
            msg = "No new gaffs found"
        logger.info(msg)
        
        time.sleep(int(config.get("CONFIG", "WAIT_PERIOD")))


def parse_webpage(soup):

    vests_found = []

    vest = soup.find_all(class_=config.get("CONFIG", "CLASS_TO_LOOK_FOR"))

    for i in vest:
        if "Carlow" in i.text or "Kilkenny" in i.text:
            vests_found.append(i.text)

    return vests_found


def send_email(vests):
    smtp = smtplib.SMTP(config.get("CONFIG", "SMTP_SERVER"), config.get("CONFIG", "SMTP_PORT"))

    receiving_emails = config.get("CONFIG", "SMTP_RECEIVING_EMAIL").split(",")
    
    try:
        email_content = "Vest Found: \n\n"
        for i in range(len(vests)):
            email_content += f"\n{vests[i]}"

        smtp.ehlo()
        smtp.starttls()

        smtp.login(config.get("CONFIG", "SMTP_SENDING_EMAIL"), config.get("CONFIG", "SMTP_PASSWORD"))

        for email in receiving_emails:
            message = MIMEMultipart()
            message["Subject"] = "Oneills Vest Update"
            message["From"] = config.get("CONFIG", "SMTP_SENDING_EMAIL")
            message["To"] = email
            message.attach(MIMEText(email_content))

            smtp.sendmail(
                from_addr=config.get("CONFIG", "SMTP_SENDING_EMAIL"),
                to_addrs=email,
                msg=message.as_string()
            )

            logger.info("Email successfully sent to:\t" + email)
    except Exception as e:
        logger.error(e)
    
    smtp.quit()


if __name__ == "__main__":
    main()