from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse
import json

#self defined
import possible_incomming 
import functions 
import dbSearch
# import nlpengine
import shortuuid
#translator
from googletrans import Translator
translator = Translator()


app = Flask(__name__)


#maintaining states
user_state = {} #to keep track of numbers
user_language = {}
sponsor_state = {} #to keep track of the sponsor's data
search_state = {}
#data
sponsor_data = {
    "sponsor_name" : None,
    "sponsor_address" : None,
    "sponsor_number" : None,
    "sponsor_individualname" : None,
    "sponsor_individualprofession":None,
    "sponsor_individualaddress": None,
    "sponsor_individualnumber": None,
    "sponsor_individualwages":None,
    "sponsor_individualreview":None,
    "sponsor_individualpicture": None,
    "uuid":None
}

search_data = {
    "service_type":None,
    "service_address":None
}

#need to use switch case instead of ifelse ideally

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()

    # print(request.values)
    user_number = request.values.get('From')[9:] #will be used to store the user state


    resp = MessagingResponse()
    msg = resp.message()
    responded = False

    print("Beginning: ",user_state)
    #need to create a filter here
    if user_number not in user_state:
        #registering the new user into the state management
        user_state[user_number] = "initial" 
        user_language[user_number] ="en"
        

    #reset
    if(incoming_msg == "reset"):
        user_state[user_number] = "initial"
        user_language[user_number] = "en"
        response_body = functions.initial_state()
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        return str(resp)
        


    #NLP ENGINE
    media_content =  request.values.get("MediaContentType0")
    if(media_content == "audio/ogg"):
        #need to run NLP Engine
        print(request.values.get('MediaUrl0'))
        msg.body("Voice Enabled, But unfortunately it is still in beta form.")
        responded = True
        user_state[user_number] = "initial"
        return str(resp)


    #state 1 - initial
    if(user_state[user_number] == "initial" and incoming_msg not in ["1","2","3","4","5"]):
        response_body = functions.initial_state()
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        responded = True
    
    elif(user_state[user_number] == "initial" and incoming_msg=="1"):
        msg.body("")
        response_body = functions.switchtosearch_state() #initial search message
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        responded = True
        user_state[user_number] = "search"
    
    elif(user_state[user_number] == "initial" and incoming_msg=="2"):
        msg.body("")
        response_body = functions.switchtosponsor_state() #initial sponsor message
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        responded = True
        user_state[user_number] ="sponsor"

    elif(user_state[user_number] == "initial" and incoming_msg=="3"):
        msg.body("")
        response_body = functions.profession_inclusion() #initial sponsor message
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        responded = True
        user_state[user_number] ="profession_acception"

    #LANGUAGE STATE MANAGEMENT
    elif(user_state[user_number] == "initial" and incoming_msg=="4"):
        user_language[user_number] ="hi"
        response_body = functions.initial_state()
        response_body = translator.translate("Language Changed\n"+response_body, dest='hi').text
        msg.body(response_body)
        user_state[user_number] = "initial"
        
        return str(resp)

    elif(user_state[user_number] == "initial" and incoming_msg=="5"):
        user_language[user_number] ="kn"
        response_body = functions.initial_state()
        response_body = translator.translate("Language Changed\n"+response_body, dest='kn').text
        msg.body(response_body)
        user_state[user_number] = "initial"
        return str(resp)

########################################################################################################
#state3 - profession inclusion
    elif(user_state[user_number] == "profession_acception"):
        msg.body("")
        response_body,success_code = functions.profession_acception(incoming_msg) 
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        responded = True
        user_state[user_number] ="initial"
        if(success_code):
            professionData = {
            "user" : user_number,
            "profession_requested": incoming_msg
            }
            #need to post this
            data=json.dumps(professionData)
            requests.post("http://localhost:3000/professionrequests",data=data,headers={"content-type": "application/json"})


########################################################################################################

    #state2 - searching
    elif(user_state[user_number] == "search"):
        msg.body("")
        response_body = functions.search_servicetype(servicetype=incoming_msg)
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        responded = True
        user_state[user_number] = "serviceaddress" #next user state

        #need to temporarily store the search data
        search_state[user_number] = search_data #initialising
        search_state[user_number]["service_type"] = incoming_msg

    elif(user_state[user_number] == "serviceaddress"):
        msg.body("")
        response_body = functions.search_serviceaddress(serviceaddress=incoming_msg)
        
        responded = True

        #need to temporarily store the search data
        search_state[user_number]["service_address"] = incoming_msg

        #need to ping the database and search for the services now
        data_received = dbSearch.individualSearch(search_state[user_number]["service_type"],search_state[user_number]["service_address"])
        user_state[user_number] = "initial" #next user state
        individual_uuids = []
        if(len(data_received)!=0):
            for individual in data_received:
                response_body += "\n" + "Name: " + individual['sponsor_individualname'] + "\nContact Number:" + individual['sponsor_individualnumber'] + "\nWage Requirements:" + individual['sponsor_individualwages'] + "\nSponsor Review:" + individual['sponsor_individualreview']
                response_body += "\n \n"
                individual_uuids.append(individual['uuid'])
            

            previewuuid = shortuuid.ShortUUID().random(length=5)
            #now we need to post the individual uuid list to the backend database also and generate a uuid for that
            previewdata = {
                "uuid" : previewuuid,
                "uuidlist" : individual_uuids
            }
            #need to post this
            data=json.dumps(previewdata)
            requests.post("http://localhost:3000/previewdata",data=data,headers={"content-type": "application/json"})

            #preview link
            link = "\nView more information such as images and more at the attached link http://3a9746c4ea7a.ngrok.io/preview={} \n".format(previewuuid)
            # msg.url=('http://localhost:8080/?preview={}'.format(previewuuid))
            # msg.url('https://cataas.com/cat')

            response_body = translator.translate(response_body, dest=user_language[user_number]).text
            response_body += link
            
            msg.body(response_body)

        else:
            response_body = "No professionals found :( "
            response_body = translator.translate(response_body, dest=user_language[user_number]).text
            msg.body(response_body)


########################################################################################################

    #state3  - sponsor
    elif(user_state[user_number] == "sponsor"):
        msg.body("")
        response_body = functions.sponsor_name(name=incoming_msg)
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
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
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        responded = True
        user_state[user_number] = "sponsor_individualprofession"

        #need to temporarily store the sponsor data
        sponsor_state[user_number]["sponsor_individualname"] = incoming_msg.title()

    
    elif(user_state[user_number] == "sponsor_individualprofession"):
        msg.body("")
        response_body = functions.sponsor_individualprofession(individualprofession=incoming_msg)
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        responded = True
        user_state[user_number] = "sponsor_individualaddress" #next state

        #need to temporarily store the sponsor data
        sponsor_state[user_number]["sponsor_individualprofession"] = incoming_msg
    
    elif(user_state[user_number] == "sponsor_individualaddress"):
        msg.body("")
        response_body = functions.sponsor_individualaddress(individualaddress=incoming_msg)
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        responded = True
        user_state[user_number] = "sponsor_individualnumber" #next state

        #need to temporarily store the sponsor data
        sponsor_state[user_number]["sponsor_individualaddress"] = incoming_msg


    elif(user_state[user_number] == "sponsor_individualnumber"):
        msg.body("")
        response_body = functions.sponsor_individualnumber(individualnumber=incoming_msg)
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        responded = True
        user_state[user_number] = "sponsor_individualwages" #next state

        #need to temporarily store the sponsor data
        sponsor_state[user_number]["sponsor_individualnumber"] = incoming_msg


    elif(user_state[user_number] == "sponsor_individualwages"):
        msg.body("")
        response_body = functions.sponsor_individualwages(individualwages=incoming_msg)
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        responded = True
        user_state[user_number] = "sponsor_individualreview" #next state

        #need to temporarily store the sponsor data
        sponsor_state[user_number]["sponsor_individualwages"] = incoming_msg


    elif(user_state[user_number] == "sponsor_individualreview"):
        msg.body("")
        response_body = functions.sponsor_individualreview(individualreview=incoming_msg)
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        responded = True
        user_state[user_number] = "sponsor_individualpicture" #next state

        #need to temporarily store the sponsor data
        sponsor_state[user_number]["sponsor_individualreview"] = incoming_msg

    elif(user_state[user_number] == "sponsor_individualpicture"):
        msg.body("")
        response_body = functions.sponsor_individualpicture(individualpicture=request.values.get('MediaUrl0'))
        
        responded = True
        user_state[user_number] = "initial"

        #need to temporarily store the sponsor data
        sponsor_state[user_number]["sponsor_individualpicture"] = request.values.get('MediaUrl0')

        #storing the number also at the end
        sponsor_state[user_number]["sponsor_number"] = user_number

        #we now need to post this data to the database with a unique uuid
        sponsor_state[user_number]["uuid"] = shortuuid.ShortUUID().random(length=5)

        #adding this to the response
        response_body += "\n Your unique registration ID is: {}".format(sponsor_state[user_number]["uuid"])
        data=json.dumps(sponsor_state[user_number])
        requests.post("http://localhost:3000/data",data=data,headers={"content-type": "application/json"})

        #finalising the response body
        response_body = translator.translate(response_body, dest=user_language[user_number]).text
        msg.body(response_body)
        

    if not responded:
        response_body = functions.initial_state()
        msg.body("We did not understand you :( \n" + response_body)

    print("Ending: ",user_state)
    return str(resp)


if __name__ == '__main__':
    app.run(debug=True)




