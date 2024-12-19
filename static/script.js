document.getElementById("subscriberForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const formData = {
        nom: document.getElementById("nom").value,
        prenom: document.getElementById("prenom").value,
        adresse: document.getElementById("adresse").value
    };

    try {
        const response = await fetch("http://127.0.0.1:5000/add_subscriber", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            const data = await response.json();
            alert("Abonné ajouté avec succès !");
        } else {
            alert("Erreur lors de l'ajout de l'abonné.");
        }
    } catch (error) {
        console.error("Erreur :", error);
        alert("Une erreur s'est produite.");
    }
});

// Exemple de script pour gérer les actions sur les abonnés
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.btn-danger');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            if (!confirm('Êtes-vous sûr de vouloir supprimer cet abonné ?')) {
                event.preventDefault();
            }
        });
    });
});
