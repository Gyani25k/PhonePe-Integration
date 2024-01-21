from flask import Flask, render_template, redirect,url_for,request,jsonify,render_template_string
import uuid
import json
from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest
from phonepe.sdk.pg.payments.v1.payment_client import PhonePePaymentClient
from phonepe.sdk.pg.env import Env
from datetime import datetime
import os 
from flask_cors import CORS
import mysql.connector

from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__, template_folder='template')
CORS(app)

app.config['SECRET_KEY'] = 'PhonePay@!(*)2024'

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Initialize PhonePePaymentClient
merchant_id = os.getenv('merchant_id')
salt_key = os.getenv('salt_key')
salt_index = 1
env = Env.UAT
should_publish_events = True
phonepe_client = PhonePePaymentClient(merchant_id, salt_key, salt_index, env, should_publish_events)


user_data = {
    'firstname': '',
    'email': '',
    'amount':'',
	'userid':'',
	'txnid':'',
    'planid':''

}


def initiate_payment(name, email, amount):

    global user_data

    unique_transaction_id = user_data.get('txnid')

    # Define URLs
    ui_redirect_url = "http://127.0.0.1:8080/CheckStatusMobileV1?unique_transaction_id="+unique_transaction_id

    s2s_callback_url = "http://127.0.0.1:8080/CheckStatusMobileV1?unique_transaction_id="+unique_transaction_id

    id_assigned_to_user_by_merchant = '1'
    cancel_redirect_url="https://creativelo.1gen.cloud/page/paymentcallback/false"

    # Build Pay Page Request
    pay_page_request = PgPayRequest.pay_page_pay_request_builder(
        merchant_transaction_id=unique_transaction_id,
        amount=amount,
        merchant_user_id=id_assigned_to_user_by_merchant,
        callback_url=s2s_callback_url,
        redirect_url=ui_redirect_url,
        cancel_redirect_url=cancel_redirect_url
    )

    # Make payment and get Pay Page URL
    pay_page_response = phonepe_client.pay(pay_page_request)
    pay_page_url = pay_page_response.data.instrument_response.redirect_info.url

    # Save payment details in JSON
    payment_details = {
        "payment_started_at":datetime.now(),
        "name": name,
        "unique_transaction_id": unique_transaction_id,
        "amount": amount,
        "callback_url": s2s_callback_url,
        "redirect_url": ui_redirect_url,
        "pay_page_url": pay_page_url,
        "status": None,
        "status_msg": None
    }

    return payment_details

def check_payment_status(unique_transaction_id):
    response = phonepe_client.check_status(unique_transaction_id)
    print("response",response)
    print(response.data.payment_instrument.type.split('.')[-1])
    return response.message,response.data.state ,response.data.response_code , response.data.payment_instrument.type.split('.')[-1] , response.data.payment_instrument.pg_transaction_id


@app.route('/PaymentSuccess')
def pay_success():
    return render_template('success.html')

@app.route('/PaymentFailed')
def pay_failed():
    return render_template('failure.html')

@app.route('/GetPaymentData')
def get_payment_data():

    user_data['firstname'] = request.args.get('Name')
    user_data['email'] = request.args.get('Email')
    user_data['amount'] = request.args.get('Amount')
    user_data['userid'] = request.args.get('UserId')
    user_data['txnid'] = request.args.get('TransactionID')
    user_data['planid'] = request.args.get('Planid')

    name = user_data.get('name', '')
    email = user_data.get('email', '')
    amount = user_data.get('amount', '')

    amount = int(amount)*100


    payment_details = initiate_payment(name, email, amount)

    payment_details_to_save = {
        "payment_started_at": payment_details["payment_started_at"].isoformat(),
        "name": payment_details["name"],
        "unique_transaction_id": payment_details["unique_transaction_id"],
        "amount": payment_details["amount"],
        "callback_url": payment_details["callback_url"],
        "redirect_url": payment_details["redirect_url"],
        "pay_page_url": payment_details["pay_page_url"],
        "Message": None,
        "status": "PENDING",
        "phonepe_transactionid": None,
        "payment_mode": None,
    }

    with open('payment_details.json', 'a') as json_file:
        json.dump(payment_details_to_save, json_file, indent=2)


    return redirect(payment_details['pay_page_url'])


@app.route('/CheckStatusMobileV1')
def check_payment():

    global user_data

    unique_transaction_id = request.args.get('unique_transaction_id')

    amount = user_data.get('amount')
    planid = user_data.get('planid')
    
    message, Update, status, payment_mode, phonepe_transactionid = check_payment_status(unique_transaction_id)

    status = status.lower()
    try:
        with open('payment_details.json', 'r') as json_file:
            # Check if the file is empty or not
            data = json_file.read().strip()
            if not data:
                raise ValueError("Empty JSON file")
            
            payment_details = json.loads(data)
            
            payment_details["payment_date"] = datetime.now().date().isoformat()
            payment_details["Message"] = message
            payment_details["payment_mode"] = payment_mode
            payment_details["status"] = status
            payment_details["phonepe_transactionid"] = phonepe_transactionid
            payment_details["payment_ended_at"] = datetime.now().isoformat()

    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"Error loading JSON file: {e}")

    with open('payment_details.json', 'w') as json_file:
        json.dump(payment_details, json_file, indent=2, default=str)
    
    if status == 'success':
        return redirect("http://127.0.0.1:8080/PaymentSuccess?txnid="+unique_transaction_id+"&amount="+amount+ "&phonepayid="+phonepe_transactionid+"&mode="+payment_mode+"&status="+status+"&planid="+planid)
    else:
        return redirect("http://127.0.0.1:8080/PaymentFailed?txnid="+unique_transaction_id+"&amount="+amount+ "&phonepayid="+phonepe_transactionid+"&mode="+payment_mode+"&status="+status+"&planid="+planid)


    
    

    


if __name__ == "__main__":
    app.run(debug=True,port=8080)