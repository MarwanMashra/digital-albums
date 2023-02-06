from server.mongo import Mongo,MongoSave,MongoLoad, MongoUpd
from flask import Flask, Blueprint, render_template, request, jsonify, redirect, session, url_for
import pprint,json,bcrypt


coll_accounts= "Admin_accounts"

url = Blueprint('url',__name__)

@url.route('/')
@url.route('/home_page')
@url.route('/home_page.html')
def home_page():
	if 'identifiant' in session:
		return render_template('home_page.html')
	else:
		return redirect(url_for('url.connexion'))


@url.route('/questionnaire')
@url.route('/questionnaire.html')
def questionnaire():
    return render_template('questionnaire.html')

@url.route('/stats')
@url.route('/stats.html')
def stats():
	if 'identifiant' in session:
		return render_template('stats.html')
	else:
		return redirect(url_for('url.connexion'))
    


@url.route('/connexion',methods=['GET','POST'])
@url.route('/connexion.html',methods=['GET','POST'])
def connexion():
	if request.method == 'POST':
		identifiant = request.form['identifiant']
		password = request.form['password']
		
		#Chercher le compte pour l'identifiant donné
		cmpt = MongoLoad({'identifiant': identifiant})
		compte = list(cmpt.retrieve(coll_accounts,limit=1))

		#Si compte trouvé	
		if compte:
			compte = compte[0]

			#si le mdp dans la base de données n'est pas encore crypté, je la crypte
			if(type(compte['password']) != bytes):
				compte['password']= bcrypt.hashpw(str(compte['password']).encode('utf-8'),bcrypt.gensalt())
				db_update = MongoUpd({'identifiant': compte['identifiant']},{'$set': {'password':compte['password']}}) 
				db_update.singleval_upd(coll_accounts)

			#Vérifier le mdp
			if bcrypt.hashpw(password.encode('utf-8'),compte['password']) == compte['password']:

				#Cookies
				session['identifiant'] = compte['identifiant']
				return redirect(url_for('url.home_page'))
					
		#Pseudo,email ou mot de passe invalide
		error = 'L\'identifiant ou le mot de passe n\'est pas valide'
		return render_template('connexion.html',error=error)
			
	elif 'identifiant' in session:
		return redirect(url_for('url.home_page'))
	
	else:
		return render_template('connexion.html')


@url.route('/inscription.html',methods=['GET','POST'])
@url.route('/inscription',methods=['GET','POST'])
def inscription():	
	if request.method == 'POST':
		identifiant = request.form['identifiant']
		password = request.form['password']
		password_confirmation = request.form['password_confirmation']

		existing_account = list(MongoLoad({'identifiant': identifiant}).retrieve(coll_accounts))

		if existing_account:
			error = 'Cet identifiant est déjà utilisé, veuillez en choisir un autre.'
		elif password != password_confirmation:
			error = 'Les deux mots de passes sont différents.'

		else:
			#Cookies
			session.clear()
			session['identifiant'] = identifiant

			#Cryptage du mot de passe
			hashpass= bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
			
			#Stockage dans mongoDB
			dic = {
					'identifiant': identifiant,
					'password': hashpass
				}
			documents = MongoSave([dic])
			documents.storeindb(coll_accounts)

			#redirection vers la map
			return redirect(url_for('url.home_page'))  

		return render_template('inscription.html',error=error)

	elif 'identifiant' in session:
		return render_template('inscription.html')

	else:
		return redirect(url_for('url.connexion'))



@url.route('/deconnexion')
def deconnexion():
	session.clear()
	return "success"


@url.route('/get_session',methods=['GET'])
def get_session():
	dic={}
	if session:
		dic={ 'identifiant':session['identifiant'] }	
	return dic



