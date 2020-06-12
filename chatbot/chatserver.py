from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse
import json
import possible_incomming
import functions

app = Flask(__name__)



#maintaining states
user_state = {} #to keep track of numbers
sponsor_state = {} #to keep track of the sponsor's data

#data
sponsor_data = {
    "sponsor_name" : None,
    "sponsor_address" : None,
    "sponsor_number" : None,
    "sponsor_individualname" : None,
    "sponsor_individualnumber": None,
    "sponsor_individualpicture": None
}



@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()

    print(request.values)
    user_number = request.values.get('From')[9:] #will be used to store the user state


    resp = MessagingResponse()
    msg = resp.message()
    responded = False

    print("Beginning: ",user_state)
    #need to create a filter here
    if user_number not in user_state:
        #registering the new user into the state management
        user_state[user_number] = "initial" 

    #reset
    if(incoming_msg == "reset"):
        user_state[user_number] = "initial"
        response_body = functions.initial_state()
        msg.body(response_body)
        return str(resp)



    #state 1 - initial
    if(user_state[user_number] == "initial" and incoming_msg not in ["1","2"]):
        response_body = functions.initial_state()
        msg.body(response_body)
        responded = True
    
    elif(user_state[user_number] == "initial" and incoming_msg=="1"):
        msg.body("")
        response_body = functions.switchtosearch_state()
        msg.body(response_body)
        responded = True
        user_state[user_number] = "search"
    
    elif(user_state[user_number] == "initial" and incoming_msg=="2"):
        msg.body("")
        response_body = functions.switchtosponsor_state()
        msg.body(response_body)
        responded = True
        user_state[user_number] ="sponsor"


    #state2 - searching


    #state3  - sponsor
    elif(user_state[user_number] == "sponsor"):
        msg.body("")
        response_body = functions.sponsor_name(name=incoming_msg)
        msg.body(response_body)
        responded = True
        user_state[user_number] = "sponsor_address"

        #need to temporarily store the sponsor data
        sponsor_state[user_number] = sponsor_data
        sponsor_state[user_number]["sponsor_name"] = incoming_msg.title()
    
    elif(user_state[user_number] == "sponsor_address"):
        msg.body("")
        response_body = functions.sponsor_address(address=incoming_msg)
        msg.body(response_body)
        responded = True
        user_state[user_number] = "sponsor_individualname"

        #need to temporarily store the sponsor data
        sponsor_state[user_number]["sponsor_address"] = incoming_msg.title()
    
    elif(user_state[user_number] == "sponsor_individualname"):
        msg.body("")
        response_body = functions.sponsor_individualname(individualname=incoming_msg)
        msg.body(response_body)
        responded = True
        user_state[user_number] = "sponsor_individualnumber"

        #need to temporarily store the sponsor data
        sponsor_state[user_number]["sponsor_individualname"] = incoming_msg.title()
    
    elif(user_state[user_number] == "sponsor_individualnumber"):
        msg.body("")
        response_body = functions.sponsor_individualnumber(individualnumber=incoming_msg)
        msg.body(response_body)
        responded = True
        user_state[user_number] = "sponsor_individualpicture"

        #need to temporarily store the sponsor data
        sponsor_state[user_number]["sponsor_individualnumber"] = incoming_msg

    elif(user_state[user_number] == "sponsor_individualpicture"):
        msg.body("")
        response_body = functions.sponsor_individualpicture(individualpicture=request.values.get('MediaUrl0'))
        msg.body(response_body)
        responded = True
        user_state[user_number] = "initial"

        #need to temporarily store the sponsor data
        sponsor_state[user_number]["sponsor_individualpicture"] = request.values.get('MediaUrl0')
        #storing the number also at the end
        sponsor_state[user_number]["sponsor_number"] = user_number
        #we now need to post this data to the database
        data=json.dumps(sponsor_state[user_number])
        requests.post("http://localhost:3000/data",data=data,headers={"content-type": "application/json"})
        

    if not responded:
        response_body = functions.initial_state()
        msg.body("We did not understand you :( \n" + response_body)

    print("Ending: ",user_state)
    return str(resp)


if __name__ == '__main__':
    app.run(debug=True)




