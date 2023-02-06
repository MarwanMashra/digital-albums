
"""
La script mongo.py possède trois classes: Mongo, MongoSave et MongoLoad

Mongo possède un ensemble de méthode permettant de faire qq manipulations comme 
vérifier l'existence d'une collection ou compter le nombre d'éléments  

###########################################

MongoSave est la classe qui gère le stockage dans la base de données, il possède la méthode storeindb permettant de
stoker les données dans la base. Pour l'utiliser il faut :

1- instancier la classe avec la liste de dictionnaires que l'on veut stocker
db_save = MongoSave([dic1,dic2,dic3...etc]) 

2- appeler la méthode storeindb en lui passant la collection da laquelle on souhaite stocker ces données
db_save.storeindb('Results')

###########################################

MongoLoad est la classe qui gère le récuperation des données depuis la base, il possède la méthode retrieve permettant de 
récupérer une liste de dictionnaires depuis la base de données. Pour l'utiliser il faut:

1- instancier la classe avec les valeurs qu'on cherche dans les données, par exemple pour chercher les utilisateurs qui ont 21 ans
db_load= MongoLoad({'âge':21})  

2- appeler la méthode retrieve en lui passant la collection dans laquelle on souhaite chercher ces données 
users= db_load.retrieve('Results',limit=5)
donc users est une liste contenant les utilisateurs ayant 21 ans (uniquement le premier 5 utilisateurs s'il y en a plus que 5)

pour les afficher on peut faire
for user in users:
    print(user['prénom']+' '+user['nom']+' a 21 ans')


"""
