from __future__ import print_function
from datetime import datetime
import pickle
import os
import os.path
import time
from flask import Flask, json,request, render_template
from flask_mail import Mail, Message

from googleapiclient import sample_tools

from app import app
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = ['https://www.googleapis.com/auth/admin.reports.audit.readonly']

from oauth2client.service_account import ServiceAccountCredentials
import googleapiclient.discovery 
from datetime import datetime

CLIENT_SECRETS_FILE = "YOUR CLIENT SECRET"
account_file = CLIENT_SECRETS_FILE


SCOPES = ['https://www.googleapis.com/auth/admin.reports.audit.readonly']

userId = 'your user Id'


def create_delegated_credentials():
    """Crea las credenciales para acceder a cada cuenta"""
    credentials = ServiceAccountCredentials.from_json_keyfile_name(filename=account_file, scopes=SCOPES)
    delegated_credentials = credentials.create_delegated(userId)
    return delegated_credentials



def service_report():
    delegated_credentials= create_delegated_credentials()
    api_name ,api_version ='admin', 'reports_v1'
    report_service =  googleapiclient.discovery.build(api_name, api_version, 
        credentials=delegated_credentials)

    service = report_service.activities()
    return service

def get_activities():
        # fecha actual
    d = datetime.utcnow()
    d = d.isoformat("T") + "Z"
    s = d.split('-')
    year = s[0]
    month = s[1]


    service = service_report()
 
    activity_list = service.list(userKey='all', applicationName='admin', 
        startTime=year+'-'+month+'-01T00:00:00.000Z').execute()
    activities_res = activity_list.get('items', [])
    return activities_res


def main():


    
    activities_api = get_activities()



    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))

    #RECOJO EL JSON DE AUDIT EN UNA VARIABLE 
    
    json_data_url_b = os.path.join(SITE_ROOT, "static", "diccionario.json")
    with open(json_data_url_b, 'r') as f:
        activities_dic = json.load(f)
    

    
    


    dates_raw, fixed_array = [], []



    for activity in activities_api:
        #una actividad es todo lo que ha hecho un usuario (todos los eventos)
        user = activity['actor']
        events = activity['events']

        name = events[0]['name'] #Valores a comparar
        tyype = events[0]['type']
        settValue_param = ''

        newValue_param = ''

        #algunos eventos no tienen parámetros, o los adecuados. Esos no los contamos
        if 'parameters' in events[0]:
            parameters = events[0]['parameters']
            for parameter in parameters:
                if parameter['name'] == 'SETTING_NAME':
                    settValue_param = parameter['value']
                if parameter['name'] == 'NEW_VALUE':
                    newValue_param = parameter['value']
    
        if settValue_param !='' and newValue_param !='':
            #si llegamos aquí, significa que el cambio registrado es comparable
            #Ahora debemos recorrer el diccionario comparando las mismas tres variables
            #En el diccionario tenemos los eventos directamente sin los usuarios
            for activityEventsD in activities_dic:
                
                nameD = activityEventsD['name'] #valores a comparar
                tyypeD = activityEventsD['type']
                settValue_paramD = ''

                newValue_paramD = ''
                
                
                parametersD = activityEventsD['parameters']
                for parameterD in parametersD:
                    if parameterD['name'] == 'SETTING_NAME':
                        settValue_paramD = parameterD['value']
                    if parameterD['name'] == 'NEW_VALUE':
                        newValue_paramD = parameterD['value']

                #Llegados aquí ya tenemos todos los valores a comparar para buscar. Ahora 
                #hay que localizar el valor de la api en el diccionario y ver si el NEW_VALUE
                #es correcto. Si no lo es, entonces lo mostraremos
                if name == nameD and tyype == tyypeD and settValue_param == settValue_paramD:
                    print('HINT')
                    if newValue_param != newValue_paramD:
                        print('ERROR, AL DASH:')
                        print(activity)
                        #ahora cambiamos el formato de la fecha
                        d = activity['id']['time'].split('T')
                        #s = d[1].split('.')
                        #t = d[0]+', '+s[0]
                        t = d[0]
                        activity['id']['time'] = t
                        fixed_array.append(activity)

    if len(fixed_array) is not 0:
        sendMail(fixed_array)
    return fixed_array
    

def sendMail(activities_api):
    app = Flask(__name__)
    app.config.update(
        dict(
            MAIL_SERVER = 'smtp.gmail.com',
            MAIL_PORT = 465,
            MAIL_USE_TLS = False,
            MAIL_USE_SSL = True,
            MAIL_USERNAME = '',
            MAIL_PASSWORD = ''
        )
    )

    mail = Mail(app)
    mail.init_app(app)
    msg = Message(
        "Report",
        sender="",
        recipients=[
            ""
        ]
    )
   

    msg.body = "testing"
    msg.html = render_template("mail.html", activities_api = activities_api)
    mail.send(msg)



if __name__ == '__main__':
    main()