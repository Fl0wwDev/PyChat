import sys
import bcrypt
import mysql.connector
from mysql.connector import Error
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox
from PyQt5.uic import loadUi
from classes.client import ClientUI, Client
from PyQt5.QtWidgets import QApplication, QStackedWidget



class DatabaseManager:
    """
    Gère les interactions avec la base de données MySQL.

    Attributes:
        db_config (dict): Configuration pour la connexion à la base de données MySQL.
    """
    def __init__(self):
        """
        Initialise la configuration de la base de données.
        """
        # Configuration pour la connexion à la base de données MySQL
        self.db_config = {
            "host": "localhost",
            "user": "root",
            "password": "password",
            "database": "SAE"
        }
        
    # Exécute une requête SQL et gère la connexion à la base de données
    def execute_query(self, query, params=None):
        """
        Exécute une requête SQL et gère la connexion à la base de données.

        Args:
            query (str): La requête SQL à exécuter.
            params (tuple, optional): Paramètres à utiliser dans la requête.

        Returns:
            list or None: Résultats de la requête pour les requêtes SELECT, sinon None.
        """
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            connection.commit()
            return None
        except Error as e:
            print(f"Erreur base de données: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                
    # Hash un mot de passe avec bcrypt
    def hash_password(self, password):
        """
        Hash un mot de passe avec bcrypt.

        Args:
            password (str): Le mot de passe à hasher.

        Returns:
            str: Le mot de passe hashé.
        """
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hashed.decode('utf-8')

    # Vérifie si un mot de passe fourni correspond au hash stocké
    def check_password(self, stored_password, provided_password):
        """
        Vérifie si un mot de passe fourni correspond au hash stocké.

        Args:
            stored_password (str): Le mot de passe hashé stocké.
            provided_password (str): Le mot de passe fourni à vérifier.

        Returns:
            bool: True si les mots de passe correspondent, False sinon.
        """
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))


class Login(QDialog):
    """
    Interface utilisateur pour la fenêtre de connexion.

    Attributes:
        stacked_widget (QStackedWidget): Le widget empilé pour la navigation entre les fenêtres.
        client (Client, optional): L'instance client pour la connexion au serveur.
    """
    def __init__(self, stacked_widget):
        """
        Initialise l'interface de connexion.

        Args:
            stacked_widget (QStackedWidget): Widget empilé pour la navigation.
        """
        super(Login, self).__init__()
        # Initialisation de la fenêtre de connexion
        loadUi("SAE/Interfaces/login.ui", self)
        self.stacked_widget = stacked_widget
        self.loginbutton.clicked.connect(self.loginfunction)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.createaccbutton.clicked.connect(self.gotocreate)

        self.errorLabel = QLabel(self)
        self.errorLabel.setGeometry(10, 10, 400, 30)
        self.errorLabel.setStyleSheet("color: red;")

        self.setMinimumSize(439, 454)
        self.client = None
        
    # Gère la tentative de connexion de l'utilisateur    
    def loginfunction(self):
        """
        Gère la tentative de connexion de l'utilisateur.
        """
        self.errorLabel.clear()
        if self.isValidLogin():
            username = self.user.text()
            self.client = Client(username)
            self.client.connection_failed.connect(self.on_connection_failed)
            self.client.connection_success.connect(self.on_connection_success)
            self.client.connect_to_server()
        else:
            self.errorLabel.setText("Nom d'utilisateur ou mot de passe invalide.")

    # Affiche un message d'erreur si la connexion au serveur échoue
    def on_connection_failed(self, error_message):
        """
        Gère l'échec de la connexion.

        Args:
            error_message (str): Le message d'erreur à afficher.
        """
        QMessageBox.critical(self, "Erreur de connexion", error_message)
        self.client = None

        # Traite la connexion réussie et affiche l'interface du client
    def on_connection_success(self):
        """
        Gère une connexion réussie au serveur.
        """
        QMessageBox.information(self, "Connexion Réussie", "Vous êtes connecté(e) au serveur.")
        username = self.user.text()
        client_ui = ClientUI(username)
        client_ui.setupClient(self.client)  # Configure le client et connecte le signal
        client_ui.setGeometry(300, 300, 600, 400)

        # Ajoutez le nouvel écran au QStackedWidget
        self.stacked_widget.addWidget(client_ui)

        # Obtenez l'index du nouvel écran ajouté (qui devrait être le dernier)
        new_screen_index = self.stacked_widget.count() - 1

        # Changez pour le nouvel écran
        self.stacked_widget.setCurrentIndex(new_screen_index)

    # Vérifie si les identifiants de l'utilisateur sont valides
    def isValidLogin(self):
        """
        Vérifie si les identifiants de l'utilisateur sont valides.

        Returns:
            bool: True si les identifiants sont valides, False sinon.
        """
        user = self.user.text()
        password = self.password.text()

        db_manager = DatabaseManager()
        result = db_manager.execute_query("SELECT password FROM user WHERE username = %s", (user,))
        if result:
            stored_password = result[0][0]
            return db_manager.check_password(stored_password, password)
        return False

    # Dirige l'utilisateur vers la fenêtre de création de compte
    def gotocreate(self):
        """
        Dirige l'utilisateur vers la fenêtre de création de compte.
        """
        createacc = CreateAcc()
        createacc.set_stacked_widget(self.stacked_widget)
        self.stacked_widget.addWidget(createacc)
        self.stacked_widget.setCurrentIndex(self.stacked_widget.currentIndex() + 1)
        
class CreateAcc(QDialog):
    """
    Interface utilisateur pour la fenêtre de création de compte.

    Attributes:
        stacked_widget (QStackedWidget): Widget empilé pour la navigation.
    """
    def __init__(self):
        """
        Initialise l'interface de création de compte.
        """
        # Initialisation de la fenêtre de création de compte
        super(CreateAcc, self).__init__()
        loadUi("SAE/Interfaces/createacc.ui", self)
        self.signupbutton.clicked.connect(self.createaccfunction)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirmpass.setEchoMode(QtWidgets.QLineEdit.Password)
        
    # Gère la création du compte utilisateur
    def createaccfunction(self):
        """
        Gère la création du compte utilisateur.
        """
        username = self.username.text()
        password = self.password.text()
        confirm_password = self.confirmpass.text()

        if not self.validate_credentials(username, password, confirm_password):
            return

        db_manager = DatabaseManager()
        hashed_password = db_manager.hash_password(password)
        try:
            db_manager.execute_query("INSERT INTO user (username, password) VALUES (%s, %s)", (username, hashed_password))
            print("Compte créé avec succès avec l'username:", username)
            QMessageBox.information(self, "Succès", "Compte créé avec succès.")
            self.go_to_login()
        except Exception as e:
            print("Error:", str(e))

    # Ramène l'utilisateur à l'écran de connexion
    def go_to_login(self):
        """
        Ramène l'utilisateur à l'écran de connexion.
        """
        index_of_login_screen = None
        for index in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(index)
            if isinstance(widget, Login):
                index_of_login_screen = index
                break

        if index_of_login_screen is not None:
            # Redirige vers l'écran de connexion
            self.stacked_widget.setCurrentIndex(index_of_login_screen)
        else:
            # Gère le cas où la fenêtre de connexion n'est pas trouvée
            print("Erreur: Fenêtre de connexion introuvable.")
            # Vous pouvez choisir de fermer la fenêtre actuelle ou de gérer cette situation différemment
            self.close()

        # Ferme la fenêtre actuelle de création de compte
        self.close()
        
    # Configure le widget empilé pour la navigation
    def set_stacked_widget(self, stacked_widget):
        """
        Configure le widget empilé pour la navigation.

        Args:
            stacked_widget (QStackedWidget): Le widget empilé à configurer.
        """
        self.stacked_widget = stacked_widget
        
    # Valide les informations d'inscription fournies par l'utilisateur
    def validate_credentials(self, username, password, confirm_password):
        """
        Valide les informations d'inscription fournies par l'utilisateur.

        Args:
            username (str): Nom d'utilisateur à valider.
            password (str): Mot de passe à valider.
            confirm_password (str): Confirmation du mot de passe.

        Returns:
            bool: True si les informations sont valides, False sinon.
        """
        
        # Vérifier si le nom d'utilisateur existe déjà
        if self.username_exists(username):
            QMessageBox.warning(self, "Erreur d'inscription", "Ce nom d'utilisateur est déjà pris.")
            return False

        if len(username) < 4:
            QMessageBox.warning(self, "Erreur d'inscription", "Le nom d'utilisateur est trop court (minimum 4 caractères).")
            return False
        if len(username) > 20:
            QMessageBox.warning(self, "Erreur d'inscription", "Le nom d'utilisateur est trop long (maximum 20 caractères).")
            return False

        if len(password) < 6:
            QMessageBox.warning(self, "Erreur d'inscription", "Le mot de passe est trop court (minimum 6 caractères).")
            return False
        if len(password) > 24:
            QMessageBox.warning(self, "Erreur d'inscription", "Le mot de passe est trop long (maximum 24 caractères).")
            return False
        if not any(char.isdigit() for char in password):
            QMessageBox.warning(self, "Erreur d'inscription", "Le mot de passe doit contenir au moins un chiffre.")
            return False
        if not any(char.islower() for char in password):
            QMessageBox.warning(self, "Erreur d'inscription", "Le mot de passe doit contenir au moins une lettre minuscule.")
            return False
        if not any(char.isupper() for char in password):
            QMessageBox.warning(self, "Erreur d'inscription", "Le mot de passe doit contenir au moins une lettre majuscule.")
            return False
        if not any(not char.isalnum() for char in password):
            QMessageBox.warning(self, "Erreur d'inscription", "Le mot de passe doit contenir au moins un caractère spécial.")
            return False
        if password != confirm_password:
            QMessageBox.warning(self, "Erreur d'inscription", "Les mots de passe ne correspondent pas.")
            return False

        return True
    
    # Vérifie si le nom d'utilisateur existe déjà dans la base de données
    def username_exists(self, username):
        """
        Vérifie si le nom d'utilisateur existe déjà dans la base de données.

        Args:
            username (str): Nom d'utilisateur à vérifier.

        Returns:
            bool: True si le nom d'utilisateur existe, False sinon.
        """
        db_manager = DatabaseManager()
        result = db_manager.execute_query("SELECT COUNT(*) FROM user WHERE LOWER(username) = LOWER(%s)", (username,))
        if result and result[0][0] > 0:
            return True
        return False
