# Importations nécessaires de PyQt5 et autres bibliothèques
from classes.login import Login
import sys
from PyQt5.QtWidgets import QApplication, QStackedWidget
from PyQt5.QtGui import QIcon

# Vérification si le script est exécuté comme programme principal et non importé comme un module
if __name__ == '__main__':
    # Création d'une instance de l'application Qt. sys.argv permet de gérer les arguments en ligne de commande
    app = QApplication(sys.argv)

    # Définition de l'icône de la fenêtre de l'application en utilisant un fichier image
    app.setWindowIcon(QIcon('assets/logo-client.png'))
    
    # Création d'une instance de QStackedWidget, un conteneur pour empiler des widgets 
    widget = QStackedWidget()

    # Création d'une instance de la fenêtre de connexion, en passant le widget empilé en paramètre
    mainwindow = Login(widget) 

    # Ajout de la fenêtre de connexion au widget empilé
    widget.addWidget(mainwindow)

    # Affichage du widget empilé (et donc de la fenêtre de connexion)
    widget.show()

    # Démarrage de la boucle d'événements de l'application. Cette ligne bloque le script jusqu'à ce que l'application soit fermée
    app.exec_()
