import socket
import threading
import datetime
from PyQt5.QtWidgets import QMainWindow, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QWidget, QTabWidget, QMessageBox
from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal, QEvent, Qt

class Client(QObject):
    """
    Gère la communication réseau côté client pour une application de chat.

    Attributes:
        message_received (pyqtSignal): Signal émis lors de la réception d'un message.
        connection_failed (pyqtSignal): Signal émis lors d'une erreur de connexion.
        connection_success (pyqtSignal): Signal émis lors d'une connexion réussie.
        formatted_message_received (pyqtSignal): Signal émis pour les messages formatés reçus.
        connection_closed (pyqtSignal): Signal émis lors de la fermeture de la connexion.
    """
    # Définition des signaux pour la communication avec l'interface utilisateur
    message_received = pyqtSignal(str)
    connection_failed = pyqtSignal(str)
    connection_success = pyqtSignal()
    formatted_message_received = pyqtSignal(str)
    connection_closed = pyqtSignal()

    def __init__(self, username, host='127.0.0.1', port=5566):
        """
        Initialise le client avec un nom d'utilisateur, une adresse hôte et un port.

        Args:
            username (str): Nom d'utilisateur pour la session de chat.
            host (str): Adresse IP du serveur. Par défaut à '127.0.0.1'.
            port (int): Port du serveur. Par défaut à 5566.
        """
        # Initialisation du client avec nom d'utilisateur, adresse hôte et port
        super().__init__()
        self.username = username
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self):
        """
        Tente de se connecter au serveur et lance le processus de réception des messages.
        """
        # Tente de se connecter au serveur et lance un thread pour recevoir des messages
        try:
            self.client_socket.connect((self.host, self.port))
            # Envoyer le nom d'utilisateur au serveur après la connexion
            self.send_messages(f"Username:{self.username}")
            # Demander l'historique des messages
            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.connection_success.emit()
        except Exception as e:
            self.connection_failed.emit(f"Erreur lors de la connexion au serveur: {e}")
            
    def receive_messages(self):
        """
        Reçoit les messages du serveur dans une boucle continue.
        """
        # Boucle pour recevoir des messages du serveur et les traiter
        message_buffer = ""  # Tampon pour stocker les données partielles

        while True:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')

                if not data:
                    self.connection_closed.emit()  # Émettre le signal si aucune donnée n'est reçue (connexion fermée)
                    break

                # Concaténer les données reçues avec le tampon
                message_buffer += data

                # Traiter les messages d'historique spécialement
                while "history" in message_buffer:
                    line_end = message_buffer.find("\n") + 1
                    if line_end == 0:  # Pas de retour à la ligne trouvé
                        line_end = len(message_buffer)

                    line = message_buffer[:line_end].strip()
                    message_buffer = message_buffer[line_end:]

                    if line.startswith("history"):
                        self.formatted_message_received.emit(line)

                # Si le tampon ne commence pas par 'history', émettre le message complet
                if message_buffer and not message_buffer.startswith("history"):
                    self.message_received.emit(message_buffer)
                    message_buffer = ""  # Vider le tampon

            except Exception as e:
                print("Erreur lors de la réception du message:", e)
                break
        
        
    def send_messages(self, message):
        """
        Envoie un message au serveur.

        Args:
            message (str): Le message à envoyer.
        """
         # Envoie un message au serveur
        try:
            self.client_socket.send(message.encode('utf-8'))
        except Exception as e:
            print("Erreur lors de l'envoi du message:", e)


    def close_connection(self):
        """
        Ferme la connexion avec le serveur.
        """
        # Ferme la connexion avec le serveur
        self.client_socket.close()

class ClientUI(QMainWindow):
    """
    Interface utilisateur pour le client de chat.

    Attributes:
        client_logic (Client): Logique client pour la communication avec le serveur.
        textAreas (dict): Dictionnaire des zones de texte pour chaque canal.
    """
    def __init__(self, username):
        """
        Initialise l'interface utilisateur avec la logique client spécifiée.

        Args:
            username (str): Nom d'utilisateur pour la session de chat.
        """
         # Initialisation de l'interface utilisateur avec la logique client
        super().__init__()
        self.client_logic = Client(username)
        self.textAreas = {}  # Dictionnaire pour les zones de texte
        self.initUI()
        self.connect_client_signals()
        self.installEventFilter(self)
        self.client_logic.connect_to_server()
        

    def initUI(self):
        """
        Initialise l'interface utilisateur avec des onglets pour différents canaux de chat.
        """
        # Crée l'interface utilisateur avec des onglets pour différents canaux de chat
        self.setWindowTitle('Client Chat Interface')
        self.setGeometry(300, 300, 600, 400)

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout(centralWidget)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.createChannelTab("Général")
        self.createChannelTab("Blabla")
        self.createChannelTab("Comptabilité")
        self.createChannelTab("Informatique")
        self.createChannelTab("Marketing")
        
    def createChannelTab(self, channel_name):
        """
        Crée un onglet pour un canal de chat spécifié.

        Args:
            channel_name (str): Nom du canal de chat.
        """
        # Crée un onglet pour un canal de chat spécifique
        tab = QWidget()
        tabLayout = QVBoxLayout()

        textArea = QTextEdit()
        textArea.setReadOnly(True)
        tabLayout.addWidget(textArea)
        self.textAreas[channel_name] = textArea

        inputField = QLineEdit()
        inputField.setPlaceholderText("Tapez votre message ici...")
        tabLayout.addWidget(inputField)

        sendButton = QPushButton("Envoyer")
        sendButton.clicked.connect(lambda: self.sendMessage(channel_name, inputField.text(), textArea, inputField))
        tabLayout.addWidget(sendButton)

        # Installer l'eventFilter directement sur le QLineEdit
        inputField.installEventFilter(self)

        tab.setLayout(tabLayout)
        self.tabs.addTab(tab, channel_name)

    def eventFilter(self, obj, event):
        """
        Filtre les événements clavier pour gérer l'envoi de messages.

        Args:
            obj (QObject): L'objet qui a reçu l'événement.
            event (QEvent): L'événement reçu.

        Returns:
            bool: Indique si l'événement a été traité.
        """
        # Filtre les événements pour gérer la saisie du texte et l'envoi de messages
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Return:
            if isinstance(obj, QLineEdit):
                index = self.tabs.currentIndex()
                channel_name = self.tabs.tabText(index)
                self.sendMessage(channel_name, obj.text(), self.textAreas[channel_name], obj)
                return True
        return super(ClientUI, self).eventFilter(obj, event)

    def sendMessage(self, channel_name, message, textArea, inputField):
        """
        Envoie un message au serveur et met à jour l'interface utilisateur.

        Args:
            channel_name (str): Le canal de chat où envoyer le message.
            message (str): Le message à envoyer.
            textArea (QTextEdit): La zone de texte du canal pour afficher le message.
            inputField (QLineEdit): Le champ de saisie pour le message.
        """
        # Envoie un message au serveur et met à jour l'interface utilisateur
        if message:
            formatted_message = f"{channel_name}:{message}"
            self.client_logic.send_messages(formatted_message)
            # Efface le contenu du champ de saisie après l'envoi du message
            inputField.clear()
            

    @pyqtSlot(str)
    def logMessage(self, message):
        """
        Traite et affiche un message reçu du serveur.

        Args:
            message (str): Le message reçu à traiter.
        """
        # Log et affiche les messages reçus du serveur
        try:
            # Obtenez l'heure actuelle pour l'horodatage
            current_time = datetime.datetime.now().strftime("%H:%M")

            # Gère les messages avec les informations d'en-tête et le contenu du message
            parts = message.split(':', 2)
            if len(parts) == 3:
                username, channel, msg = parts
                formatted_message = f"{current_time} - {username}: {msg}"  # Ajoutez l'horodatage ici
                if channel in self.textAreas:
                    self.textAreas[channel].append(formatted_message)

            elif len(parts) == 2:
                # Gère les autres types de messages, comme les messages du serveur
                source_or_channel, msg = parts
                if source_or_channel == "Server":
                    for textArea in self.textAreas.values():
                        textArea.append(f"{current_time} - Server: {msg}")  # Ajoutez l'horodatage aussi pour les messages du serveur
                elif source_or_channel in self.textAreas:
                    self.textAreas[source_or_channel].append(f"{current_time} - Server: {msg}")
                else:
                    print(f"Source ou canal inconnu: {source_or_channel}")
            else:
                print(f"Format de message incorrect: {message}")
        except ValueError:
            print(f"Erreur lors du traitement du message: {message}")

    def connect_client_signals(self):
        """
        Connecte les signaux du client aux slots appropriés pour la gestion des messages.
        """
        # Connecte les signaux du client aux slots appropriés
        self.client_logic.message_received.connect(self.logMessage)
        self.client_logic.formatted_message_received.connect(self.logHistoryMessage)
        self.client_logic.connection_closed.connect(self.close_client)
        
    def close_client(self):
        """
        Ferme l'interface utilisateur du client.
        """
        self.close()  # Ferme la fenêtre principale   
        
     # Traite et affiche les messages historiques reçus du serveur
    @pyqtSlot(str)
    def logHistoryMessage(self, message):
        """
        Traite et affiche les messages historiques reçus du serveur.

        Args:
            message (str): Les messages historiques reçus.
        """
        # Diviser le message en lignes individuelles
        lines = message.split('\n')
        

        for line in lines:
            # Supprimez le préfixe "history" de chaque ligne
            if line.startswith("history"):
                line = line[len("history"):].lstrip()

            try:
                # Vérifiez si la ligne contient les séparateurs attendus
                if " - " in line and ":" in line:
                    time_user, rest = line.split(" - ", 1)
                    username, channel_msg = rest.split(": ", 1)
                    channel, msg = channel_msg.split(":", 1)

                    channel = channel.strip()

                    # Formatez le message
                    formatted_message = f"{time_user} - {username}: {msg}"

                    # Vérifiez si le canal existe dans l'interface utilisateur
                    if channel in self.textAreas:
                        self.textAreas[channel].append(formatted_message)
                    else:
                        print(f"Canal inconnu: {channel}")
                else:
                    print(f"Message non affiché :{message}")
                    continue  # Passez au message suivant en cas de format non reconnu
                
            except ValueError as e:
                print(f"Erreur lors du traitement du message historique: {line}, Erreur: {e}")
                continue  # Passez au message suivant en cas d'erreur

    # Configure le client avec la logique client existante
    def setupClient(self, client):
        """
        Configure le client avec la logique client existante.

        Args:
            client (Client): Le client à configurer.
        """
        self.client_logic = client
        self.client_logic.connection_closed.connect(self.onConnectionClosed)

    @pyqtSlot()
    def onConnectionClosed(self):
        """
        Gère la fermeture de la connexion avec le serveur.
        """
        # Gère la fermeture de la connexion avec le serveur
        QMessageBox.warning(self, "Connexion perdue", "La connexion avec le serveur a été perdue.")
        self.close()  # Ferme la fenêtre