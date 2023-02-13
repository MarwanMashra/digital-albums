#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import join, dirname
import dns, pymongo, sys, pprint, urllib


"""Extrait de mongoDB manual:
'For a compound multikey index, each indexed document can have at most one indexed
field whose value is an array.'
'If you use the unique constraint on a compound index, then MongoDB will enforce
uniqueness on the combination of the index key values.'
"""

with open(join(dirname(__file__), "mongo.ini"), "r") as initfile:
    f = initfile.readlines()

init = {}

for line in f:
    if not (line.strip().startswith("#")):
        index = line.find("=")
        if index != -1:
            init[line[:index].strip()] = line[index + 1 :].strip()

client = pymongo.MongoClient(
    "mongodb+srv://"
    + urllib.parse.quote_plus(init["username"])
    + ":"
    + urllib.parse.quote_plus(init["password"])
    + "@cluster0.x6qcjdn.mongodb.net/"
    + urllib.parse.quote_plus(init["dbname"])
    + "?retryWrites=true&w=majority"
)[init["dbname"]]


class Mongo:
    """Classe de base dont héritent les autres. Permet d'obtenir des informations sur la
    base de données, mais pas d'opérer dessus.
    """

    @classmethod
    def mongocheck(cls, coll_exists):
        """Vérifie l'existence d'une collection."""
        return coll_exists in client.list_collection_names()

    @classmethod
    def indexcheck(cls, coll_tocheck, index):
        """Vérifie l'existence d'un index. Renvoie vrai s'il existe, faux sinon. L'index
        en paramètre doit être une liste de champs à indexer.
        Retour de list_indexes(): itérateur sur des documents au format SON (dictionnaire
        ordonné). Convertir en dico Python avant utilisation.
        """
        coll = client[coll_tocheck]
        for idx in coll.list_indexes():
            idx = idx.to_dict()  # SON -> dictionnaire
            if all(name in index for name in idx["key"].keys()):
                return True
        return False

    @classmethod
    def nonunique_index(cls, coll_toindex, **index):
        """Création d'un index n'imposant pas une contrainte d'unicité.
        Syntaxe pour l'index en paramètre: <nom champ du document>=<'A' ou 'D'>,... Sera
        passé à la fonction comme dictionnaire, puis converti en liste de tuples pour le
        passage à la méthode de pymongo.collections.
        """
        coll = client[coll_toindex]
        if len(index) > 0 and cls.indexcheck(coll_toindex, list(index.keys())):
            return

        index_list = [
            (key, pymongo.ASCENDING) if val == "A" else (key, pymongo.DESCENDING)
            for key, val in index.items()
        ]
        if index_list:
            index_name = "_".join(i[0].split("_")[0] for i in index_list)
            coll.create_index(index_list, name=index_name)

    @classmethod
    def mongocount(cls, coll_tocount, query={}):
        """Compte et renvoit le nombre de documents dans une collection.
        'query' est une requête pour filtrer les documents devant être comptés.
        """
        coll = client[coll_tocount]
        return coll.count_documents(query)


class MongoSave(Mongo):
    """Insertion de documents: création de la collection si elle n'existe pas, et création
    optionnelle d'un index sur les champs passés en paramètre. Syntaxe pour l'index en
    paramètre: <nom champ du document>=<'A' ou 'D'>,... L'index impose une contrainte
    d'unicité sur ces champs.
    De pymongo: 'An important note about collections (and databases) in MongoDB is that
    they are created lazily (...) Collections and databases are created when the first
    document is inserted into them.'
    """

    def __init__(self, dblist):
        self.document = dblist

    def reinit(self, dblist):
        self.document = dblist

    def storeindb(self, coll_tostore, **index):
        if (
            len(self.document) == 0
        ):  # Une liste vide passée à insert_many provoque un bug
            return

        coll = client[coll_tostore]
        if not self.indexcheck(coll_tostore, list(index.keys())):
            index_list = [
                (key, pymongo.ASCENDING) if val == "A" else (key, pymongo.DESCENDING)
                for key, val in index.items()
            ]
            if index_list:
                index_name = "_".join(i[0].split("_")[0] for i in index_list)
                coll.create_index(index_list, name=index_name, unique=True)

        try:
            coll.insert_many(self.document, ordered=False)
        except pymongo.errors.BulkWriteError as error:
            for e in error.details["writeErrors"]:
                if e["code"] == 11000:  # DuplicateKeyError
                    print(
                        "Document "
                        + str(e["op"]["_id"])
                        + " déjà présent dans la collection "
                        + coll.name
                        + " de la base de données."
                    )
                    pprint.pprint(e)
                else:
                    raise
        else:
            pass


class MongoLoad(Mongo):
    """Recherche et extraction d'un document sous forme de liste de document(s).
    Format paramètres:
    La requête:
    {
            <champs>: <valeur>,
            ...
            <champs>: { <opérateur>: <valeur> }
            ...
            <opérateur logique>: { <champ>: <valeur>
                                                       ...
                                                       <champ>: <valeur>
                                                     }
    }
    La projection par inclusion:
    {
            <champ>: 1
            ...
            <champ>: 1
            (optionnel) '_id': 0 (seul exclusion qui marche avec l'inclusion)
    }
    OU par exclusion
    {
            <champ>: 0
            ...
            <champ>: 0
    }
    Si on veut retourner tous les champ laisser le paramètre par défaut (on ne
    veut jamais récupérer l'objet _id, non directement convertible en JSON).
    """

    def __init__(self, query=None, proj={"_id": 0}):
        self.query = query
        self.projection = proj

    def reinit(self, query=None, proj={"_id": 0}):
        self.query = query
        self.projection = proj

    def retrieve(self, coll_tosearch, limit=0):
        coll = client[coll_tosearch]
        if not self.projection and limit == 0:
            return coll.find(self.query)
        elif not self.projection:
            return coll.find(self.query, limit=limit)
        elif limit == 0:
            return coll.find(self.query, self.projection)
        else:
            return coll.find(self.query, self.projection, limit=limit)

    def dltdocument(self, coll_toupd):
        """Efface un ou plusieurs documents correspondants à la requête."""
        coll = client[coll_toupd]
        return coll.delete_many(self.query).deleted_count


class MongoUpd(Mongo):
    """Mises à jour.
    Format paramètres:
    La requête: voir classe précédente.
    La mise à jour, pour un document ou un ensemble de documents:
    {
            <opérateur>:
                                    {
                                            <champ>: <nouvelle_valeur>
                                            ...
                                    }
            ...
    }
    """

    def __init__(self, query, update, list_id=[], list_val=[]):
        self.query = query
        self.update = update
        self.list_id = list_id
        self.list_val = list_val

    def reinit(self, query=None, update=None, list_id=[], list_val=[]):
        if query is not None:
            self.query = query
        if update is not None:
            self.update = update
        self.list_id = list_id
        self.list_val = list_val

    def singleval_upd(self, coll_toupd):
        """Mise à jour groupée: plusieurs documents reçoivent la même mise à jour,
        c'est-à-dire un même champ est mis à jour avec la même valeur pour tous.
        """
        coll = client[coll_toupd]
        coll.update_many(self.query, self.update)

    def multval_upd(self, coll_toupd, multfield):
        """Mise à jour individualisée: pour le même champ, chaque document reçoit
        une valeur propre. Le paramètre multfield désigne ce champ individualisé.
        """
        coll = client[coll_toupd]
        assert (
            self.list_id and self.list_val
        ), "Listes manquantes pour la méthode de mise à jour."
        for ident, value in zip(self.list_id, self.list_val):
            self.query[multfield] = ident
            for operator in self.update.keys():
                for key in self.update[operator].keys():
                    self.update[operator][key] = value
            coll.update_one(self.query, self.update)


class MongoRemove(Mongo):
    def __init__(self, query):
        self.query = query

    def remove(self, coll_toupd):
        coll = client[coll_toupd]
        print(self.query)
        coll.delete_one(self.query)
