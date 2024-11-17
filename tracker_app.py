from flask import Flask, request, render_template, redirect, url_for
from flask_mysqldb import MySQL
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import time
import re
import threading


app = Flask(__name__)

# Database configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'system'
app.config['MYSQL_DB'] = 'shoppingdb'
mysql = MySQL(app)

# Function to get the price of the product
def get_price(url):
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Cache-Control': 'max-age=0'
        })
        soup = BeautifulSoup(response.content, 'html.parser')

        price_element = soup.select_one('.a-price-whole')  # For Amazon

        if price_element:
            price_text = price_element.text.strip()
            price_number = re.findall(r'[\d,]+', price_text)
            if price_number:
                price = float(price_number[0].replace(',', ''))
                return price
        return None
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

# Function to send email notifications
def send_email(subject, body, to_email, from_email, from_password):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

# Function to track price in the background
def track_price_from_db(id, product_link, target_price, user_email, from_email, from_password):
    check_interval = 3000  # Check every hour
    while True:
        current_price = get_price(product_link)
        if current_price is not None:
            print(f"Current Price: ₹{current_price}")
            if current_price <= target_price:
                subject = "Product Price Dropped!"
                body = f"The price dropped to ₹{current_price}!\nThis is below your target price of ₹{target_price}.\nCheck the product here: {product_link}"
                send_email(subject, body, user_email, from_email, from_password)

                # Mark as notification sent in database
                cursor = mysql.connection.cursor()
                cursor.execute("UPDATE price_tracker SET notification_sent = 1 WHERE id = %s", (id,))
                mysql.connection.commit()
                cursor.close()
                break
            else:
                print("Price not yet low enough, checking again later.")
        else:
            print("Could not retrieve the current price, will try again.")
        
        time.sleep(check_interval)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add_price_tracker():
    product_link = request.form['product_link']
    target_price = float(request.form['target_price'])
    user_email = request.form['user_email']
    from_email = "my.projects.testt@gmail.com"
    from_password = "rtta abci arqp syhl"  # Use environment variables or a more secure method

    # Insert the user's information into the database
    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO price_tracker (product_link, target_price, user_email, notification_sent) VALUES (%s, %s, %s, %s)",
        (product_link, target_price, user_email, 0)
    )
    mysql.connection.commit()

    # Get the ID of the last inserted record
    cursor.execute("SELECT LAST_INSERT_ID()")
    id = cursor.fetchone()[0]
    cursor.close()

    # Start the price tracking in the background
    threading.Thread(target=track_price_from_db, args=(id, product_link, target_price, user_email, from_email, from_password)).start()

    # Render a success page
    return render_template('success.html', product_link=product_link, target_price=target_price, user_email=user_email)






if __name__ == '__main__':
    app.run(debug=True)
















def send_email(subject, body, to_email, from_email, from_password):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

@app.route('/send_price_drop_email', methods=['POST'])
def send_price_drop_email():
    data = request.get_json()
    subject = data['subject']
    body = data['body']
    to_email = data['to_email']
    from_email = "your_email@gmail.com"
    from_password = "your_email_password"

    send_email(subject, body, to_email, from_email, from_password)
    return jsonify({"message": "Email sent successfully!"}), 200
