import mysql.connector
import google.generativeai as genai
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configure Gemini API Key
genai.configure(api_key="AIzaSyARAPLVRZJ6HDceimzpZU8--rwRdnHke3E")

# Connect to MySQL Database
mydb = mysql.connector.connect(host="localhost", user="root", password="saieshwar1811", database="bot")
cursor = mydb.cursor()

def gemini_flash_model(prompt):
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    }
    model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(prompt)
    return response.text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_available_slots', methods=['POST'])
def get_available_slots():
    user_details = request.json
    name = user_details['name']
    age = user_details['age']
    phone = user_details['phone']
    email = user_details['email']

    # Check user in the database
    sql = "SELECT User_ID FROM user_table WHERE Username = %s and age = %s and Phone_Number = %s and Email = %s"
    val = (name, age, phone, email)
    cursor.execute(sql, val)
    result = cursor.fetchone()

    if result:
        user_id = result[0]
    else:
        cursor.execute("INSERT INTO user_table (Username, age, Phone_Number, Email) VALUES (%s, %s, %s, %s)", (name, age, phone, email))
        mydb.commit()
        cursor.execute(sql, val)
        result = cursor.fetchone()
        user_id = result[0]

    # Fetch existing appointments from the database
    Date_Extractor = "SELECT Date, Time FROM appointment_details;"
    cursor.execute(Date_Extractor)
    result_Date_Extractor = cursor.fetchall()

    # Format booked slots into the required format for the model
    Specified_format = [{"Book_date": i, "time_start_End": j} for i, j in result_Date_Extractor]

    # Prepare the prompt
    example_format = """[{"Book_date": "29-09-2023", "time_start_End": "12:15PM-1hr"},{"Book_date": "28-09-2023", "time_start_End": "12:15PM-1hr"}]"""
    output_format = """[ {"Book_date": "date", "time_start_end": "starting time - ending time"}]"""

    prompt = f"""Task Prompt: Appointment Slot Booking**

    You need to develop a function that provides available appointment slots for booking within specified office hours.
    1. Office Timing: 9:00 AM to 6:00 PM.
    2. Lunch Break: No appointments can be booked from 1:00 PM to 2:00 PM.
    3. Weekends: No appointments can be scheduled on Saturdays and Sundays.
    4. Already Booked Slots: {Specified_format}
    5. Output Requirement: Available slots for the next 20 days.
    6. the available slots timing duration should be 1hr example : 9:00AM-10:00AM or 9:45AM-10:45AM

    Output: {output_format}
    """

    # Call the AI model to get available slots
    model_Result = gemini_flash_model(prompt)
    available_slots = json.loads(model_Result)

    # Return available slots and user ID
    return jsonify({"available_slots": available_slots, "user_id": user_id})


@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    print(1)
    user_details = request.json
    date = user_details['date']
    time = user_details['time']
    sql = "SELECT User_ID FROM user_table WHERE Username = %s and age = %s and Phone_Number = %s and Email =%s"
    val = (user_details['name'],user_details['age'],user_details['phone'],user_details['email'],)

    cursor.execute(sql, val)
    result = cursor.fetchone()
    
    print(date,time,result[0])
    cursor.execute("INSERT INTO appointment_details (User_ID, Date, Time) VALUES (%s, %s, %s)", (result[0], date[0], date[1]))
    mydb.commit()
    
    return jsonify({"status": "success", "message": "Appointment successfully booked!"})

    """
    booking_details = request.json
    user_id = booking_details['user_id']
    selected_date = booking_details['selected_date']
    selected_time = booking_details['selected_time']
    print(2)
    # Insert the booking into the appointment_details table
    cursor.execute("INSERT INTO appointment_details (User_ID, Date, Time) VALUES (%s, %s, %s)", (user_id, selected_date, selected_time))
    mydb.commit()
    print(3)"""
   # return jsonify({"status": "success", "message": "Appointment successfully booked!"})

if __name__ == '__main__':
    app.run(debug=True)
