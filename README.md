# PhonePe Integration 

## Overview
This repository contains files related to the integration of PhonePe payment services into your application. The integration involves three main components, each serving a specific purpose in the payment flow:

1. **PhoneIntegration_JSON.py**: This file is responsible for saving payment-related data to a JSON file after a successful transaction using PhonePe.

2. **PhonePeInstegration_MYSQL.py**: This file handles the storage of payment information into a SQL database. It ensures that transaction data is securely stored and can be easily queried when needed.

3. **MobilePhonePe.py**: This file focuses on the integration of PhonePe payment services into your application. It includes functions and methods to initiate payments, handle callbacks, and manage the overall payment flow.

## Requirements
Ensure that the following dependencies are installed before integrating PhonePe into your application:

- Python (>=3.6)
- PhonePe API credentials (Merchant ID, API Key, etc.)
- Required Python packages (specified in requirements.txt)

## Integration Steps

### 1. PhonePe API Credentials
Obtain your PhonePe API credentials (Merchant ID, API Key, etc.) from the PhonePe developer portal. You need these credentials to authenticate and interact with PhonePe's services.

### 2. Configure Integration Files
Update the configuration settings in the `py` file with your PhonePe API credentials. Additionally, configure any other settings such as callback URLs, transaction endpoints, etc.

### 3. Integrate PhonePe Payment in Your Application
Use the functions and methods provided in `py` to initiate and manage payments. Ensure that you handle callbacks appropriately to update the payment status in your application.

### 4. Save Payment Data
After a successful payment, use `PhoneIntegration_JSON.py` to save payment-related data to a JSON file for record-keeping. Utilize `MobilePhonePe.py` to store the same information securely in a SQL database.

## Support
For any questions or issues related to PhonePe integration, please contact our support team at kgyanender4@gmail.com.

Happy integrating!
