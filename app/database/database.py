from server.mongo import Mongo,MongoSave,MongoLoad, MongoUpd, MongoRemove
from flask import Flask, Blueprint, render_template, request, jsonify, redirect, session, url_for
import pprint,json


coll_questionnaires= "Questionnaires"

mdb = Blueprint('mdb',__name__)

@mdb.route('/getQuestionnaireById',methods=['GET'])
def getQuestionnaireById():
    id = int(request.args.get('id'))
    currentTime = int(request.args.get('currentTime'))
    time_out=0
    while True:
        db_load= MongoLoad({'id':id})
        questionnaire= list(db_load.retrieve(coll_questionnaires,limit=1))
        time_out+=1
        if questionnaire :  

            db_update = MongoUpd({'id': id},{'$set': {'last_open':currentTime}}) 
            db_update.singleval_upd(coll_questionnaires)

            db_load= MongoLoad({'id':id})
            questionnaire= list(db_load.retrieve(coll_questionnaires,limit=1))[0]
            break

        elif time_out> 1000:
            return None
    
    return questionnaire

@mdb.route('/getQuestionnaireRecent',methods=['GET'])
def getQuestionnaireRecent():
    limit = int(request.args.get('limit'))
    db_load= MongoLoad({})
    questionnaire= list(db_load.retrieve(coll_questionnaires,limit=1000000))
    list_result=[]
    for x in range(0,limit):
        lastQ= None
        max= 0
        for q in questionnaire:
            if q not in list_result and q['last_open']>max:
                lastQ= q
                max= q['last_open']
        if lastQ != None:
            list_result.append(lastQ)

    return {'data':list_result}

@mdb.route('/getQuestionnaireByPeriod',methods=['GET'])
def getQuestionnaireByPeriod():
    period = int(request.args.get('period'))
    db_load= MongoLoad({})
    questionnaire= list(db_load.retrieve(coll_questionnaires,limit=100))
    list_result=[]
    for q in questionnaire:
        if q['id']>= period:
            list_result.append(q)

    return {'data':list_result}
    

@mdb.route('/getQuestionnaireByDate',methods=['GET'])
def getQuestionnaireByDate():
    startDate = int(request.args.get('startDate'))
    endDate = int(request.args.get('endDate'))
    db_load= MongoLoad({})
    questionnaire= list(db_load.retrieve(coll_questionnaires,limit=100))
    list_result=[]
    for q in questionnaire:
        if q['id']>= startDate and q['id']<= endDate:
            list_result.append(q)

    return {'data':list_result}

@mdb.route('/getAllQuestionnaire',methods=['GET'])
def getAllQuestionnaire():
    db_load= MongoLoad({})
    questionnaire= list(db_load.retrieve(coll_questionnaires,limit=100))

    return {'data':questionnaire}

@mdb.route('/uploadQuestionnaire',methods=['POST'])
def uploadQuestionnaire():
    data = json.loads(request.data.decode('utf-8'))
    questionnaire = data['questionnaire']
    questionnaire['last_open']= questionnaire['id']
    db_save = MongoSave([questionnaire]) 
    db_save.storeindb(coll_questionnaires)

    return "succes"

@mdb.route('/getResults',methods=['GET'])
def getResults():
    id = int(request.args.get('id'))
    db_load= MongoLoad({'id':id},{'results':1})
    result= list(db_load.retrieve(coll_questionnaires,limit=1))[0]['results']
    return result

"""
let dico_result= this.questionnaire.results[answer.question.text][answer.text];
dico_result['total']++;
dico_result[this.color.text]++;"""

@mdb.route('/sendResults',methods=['POST'])
def sendResults():
    data = json.loads(request.data.decode('utf-8'))
    list_question_answer = data['list_question_answer']
    color= data['color']
    id= data['id']
    dico={}
    for question_answer in list_question_answer:
        field= 'results.'+question_answer[0]+'.'+question_answer[1]+'.'+color
        dico[field]=1
        field= 'results.'+question_answer[0]+'.'+question_answer[1]+'.total'
        dico[field]=1

    db_update = MongoUpd({'id': id},{'$inc': dico})
    db_update.singleval_upd(coll_questionnaires)

    return "succes"

@mdb.route('/removeQuestionnaire',methods=['POST'])
def removeQuestionnaire():
    data = json.loads(request.data.decode('utf-8'))
    id = int(data['id'])
    db_remove= MongoRemove({'id':id})
    db_remove.remove(coll_questionnaires)
    return "succes"