from flask import Flask, render_template, request, redirect, url_for

from datetime import datetime

from flask_pymongo import PyMongo

from bson.objectid import ObjectId  # Necessary for handling ObjectId in MongoDB

from pymongo import MongoClient  # For MongoDB connection



app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/mediatheque_db"

mongo = PyMongo(app)



# Additional connection for PyMongo

client = MongoClient("mongodb://localhost:27017/")

db = client['mediatheque_db']  # Database name

abonnees_collection = db['abonnees']  # Collection name

document_collection = db['documents']  # Collection for documents

emprunts_collection = db['emprunts']







# Route pour afficher l'interface principale

@app.route('/')

def index():

    return render_template('tableau_bord_emprunt.html')



# API pour récupérer les emprunts en JSON

@app.route('/api/emprunts')

def get_emprunts():

    emprunts = list(collection.find({}, {"_id": 0}))  # Récupérer tout sauf l'ID MongoDB



    return jsonify(emprunts)



@app.route('/ajouter-emprunt', methods=['GET', 'POST'])
def ajouter_emprunt():
    if request.method == 'POST':
        # Récupérer les données envoyées par le formulaire
        abonne_id = request.form.get('abonne_id')
        document_id = request.form.get('document_id')
        date_emprunt = request.form.get('date_emprunt')
        date_retour_prevue = request.form.get('date_retour_prevue')
        statut = request.form.get('statut')

        # Créer un nouvel emprunt
        emprunt = {
            'abonne_id': ObjectId(abonne_id),
            'document_id': ObjectId(document_id),
            'date_emprunt': datetime.fromisoformat(date_emprunt),
            'date_retour_prevue': datetime.fromisoformat(date_retour_prevue),
            'statut': statut
        }

        # Insérer l'emprunt dans la base de données
        emprunts_collection.insert_one(emprunt)

        # Rediriger vers la page de tableau de bord des emprunts
        return redirect(url_for('tableau_bord_emprunt'))

    # Récupérer les abonnés et documents pour remplir les listes déroulantes
    abonnes = abonnees_collection.find()
    documents = document_collection.find()

    return render_template('ajouter_emprunt.html', abonnes=abonnes, documents=documents)



@app.route('/dashboard')

def dashboard():

    emprunts = mongo.db.emprunts.find()

    abonnes = mongo.db.abonnes.find()  # Exemple pour les types d'abonnés



    # Compter les statuts des emprunts

    en_cours = 0

    emprunte = 0

    retourne = 0

    type_abonne_counts = {}



    for emprunt in emprunts:

        statut = emprunt.get('statut', '')

        if statut == 'En cours':

            en_cours += 1

        elif statut == 'Emprunte':

            emprunte += 1

        elif statut == 'Retourne':

            retourne += 1



    # Compter les types d'abonnés

    for abonne in abonnes:

        type_abonne = abonne.get('type', 'Autre')

        type_abonne_counts[type_abonne] = type_abonne_counts.get(type_abonne, 0) + 1



    return render_template(

        'dashboard.html', 

        en_cours=en_cours, 

        emprunte=emprunte, 

        retourne=retourne, 

        type_abonne_counts=type_abonne_counts

    )

@app.route('/abonnees')

def abonnees():

    abonnees = list(abonnees_collection.find())

    # Ajouter un peu de logique pour extraire les titres des livres et les autres données de chaque emprunt

    for abonne in abonnees:

        for emprunt in abonne.get('emprunts_en_cours', []):

            livre = document_collection.find_one({"_id": emprunt["livre_id"]})  # Trouver le livre par son ID

            emprunt["livre_titre"] = livre["titre"] if livre else "Inconnu"  # Ajouter le titre du livre

        for historique in abonne.get('historique_emprunts', []):

            livre = document_collection.find_one({"_id": historique["livre_id"]})



            historique["livre_titre"] = livre["titre"] if livre else "Inconnu"  # Ajouter le titre du livre

         

    return render_template('abonnees.html', abonnees=abonnees)
                        


# Route to add a subscriber

@app.route('/abonnees/create', methods=['POST'])

def add_abonne():

    data = request.form

    abonnees_collection.insert_one({

        "nom": data["nom"],

        "prenom": data["prenom"],

        "adresse": data["adresse"],

        "date_inscription": data["date_inscription"],

        "liste_d_emprunts_en_cours": request.form.getlist("liste_d_emprunts_en_cours"),

        "historique_d_emprunts": request.form.getlist("historique_d_emprunts")

    })

    return redirect(url_for('abonnees'))



# Route to delete a subscriber

@app.route('/abonnees/delete/<id>')

def delete_abonne(id):

    abonnees_collection.delete_one({"_id": ObjectId(id)})

    return redirect(url_for('abonnees'))



# Route to edit a subscriber

@app.route("/abonnees/edit/<id>", methods=["GET", "POST"])
def edit_abonne(id):
    if request.method == 'GET':
        # Récupérer l'abonné depuis la base de données
        abonne = abonnees_collection.find_one({"_id": ObjectId(id)})

        # Récupérer les emprunts en cours pour cet abonné
        emprunts_en_cours = db.emprunts.find({"abonne_id": abonne["_id"], "statut": "En cours"})
        
        # Pour chaque emprunt en cours, récupérer le nom du document et la date
        documents_en_cours = []
        for emprunt in emprunts_en_cours:
            document = db.documents.find_one({"_id": emprunt["document_id"]})
            documents_en_cours.append(f"{document['ObjectId']} - {emprunt['date_emprunt']}")

        # Récupérer l'historique des emprunts
        historique_emprunts = db.emprunts.find({"abonne_id": abonne["_id"], "statut": "Terminé"})
        historique_d_emprunts = []
        for emprunt in historique_emprunts:
            document = db.documents.find_one({"_id": emprunt["document_id"]})
            historique_d_emprunts.append(f"{document['ObjectId']} - {emprunt['date_emprunt']}")

        # Passer les données à la vue pour le formulaire
        return render_template('edit_abonne.html', abonne=abonne, 
                               documents_en_cours=documents_en_cours, historique_d_emprunts=historique_d_emprunts)

    else:
        # Récupérer les données du formulaire
        data = request.form

        # Mettre à jour les informations de l'abonné dans la base de données
        abonnees_collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "nom": data["nom"],
                "prenom": data["prenom"],
                "adresse": data["adresse"],
                "date_inscription": data["date_inscription"],
                "liste_d_emprunts_en_cours": data.getlist("liste_d_emprunts_en_cours"),  # Liste des emprunts en cours
                "historique_d_emprunts": data.getlist("historique_d_emprunts")  # Liste de l'historique des emprunts
            }}
        )

        # Rediriger vers la page des abonnés après la mise à jour
        return redirect(url_for('abonnees'))

        
# Route for the Library Catalog pag



@app.route('/catalogue')

def catalogue():

    # Retrieve all documents from the collection

    documents = list(document_collection.find())

    

    # Debugging: Print documents to check if data is being fetched

    print(documents)



    # Pass the documents to the template

    return render_template('catalogue.html', documents=documents)



@app.route('/catalogue/add', methods=['GET', 'POST'])

def add_document():

    if request.method == 'POST':

        # Getting form data

        titre = request.form['titre']

        type_ = request.form['type']

        auteur = request.form['auteur']

        date_publication = request.form['date_publication']

        disponibilite = request.form['disponibilite']



        # Insert the new document into the MongoDB collection

        document_collection.insert_one({

            'titre': titre,

            'type': type_,

            'auteur': auteur,

            'date_publication': date_publication,

            'disponibilite': disponibilite

        })

        return redirect(url_for('catalogue'))



    return render_template('add_document.html')



@app.route('/catalogue/edit/<document_id>', methods=['GET', 'POST'])

def edit_document(document_id):

    document = document_collection.find_one({'_id': ObjectId(document_id)})



    if request.method == 'POST':

        # Getting updated form data

        titre = request.form['titre']

        type_ = request.form['type']

        auteur = request.form['auteur']

        date_publication = request.form['date_publication']

        disponibilite = request.form['disponibilite']



        # Update the document in the collection

        document_collection.update_one(

            {'_id': ObjectId(document_id)},

            {'$set': {

                'titre': titre,

                'type': type_,

                'auteur': auteur,

                'date_publication': date_publication,

                'disponibilite': disponibilite

            }}

        )

        return redirect(url_for('catalogue'))



    return render_template('edit_document.html', document=document)



@app.route('/catalogue/delete/<document_id>')

def delete_document(document_id):

    # Delete the document from the collection


    document_collection.delete_one({'_id': ObjectId(document_id)})

    return redirect(url_for('catalogue'))


@app.route('/tableau-bord-emprunt')
def tableau_bord_emprunt():
    # Récupérer tous les emprunts de la base de données
    emprunts = emprunts_collection.find()

    # Pour chaque emprunt, récupérer les informations de l'abonné et du document
    emprunts_list = []

    for emprunt in emprunts:
        # Récupérer les informations de l'abonné
        abonne = abonnees_collection.find_one({'_id': ObjectId(emprunt['abonne_id'])})
        if abonne:
            emprunt['abonne_nom'] = abonne['nom']
        else:
            emprunt['abonne_nom'] = "Abonné introuvable"

        # Récupérer les informations du document
        # Récupérer les informations du document
        document = document_collection.find_one({'_id': ObjectId(emprunt['document_id'])})

        if document:
            emprunt['document_titre'] = document['titre']
        else:
            emprunt['document_titre'] = "Document introuvable"

        # Ajouter l'emprunt à la liste
        emprunts_list.append(emprunt)

    return render_template('tableau_bord_emprunt.html', emprunts=emprunts_list)

  


   

    
    


 
     
# Route pour modifier un emprunt
@app.route('/emprunts/modifier/<emprunt_id>', methods=['GET', 'POST'])
def modifier_emprunt(emprunt_id):
    emprunt = emprunts_collection.find_one({'_id': ObjectId(emprunt_id)})
    if not emprunt:
        return "Emprunt introuvable", 404

    if request.method == 'POST':
        # Mettre à jour les données de l'emprunt
        emprunts_collection.update_one(
            {'_id': ObjectId(emprunt_id)},
            {'$set': {
                'abonne_id': request.form['abonne_id'],
                'document_id': request.form['document_id'],
                'date_emprunt': request.form['date_emprunt'],
                'date_retour_prevue': request.form['date_retour_prevue'],
                'statut': request.form['statut']
            }}
        )
        return redirect(url_for('tableau_bord_emprunt'))

    abonnes = abonnees_collection.find()
    documents = document_collection.find()

    return render_template('edit_emprunt.html', emprunt=emprunt, abonnes=abonnes, documents=documents)

# Route pour supprimer un emprunt
@app.route('/emprunts/supprimer/<emprunt_id>')
def supprimer_emprunt(emprunt_id):
    emprunts_collection.delete_one({'_id': ObjectId(emprunt_id)})
    return redirect(url_for('tableau_bord_emprunt'))
 


if __name__ == '__main__':

    app.run(debug=True)
