# Importations nécessaires de PyQt5 et autres bibliothèques
from PyQt5.QtWidgets import QMainWindow, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QWidget, QTabWidget, QMessageBox
from PyQt5.QtCore import pyqtSlot, QEvent, Qt
from PyQt5.QtGui import QIcon
from datetime import datetime

class ServerUI(QMainWindow):
    """
    Interface utilisateur pour le serveur de chat.

    Attributes:
        server (ServerBackend): Instance du backend du serveur pour la communication.
        textAreas (dict): Dictionnaire stockant les zones de texte par canal.
        inputFields (dict): Dictionnaire stockant les champs de saisie par canal.
    """
    def __init__(self, server_backend=None):
        """
        Initialise l'interface utilisateur du serveur.

        Args:
            server_backend (ServerBackend, optional): Instance du backend du serveur.
        """
        super().__init__()
        # Initialisation de la référence au backend du serveur et des dictionnaires pour les zones de texte et les champs de saisie
        self.server = server_backend
        self.textAreas = {}
        self.inputFields = {}
        self.initUI()
        if self.server:
            self.setServer(self.server)
            
    def format_timestamp(self, timestamp):
        """
        Formate un timestamp pour l'affichage.

        Args:
            timestamp (datetime or str): Le timestamp à formater.

        Returns:
            str: Le timestamp formaté.
        """
        # Obtenir la date et l'heure actuelles
        now = datetime.now()

        # Vérifier si timestamp est déjà un objet datetime
        if not isinstance(timestamp, datetime):
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')

        # Calculer la différence entre maintenant et le timestamp
        delta = now - timestamp

        # Si le message a été envoyé il y a moins de 24 heures, afficher uniquement l'heure (sans les secondes)
        if delta.days < 1:
            return timestamp.strftime('%H:%M')
        else:
            # Sinon, afficher la date complète (sans les secondes)
            return timestamp.strftime('%d/%m/%Y %H:%M')

    def initUI(self):
        """
        Initialise l'interface utilisateur.
        """
        # Configuration initiale de l'interface utilisateur de la fenêtre du serveur.
        self.setWindowTitle('Server')
        self.setGeometry(300, 300, 600, 400)
        self.setWindowIcon(QIcon('/assets/logo-server.png'))

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout(centralWidget)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Création des onglets pour différents canaux de chat
        self.createChannelTab("Général")
        self.createChannelTab("Blabla")
        self.createChannelTab("Comptabilité")
        self.createChannelTab("Informatique")
        self.createChannelTab("Marketing")

    def createChannelTab(self, channel_name):
        """
        Crée un onglet pour un canal spécifique.

        Args:
            channel_name (str): Le nom du canal.
        """
        tab = QWidget()
        tabLayout = QVBoxLayout()

        # Zone de texte pour afficher les messages
        textArea = QTextEdit()
        textArea.setReadOnly(True)
        tabLayout.addWidget(textArea)
        self.textAreas[channel_name] = textArea

        # Champ de saisie pour taper les messages
        inputField = QLineEdit()
        inputField.setPlaceholderText("Tapez votre message ici...")
        tabLayout.addWidget(inputField)
        self.inputFields[channel_name] = inputField

        # Installer l'eventFilter sur le QLineEdit
        inputField.installEventFilter(self)

        # Bouton pour envoyer les messages
        sendButton = QPushButton("Envoyer")
        # S'assure que la connexion au signal est correctement établie
        sendButton.clicked.connect(lambda: self.sendMessage(channel_name, inputField.text(), textArea))
        tabLayout.addWidget(sendButton)

        tab.setLayout(tabLayout)
        self.tabs.addTab(tab, channel_name)
        

    def eventFilter(self, obj, event):
        """
        Filtre les événements pour gérer les saisies clavier.

        Args:
            obj (QObject): L'objet sur lequel l'événement est déclenché.
            event (QEvent): L'événement à filtrer.

        Returns:
            bool: True si l'événement est traité, False sinon.
        """
        # Filtre les événements pour gérer les appuis sur 'Entrée' dans les champs de saisie.
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Return:
            if isinstance(obj, QLineEdit):
                channel_name = self.tabs.tabText(self.tabs.currentIndex())
                self.sendMessage(channel_name, obj.text(), self.textAreas[channel_name])
                return True
        return super(ServerUI, self).eventFilter(obj, event)


    def load_message_history(self):
        """
        Charge l'historique des messages du serveur et les affiche.
        """
        # Charge l'historique des messages du serveur et les affiche dans l'interface utilisateur.
        history = self.server.get_message_history()
        if not history:
            print("Aucun historique de messages à charger.")
            return
        for username, content, timestamp in history:
            try:
                channel, message = content.split(':', 1)
                readable_timestamp = self.format_timestamp(timestamp)
                formatted_message = f"{readable_timestamp} - {username}: {message}"
                if channel in self.textAreas:
                    self.textAreas[channel].append(formatted_message)
                else:
                    print(f"Canal inconnu: {channel}")
            except ValueError:
                print(f"Erreur de format du message: {content}")

    def sendMessage(self, channel_name, message, textArea):
        """
        Envoie un message au canal spécifié et met à jour l'interface utilisateur.

        Args:
            channel_name (str): Le nom du canal.
            message (str): Le message à envoyer.
            textArea (QTextEdit): La zone de texte où afficher le message.
        """
        if message:
            # Vérifier si le message est une commande admin
            if message.startswith("/"):  # Utilisez un préfixe, par exemple '/'
                self.handleAdminCommand(message[1:])
            else:
                # Traitement pour les messages normaux
                if self.server:
                    self.server.send_message_to_channel(channel_name, message)
                    textArea.append(f"Vous ({channel_name}): {message}")
                else:
                    textArea.append("Erreur: le serveur n'est pas connecté.")

            # Effacer le champ de saisie après l'envoi du message
            self.inputFields[channel_name].clear()

    
    def handleAdminCommand(self, command):
        """
        Traite une commande administrateur envoyée par l'utilisateur.

        Args:
            command (str): La commande à traiter.
        """
         # Traite les commandes administratives comme 'ban', 'kick', etc.
        parts = command.split(' ', 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else None

        if cmd in ['ban', 'deban', 'kick']:
            if args:
                self.server.handle_command(cmd, args)
            else:
                QMessageBox.warning(self, "Erreur", f"La commande '{cmd}' nécessite un argument.")
        elif cmd == 'kill':
            # La commande 'kill' n'a pas besoin d'arguments
            self.server.handle_command(cmd, None)
        else:
            QMessageBox.warning(self, "Erreur", "Commande inconnue.")
            
    @pyqtSlot(str)
    def logMessage(self, message):
        """
        Log et affiche un message reçu du serveur.

        Args:
            message (str): Le message reçu.
        """

        # Traite et affiche les messages reçus du serveur.
        print("Message reçu:", message)  # Pour débogage

        now = datetime.now()
        formatted_time = now.strftime('%H:%M')  # Formatte l'heure actuelle

        parts = message.split(':', 2)
        if len(parts) == 3:
            username, channel, msg = parts
            formatted_message = f"{formatted_time} - {username}: {msg}"
            if channel.strip() in self.textAreas:
                self.textAreas[channel.strip()].append(formatted_message)
            else:
                print(f"Canal inconnu: {channel}")
        else:
            print("Format de message incorrect:", message)

    def setServer(self, server):
        """
        Configure le serveur pour l'interface utilisateur.

        Args:
            server (ServerBackend): L'instance du serveur à configurer.
        """
        # Configure le serveur et connecte les signaux aux slots.
        self.server = server
        self.server.new_message.connect(self.logMessage) 
        self.server.new_connection.connect(self.showNewConnectionPopup)
        
        # Charger l'historique des messages
        self.load_message_history()
        
    @pyqtSlot(str)
    def showNewConnectionPopup(self, message):
        """
        Affiche une fenêtre popup pour les nouvelles connexions.

        Args:
            message (str): Le message à afficher dans la popup.
        """

        # Affiche une fenêtre popup pour les nouvelles connexions.
        QMessageBox.information(self, "Nouvelle Connexion", message)
