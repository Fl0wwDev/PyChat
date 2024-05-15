# Importations nécessaires de PyQt5 et autres bibliothèques
import sys
from PyQt5.QtWidgets import QApplication
from server import ServerBackend
from server_ui import ServerUI

# Définition de la fonction principale 'main'
def main():
    # Création d'une instance de l'application Qt. sys.argv permet de gérer les arguments en ligne de commande
    app = QApplication(sys.argv)

    # Création de l'instance du backend du serveur, avec l'adresse IP et le port spécifiés
    server_backend = ServerBackend("127.0.0.1", 5566)

    # Démarrage du serveur backend
    server_backend.start()

    # Création de l'interface utilisateur du serveur et passage du backend en tant que paramètre
    ex = ServerUI(server_backend)

    # Affichage de l'interface utilisateur
    ex.show()

    # Démarrage de la boucle d'événements de l'application et sortie propre lorsque l'application est fermée
    sys.exit(app.exec_())

# Vérification si le script est exécuté comme programme principal et non importé comme module
if __name__ == '__main__':
    # Appel de la fonction main
    main()
